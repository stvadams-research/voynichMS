# SK-M2.4 Method Selection Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_4_EXECUTION_PLAN.md`

## Pre-Registered Selection Rule

Selection order for publication lane:

1. field completeness (`metric_validity.required_fields_present=true`),
2. lane eligibility consistency across registered matrix,
3. reproducibility parity with release/checker automation.

Anti-tuning constraint:

- never select a lane by preferred nearest-neighbor identity or preferred confidence class.

## Registered Matrix Inputs

- Seeds: `42`, `314`, `2718`
- Profiles:
  - `smoke` (`400` iterations)
  - `standard` (`2000` iterations)
  - `release-depth` (`8000` iterations)
- Summary artifact: `/tmp/m2_4_sweep/summary.json`

## Lane Results

| Seed | Profile | Iterations | Status | Reason | Lane | NN Stability | Rank Stability | Margin | Top2 CI Lower |
|---:|---|---:|---|---|---|---:|---:|---:|---:|
| 42 | smoke | 400 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4575 | 0.4625 | 0.0525 | 0.0085 |
| 42 | standard | 2000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4565 | 0.4565 | 0.0670 | 0.0263 |
| 42 | release-depth | 8000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4566 | 0.4479 | 0.0701 | 0.0251 |
| 314 | smoke | 400 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4500 | 0.4575 | 0.0250 | 0.0393 |
| 314 | standard | 2000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4520 | 0.4630 | 0.0610 | 0.0258 |
| 314 | release-depth | 8000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4514 | 0.4564 | 0.0628 | 0.0262 |
| 2718 | smoke | 400 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.3775 | 0.4275 | 0.0000 | 0.0080 |
| 2718 | standard | 2000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4495 | 0.4555 | 0.0575 | 0.0221 |
| 2718 | release-depth | 8000 | INCONCLUSIVE_UNCERTAINTY | TOP2_IDENTITY_FLIP_DOMINANT | M2_4_BOUNDED | 0.4554 | 0.4574 | 0.0704 | 0.0237 |

## Selection Outcome

Selected publication lane:

- seed `42`, profile `standard`, iterations `2000`

Rationale:

1. It is the canonical lane already used by release-path automation:
   - `scripts/core_audit/pre_release_check.sh`
   - `scripts/verify_reproduction.sh`
2. It preserves reproducibility while remaining representative of matrix-wide behavior.
3. Matrix behavior was homogeneous (all lanes remained `M2_4_BOUNDED`), so no lane supported stronger entitlement.
