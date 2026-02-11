# SK-M4.5 Baseline Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`  
Source assessment: `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`

## Pass-5 Finding Freeze

Assessment finding frozen for this remediation cycle:

- `SK-M4 (Medium): Provenance is synchronized and lane-governed, but historical confidence remains bounded.`

## Canonical Baseline Snapshot

Source artifacts:

- `core_status/core_audit/provenance_health_status.json`
- `core_status/core_audit/provenance_register_sync_status.json`
- `core_status/core_audit/release_gate_health_status.json`

Current canonical state:

- `status`: `PROVENANCE_QUALIFIED`
- `reason_code`: `HISTORICAL_ORPHANED_ROWS_PRESENT`
- `recoverability_class`: `HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `orphaned_rows`: `63`
- `threshold_policy_pass`: `true`
- `contract_coupling_pass`: `true`
- `m4_5_historical_lane`: `M4_5_BOUNDED`
- `m4_5_residual_reason`: `historical_orphaned_rows_irrecoverable_with_current_source_scope`
- `m4_5_data_availability_linkage.missing_folio_blocking_claimed`: `false`
- `m4_5_data_availability_linkage.objective_provenance_contract_incompleteness`: `false`
- `m4_5_data_availability_linkage.approved_irrecoverable_loss_classification`: `true`
- `m4_5_data_availability_linkage.blocker_classification`: `NON_BLOCKING_APPROVED_IRRECOVERABLE_LOSS`
- sync `status`: `IN_SYNC`
- sync `drift_detected`: `false`
- sync `provenance_health_m4_5_lane`: `M4_5_BOUNDED`
- gate-health `status`: `GATE_HEALTH_DEGRADED`
- gate-health `reason_code`: `GATE_CONTRACT_BLOCKED`

## Contradiction and Defect Classification

| ID | Observation | Classification | Disposition |
|---|---|---|---|
| M4.5-CX1 | Producer/checker/policy/register surfaces were M4.4-only. | Fixable SK-M4 contract defect | Remediated with deterministic M4.5 fields and parity checks. |
| M4.5-CX2 | Missing-folio objection could be repeated as SK-M4 blocker without objective linkage. | Fixable SK-M4 governance defect | Remediated with checker-level objective-linkage guard and linkage fields. |
| M4.5-CX3 | Gate dependency snapshot did not project SK-M4 lane/reason data. | Fixable SK-M4 observability defect | Remediated in `build_release_gate_health_status.py`. |
| M4.5-CX4 | Historical orphaned residual (`orphaned_rows=63`) remains under current source scope. | Non-fixable bounded SK-M4 residual | Explicitly classified as bounded and reopen-triggered, not silently ignored. |
| M4.5-CX5 | Release-path scripts remain degraded due missing release sensitivity evidence artifacts. | Out-of-scope external blocker (SK-C1) | Explicitly routed out of SK-M4 scope; documented but not misclassified as SK-M4. |

## Blocker Taxonomy (Pass-5)

Fixable blockers remediated:

1. Missing deterministic M4.5 lane semantics across producer/checker/sync/policy.
2. Missing objective-linkage guard for folio-based SK-M4 blocking claims.
3. Missing SK-M4 lane visibility in release gate-health dependency snapshots.
4. Missing SK-M4.5 contract checks in CI/pre-release/verify scripts.

Non-fixable or out-of-scope blockers remaining:

1. Historical irrecoverability residual remains bounded (`M4_5_BOUNDED`) with current source scope.
2. SK-C1 release evidence artifacts are still missing (`core_status/core_audit/sensitivity_sweep_release.json`, `reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md`).
