#!/usr/bin/env python3
"""
Build canonical historical provenance-health status artifact for SK-M4.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_health_status.json"
DEFAULT_BY_RUN_DIR = PROJECT_ROOT / "core_status/core_audit/by_run"
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m4_provenance_policy.json"
DEFAULT_GATE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/release_gate_health_status.json"
DEFAULT_REPAIR_REPORT_PATH = PROJECT_ROOT / "core_status/core_audit/run_status_repair_report.json"
DEFAULT_DB_PATH = PROJECT_ROOT / "data/voynich.db"
DEFAULT_RUNS_ROOT = PROJECT_ROOT / "runs"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")  # noqa: UP017


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_policy_thresholds(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = _load_json(path)
    return payload.get("threshold_policy", {})


def _load_gate_health(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = _load_json(path)
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _collect_db_status_counts(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {}
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "select status, count(*) from runs group by status order by status"
        ).fetchall()
        return {str(status): int(count) for status, count in rows}
    finally:
        con.close()


def _collect_manifest_health(db_path: Path, runs_root: Path) -> dict[str, int]:
    if not db_path.exists():
        return {
            "missing_manifests": 0,
            "backfilled_manifests": 0,
        }
    con = sqlite3.connect(db_path)
    try:
        run_ids = [str(row[0]) for row in con.execute("select id from runs").fetchall()]
    finally:
        con.close()

    missing = 0
    backfilled = 0
    for run_id in run_ids:
        manifest_path = runs_root / run_id / "manifest.json"
        if not manifest_path.exists():
            missing += 1
        elif ".backfilled." in manifest_path.read_text(encoding="utf-8"):
            backfilled += 1
    return {
        "missing_manifests": missing,
        "backfilled_manifests": backfilled,
    }


def _derive_historical_lane(
    *,
    orphaned_rows: int,
    missing_manifests: int,
    backfilled_manifests: int,
    status: str,
) -> tuple[str, str, list[str]]:
    if missing_manifests > 0:
        return (
            "M4_5_BLOCKED",
            "missing_run_manifests_detected",
            [
                "Restore missing run manifests from deep-archive storage.",
                "Backfill provenance metadata from recovered artifacts.",
            ],
        )

    if orphaned_rows > 0:
        if backfilled_manifests >= orphaned_rows:
            return (
                "M4_5_QUALIFIED",
                "historical_orphaned_rows_backfilled_qualified",
                [
                    "Audit backfilled manifest integrity against primary source logs.",
                    "Verify drift_detected=false in SK-M4 register sync.",
                ],
            )

        if status == "PROVENANCE_QUALIFIED":
            return (
                "M4_5_QUALIFIED",
                "historical_orphaned_rows_within_threshold",
                [
                    "Promote only if orphaned historical rows are eliminated "
                    "under canonical thresholds.",
                    "Verify drift_detected=false in SK-M4 register sync.",
                ],
            )

        return (
            "M4_5_BLOCKED",
            "historical_orphaned_rows_irrecoverable_with_current_source_scope",
            [
                "Promote only if orphaned historical rows are eliminated "
                "under canonical thresholds.",
                "Reopen if register sync reports drift_detected=true.",
                "Reopen if provenance contract coupling with gate health fails.",
                "Reopen if new primary source evidence changes "
                "irrecoverability classification.",
            ],
        )

    return (
        "M4_5_ALIGNED",
        "no_historical_provenance_gaps",
        [
            "Maintain deterministic replication cycle.",
            "Reopen if orphaned rows are introduced in future production runs.",
        ],
    )


def _inconclusive_lane() -> tuple[str, str, list[str]]:
    return (
        "M4_5_INCONCLUSIVE",
        "insufficient_provenance_scope",
        [
            "Reopen after sufficient historical provenance evidence is "
            "available for lane assignment.",
        ],
    )


def _allowed_claim_meta(
    *,
    recoverability_class: str,
    status: str,
) -> dict[str, Any]:
    approved_irrecoverable = recoverability_class in {
        "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
        "HISTORICAL_ORPHANED_WITHIN_THRESHOLD",
        "NO_HISTORICAL_GAPS",
    }
    if status == "PROVENANCE_ALIGNED":
        return {
            "allowed_claim": "UNRESTRICTED_FRAMEWORK_CONFIDENCE",
            "allowed_closure": "FULL_CLOSURE_ALIGNED",
        }
    if status == "PROVENANCE_QUALIFIED" and approved_irrecoverable:
        return {
            "allowed_claim": "QUALIFIED_FRAMEWORK_CONFIDENCE",
            "allowed_closure": "CONDITIONAL_CLOSURE_QUALIFIED",
        }
    return {
        "allowed_claim": "INCONCLUSIVE_PROVENANCE_REQUIRING_DISCLAIMER",
        "allowed_closure": "UNSAFE_FOR_CLOSURE",
    }


def _m4_4_historical_lane(
    *,
    orphaned_rows: int,
    missing_manifests: int,
    backfilled_manifests: int,
    status: str,
) -> tuple[str, str, list[str]]:
    if missing_manifests > 0:
        return (
            "M4_4_BLOCKED",
            "missing_run_manifests_detected",
            [
                "Restore missing run manifests from deep-archive storage.",
            ],
        )

    if orphaned_rows > 0:
        if backfilled_manifests >= orphaned_rows:
            return (
                "M4_4_QUALIFIED",
                "historical_orphaned_rows_backfilled_qualified",
                [
                    "Audit backfilled manifest integrity against primary source logs.",
                ],
            )

        if status == "PROVENANCE_QUALIFIED":
            return (
                "M4_4_QUALIFIED",
                "historical_orphaned_rows_within_threshold",
                [],
            )

        return (
            "M4_4_BLOCKED",
            "historical_orphaned_rows_irrecoverable_with_current_source_scope",
            [
                "Promote only if orphaned historical rows are eliminated "
                "under canonical thresholds.",
                "Reopen if register sync reports drift_detected=true.",
                "Reopen if provenance contract coupling with gate health fails.",
            ],
        )

    return (
        "M4_4_ALIGNED",
        "no_historical_provenance_gaps",
        [],
    )


def _m4_4_inconclusive_lane() -> tuple[str, str, list[str]]:
    return (
        "M4_4_INCONCLUSIVE",
        "insufficient_provenance_scope",
        [
            "Reopen after sufficient historical provenance evidence is "
            "available for lane assignment.",
        ],
    )


def _evaluate_thresholds(
    *,
    orphaned_rows: int,
    total_runs: int,
    missing_manifests: int,
    backfilled_manifests: int,
    thresholds: dict[str, Any],
    gate_health_status: str,
    gate_health_reason_code: str,
) -> dict[str, Any]:
    orphaned_ratio_max = float(thresholds.get("orphaned_ratio_max", 1.0))
    orphaned_count_max = int(thresholds.get("orphaned_count_max", 10**9))
    missing_manifests_max = int(thresholds.get("missing_manifests_max", 0))

    orphaned_ratio = orphaned_rows / total_runs if total_runs > 0 else 0.0
    ratio_pass = orphaned_ratio <= orphaned_ratio_max
    count_pass = orphaned_rows <= orphaned_count_max
    manifest_pass = missing_manifests <= missing_manifests_max

    threshold_pass = ratio_pass and count_pass and manifest_pass

    # SK-M4.5 contract coupling requirements
    contract_coupling_pass = True
    contract_reason_codes = []
    if gate_health_status == "GATE_HEALTH_DEGRADED":
        if gate_health_reason_code == "GATE_CONTRACT_BLOCKED":
            contract_reason_codes.append("PROVENANCE_CONTRACT_BLOCKED")
        else:
            contract_coupling_pass = False

    if total_runs == 0:
        status = "INCONCLUSIVE_PROVENANCE_SCOPE"
        reason_code = "NO_RUN_ROWS"
    elif threshold_pass and contract_coupling_pass:
        if orphaned_rows == 0:
            status = "PROVENANCE_ALIGNED"
            reason_code = "THRESHOLD_POLICY_PASSED_ZERO_ORPHANS"
        else:
            status = "PROVENANCE_QUALIFIED"
            reason_code = "THRESHOLD_POLICY_PASSED_WITH_ORPHANS"
    else:
        status = "PROVENANCE_BLOCKED"
        reason_code = "THRESHOLD_OR_CONTRACT_FAILED"

    return {
        "status": status,
        "reason_code": reason_code,
        "threshold_policy_pass": threshold_pass,
        "contract_coupling_pass": contract_coupling_pass,
        "contract_reason_codes": contract_reason_codes,
        "orphaned_ratio": orphaned_ratio,
    }


def build_provenance_health_status(
    *,
    output_path: Path,
    by_run_dir: Path,
    db_path: Path,
    runs_root: Path,
    policy_path: Path,
    gate_health_path: Path,
    repair_report_path: Path,
) -> dict[str, Any]:
    run_id = str(sqlite3.connect(":memory:").execute("select hex(randomblob(16))").fetchone()[0])
    db_counts = _collect_db_status_counts(db_path)
    manifest_health = _collect_manifest_health(db_path, runs_root)
    thresholds = _load_policy_thresholds(policy_path)
    gate_health = _load_gate_health(gate_health_path)

    orphaned_rows = db_counts.get("orphaned", 0)
    total_runs = sum(db_counts.values())
    missing_manifests = manifest_health["missing_manifests"]
    backfilled_manifests = manifest_health["backfilled_manifests"]

    status_meta = _evaluate_thresholds(
        orphaned_rows=orphaned_rows,
        total_runs=total_runs,
        missing_manifests=missing_manifests,
        backfilled_manifests=backfilled_manifests,
        thresholds=thresholds,
        gate_health_status=gate_health.get("status", "UNKNOWN"),
        gate_health_reason_code=gate_health.get("reason_code", "UNKNOWN"),
    )

    if total_runs > 0:
        m4_5_lane, m4_5_reason, m4_5_reopen = _derive_historical_lane(
            orphaned_rows=orphaned_rows,
            missing_manifests=missing_manifests,
            backfilled_manifests=backfilled_manifests,
            status=status_meta["status"],
        )
        m4_4_lane, m4_4_reason, m4_4_reopen = _m4_4_historical_lane(
            orphaned_rows=orphaned_rows,
            missing_manifests=missing_manifests,
            backfilled_manifests=backfilled_manifests,
            status=status_meta["status"],
        )
    else:
        m4_5_lane, m4_5_reason, m4_5_reopen = _inconclusive_lane()
        m4_4_lane, m4_4_reason, m4_4_reopen = _m4_4_inconclusive_lane()

    recoverability_class = m4_5_reason.upper()

    claim_meta = _allowed_claim_meta(
        recoverability_class=recoverability_class,
        status=status_meta["status"],
    )

    repair_summary: dict[str, Any] = {}
    if repair_report_path.exists():
        with contextlib.suppress(json.JSONDecodeError):
            repair_summary = _load_json(repair_report_path)

    generated_utc = _utc_now_iso()
    payload: dict[str, Any] = {
        "version": "2026-02-10-m4.5",
        "status": status_meta["status"],
        "reason_code": status_meta["reason_code"],
        "total_runs": total_runs,
        "orphaned_rows": orphaned_rows,
        "orphaned_ratio": status_meta["orphaned_ratio"],
        "running_rows": db_counts.get("running", 0),
        "missing_manifests": missing_manifests,
        "backfilled_manifests": backfilled_manifests,
        "threshold_policy_pass": status_meta["threshold_policy_pass"],
        "contract_coupling_pass": status_meta["contract_coupling_pass"],
        "contract_reason_codes": status_meta["contract_reason_codes"],
        "generated_utc": generated_utc,
        "last_reviewed": generated_utc,
        "recoverability_class": recoverability_class,
        "m4_5_historical_lane": m4_5_lane,
        "m4_5_residual_reason": m4_5_reason,
        "m4_5_reopen_conditions": m4_5_reopen,
        "m4_5_data_availability_linkage": {
            "missing_folio_blocking_claimed": False,
            "objective_provenance_contract_incompleteness": False,
            "approved_irrecoverable_loss_classification": False,
        },
        "m4_4_historical_lane": m4_4_lane,
        "m4_4_residual_reason": m4_4_reason,
        "m4_4_reopen_conditions": m4_4_reopen,
        "allowed_claim": claim_meta["allowed_claim"],
        "allowed_closure": claim_meta["allowed_closure"],
        "run_status_counts": db_counts,
        "repair_summary": repair_summary,
        "contract_health_status": gate_health.get("status"),
        "contract_health_reason_code": gate_health.get("reason_code"),
    }

    results_payload = {
        "provenance": {
            "run_id": run_id,
            "timestamp": generated_utc,
            "command": "build_provenance_health_status",
        },
        "results": payload,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results_payload, indent=2) + "\n", encoding="utf-8")

    by_run_dir.mkdir(parents=True, exist_ok=True)
    by_run_path = by_run_dir / f"provenance_health_status.{run_id}.json"
    by_run_path.write_text(json.dumps(results_payload, indent=2) + "\n", encoding="utf-8")

    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build canonical historical provenance-health status artifact."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_PATH),
        help="Output path for provenance health artifact.",
    )
    parser.add_argument(
        "--by-run-dir",
        default=str(DEFAULT_BY_RUN_DIR),
        help="Directory for run-scoped provenance health artifacts.",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="Path to metadata DB.",
    )
    parser.add_argument(
        "--runs-root",
        default=str(DEFAULT_RUNS_ROOT),
        help="Root directory for run artifacts.",
    )
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-M4 provenance policy.",
    )
    parser.add_argument(
        "--gate-health-path",
        default=str(DEFAULT_GATE_HEALTH_PATH),
        help="Path to release gate-health artifact.",
    )
    parser.add_argument(
        "--repair-report-path",
        default=str(DEFAULT_REPAIR_REPORT_PATH),
        help="Path to repair summary artifact.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    res = build_provenance_health_status(
        output_path=Path(args.output).resolve(),
        by_run_dir=Path(args.by_run_dir).resolve(),
        db_path=Path(args.db_path).resolve(),
        runs_root=Path(args.runs_root).resolve(),
        policy_path=Path(args.policy_path).resolve(),
        gate_health_path=Path(args.gate_health_path).resolve(),
        repair_report_path=Path(args.repair_report_path).resolve(),
    )
    print(
        "status={status} reason_code={reason_code} lane={m4_5_historical_lane} "
        "total_runs={total_runs} orphaned_rows={orphaned_rows} "
        "running_rows={running_rows}".format(
            **res
        )
    )
