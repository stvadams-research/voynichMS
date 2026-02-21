# SK-M4 Provenance Register

**Date:** 2026-02-21  
**Source finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md` (`SK-M4` pass-5 residual)  
**Plan:** `planning/core_skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`

---

## Source Snapshot

- generated_utc: `2026-02-21T00:06:42.348243Z`
- source_snapshot.provenance_health_path: `core_status/core_audit/provenance_health_status.json`
- source_snapshot.provenance_health_generated_utc: `2026-02-21T00:06:42.311299Z`
- source_snapshot.repair_report_path: `core_status/core_audit/run_status_repair_report.json`
- source_snapshot.repair_report_generated_utc: `2026-02-10T17:39:06.686478Z`
- source_snapshot.gate_health_path: `core_status/core_audit/release_gate_health_status.json`
- source_snapshot.sync_status_path: `core_status/core_audit/provenance_register_sync_status.json`

## Canonical Provenance Status

- status: `PROVENANCE_QUALIFIED`
- reason_code: `HISTORICAL_ORPHANED_ROWS_PRESENT`
- allowed_claim: `Historical provenance is qualified: uncertainty is explicitly bounded and tracked.`
- m4_5_historical_lane: `M4_5_BOUNDED`
- m4_5_residual_reason: `historical_orphaned_rows_irrecoverable_with_current_source_scope`
- threshold_policy_pass: `True`
- orphaned_rows: `63`
- orphaned_ratio: `0.159494`
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
- m4_5_lane_parity: `M4_5_BOUNDED` aligned to canonical provenance-health artifact

### Count Comparison (Canonical Artifact vs Runtime DB)

| Status | Artifact Count | Runtime DB Count | Delta (DB - Artifact) |
|---|---:|---:|---:|
| `orphaned` | 63 | 63 | 0 |
| `success` | 332 | 332 | 0 |

## Residual Statement (Pass 5 / SK-M4.5)

- Historical provenance confidence is lane-governed; current lane is `M4_5_BOUNDED` under current source scope.
- Register synchronization is machine-tracked via `core_status/core_audit/provenance_register_sync_status.json`.
- Any non-zero drift or degraded contract posture blocks provenance-confidence upgrades.
