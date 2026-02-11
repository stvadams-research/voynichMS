# SK-M2.5 Decision Record

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_5_EXECUTION_PLAN.md`

## Decision

Set SK-M2.5 closure state to:

- `M2_5_BOUNDED`

Supporting canonical fields:

- `status=INCONCLUSIVE_UNCERTAINTY`
- `reason_code=TOP2_IDENTITY_FLIP_DOMINANT`
- `m2_5_residual_reason=top2_identity_flip_rate_remains_dominant`

## Why This Decision Is Defensible

1. Pass-5 contract defects are remediated:
   - non-null residual reasons,
   - deterministic `m2_5_*` lane/residual/reopen fields,
   - checker enforcement for folio-based non-blocking SK-M2 criteria.
2. Canonical comparative instability remains objective and reproducible:
   - rank/top-2 instability remains below promotion floors.
3. Claim boundaries and tracked reports now align to `M2_5_BOUNDED` entitlement language.
4. Release gate-health snapshots now carry SK-M2 lane/reason dependency fields, preserving auditable parity even when SK-C1 is degraded.

## Why Stronger Closure Was Not Selected

`M2_5_ALIGNED` is not eligible because confirmed-threshold stability floors are not met.

`M2_5_QUALIFIED` is not eligible because nearest-neighbor/rank stability remain below qualified floors in the canonical artifact.

## Fixable vs Non-Fixable Ledger

Fixable blockers resolved this pass:

1. Null residual reason fields (`m2_4_residual_reason`).
2. Missing M2.5 lane contract fields (`m2_5_closure_lane`, `m2_5_residual_reason`, `m2_5_reopen_triggers`).
3. Missing checker enforcement for unsupported folio-based SK-M2 blocking.
4. Missing SK-M2 lane visibility in release gate-health dependency snapshots.

Non-fixable or out-of-scope blockers (explicitly documented, not waived):

1. Persistent top-2 identity flip fragility in canonical comparative metrics.
2. SK-C1 release sensitivity evidence artifact missing (`core_status/core_audit/sensitivity_sweep_release.json`) causing release-path failures outside SK-M2 scope.

## Objective Reopen Triggers

1. Promote only when qualified/confirmed stability predicates are met in canonical reruns.
2. Reopen if dominant fragility signal or nearest-neighbor identity materially changes.
3. Reopen if checker/policy/report parity fails.
4. Reopen missing-folio SK-M2 blocking only if objective comparative-input validity failure is demonstrated.
