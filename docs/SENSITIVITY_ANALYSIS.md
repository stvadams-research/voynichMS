# Sensitivity Analysis

## Status

**STATUS: EXECUTED (canonical release-mode sweep, quality-gated).**

Sensitivity sweep assets:

- Runner: `scripts/analysis/run_sensitivity_sweep.py`
- Machine-readable output: `status/audit/sensitivity_sweep.json` (provenance-wrapped)
- Human report: `reports/audit/SENSITIVITY_RESULTS.md`
- Latest canonical run snapshot:
  - Date: `2026-02-10T05:52:43Z`
  - Provenance command: `run_sensitivity_sweep`
  - Execution mode: `release`
  - Dataset: `voynich_synthetic_grammar` (`18` pages, `216` tokens)
  - Executed scenarios: `17/17`
  - Release evidence ready: `True`
  - Robustness decision: `PASS`
  - Quality gate passed: `True`
  - Robustness conclusive: `True`

Current evidence caveat policy:

- Canonical full-sweep execution alone is not sufficient for release evidence.
- `release_evidence_ready` is only true when all conditions are met:
  - release mode,
  - full scenario execution,
  - quality gate passed,
  - conclusive robustness decision (`PASS` or `FAIL`, not `INCONCLUSIVE`).
- If robustness is `INCONCLUSIVE`, release evidence readiness must remain false.

Interpretation policy:

- Do not treat top-model/anomaly stability rates as a standalone PASS.
- Robustness is only considered PASS when quality gates also pass:
  - valid scenario rate threshold,
  - no all-scenario zero-survivor collapse,
  - explicit caveat review.
- Release automation (`pre_release_check.sh` and `verify_reproduction.sh`) enforces the same conclusive+quality policy.

## Purpose

The pipeline uses threshold and weight parameters that can affect model status and rankings.  
This analysis tests whether high-level conclusions remain stable under controlled parameter variation while explicitly tracking data-quality caveats.

## Parameter Scope

### Perturbation Thresholds
- File: `configs/functional/model_params.json`
- Variable: `disconfirmation.perturbation_battery[].failure_threshold`
- Sweep range: `[0.40, 0.80]` in `0.05` increments
- Primary metric: explanation-model survival profile

### Model Sensitivities
- File: `configs/functional/model_params.json`
- Variable: `models.*.sensitivities`
- Sweep range: uniform `+/-20%` scaling
- Primary metric: model ranking stability

### Evaluation Dimension Weights
- File: `configs/functional/model_params.json`
- Variable: `evaluation.dimension_weights`
- Sweep: constrained focus permutations with `sum(weights)=1.0`
- Primary metric: top-ranked model identity

## Execution Strategy

1. Validate dataset existence and minimum data availability before running scenarios.
2. Generate scenario configs from baseline model-parameter config.
3. Re-run disconfirmation + cross-model evaluation per scenario.
4. Re-run anomaly stability per scenario.
5. Record warning and quality signals per scenario.
   - Perturbation paths with sparse records use deterministic fallback estimates
     (`computed_from: "sparse_data_estimate"`) rather than NaN propagation.
   - Sparse-data fallback remains explicit in metrics payloads via `fallback_reason`.
6. Apply robustness gate only if quality conditions are satisfied.
7. Write outputs:
   - `status/audit/sensitivity_sweep.json`
   - `reports/audit/SENSITIVITY_RESULTS.md`

## Required Caveat Reporting

`reports/audit/SENSITIVITY_RESULTS.md` must include:

- valid scenario rate,
- insufficient-data scenario count,
- whether all scenarios had zero surviving models,
- explicit caveat bullets,
- final robustness decision (`PASS`, `FAIL`, or `INCONCLUSIVE`).
