# SK-M2.2 Confidence Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_2_EXECUTION_PLAN.md`  
Source assessment: `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`

## Baseline Artifact (Publication Lane)

- Artifact: `results/phase7_human/phase_7c_uncertainty.json`
- Run ID: `4483aee5-7ae5-cd67-98e6-3c66ba21ac32`
- Seed / iterations: `42 / 2000`
- Status: `INCONCLUSIVE_UNCERTAINTY`
- Reason code: `TOP2_GAP_FRAGILE`
- Allowed claim: comparative claim remains provisional.

Core metrics:

- `nearest_neighbor`: `Lullian Wheels`
- `nearest_neighbor_stability`: `0.4565`
- `jackknife_nearest_neighbor_stability`: `0.8333`
- `rank_stability`: `0.4565`
- `nearest_neighbor_probability_margin`: `0.0670`
- `top2_gap.ci95_lower`: `0.0263`

## Threshold Gap Decomposition

Policy source: `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json`

### Confirmed-class thresholds

| Metric | Observed | Threshold | Gap (Observed - Threshold) | Pass |
|---|---:|---:|---:|---|
| nearest neighbor stability | 0.4565 | 0.7500 | -0.2935 | No |
| jackknife stability | 0.8333 | 0.7500 | +0.0833 | Yes |
| rank stability | 0.4565 | 0.6500 | -0.1935 | No |
| nearest-neighbor probability margin | 0.0670 | 0.1000 | -0.0330 | No |
| top-2 gap CI lower | 0.0263 | 0.0500 | -0.0237 | No |

### Qualified-class thresholds

| Metric | Observed | Threshold | Gap (Observed - Threshold) | Pass |
|---|---:|---:|---:|---|
| nearest neighbor stability | 0.4565 | 0.5000 | -0.0435 | No |
| jackknife stability | 0.8333 | 0.7000 | +0.1333 | Yes |
| rank stability | 0.4565 | 0.5500 | -0.0935 | No |
| nearest-neighbor probability margin | 0.0670 | 0.0300 | +0.0370 | Yes |

Interpretation:

- Confidence is not blocked by jackknife behavior.
- Residual weakness is concentrated in nearest-neighbor consistency, rank stability, and top-2 separation robustness.

## Registered Confidence Matrix Results

Source: `/tmp/m2_2_sweep/summary.json`

Matrix definition:

- Seeds: `42`, `314`, `2718`
- Iterations: `2000`, `4000`, `8000`
- Total lanes: `9`

Observed envelope:

- Statuses observed: `INCONCLUSIVE_UNCERTAINTY` only (9/9).
- Reason codes observed: `TOP2_GAP_FRAGILE` only (9/9).
- `nearest_neighbor_stability`: min `0.4485`, max `0.4630`.
- `rank_stability`: min `0.4465`, max `0.4708`.
- `nearest_neighbor_probability_margin`: min `0.0555`, max `0.0858`.
- `top2_gap.ci95_lower`: min `0.0221`, max `0.0283`.
- `metric_validity.required_fields_present`: `True` across all lanes.

Conclusion:

- The residual appears stable under the registered matrix and is not a single-seed artifact.
- SK-M2.2 remains confidence-limited under current matrix/features, with top-2 separation fragility as the dominant reason.
