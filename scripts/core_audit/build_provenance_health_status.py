#!/usr/bin/env python3
"""
Build canonical historical provenance-health status artifact for SK-M4.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m4_provenance_policy.json"
DEFAULT_DB_PATH = PROJECT_ROOT / "data/voynich.db"
DEFAULT_REPAIR_REPORT_PATH = PROJECT_ROOT / "core_status/core_audit/run_status_repair_report.json"
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_health_status.json"
DEFAULT_GATE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/release_gate_health_status.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_policy_thresholds(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = _load_json(path)
    except json.JSONDecodeError:
        return {}
    return dict(payload.get("threshold_policy", {}))


def _load_gate_health(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = _load_json(path)
    except json.JSONDecodeError:
        return {}
    if isinstance(payload.get("results"), dict):
        return dict(payload["results"])
    return payload if isinstance(payload, dict) else {}


def _collect_db_status_counts(db_path: Path) -> Dict[str, int]:
    if not db_path.exists():
        raise FileNotFoundError(f"Missing DB file: {db_path}")
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "select status, count(*) from runs group by status order by status"
        ).fetchall()
        return {str(status): int(count) for status, count in rows}
    finally:
        con.close()


def _collect_manifest_health(db_path: Path, runs_root: Path) -> Dict[str, int]:
    con = sqlite3.connect(db_path)
    try:
        run_ids = [str(row[0]) for row in con.execute("select id from runs").fetchall()]
    finally:
        con.close()

    missing_manifests = 0
    backfilled_manifests = 0
    for run_id in run_ids:
        manifest = runs_root / run_id / "run.json"
        if not manifest.exists():
            missing_manifests += 1
            continue
        try:
            payload = _load_json(manifest)
        except json.JSONDecodeError:
            continue
        if payload.get("manifest_backfilled") is True:
            backfilled_manifests += 1

    return {
        "missing_manifests": missing_manifests,
        "backfilled_manifests": backfilled_manifests,
    }


def _recoverability_class(
    *, orphaned_rows: int, missing_manifests: int, backfilled_manifests: int
) -> str:
    if missing_manifests > 0:
        return "RECOVERABLE_MISSING_MANIFESTS"
    if orphaned_rows > 0 and backfilled_manifests >= orphaned_rows:
        return "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED"
    if orphaned_rows > 0:
        return "HISTORICAL_ORPHANED_UNBACKFILLED"
    return "NO_HISTORICAL_GAPS"


def _derive_m4_5_lane(
    *,
    status: str,
    recoverability_class: str,
) -> tuple[str, str, list[str]]:
    if status == "PROVENANCE_ALIGNED":
        return (
            "M4_5_ALIGNED",
            "no_historical_residual",
            [
                "Downgrade lane if provenance thresholds fail or drift is detected.",
                "Downgrade lane if gate-coupled contract checks fail.",
            ],
        )

    if status == "PROVENANCE_QUALIFIED":
        if recoverability_class in {
            "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
            "HISTORICAL_ORPHANED_UNBACKFILLED",
        }:
            return (
                "M4_5_BOUNDED",
                "historical_orphaned_rows_irrecoverable_with_current_source_scope",
                [
                    "Promote only if orphaned historical rows are eliminated under canonical thresholds.",
                    "Reopen if register sync reports drift_detected=true.",
                    "Reopen if provenance contract coupling with gate health fails.",
                    "Reopen if new primary source evidence changes irrecoverability classification.",
                ],
            )
        return (
            "M4_5_QUALIFIED",
            "qualified_provenance_with_recoverable_components",
            [
                "Promote only when recoverable provenance gaps are remediated and thresholds pass.",
                "Reopen if artifact freshness or parity checks fail.",
            ],
        )

    if status == "PROVENANCE_BLOCKED":
        return (
            "M4_5_BLOCKED",
            "provenance_threshold_or_contract_blocked",
            [
                "Reopen after threshold-policy and contract-coupling violations are remediated.",
            ],
        )

    return (
        "M4_5_INCONCLUSIVE",
        "insufficient_provenance_scope",
        [
            "Reopen after sufficient historical provenance evidence is available for lane assignment.",
        ],
    )


def _derive_m4_5_data_availability_linkage(
    *,
    recoverability_class: str,
    status: str,
) -> Dict[str, Any]:
    approved_irrecoverable = recoverability_class in {
        "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
        "HISTORICAL_ORPHANED_UNBACKFILLED",
    }
    blocker_classification = "NO_BLOCKING_CLAIM"
    if approved_irrecoverable and status == "PROVENANCE_QUALIFIED":
        blocker_classification = "NON_BLOCKING_APPROVED_IRRECOVERABLE_LOSS"
    elif status == "PROVENANCE_BLOCKED":
        blocker_classification = "THRESHOLD_OR_CONTRACT_BLOCKED"
    return {
        "missing_folio_blocking_claimed": False,
        "objective_provenance_contract_incompleteness": False,
        "approved_irrecoverable_loss_classification": approved_irrecoverable,
        "blocker_classification": blocker_classification,
    }


def _m4_4_lane_from_m4_5(lane: str) -> str:
    return lane.replace("M4_5_", "M4_4_", 1) if lane.startswith("M4_5_") else "M4_4_INCONCLUSIVE"


def _derive_m4_4_lane(
    *,
    status: str,
    recoverability_class: str,
) -> tuple[str, str, list[str]]:
    if status == "PROVENANCE_ALIGNED":
        return (
            "M4_4_ALIGNED",
            "no_historical_residual",
            [
                "Downgrade lane if provenance thresholds fail or drift is detected.",
                "Downgrade lane if gate-coupled contract checks fail.",
            ],
        )

    if status == "PROVENANCE_QUALIFIED":
        if recoverability_class in {
            "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
            "HISTORICAL_ORPHANED_UNBACKFILLED",
        }:
            return (
                "M4_4_BOUNDED",
                "historical_orphaned_rows_irrecoverable_with_current_source_scope",
                [
                    "Promote only if orphaned historical rows are eliminated under canonical thresholds.",
                    "Reopen if register sync reports drift_detected=true.",
                    "Reopen if provenance contract coupling with gate health fails.",
                ],
            )
        return (
            "M4_4_QUALIFIED",
            "qualified_provenance_with_recoverable_components",
            [
                "Promote only when recoverable provenance gaps are remediated and thresholds pass.",
                "Reopen if artifact freshness or parity checks fail.",
            ],
        )

    if status == "PROVENANCE_BLOCKED":
        return (
            "M4_4_BLOCKED",
            "provenance_threshold_or_contract_blocked",
            [
                "Reopen after threshold-policy and contract-coupling violations are remediated.",
            ],
        )

    return (
        "M4_4_INCONCLUSIVE",
        "insufficient_provenance_scope",
        [
            "Reopen after sufficient historical provenance evidence is available for lane assignment.",
        ],
    )


def _determine_status(
    *,
    total_runs: int,
    orphaned_rows: int,
    orphaned_ratio: float,
    running_rows: int,
    missing_manifests: int,
    backfilled_manifests: int,
    thresholds: Dict[str, Any],
    gate_health_status: str,
    gate_health_reason_code: str,
) -> Dict[str, Any]:
    orphaned_ratio_max = float(thresholds.get("orphaned_ratio_max", 1.0))
    orphaned_count_max = int(thresholds.get("orphaned_count_max", 10**9))
    running_count_max = int(thresholds.get("running_count_max", 0))
    missing_manifests_max = int(thresholds.get("missing_manifests_max", 0))

    failures = []
    if running_rows > running_count_max:
        failures.append("RUNNING_ROWS_EXCEED_THRESHOLD")
    if missing_manifests > missing_manifests_max:
        failures.append("MISSING_MANIFESTS_EXCEED_THRESHOLD")
    if orphaned_rows > orphaned_count_max:
        failures.append("ORPHANED_COUNT_EXCEED_THRESHOLD")
    if orphaned_ratio > orphaned_ratio_max:
        failures.append("ORPHANED_RATIO_EXCEED_THRESHOLD")

    threshold_policy_pass = len(failures) == 0

    if total_runs == 0:
        status = "INCONCLUSIVE_PROVENANCE_SCOPE"
        reason_code = "NO_RUN_ROWS"
        allowed_claim = "Historical provenance confidence is provisional due missing run history."
    elif not threshold_policy_pass:
        status = "PROVENANCE_BLOCKED"
        reason_code = "THRESHOLD_POLICY_FAILED"
        allowed_claim = (
            "Historical provenance confidence is blocked until threshold violations are remediated."
        )
    elif orphaned_rows > 0 or backfilled_manifests > 0:
        status = "PROVENANCE_QUALIFIED"
        if orphaned_rows > 0:
            reason_code = "HISTORICAL_ORPHANED_ROWS_PRESENT"
        else:
            reason_code = "BACKFILLED_MANIFESTS_PRESENT"
        allowed_claim = (
            "Historical provenance is qualified: uncertainty is explicitly bounded and tracked."
        )
    else:
        status = "PROVENANCE_ALIGNED"
        reason_code = "NO_HISTORICAL_GAPS_DETECTED"
        allowed_claim = "Historical provenance is aligned under current policy thresholds."

    contract_reason_codes: list[str] = []
    if gate_health_status == "GATE_HEALTH_DEGRADED":
        contract_reason_codes.append("PROVENANCE_CONTRACT_BLOCKED")
        if status == "PROVENANCE_ALIGNED":
            status = "PROVENANCE_QUALIFIED"
            reason_code = "PROVENANCE_CONTRACT_BLOCKED"
            allowed_claim = (
                "Historical provenance is qualified while operational gate health remains degraded."
            )

    contract_coupling_pass = not (
        gate_health_status == "GATE_HEALTH_DEGRADED" and status == "PROVENANCE_ALIGNED"
    )

    return {
        "status": status,
        "reason_code": reason_code,
        "allowed_claim": allowed_claim,
        "threshold_policy_pass": threshold_policy_pass,
        "threshold_failures": failures,
        "contract_health_status": gate_health_status or "UNKNOWN",
        "contract_health_reason_code": gate_health_reason_code or "UNKNOWN",
        "contract_reason_codes": contract_reason_codes,
        "contract_coupling_pass": contract_coupling_pass,
    }


def build_provenance_health_status(
    *,
    db_path: Path,
    repair_report_path: Path,
    output_path: Path,
    policy_path: Path,
    gate_health_path: Path,
) -> Dict[str, Any]:
    thresholds = _load_policy_thresholds(policy_path)
    gate_health = _load_gate_health(gate_health_path)
    gate_health_status = str(gate_health.get("status", "UNKNOWN"))
    gate_health_reason_code = str(gate_health.get("reason_code", "UNKNOWN"))
    status_counts = _collect_db_status_counts(db_path)
    total_runs = int(sum(status_counts.values()))
    orphaned_rows = int(status_counts.get("orphaned", 0))
    running_rows = int(status_counts.get("running", 0))
    orphaned_ratio = float(orphaned_rows / total_runs) if total_runs > 0 else 0.0

    manifest_stats = _collect_manifest_health(db_path, PROJECT_ROOT / "runs")
    missing_manifests = int(manifest_stats["missing_manifests"])
    backfilled_manifests = int(manifest_stats["backfilled_manifests"])
    recoverability_class = _recoverability_class(
        orphaned_rows=orphaned_rows,
        missing_manifests=missing_manifests,
        backfilled_manifests=backfilled_manifests,
    )

    repair_summary: Dict[str, Any] = {}
    if repair_report_path.exists():
        try:
            repair_summary = _load_json(repair_report_path)
        except json.JSONDecodeError:
            repair_summary = {}

    status_meta = _determine_status(
        total_runs=total_runs,
        orphaned_rows=orphaned_rows,
        orphaned_ratio=orphaned_ratio,
        running_rows=running_rows,
        missing_manifests=missing_manifests,
        backfilled_manifests=backfilled_manifests,
        thresholds=thresholds,
        gate_health_status=gate_health_status,
        gate_health_reason_code=gate_health_reason_code,
    )
    (
        m4_5_historical_lane,
        m4_5_residual_reason,
        m4_5_reopen_conditions,
    ) = _derive_m4_5_lane(
        status=str(status_meta["status"]),
        recoverability_class=recoverability_class,
    )
    m4_4_historical_lane = _m4_4_lane_from_m4_5(m4_5_historical_lane)
    m4_4_residual_reason = m4_5_residual_reason
    m4_4_reopen_conditions = list(m4_5_reopen_conditions)
    m4_5_data_availability_linkage = _derive_m4_5_data_availability_linkage(
        recoverability_class=recoverability_class,
        status=str(status_meta["status"]),
    )

    generated_utc = _utc_now_iso()
    payload: Dict[str, Any] = {
        "version": "2026-02-10-m4.5",
        "status": status_meta["status"],
        "reason_code": status_meta["reason_code"],
        "allowed_claim": status_meta["allowed_claim"],
        "generated_utc": generated_utc,
        "last_reviewed": generated_utc[:10],
        "status_source": [
            str(db_path.relative_to(PROJECT_ROOT)),
            str(repair_report_path.relative_to(PROJECT_ROOT)),
            str(policy_path.relative_to(PROJECT_ROOT)),
            str(gate_health_path.relative_to(PROJECT_ROOT)),
        ],
        "total_runs": total_runs,
        "run_status_counts": status_counts,
        "orphaned_rows": orphaned_rows,
        "orphaned_ratio": round(orphaned_ratio, 6),
        "running_rows": running_rows,
        "missing_manifests": missing_manifests,
        "backfilled_manifests": backfilled_manifests,
        "recoverability_class": recoverability_class,
        "m4_5_historical_lane": m4_5_historical_lane,
        "m4_5_residual_reason": m4_5_residual_reason,
        "m4_5_reopen_conditions": m4_5_reopen_conditions,
        "m4_5_data_availability_linkage": m4_5_data_availability_linkage,
        "m4_4_historical_lane": m4_4_historical_lane,
        "m4_4_residual_reason": m4_4_residual_reason,
        "m4_4_reopen_conditions": m4_4_reopen_conditions,
        "repair_report_summary": {
            "path": str(repair_report_path.relative_to(PROJECT_ROOT)),
            "report_generated_utc": repair_summary.get("report_generated_utc"),
            "scanned": repair_summary.get("scanned"),
            "updated": repair_summary.get("updated"),
            "reconciled": repair_summary.get("reconciled"),
            "orphaned": repair_summary.get("orphaned"),
            "missing_manifests": repair_summary.get("missing_manifests"),
            "backfilled_manifests": repair_summary.get("backfilled_manifests"),
        },
        "thresholds": {
            "orphaned_ratio_max": float(thresholds.get("orphaned_ratio_max", 1.0)),
            "orphaned_count_max": int(thresholds.get("orphaned_count_max", 10**9)),
            "running_count_max": int(thresholds.get("running_count_max", 0)),
            "missing_manifests_max": int(thresholds.get("missing_manifests_max", 0)),
            "max_artifact_age_hours": int(thresholds.get("max_artifact_age_hours", 168)),
        },
        "threshold_policy_pass": bool(status_meta["threshold_policy_pass"]),
        "threshold_failures": list(status_meta["threshold_failures"]),
        "contract_health_status": status_meta["contract_health_status"],
        "contract_health_reason_code": status_meta["contract_health_reason_code"],
        "contract_reason_codes": list(status_meta["contract_reason_codes"]),
        "contract_coupling_pass": bool(status_meta["contract_coupling_pass"]),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build canonical historical provenance-health status artifact."
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="Path to metadata DB (default: data/voynich.db).",
    )
    parser.add_argument(
        "--repair-report-path",
        default=str(DEFAULT_REPAIR_REPORT_PATH),
        help="Path to run status repair summary JSON.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output path for provenance health artifact.",
    )
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-M4 policy JSON for threshold defaults.",
    )
    parser.add_argument(
        "--gate-health-path",
        default=str(DEFAULT_GATE_HEALTH_PATH),
        help="Path to release gate-health artifact for contract coupling.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    result = build_provenance_health_status(
        db_path=Path(args.db_path).resolve(),
        repair_report_path=Path(args.repair_report_path).resolve(),
        output_path=Path(args.output).resolve(),
        policy_path=Path(args.policy_path).resolve(),
        gate_health_path=Path(args.gate_health_path).resolve(),
    )
    print(
        "status={status} reason_code={reason_code} lane={m4_5_historical_lane} "
        "total_runs={total_runs} orphaned_rows={orphaned_rows} "
        "running_rows={running_rows}".format(**result)
    )
