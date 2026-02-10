# Audit Execution Plan: Critical Issues (C1 - C14)

This document outlines the execution plan to address the 14 critical (C-level) issues identified in the `COMPREHENSIVE_AUDIT_REPORT.md`. The primary goals are to ensure deterministic results, externalize hardcoded thresholds into manageable configurations, and provide necessary documentation for reproducibility.

## Phase 1: Randomness Normalization
**Goal:** Achieve 100% deterministic output by ensuring all random processes are seeded via the `RandomnessController`.

### C2: Grammar-Based Generator Seeding
- **Action:** Modify `src/synthesis/generators/grammar_based.py` to accept a seed or utilize the global `RandomnessController`.
- **Implementation:** Replace `random.choices()` calls with `random.Random(seed).choices()`.

### C3: Feature Discovery Seeding
- **Action:** Audit all 12+ `random.uniform()` calls in `src/synthesis/refinement/feature_discovery.py`.
- **Implementation:** Inject a seed into the feature discovery functions or wrap them with the `RandomnessController` enforcement decorators.

### C4: Indistinguishability Determinism
- **Action:** Fix non-deterministic scrambled control generation in `src/synthesis/indistinguishability.py`.
- **Implementation:** Ensure `random.Random(seed)` is used for all shuffling and scrambling operations within the test.

### C12: Mechanism Simulator Seeding
- **Action:** Update all 8+ files in `src/mechanism/*/simulators.py` to ensure local RNG state.
- **Implementation:** Pass a `seed` parameter to all simulator entry points and instantiate `random.Random(seed)` or `np.random.RandomState(seed)` locally.

## Phase 2: Threshold Externalization & Centralization
**Goal:** Move 150+ hardcoded "magic numbers" into the configuration layer to allow for sensitivity analysis and documented justification.

### C1, C5, C6: Model & Evaluation Weights
- **Action:** Extract perturbation thresholds, sensitivity weights, and evaluation dimension weights from `disconfirmation.py`, `constructed_system.py`, `visual_grammar.py`, and `evaluation.py`.
- **Implementation:** Move these to a new `configs/functional/model_params.json` or update `src/foundation/core/config.py`.

### C7, C8: Capacity & Stability Baselines
- **Action:** Relocate capacity bounding constants and stability baselines from `capacity_bounding.py` and `stability_analysis.py`.
- **Implementation:** Centralize in `configs/functional/baselines.json`.

### C9, C13, C14: Synthesis & Perturbation Constraints
- **Action:** Externalize synthesis tolerances, equivalence thresholds, and perturbation battery strengths from `interface.py`, `refinement/interface.py`, and `disconfirmation.py`.
- **Implementation:** Ensure these can be overridden via command-line arguments or run-specific config files.

## Phase 3: Fallback Data Sanitization
**Goal:** Remove potential biases introduced by hardcoded fallback tokens.

### C11: Voynichese Token Seeds
- **Action:** Remove hardcoded "daiin", "chedy", "qokedy" seeds from `profile_extractor.py`.
- **Implementation:** Replace with a required transcription source or a procedurally generated, neutral character set if no source is available.

## Phase 4: Documentation & Reference
**Goal:** Provide the "Methods" and "Configuration" context required for external readers to understand and modify the program.

### C10: Configuration Reference
- **Action:** Create `docs/CONFIG_REFERENCE.md`.
- **Content:** Document every parameter externalized in Phase 2, including its type, default value, impact on the system, and the rationale/source for the default.

## Phase 5: Verification
- **Test:** Run the `acceptance_test.py` with the same seed twice to verify identical JSON outputs.
- **Audit:** Confirm that no `random` calls in the critical path remain unseeded.
- **Check:** Ensure all C1-C14 issues are marked as resolved in a follow-up audit report.
