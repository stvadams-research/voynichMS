# Execution Plan: Critical Audit Remediation (C2 Series)

This plan addresses the critical findings identified in `COMPREHENSIVE_AUDIT_REPORT_2.md` regarding result reproducibility and model parameter integrity.

## Issue C1: Unseeded Randomness in Grammar Generator
**Finding:** `grammar_based.py` uses global `random.choices()` without local RNG state.
**Remediation:**
1. Update `GrammarBasedGenerator.__init__` to accept an optional `seed`.
2. Instantiate `self.rng = random.Random(seed)`.
3. Replace all `random.choices()` and `random.choice()` calls with `self.rng` equivalents.
4. Update calling scripts to pass the run-level seed to the generator.

## Issue C2: Hardcoded Model Sensitivity Weights
**Finding:** Sensitivity profiles in `constructed_system.py` and `visual_grammar.py` are hardcoded without empirical justification.
**Remediation:**
1. Extract sensitivity dictionaries from model classes.
2. Move these parameters to `configs/functional/model_params.json`.
3. Update `ExplicitModel` implementations to load these values from the centralized config via `foundation.config`.
4. Document the baseline rationale for each sensitivity value in `docs/CALIBRATION_NOTES.md`.
