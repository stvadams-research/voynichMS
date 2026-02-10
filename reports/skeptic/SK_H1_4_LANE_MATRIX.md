# SK-H1.4 Lane Matrix

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_4_EXECUTION_PLAN.md`

## Purpose

Pre-register robustness lanes so SK-H1 conclusions are evaluated prospectively, not tuned after observing outcomes.

## Matrix Definition (Policy-Bound)

Source: `configs/skeptic/sk_h1_multimodal_policy.json`

- `matrix_id=SK_H1_4_MATRIX_2026-02-10`
- `version=2026-02-10-h1.4`
- `publication_lane_id=publication-default`
- `required_conclusive_agreement_ratio_for_robust=1.0`
- `max_ambiguity_lane_count_for_robust=0`
- `max_underpowered_lane_count_for_robust=0`
- `max_blocked_lane_count_for_robust=0`

## Active Lane Registry

| Lane ID | Purpose | Seed | Max Lines/Cohort | Method | Latest Run ID | Latest Status | Lane Outcome |
|---|---:|---:|---|---|---|---|---|
| `publication-default` | canonical publication lane | 42 | 1600 | `geometric_v1_t001` | `ef7fffef-968d-30d6-f34d-f4efadff6f7e` | `CONCLUSIVE_NO_COUPLING` | `H1_4_QUALIFIED` (matrix class remains mixed) |
| `stability-probe-seed-2718` | seed robustness probe | 2718 | 1600 | `geometric_v1_t001` | `cd893dae-7211-fa59-02b5-99d7068a7f7e` | `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | `H1_4_INCONCLUSIVE` |
| `adequacy-floor` | adequacy floor probe | 42 | 20 | `geometric_v1_t001` | `869b6f8d-90d8-e75c-0269-ecd69c0c7b86` | `INCONCLUSIVE_UNDERPOWERED` | `H1_4_INCONCLUSIVE` |

## Deferred Lane (Explicitly Not Active)

| Lane ID | Status | Rationale |
|---|---|---|
| `method-variance` | deferred | Not included in matrix `2026-02-10-h1.4` to prevent post-hoc method retuning. May be added only via policy version change plus full rerun evidence. |

## Anti-Tuning Rules

1. Publication lane is fixed to `publication-default` for this matrix version.
2. Registered lanes and thresholds cannot be changed after seeing outcomes for the same matrix version.
3. Any lane additions/removals require a versioned policy update and full matrix regeneration.
4. Reports must use lane-qualified language matching emitted `h1_4_closure_lane` and `robustness_class`.

## Reopen Conditions

- `registered lane matrix reaches robust class without inferential ambiguity`
- `policy thresholds are revised with documented rationale and rerun evidence`
