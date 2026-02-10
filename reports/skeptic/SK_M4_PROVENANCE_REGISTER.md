# SK-M4 Provenance Register

**Date:** 2026-02-10  
**Source finding:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-M4` pass-2 residual)  
**Plan:** `planning/skeptic/SKEPTIC_M4_2_EXECUTION_PLAN.md`

---

## Source Snapshot

- generated_utc: `2026-02-10T17:39:46.899917Z`
- source_snapshot.provenance_health_path: `status/audit/provenance_health_status.json`
- source_snapshot.provenance_health_generated_utc: `2026-02-10T17:39:46.863298Z`
- source_snapshot.repair_report_path: `status/audit/run_status_repair_report.json`
- source_snapshot.repair_report_generated_utc: `2026-02-10T17:39:06.686478Z`
- source_snapshot.gate_health_path: `status/audit/release_gate_health_status.json`
- source_snapshot.sync_status_path: `status/audit/provenance_register_sync_status.json`

## Canonical Provenance Status

- status: `PROVENANCE_QUALIFIED`
- reason_code: `HISTORICAL_ORPHANED_ROWS_PRESENT`
- allowed_claim: `Historical provenance is qualified: uncertainty is explicitly bounded and tracked.`
- threshold_policy_pass: `True`
- orphaned_rows: `63`
- orphaned_ratio: `0.287671`
- missing_manifests: `0`
- backfilled_manifests: `63`
- recoverability_class: `HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`

## Operational Contract Coupling

- gate_health_status: `GATE_HEALTH_DEGRADED`
- gate_health_reason_code: `GATE_CONTRACT_BLOCKED`
- allowed_claim_class: `QUALIFIED`
- coupling_status: `COUPLED_DEGRADED`

## Register Synchronization Status

- sync_status: `IN_SYNC`
- drift_detected: `False`
- drift_by_status: `none`

### Count Comparison (Canonical Artifact vs Runtime DB)

| Status | Artifact Count | Runtime DB Count | Delta (DB - Artifact) |
|---|---:|---:|---:|
| `orphaned` | 63 | 63 | 0 |
| `success` | 156 | 156 | 0 |

## Residual Statement (Pass 2)

- Historical provenance remains bounded and explicit, but currently qualified.
- Register synchronization is machine-tracked via `status/audit/provenance_register_sync_status.json`.
- Any non-zero drift or degraded contract posture blocks provenance-confidence upgrades.
