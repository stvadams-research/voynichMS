# SK-M4.4 Diagnostic Matrix

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M4_4_EXECUTION_PLAN.md`

## Canonical Lane-Derivation Matrix

Source artifact: `core_status/core_audit/provenance_health_status.json`

| Predicate Group | Predicate | Observed | Expected for Current Closure | Pass |
|---|---|---|---|---|
| Provenance class | `status` | `PROVENANCE_QUALIFIED` | `PROVENANCE_QUALIFIED` | Yes |
| Residual reason | `reason_code` | `HISTORICAL_ORPHANED_ROWS_PRESENT` | historical residual present | Yes |
| Recoverability class | `recoverability_class` | `HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED` | bounded historical class | Yes |
| Lane derivation | `m4_4_historical_lane` | `M4_4_BOUNDED` | `M4_4_BOUNDED` | Yes |
| Lane reason | `m4_4_residual_reason` | `historical_orphaned_rows_irrecoverable_with_current_source_scope` | bounded residual reason | Yes |
| Reopen governance | `m4_4_reopen_conditions` | non-empty list | required for bounded lane | Yes |
| Threshold gating | `threshold_policy_pass` | `true` | `true` | Yes |
| Contract gating | `contract_coupling_pass` | `true` | `true` | Yes |

## Sync and Parity Matrix

Primary sync artifact: `core_status/core_audit/provenance_register_sync_status.json`

| Parity Check | Health Artifact | Sync Artifact | Result |
|---|---|---|---|
| status parity | `PROVENANCE_QUALIFIED` | `provenance_status=PROVENANCE_QUALIFIED` | Match |
| reason parity | `HISTORICAL_ORPHANED_ROWS_PRESENT` | `provenance_reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT` | Match |
| lane parity | `M4_4_BOUNDED` | `provenance_health_lane=M4_4_BOUNDED` | Match |
| residual parity | `historical_orphaned_rows_irrecoverable_with_current_source_scope` | `provenance_health_residual_reason=historical_orphaned_rows_irrecoverable_with_current_source_scope` | Match |
| orphan count parity | `orphaned_rows=63` | `health_orphaned_rows=63` and `register_orphaned_rows=63` | Match |
| drift consistency | `drift_by_status={orphaned:0,success:0}` | `status=IN_SYNC`, `drift_detected=false` | Match |

## Freshness Matrix

Current policy source: `configs/core_skeptic/sk_m4_provenance_policy.json`

| Artifact | generated_utc | Policy max age | Status |
|---|---|---|---|
| `core_status/core_audit/provenance_health_status.json` | `2026-02-10T20:53:37.897691Z` | `168h` | within limit at validation time |
| `core_status/core_audit/provenance_register_sync_status.json` | `2026-02-10T20:53:37.935152Z` | `168h` | within limit at validation time |

## Diagnostic Conclusion

The current SK-M4.4 state is deterministic and fully synchronized:

- lane: `M4_4_BOUNDED`
- residual class: historical and bounded under current source scope
- no drift, no freshness violations, and no cross-artifact parity mismatches

This supports anti-repeat closure on unchanged evidence while remaining fail-closed under objective reopen triggers.
