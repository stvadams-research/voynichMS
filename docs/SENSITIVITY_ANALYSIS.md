# Sensitivity Analysis

## Status

**STATUS: NOT YET EXECUTED (as of 2026-02-10).**

This document currently describes the intended sweep design only. No sensitivity
result set has been produced yet, and no `reports/audit/SENSITIVITY_RESULTS.md`
artifact exists for this plan.

## Purpose

The pipeline uses threshold and weight parameters that can affect downstream
classification and ranking outcomes. This analysis is intended to test how
stable the high-level conclusions are under controlled parameter variation.

## Planned Parameter Scope

### Perturbation Thresholds
- File: `configs/functional/model_params.json`
- Variable: `disconfirmation.perturbation_battery[].failure_threshold`
- Planned sweep: `[0.40, 0.80]` in `0.05` increments
- Primary metric: explanation-model survival profile

### Model Sensitivities
- File: `configs/functional/model_params.json`
- Variable: `models.*.sensitivities`
- Planned sweep: uniform `+/-20%` offsets
- Primary metric: model ranking stability

### Evaluation Dimension Weights
- File: `configs/functional/model_params.json`
- Variable: `evaluation.dimension_weights`
- Planned sweep: constrained permutations with `sum(weights)=1.0`
- Primary metric: top-ranked model identity

## Planned Execution Strategy

1. Implement `scripts/analysis/run_sensitivity_sweep.py`.
2. Re-run Phase 2.4 analyses under each parameter configuration.
3. Mark findings as stable if top-ranked model and anomaly confirmation status
   are unchanged in more than 90% of runs.
4. Write full output to `reports/audit/SENSITIVITY_RESULTS.md`.
