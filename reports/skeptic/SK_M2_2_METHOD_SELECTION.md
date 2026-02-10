# SK-M2.2 Method Selection Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M2_2_EXECUTION_PLAN.md`  
Scope: Registered confidence-matrix execution and publication-lane selection.

## Pre-Registered Selection Rule

Selection must be based on:

1. field completeness and metric validity,
2. stability diagnostics across the registered matrix,
3. reproducibility and release-path consistency,
4. never on desired nearest-neighbor identity or desired conclusion class.

Policy source: `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`

## Candidate Matrix

Summary source: `/tmp/m2_2_sweep/summary.json`

| Tag | Seed | Iterations | Status | Reason | NN Stability | Rank Stability | Margin | Top2 CI Lower |
|---|---:|---:|---|---|---:|---:|---:|---:|
| `s42_i2000` | 42 | 2000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4565 | 0.4565 | 0.0670 | 0.0263 |
| `s42_i4000` | 42 | 4000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4630 | 0.4465 | 0.0858 | 0.0238 |
| `s42_i8000` | 42 | 8000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4566 | 0.4479 | 0.0701 | 0.0251 |
| `s314_i2000` | 314 | 2000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4520 | 0.4630 | 0.0610 | 0.0258 |
| `s314_i4000` | 314 | 4000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4578 | 0.4708 | 0.0760 | 0.0283 |
| `s314_i8000` | 314 | 8000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4514 | 0.4564 | 0.0628 | 0.0262 |
| `s2718_i2000` | 2718 | 2000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4495 | 0.4555 | 0.0575 | 0.0221 |
| `s2718_i4000` | 2718 | 4000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4485 | 0.4565 | 0.0555 | 0.0228 |
| `s2718_i8000` | 2718 | 8000 | `INCONCLUSIVE_UNCERTAINTY` | `TOP2_GAP_FRAGILE` | 0.4554 | 0.4574 | 0.0704 | 0.0237 |

## Selection Outcome

Selected publication lane: `s42_i2000`

Rationale:

- It is the canonical lane already used in release-path automation:
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
- It preserves deterministic reproducibility expectations and minimizes process drift.
- Matrix behavior is homogeneous across lanes (all remain `INCONCLUSIVE_UNCERTAINTY` with same reason code), so no lane provided policy-eligible confidence closure.

## Anti-Tuning Evidence

1. All 9 registered lanes were executed and documented before selecting publication lane.
2. No lane achieved `DISTANCE_QUALIFIED` or `STABILITY_CONFIRMED`; publication lane was not selected to force a stronger status.
3. Final selection prioritized reproducibility contract alignment, not inferential direction.
