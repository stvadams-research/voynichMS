# Sensitivity Results

- Sweep date: 2026-02-10T05:52:43Z
- Dataset: `voynich_synthetic_grammar`
- Dataset pages: `18`
- Dataset tokens: `216`
- Execution mode: `release`
- Scenario execution: `17/17`
- Release evidence ready (full sweep + conclusive robustness + quality gate): `True`
- Total scenarios: 17
- Valid scenarios: 17 (100.00%)
- Baseline top model: `cs_procedural_generation`
- Baseline anomaly confirmed: `True`
- Top-model stability rate (valid scenarios): `100.00%`
- Anomaly-status stability rate (valid scenarios): `100.00%`
- Robustness decision: `PASS`
- Robustness conclusive (`PASS`/`FAIL`, excludes `INCONCLUSIVE`): `True`
- Quality gate passed (valid-scenario-rate threshold + non-collapse): `True`
- Robustness gate passed (>90% both + quality gates): `True`

## Data Quality Caveats

- Total warnings observed: `918`
- Scenarios with insufficient-data warnings: `0/17`
- All scenarios zero-survivor: `False`
- Caveat: none

## Scenario Results

| Scenario | Family | Top Model | Top Score | Surviving | Falsified | Warnings | Quality Flags | Valid |
|---|---|---|---:|---:|---:|---:|---|---|
| `baseline` | baseline | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.40` | threshold_sweep | `cs_procedural_generation` | 0.566 | 2 | 4 | 54 | - | True |
| `threshold_0.45` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.50` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.55` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.60` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.65` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.70` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.75` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `threshold_0.80` | threshold_sweep | `cs_procedural_generation` | 0.566 | 3 | 3 | 54 | - | True |
| `sensitivity_x0.80` | sensitivity_scale | `cs_procedural_generation` | 0.571 | 4 | 2 | 54 | - | True |
| `sensitivity_x1.20` | sensitivity_scale | `cs_procedural_generation` | 0.561 | 3 | 3 | 54 | - | True |
| `weights_focus_prediction_accuracy` | weight_permutation | `cs_procedural_generation` | 0.534 | 3 | 3 | 54 | - | True |
| `weights_focus_robustness` | weight_permutation | `cs_procedural_generation` | 0.582 | 3 | 3 | 54 | - | True |
| `weights_focus_explanatory_scope` | weight_permutation | `cs_procedural_generation` | 0.567 | 3 | 3 | 54 | - | True |
| `weights_focus_parsimony` | weight_permutation | `cs_procedural_generation` | 0.569 | 3 | 3 | 54 | - | True |
| `weights_focus_falsifiability` | weight_permutation | `cs_procedural_generation` | 0.579 | 3 | 3 | 54 | - | True |
