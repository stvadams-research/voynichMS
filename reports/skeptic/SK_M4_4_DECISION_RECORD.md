# SK-M4.4 Decision Record

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M4_4_EXECUTION_PLAN.md`

## Decision

Set SK-M4.4 closure state to:

- `M4_4_BOUNDED`

Supporting canonical fields:

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `m4_4_historical_lane=M4_4_BOUNDED`
- `drift_detected=false`
- `contract_coupling_pass=true`

## Why This Decision Is Defensible

1. Lane derivation is deterministic and machine-enforced.
2. Cross-artifact parity is synchronized (`status`, `reason`, lane, orphan counts).
3. Freshness and threshold checks are fail-closed and currently passing.
4. Residual uncertainty is explicitly classified as bounded historical irrecoverability under current source scope.
5. Claim boundaries are synchronized across policy, register, README, and closure-facing reports.

## Why Stronger Closure Was Not Selected

`M4_4_ALIGNED` was not eligible because:

- orphaned legacy rows remain present (`orphaned_rows=63`),
- canonical status remains `PROVENANCE_QUALIFIED`, and
- gate-health state remains degraded (`GATE_HEALTH_DEGRADED`).

`M4_4_QUALIFIED` (non-bounded variant) was not selected because recoverability class remains in bounded historical classes, which policy maps to `M4_4_BOUNDED`.

## Objective Reopen Triggers

1. Drift trigger: sync artifact shows `drift_detected=true` or parity mismatches.
2. Freshness trigger: provenance/sync artifact age exceeds policy limits.
3. Threshold trigger: provenance threshold checks fail.
4. Coupling trigger: degraded gate state and provenance lane/status become policy-incoherent.
5. Recovery trigger: historical source scope changes and bounded recoverability classification no longer applies.

## Anti-Repeat Guardrail

Do not reopen SK-M4.4 solely because the bounded lane remains `M4_4_BOUNDED` under unchanged evidence with passing parity/freshness/coupling predicates.
