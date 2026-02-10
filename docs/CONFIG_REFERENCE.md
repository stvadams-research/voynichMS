# Configuration Reference

This document describes the externalized configuration parameters for the Voynich MS analysis and synthesis pipeline. These parameters were centralized to ensure reproducibility and allow for sensitivity analysis.

## 1. Model Parameters (`configs/functional/model_params.json`)

Controls the behavior of explanation models and the disconfirmation engine.

### Disconfirmation Engine
- `perturbation_battery`: List of systematic tests to falsify models.
  - `perturbation_type`: Type of disruption (segmentation, ordering, omission, anchor_disruption).
  - `strength_levels`: Magnitudes of perturbation tested.
  - `failure_threshold`: Degradation score above which a model is considered falsified.

### Model Sensitivities
Per-model sensitivity to different perturbation types. Used to calculate degradation scores.
- Models: `cs_procedural_generation`, `cs_glossolalia`, `cs_meaningful_construct`, `vg_adjacency_grammar`, `vg_containment_grammar`, `vg_diagram_annotation`.

### Evaluation Dimensions
Weights for comparative model evaluation.
- `prediction_accuracy` (0.30): How many model predictions match observed data.
- `robustness` (0.25): Ability to survive perturbations.
- `explanatory_scope` (0.20): Breadth of phenomena explained.
- `parsimony` (0.10): Simplicity of the model (fewer rules).
- `falsifiability` (0.15): Number of defined failure conditions.

---

## 2. Baselines (`configs/functional/baselines.json`)

Stores observed values from the Voynich MS and benchmark values for comparable system classes.

### Observations
- `info_density_z`: Observed information density z-score (baseline 4.0).
- `locality_min/max`: Observed locality radius window (2-4).
- `repetition_rate`: Observed token repetition rate (0.20).
- `vocabulary_size`: Approximate unique tokens in the section (8000).

### System Classes
Benchmark property ranges for:
- `random_markov_order_1/2`
- `constrained_markov`
- `glossolalia_human`
- `local_notation_system`
- `simple_substitution_cipher`
- `natural_language`
- `diagram_label_system`

### Stability Variants
Defined variants for representation stability testing (coarse/fine segmentation, alternate unit definitions).

---

## 3. Synthesis Parameters (`configs/functional/synthesis_params.json`)

Controls the generation of synthetic continuation pages and equivalence testing.

### Continuation Constraints
- `locality_window`: Target locality radius (2-4).
- `information_density_tolerance`: Allowed deviation from observed density.
- `repetition_rate_tolerance`: Allowed deviation from observed repetition.
- `max_novel_tokens`: Maximum percentage of tokens not found in the original section (0.10).

### Indistinguishability
- `scrambled_separation_threshold` (0.7): Minimum separation from scrambled controls.
- `real_separation_threshold` (0.3): Maximum separation from real pages (lower is better).

### Equivalence Testing
- `equivalence_threshold` (0.30): Separation score below which a gap is considered "closed".
- `improvement_threshold` (0.10): Minimum reduction in separation to be considered "meaningful improvement".
