# SK-M4.5 Decision Record

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`

## Decision

Set SK-M4.5 closure state to:

- `M4_5_BOUNDED`

Supporting canonical fields:

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `m4_5_residual_reason=historical_orphaned_rows_irrecoverable_with_current_source_scope`
- `provenance_register_sync_status.status=IN_SYNC`
- `provenance_register_sync_status.drift_detected=false`

## Why This Decision Is Defensible

1. All pass-5 SK-M4 fixable contract defects were remediated:
   - deterministic M4.5 fields in producer/checker/sync/policy,
   - explicit missing-folio objective-linkage guard,
   - gate dependency snapshot parity,
   - CI/pre-release/verify M4.5 checks.
2. Canonical synchronization remains coherent (`IN_SYNC`, zero drift) and coupling checks pass.
3. Historical residual remains explicitly bounded and classified, not hidden.
4. Missing-folio objections are now explicitly non-blocking for SK-M4 without objective provenance-contract incompleteness linkage.

## Why Stronger Closure Was Not Selected

`M4_5_ALIGNED` is not eligible because historical orphaned residual persists (`orphaned_rows=63`) and recoverability class remains bounded under current source scope.

`M4_5_QUALIFIED` is weaker than current bounded state semantics because irrecoverable residual classification is explicit and stable.

## Fixable vs Non-Fixable Ledger

Fixable blockers resolved this pass:

1. M4.4-only contract fields and checker lane semantics.
2. Missing folio-based blocker objective-linkage enforcement.
3. Missing M4.5 visibility in release gate dependency snapshots.
4. Missing M4.5 semantic checks in shell contract gates.

Non-fixable or out-of-scope blockers (explicitly documented):

1. Historical irrecoverable residual (bounded by current source scope).
2. SK-C1 release sensitivity evidence artifacts remain missing and keep global release gates degraded.

## Objective Reopen Triggers

1. Promote only if orphaned residual is eliminated under canonical threshold policy.
2. Reopen if sync parity/freshness breaks (`drift_detected=true`, stale artifacts, lane mismatch).
3. Reopen if contract coupling with release gate health fails.
4. Reopen folio-based SK-M4 blocking only with objective provenance-contract incompleteness evidence.
5. Reopen if new primary source evidence changes irrecoverability classification.
