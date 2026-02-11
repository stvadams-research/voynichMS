# SK-M4.2 Gap Register

**Date:** 2026-02-10  
**Source finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-M4`)  
**Plan:** `planning/core_skeptic/SKEPTIC_M4_2_EXECUTION_PLAN.md`

---

## Baseline Snapshot (Pass-2 Finding)

- Provenance class in assessment: `PROVENANCE_QUALIFIED`
- Assessment-cited runtime spot-check: `orphaned=63`, `success=135`
- Identified drift issue: core_skeptic register snapshot showed stale `success=133`.

## Current Canonical Snapshot

From `core_status/core_audit/provenance_health_status.json` and runtime DB:

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `orphaned=63`
- `success=156`
- `threshold_policy_pass=true`

From `core_status/core_audit/provenance_register_sync_status.json`:

- `status=IN_SYNC`
- `drift_detected=false`
- `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`

## Gap Classification

| Gap ID | Gap Description | Class | Baseline | Current | State | Remediation Lever |
|---|---|---|---|---|---|---|
| M4.2-G1 | Skeptic register count drift vs runtime/canonical artifacts | Synchronization gap | drift present (`133` vs runtime) | `IN_SYNC` (`156` vs `156`) | RESOLVED | `scripts/core_audit/sync_provenance_register.py` |
| M4.2-G2 | Provenance confidence still qualified due historical orphaned rows | Data irrecoverability/legacy gap | `PROVENANCE_QUALIFIED` | `PROVENANCE_QUALIFIED` | OPEN (bounded) | policy-bounded qualified closure |
| M4.2-G3 | Provenance confidence could overstate under degraded operational contracts | Contract coupling gap | implicit/partial | explicit coupling fields + checks | RESOLVED (guarded) | `check_provenance_uncertainty.py` + gate-health coupling |

## Residual Statement

- Remaining SK-M4.2 residual is historical, bounded, and explicit (`PROVENANCE_QUALIFIED`), not silent drift.
- Confidence upgrade to `PROVENANCE_ALIGNED` requires elimination of qualifying legacy constraints, not wording changes.
