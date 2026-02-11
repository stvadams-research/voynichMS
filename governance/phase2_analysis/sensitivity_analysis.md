# Sensitivity Analysis

## Status

**STATUS: EXECUTED (canonical release-mode sweep, quality-gated).**

Sensitivity sweep assets:

- Runner: `scripts/phase2_analysis/run_sensitivity_sweep.py`
- Machine-readable output (CI/latest snapshot): `core_status/core_audit/sensitivity_sweep.json` (provenance-wrapped)
- Machine-readable output (release candidate): `core_status/core_audit/sensitivity_sweep_release.json`
- Quality diagnostics sidecar (CI/latest): `core_status/core_audit/sensitivity_quality_diagnostics.json`
- Quality diagnostics sidecar (release candidate): `core_status/core_audit/sensitivity_quality_diagnostics_release.json`
- Runtime progress file: `core_status/core_audit/sensitivity_progress.json`
- Release preflight status: `core_status/core_audit/sensitivity_release_preflight.json`
- Scenario checkpoint state: `core_status/core_audit/sensitivity_checkpoint.json`
- Release run-status lifecycle: `core_status/core_audit/sensitivity_release_run_status.json`
- Human report (CI/latest): `reports/core_audit/SENSITIVITY_RESULTS.md`
- Human report (release candidate): `reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md`
- Latest CI/local metadata should be read from:
  - `core_status/core_audit/sensitivity_sweep.json` -> `provenance.timestamp`, `results.summary.*`
- Release-gate metadata should be read from:
  - `core_status/core_audit/sensitivity_sweep_release.json` -> `provenance.timestamp`, `results.summary.*`
- Contract policy: `configs/core_audit/sensitivity_artifact_contract.json`
- Contract checker: `scripts/core_audit/check_sensitivity_artifact_contract.py`

Contract checks:

```bash
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode ci
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
```

Release preflight check (no scenario execution):

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
```

Current evidence caveat policy:

- Canonical full-sweep execution alone is not sufficient for release evidence.
- `release_evidence_ready` is only true when all conditions are met:
  - release mode,
  - full scenario execution,
  - dataset representativeness policy pass (`dataset_policy_pass=true`),
  - warning burden policy pass (`warning_policy_pass=true`),
  - quality gate passed,
  - conclusive robustness decision (`PASS` or `FAIL`, not `INCONCLUSIVE`).
- If robustness is `INCONCLUSIVE`, release evidence readiness must remain false.

Interpretation policy:

- Do not treat top-model/anomaly stability rates as a standalone PASS.
- Robustness is only considered PASS when quality gates also pass:
  - valid scenario rate threshold,
  - no all-scenario zero-survivor collapse,
  - warning burden thresholds (aggregate + per-scenario density),
  - explicit caveat review.
- Release automation (`pre_release_check.sh` and `verify_reproduction.sh`) enforces the same conclusive+quality policy.
  - Release automation reads release-candidate artifacts (`*_release.json` / `*_RELEASE.md`) to avoid iterative snapshot contamination.
- If warnings are present (`total_warning_count > 0`), caveat output must be non-empty.
- Release run lifecycle states are explicit:
  - `STARTED`: release sweep initiated.
  - `RUNNING`: scenarios in progress or resumed.
  - `COMPLETED`: release artifacts/report emitted.
  - `FAILED`: runner terminated with captured error details.

## Purpose

The pipeline uses threshold and weight parameters that can affect model status and rankings.  
This phase2_analysis tests whether high-level conclusions remain stable under controlled parameter variation while explicitly tracking data-quality caveats.

## Parameter Scope

### Perturbation Thresholds
- File: `configs/phase6_functional/model_params.json`
- Variable: `disconfirmation.perturbation_battery[].failure_threshold`
- Sweep range: `[0.40, 0.80]` in `0.05` increments
- Primary metric: explanation-model survival profile

### Model Sensitivities
- File: `configs/phase6_functional/model_params.json`
- Variable: `models.*.sensitivities`
- Sweep range: uniform `+/-20%` scaling
- Primary metric: model ranking stability

### Evaluation Dimension Weights
- File: `configs/phase6_functional/model_params.json`
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
   - Warning families are tracked separately:
     - insufficient-data warnings,
     - sparse-data warnings,
     - NaN-sanitized warnings,
     - fallback-estimate warnings.
6. Apply robustness gate only if quality conditions are satisfied.
7. Write outputs:
   - `core_status/core_audit/sensitivity_sweep.json` (non-release latest snapshot)
   - `core_status/core_audit/sensitivity_sweep_release.json` (release mode)
   - `core_status/core_audit/sensitivity_progress.json`
   - `core_status/core_audit/sensitivity_release_preflight.json` (`--preflight-only` path)
   - `core_status/core_audit/sensitivity_checkpoint.json` (resume support)
   - `core_status/core_audit/sensitivity_quality_diagnostics.json` (non-release latest snapshot)
   - `core_status/core_audit/sensitivity_quality_diagnostics_release.json` (release mode)
   - `reports/core_audit/SENSITIVITY_RESULTS.md` (non-release latest snapshot)
   - `reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md` (release mode)

## Testability Modes

Use reduced-cost runs for development and debugging; reserve release mode for final evidence.

Profile mapping:

- `smoke` profile -> `--mode smoke` (minimum scenarios, non-release entitlement)
- `standard` profile -> `--mode iterative` (reduced subset, non-release entitlement)
- `release-depth` profile -> `--mode release` (full contract path, release entitlement candidate)

- **Release mode (authoritative evidence):**

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
```

- **Release preflight (fail-fast policy check):**

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
```

- **Iterative mode (faster, representative workflow checks):**

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode iterative
```

- **Quick shortcut (forces iterative defaults):**

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke --quick
```

`--quick` defaults to:

- dataset `voynich_synthetic_grammar`,
- reduced scenario subset,
- scenario cap suitable for local iteration.

Progress can be tailed at any time:

```bash
cat core_status/core_audit/sensitivity_progress.json
```

Run-status lifecycle can be inspected in parallel:

```bash
cat core_status/core_audit/sensitivity_release_run_status.json
```

Checkpoint/resume notes:

- The runner writes `core_status/core_audit/sensitivity_checkpoint.json` after each completed scenario.
- Re-running the same mode/dataset/scenario signature resumes from completed scenarios by default.
- Disable resume explicitly if needed:

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --no-resume
```

## Required Caveat Reporting

`reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md` must include:

- valid scenario rate,
- insufficient-data scenario count,
- sparse-data scenario count,
- warning density per scenario,
- warning policy pass/fail,
- dataset policy pass/fail,
- whether all scenarios had zero surviving models,
- explicit caveat bullets,
- final robustness decision (`PASS`, `FAIL`, or `INCONCLUSIVE`).
