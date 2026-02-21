# SK-M4 Provenance Register

**Date:** 2026-02-21  
**Source finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md` (`SK-M4` pass-5 residual)  
**Plan:** `planning/core_skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`

---

## Source Snapshot

- generated_utc: `2026-02-21T19:36:04.362061Z`
- source_snapshot.provenance_health_path: `core_status/core_audit/provenance_health_status.json`
- source_snapshot.provenance_health_generated_utc: `2026-02-21T19:36:04.240710Z`
- source_snapshot.repair_report_path: `core_status/core_audit/run_status_repair_report.json`
- source_snapshot.repair_report_generated_utc: `2026-02-10T17:39:06.686478Z`
- source_snapshot.gate_health_path: `core_status/core_audit/release_gate_health_status.json`
- source_snapshot.sync_status_path: `core_status/core_audit/provenance_register_sync_status.json`

## Canonical Provenance Status

- status: `PROVENANCE_QUALIFIED`
- reason_code: `THRESHOLD_POLICY_PASSED_WITH_ORPHANS`
- allowed_claim: `INCONCLUSIVE_PROVENANCE_REQUIRING_DISCLAIMER`
- m4_5_historical_lane: `M4_5_QUALIFIED`
- m4_5_residual_reason: `historical_orphaned_rows_within_threshold`
- threshold_policy_pass: `True`
- orphaned_rows: `63`
- orphaned_ratio: `0.12233009708737864`
- missing_manifests: `0`
- backfilled_manifests: `0`
- recoverability_class: `HISTORICAL_ORPHANED_UNBACKFILLED`

## Operational Contract Coupling

- gate_health_status: `GATE_HEALTH_DEGRADED`
- gate_health_reason_code: `GATE_CONTRACT_BLOCKED`
- allowed_claim_class: `QUALIFIED`
- coupling_status: `COUPLED_DEGRADED`

## Register Synchronization Status

- sync_status: `IN_SYNC`
- drift_detected: `False`
- drift_by_status: `none`
- m4_5_lane_parity: `M4_5_QUALIFIED` aligned to canonical provenance-health artifact

### Count Comparison (Canonical Artifact vs Runtime DB)

| Status | Artifact Count | Runtime DB Count | Delta (DB - Artifact) |
|---|---:|---:|---:|
| `orphaned` | 63 | 63 | 0 |
| `success` | 452 | 452 | 0 |

## Residual Statement (Pass 5 / SK-M4.5)

- Historical provenance confidence is lane-governed; current lane is `M4_5_QUALIFIED` under current source scope.
- Register synchronization is machine-tracked via `core_status/core_audit/provenance_register_sync_status.json`.
- Any non-zero drift or degraded contract posture blocks provenance-confidence upgrades.
