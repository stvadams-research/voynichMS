# SK-M2.4 Baseline Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M2_4_EXECUTION_PLAN.md`  
Source assessment: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## Pass-4 Finding Freeze

Assessment finding frozen for this remediation cycle:

- `SK-M2 (Medium): Comparative uncertainty remains explicitly inconclusive.`
- Evidence references from assessment:
  - `results/human/phase_7c_uncertainty.json:35`
  - `results/human/phase_7c_uncertainty.json:36`
  - `results/human/phase_7c_uncertainty.json:37`
  - `results/human/phase_7c_uncertainty.json:40`
  - `results/human/phase_7c_uncertainty.json:42`
  - `results/human/phase_7c_uncertainty.json:50`

## Canonical Baseline Snapshot

Source: `results/human/phase_7c_uncertainty.json`

- `status`: `INCONCLUSIVE_UNCERTAINTY`
- `reason_code`: `TOP2_IDENTITY_FLIP_DOMINANT`
- `m2_4_closure_lane`: `M2_4_BOUNDED`
- `allowed_claim`: comparative claim remains provisional due unstable nearest-neighbor identity under perturbation.
- `nearest_neighbor`: `Lullian Wheels`
- `nearest_neighbor_stability`: `0.4565`
- `jackknife_nearest_neighbor_stability`: `0.8333`
- `rank_stability`: `0.4565`
- `nearest_neighbor_probability_margin`: `0.0670`
- `top2_gap.ci95_lower`: `0.0263`
- `top2_set_stability`: `0.5580`
- `top2_identity_flip_rate`: `0.4420`
- `top2_order_flip_rate`: `0.7220`

## Residual Vector Decomposition

| Residual Vector | Baseline Evidence | Diagnosis |
|---|---|---|
| `rank_instability` | `rank_stability=0.4565` vs qualified floor `0.55` | Rank ordering remains unstable under perturbation. |
| `top2_gap_fragility` | `top2_gap.ci95_lower=0.0263` vs confirmed floor `0.05` | Top-2 separation does not support robust closure. |
| `top2_identity_flip` | `top2_set_stability=0.558` and `flip_rate=0.442` | Near-tie competition causes frequent top-2 identity swaps. |
| `margin_sensitivity` | `margin=0.067` (above qualified floor `0.03`, below confirmed floor `0.10`) | Margin supports directional signal but not robust confidence. |
| `model_assumption_risk` | `nearest_rank_entropy=1.747`, `runner_up_rank_entropy=2.082` | Rank entropy remains high; deterministic rank assertions are not entitled. |

## Objective Reopen / Transition Triggers

SK-M2.4 should be reopened only when at least one objective trigger is met:

1. Status promotion candidate: thresholds for `STABILITY_CONFIRMED` are all satisfied simultaneously.
2. Lane degradation candidate: `metric_validity.required_fields_present != true` or checker/report coherence fails.
3. Comparative result shift: nearest-neighbor identity or dominant fragility signal changes under registered matrix reruns.
4. Policy threshold revision: thresholds changed with documented rationale and full rerun evidence.
