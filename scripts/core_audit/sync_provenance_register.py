#!/usr/bin/env python3
"""
Synchronize SK-M4 provenance register from canonical status artifacts.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_PROVENANCE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_health_status.json"
DEFAULT_GATE_HEALTH_PATH = PROJECT_ROOT / "core_status/core_audit/release_gate_health_status.json"
DEFAULT_REPAIR_REPORT_PATH = PROJECT_ROOT / "core_status/core_audit/run_status_repair_report.json"
DEFAULT_DB_PATH = PROJECT_ROOT / "data/voynich.db"
DEFAULT_REGISTER_PATH = PROJECT_ROOT / "results/reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md"
DEFAULT_SYNC_STATUS_PATH = PROJECT_ROOT / "core_status/core_audit/provenance_register_sync_status.json"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if isinstance(payload, dict):
        return payload
    return {}


def _as_results(payload: dict[str, Any]) -> dict[str, Any]:
    results = payload.get("results")
    if isinstance(results, dict):
        return results
    return payload


def _db_status_counts(db_path: Path) -> dict[str, int]:
    if not db_path.exists():
        return {}
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "select status, count(*) from runs group by status order by status"
        ).fetchall()
    finally:
        con.close()
    return {str(status): int(count) for status, count in rows}


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


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def _render_register_markdown(
    *,
    generated_utc: str,
    provenance_health_path: Path,
    repair_report_path: Path,
    gate_health_path: Path,
    sync_status_path: Path,
    provenance: dict[str, Any],
    gate: dict[str, Any],
    repair: dict[str, Any],
    db_counts: dict[str, int],
    drift_by_status: dict[str, int],
    drift_detected: bool,
    recoverability_class: str,
) -> str:
    provenance_generated_utc = str(provenance.get("generated_utc", "unknown"))
    gate_status = str(gate.get("status", "UNKNOWN"))
    gate_reason_code = str(gate.get("reason_code", "UNKNOWN"))
    allowed_claim_class = str(gate.get("allowed_claim_class", "UNKNOWN"))
    m4_5_lane = str(
        provenance.get("m4_5_historical_lane")
        or provenance.get("m4_4_historical_lane")
        or "M4_5_INCONCLUSIVE"
    )
    m4_5_residual_reason = str(
        provenance.get("m4_5_residual_reason")
        or provenance.get("m4_4_residual_reason")
        or "unknown"
    )

    artifact_counts = provenance.get("run_status_counts", {})
    if not isinstance(artifact_counts, dict):
        artifact_counts = {}

    status_keys = sorted(set(db_counts.keys()) | set(artifact_counts.keys()))
    count_rows = []
    for key in status_keys:
        artifact_count = int(artifact_counts.get(key, 0))
        db_count = int(db_counts.get(key, 0))
        delta = db_count - artifact_count
        count_rows.append(
            f"| `{key}` | {artifact_count} | {db_count} | {delta} |"
        )
    if not count_rows:
        count_rows.append("| `none` | 0 | 0 | 0 |")

    sync_status = "DRIFT_DETECTED" if drift_detected else "IN_SYNC"
    drift_pairs = ", ".join(f"{k}={v:+d}" for k, v in sorted(drift_by_status.items()) if v != 0)
    if not drift_pairs:
        drift_pairs = "none"

    return f"""# SK-M4 Provenance Register

**Date:** {generated_utc[:10]}  
**Source finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md` (`SK-M4` pass-5 residual)  
**Plan:** `planning/core_skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`

---

## Source Snapshot

- generated_utc: `{generated_utc}`
- source_snapshot.provenance_health_path: `{provenance_health_path.relative_to(PROJECT_ROOT)}`
- source_snapshot.provenance_health_generated_utc: `{provenance_generated_utc}`
- source_snapshot.repair_report_path: `{repair_report_path.relative_to(PROJECT_ROOT)}`
- source_snapshot.repair_report_generated_utc: `{repair.get('report_generated_utc', 'unknown')}`
- source_snapshot.gate_health_path: `{gate_health_path.relative_to(PROJECT_ROOT)}`
- source_snapshot.sync_status_path: `{_display_path(sync_status_path)}`

## Canonical Provenance Status

- status: `{provenance.get('status', 'UNKNOWN')}`
- reason_code: `{provenance.get('reason_code', 'UNKNOWN')}`
- allowed_claim: `{provenance.get('allowed_claim', 'unknown')}`
- m4_5_historical_lane: `{m4_5_lane}`
- m4_5_residual_reason: `{m4_5_residual_reason}`
- threshold_policy_pass: `{provenance.get('threshold_policy_pass', False)}`
- orphaned_rows: `{provenance.get('orphaned_rows', 0)}`
- orphaned_ratio: `{provenance.get('orphaned_ratio', 0)}`
- missing_manifests: `{provenance.get('missing_manifests', 0)}`
- backfilled_manifests: `{provenance.get('backfilled_manifests', 0)}`
- recoverability_class: `{recoverability_class}`

## Operational Contract Coupling

- gate_health_status: `{gate_status}`
- gate_health_reason_code: `{gate_reason_code}`
- allowed_claim_class: `{allowed_claim_class}`
- coupling_status: `{ "COUPLED_DEGRADED" if gate_status == "GATE_HEALTH_DEGRADED" else ("COUPLED_OK" if gate_status == "GATE_HEALTH_OK" else "COUPLING_UNKNOWN") }`

## Register Synchronization Status

- sync_status: `{sync_status}`
- drift_detected: `{drift_detected}`
- drift_by_status: `{drift_pairs}`
- m4_5_lane_parity: `{m4_5_lane}` aligned to canonical provenance-health artifact

### Count Comparison (Canonical Artifact vs Runtime DB)

| Status | Artifact Count | Runtime DB Count | Delta (DB - Artifact) |
|---|---:|---:|---:|
{chr(10).join(count_rows)}

## Residual Statement (Pass 5 / SK-M4.5)

- Historical provenance confidence is lane-governed; current lane is `{m4_5_lane}` under current source scope.
- Register synchronization is machine-tracked via `core_status/core_audit/provenance_register_sync_status.json`.
- Any non-zero drift or degraded contract posture blocks provenance-confidence upgrades.
"""


def sync_provenance_register(
    *,
    provenance_health_path: Path,
    repair_report_path: Path,
    gate_health_path: Path,
    db_path: Path,
    register_path: Path,
    sync_status_path: Path,
) -> dict[str, Any]:
    generated_utc = _utc_now_iso()
    provenance_payload = _read_json(provenance_health_path)
    provenance = _as_results(provenance_payload)
    gate = _as_results(_read_json(gate_health_path))
    repair = _read_json(repair_report_path)
    db_counts = _db_status_counts(db_path)

    artifact_counts = provenance.get("run_status_counts", {})
    if not isinstance(artifact_counts, dict):
        artifact_counts = {}
    status_keys = sorted(set(db_counts.keys()) | set(artifact_counts.keys()))
    drift_by_status = {
        key: int(db_counts.get(key, 0)) - int(artifact_counts.get(key, 0))
        for key in status_keys
    }
    drift_detected = any(delta != 0 for delta in drift_by_status.values())
    sync_status = "DRIFT_DETECTED" if drift_detected else "IN_SYNC"

    orphaned_rows = int(provenance.get("orphaned_rows", 0) or 0)
    missing_manifests = int(provenance.get("missing_manifests", 0) or 0)
    backfilled_manifests = int(provenance.get("backfilled_manifests", 0) or 0)
    recoverability_class = _recoverability_class(
        orphaned_rows=orphaned_rows,
        missing_manifests=missing_manifests,
        backfilled_manifests=backfilled_manifests,
    )

    markdown = _render_register_markdown(
        generated_utc=generated_utc,
        provenance_health_path=provenance_health_path,
        repair_report_path=repair_report_path,
        gate_health_path=gate_health_path,
        sync_status_path=sync_status_path,
        provenance=provenance,
        gate=gate,
        repair=repair,
        db_counts=db_counts,
        drift_by_status=drift_by_status,
        drift_detected=drift_detected,
        recoverability_class=recoverability_class,
    )
    register_path.parent.mkdir(parents=True, exist_ok=True)
    register_path.write_text(markdown.strip() + "\n", encoding="utf-8")

    m4_5_lane = provenance.get("m4_5_historical_lane") or provenance.get("m4_4_historical_lane")
    m4_5_residual_reason = provenance.get("m4_5_residual_reason") or provenance.get("m4_4_residual_reason")
    m4_5_reopen_conditions = provenance.get("m4_5_reopen_conditions") or provenance.get("m4_4_reopen_conditions")
    payload: dict[str, Any] = {
        "version": "2026-02-10-m4.5",
        "generated_utc": generated_utc,
        "status": sync_status,
        "drift_detected": drift_detected,
        "drift_by_status": drift_by_status,
        "provenance_status": provenance.get("status"),
        "provenance_reason_code": provenance.get("reason_code"),
        "provenance_health_generated_utc": provenance.get("generated_utc"),
        "provenance_health_lane": m4_5_lane,
        "provenance_health_residual_reason": m4_5_residual_reason,
        "provenance_health_reopen_conditions": m4_5_reopen_conditions,
        "provenance_health_m4_5_lane": m4_5_lane,
        "provenance_health_m4_5_residual_reason": m4_5_residual_reason,
        "provenance_health_m4_5_reopen_conditions": m4_5_reopen_conditions,
        "provenance_health_m4_5_data_availability_linkage": provenance.get(
            "m4_5_data_availability_linkage"
        ),
        "provenance_health_m4_4_lane": provenance.get("m4_4_historical_lane"),
        "provenance_health_m4_4_residual_reason": provenance.get("m4_4_residual_reason"),
        "provenance_health_m4_4_reopen_conditions": provenance.get("m4_4_reopen_conditions"),
        "db_counts": db_counts,
        "artifact_counts": artifact_counts,
        "health_orphaned_rows": provenance.get("orphaned_rows"),
        "register_orphaned_rows": artifact_counts.get("orphaned", 0),
        "repair_report_generated_utc": repair.get("report_generated_utc"),
        "recoverability_class": recoverability_class,
        "gate_health_status": gate.get("status"),
        "gate_health_reason_code": gate.get("reason_code"),
        "allowed_claim_class": gate.get("allowed_claim_class"),
        "contract_coupling_state": (
            "COUPLED_DEGRADED"
            if gate.get("status") == "GATE_HEALTH_DEGRADED"
            else ("COUPLED_OK" if gate.get("status") == "GATE_HEALTH_OK" else "COUPLING_UNKNOWN")
        ),
        "register_path": _display_path(register_path),
        "status_source": [
            _display_path(provenance_health_path),
            _display_path(repair_report_path),
            _display_path(gate_health_path),
            _display_path(db_path),
        ],
    }
    sync_status_path.parent.mkdir(parents=True, exist_ok=True)
    sync_status_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize SK-M4 provenance register from canonical status artifacts."
    )
    parser.add_argument(
        "--provenance-health-path",
        default=str(DEFAULT_PROVENANCE_HEALTH_PATH),
        help="Path to canonical provenance health artifact.",
    )
    parser.add_argument(
        "--repair-report-path",
        default=str(DEFAULT_REPAIR_REPORT_PATH),
        help="Path to repair summary artifact.",
    )
    parser.add_argument(
        "--gate-health-path",
        default=str(DEFAULT_GATE_HEALTH_PATH),
        help="Path to release gate-health artifact.",
    )
    parser.add_argument(
        "--db-path",
        default=str(DEFAULT_DB_PATH),
        help="Path to metadata DB.",
    )
    parser.add_argument(
        "--register-path",
        default=str(DEFAULT_REGISTER_PATH),
        help="Path to SK-M4 provenance register markdown.",
    )
    parser.add_argument(
        "--sync-status-path",
        default=str(DEFAULT_SYNC_STATUS_PATH),
        help="Path for provenance register sync status JSON.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    payload = sync_provenance_register(
        provenance_health_path=Path(args.provenance_health_path).resolve(),
        repair_report_path=Path(args.repair_report_path).resolve(),
        gate_health_path=Path(args.gate_health_path).resolve(),
        db_path=Path(args.db_path).resolve(),
        register_path=Path(args.register_path).resolve(),
        sync_status_path=Path(args.sync_status_path).resolve(),
    )
    print(
        "status={status} drift_detected={drift_detected} recoverability_class={recoverability_class}".format(
            **payload
        )
    )
