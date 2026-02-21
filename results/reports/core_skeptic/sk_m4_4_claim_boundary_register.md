# SK-M4.4 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M4_4_EXECUTION_PLAN.md`

## Canonical Evidence Sources

- `core_status/core_audit/provenance_health_status.json`
- `core_status/core_audit/provenance_register_sync_status.json`
- `core_status/core_audit/release_gate_health_status.json`

Current lane:

- `status=PROVENANCE_QUALIFIED`
- `m4_4_historical_lane=M4_4_BOUNDED`
- `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `contract_health_status=GATE_HEALTH_DEGRADED`

## Allowed and Disallowed Claims by Lane

### `M4_4_ALIGNED`

Allowed:

- historical provenance confidence is aligned under current thresholds and coupling constraints.

Disallowed:

- aligned-certainty claims when drift, threshold failure, or degraded coupling preconditions are present.

### `M4_4_QUALIFIED`

Allowed:

- provenance confidence is qualified and synchronized with bounded uncertainty.

Disallowed:

- deterministic historical certainty language.

### `M4_4_BOUNDED` (Current Lane)

Allowed:

- historical provenance confidence remains bounded by irrecoverable legacy gaps under current source scope.
- register synchronization is in sync, but certainty class remains qualified.
- stronger confidence requires objective evidence change (not narrative reinterpretation).

Disallowed:

- "historical provenance is fully aligned/certain."
- "orphaned legacy rows are fully resolved."
- "SK-M4 residual is eliminated" without lane/predicate change.

## Required Marker Semantics Across Tracked Surfaces

Tracked surfaces:

- `README.md`
- `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`
- `results/reports/phase3_synthesis/final_phase_3_3_report.md`
- `governance/PROVENANCE.md`
- `governance/HISTORICAL_PROVENANCE_POLICY.md`
- `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md`

Required SK-M4.4 marker family:

- `core_status/core_audit/provenance_health_status.json`
- `PROVENANCE_QUALIFIED` or `PROVENANCE_ALIGNED` (as lane-entitled)
- `m4_4_historical_lane`
- `M4_4_BOUNDED` where irrecoverable class remains active

## Reopen Boundary Conditions

Reopen SK-M4.4 claim boundaries only if:

1. lane changes (`M4_4_BOUNDED` -> `M4_4_QUALIFIED` or `M4_4_ALIGNED`, or blocked/inconclusive regression),
2. sync parity or drift checks fail,
3. freshness policies fail,
4. contract coupling semantics break, or
5. historical source scope materially changes and recoverability class is reclassified.
