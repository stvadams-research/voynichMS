# Phase 1: Results Integrity Audit Findings

## 1.1 Placeholder and Temporary Code

A search for `TODO`, `FIXME`, `HACK`, `TEMP`, `DEBUG` revealed 349 matches.

### Key Risk Areas (TODOs in Logic)
- **Synthesis Baseline Assessment:** `scripts/phase3_synthesis/run_baseline_assessment.py` notes "TODO: Info Density and Locality require control datasets". This implies these metrics might be running without proper controls in this script.
- **Formal System Simulators:** `src/phase6_functional/formal_system/simulators.py` mentions "attempts to 'exhaust' its state space". (Context check: likely docstring, low risk).
- **Hardcoded Bounds:** `planning/phase3_synthesis/PHASE_3_1_EXECUTION_PLAN.md` mentions "hard_bound" in a table.
- **Hypothesis Manager:** `src/phase1_foundation/hypotheses/manager.py` has "Instantiate temporarily to get ID?". Indicates potential instantiation overhead or unclean registry pattern.
- **Debug Prints:** Found `print(f"DEBUG: ...")` in `src/phase1_foundation/anchors/engine.py` and commented out in `scripts/phase5_mechanism/run_5i_anchor_coupling.py`.
- **Atomic Writes:** `src/phase1_foundation/storage/filesystem.py` uses temp files for atomic writes. This is a **GOOD** pattern, not a bug.

### "TEMP" False Positives
Many matches for "temp" are related to "temporal" or "template" or "temperature" (in Latin corpus).
- `temp_repetition_spacing` (Feature ID)
- `temp_token_burst_rate` (Feature ID)
- `FormalizationAttempt` (Class name)

## 1.2 Hardcoded Values & Magic Numbers (Preliminary Scan)

### `src/phase1_foundation/metrics/library.py`
- `ClusterTightness`:
  - `value=0.5` (Fallback default)
  - `details={"error": ...}` (Fallback behavior)
  - Formula: `1.0 / (1.0 + mean_distance)` (Implicit constants 1.0)

### `src/phase1_foundation/hypotheses/destructive.py`
- `FixedGlyphIdentityHypothesis`:
  - `perturbation_levels = [0.01, 0.05, 0.10, 0.15, 0.20]`
  - `collapse_threshold = 0.20` (Falsification criteria)
  - `0.10` (Weak support threshold)
- `WordBoundaryStabilityHypothesis`:
  - `0.70` (Falsified threshold)
  - `0.80` (Weakly supported threshold)
- `DiagramTextAlignmentHypothesis`:
  - `std_control = 0.1` (Fallback if variance is 0)
  - `z_score >= 2.0` (Supported threshold)
  - `z_score >= 1.0` (Weakly supported threshold)
- `AnchorDisruptionHypothesis`:
  - `perturbation_levels = [0.05, 0.10, 0.15, 0.20]`
  - `survival_at_10pct < 0.50` (Falsification threshold)
  - `survival_at_10pct < 0.70` (Weakly supported threshold)

### `src/phase2_analysis/stress_tests/mapping_stability.py`
- `MAX_PAGES_PER_TEST = 50`
- `MAX_LINES_PER_PAGE = 100`
- `MAX_WORDS_PER_LINE = 50`
- `perturbation = 0.05` (Segmentation shift)
- `control_ids` fallback `return 0.3` if no controls.
- Thresholds for `constructed_system`: `ord < 0.5`, `min_stability < 0.6`.
- Thresholds for `visual_grammar`: `seg < 0.4`, `min_stability < 0.5`.
- Thresholds for `hybrid_system`: `variance > 0.3`.

### `src/phase2_analysis/models/disconfirmation.py`
- `model_sensitivities`:
  - `segmentation: 0.35`
  - `ordering: 0.25`
  - `omission: 0.40`
  - `anchor_disruption: 0.70`
- `degradation < 0.6` (Survival threshold)

## 1.3 Silent Defaults

- `src/phase1_foundation/metrics/library.py`: Returns `0.0` or `0.5` when data is missing, sometimes with an error detail, but potentially silent if the caller only checks the value.
- `src/phase1_foundation/hypotheses/destructive.py`: `std_control` defaults to `0.1` if variance is 0. This prevents division by zero but is an arbitrary smoothing factor.

