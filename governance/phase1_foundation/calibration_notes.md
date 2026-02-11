# Calibration and Threshold Justification

This document provides the statistical and methodological rationales for the various heuristic thresholds used across the Voynich MS phase2_analysis pipeline.

## 1. Information Theory Thresholds

### 1.1 Topical Keyword Threshold (1.0 bits)
- **Used in:** `MontemurroAnalyzer` (`src/phase4_inference/info_clustering/analyzer.py`)
- **Rationale:** A mutual information score of 1.0 bits suggests that the presence of a word reduces uncertainty about the section identity by half. This is a standard conservative cutoff for "high-information" keywords in unsupervised topic induction.

### 1.2 Morphological Suffix Threshold (Top 20)
- **Used in:** `MorphologyAnalyzer` (`src/phase4_inference/morph_induction/analyzer.py`)
- **Rationale:** Based on the Zipfian distribution of Voynichese suffixes, the top 20 candidates typically cover >80% of morphological variations.

## 2. Stability and Perturbation Thresholds

### 2.1 High-Confidence Stability (0.7)
- **Used in:** `MappingStabilityTester` (`src/phase2_analysis/stress_tests/mapping_stability.py`)
- **Rationale:** 0.7 represents a strong majority agreement. In noise-sensitive systems like the Voynich MS, mappings that fall below this level under minor (5%) perturbation are considered structurally unsupported.

### 2.2 Model Disconfirmation Thresholds (0.5 - 0.7)
- **Used in:** `DisconfirmationEngine` (`src/phase2_analysis/models/disconfirmation.py`)
- **Rationale:**
  - **0.5 (Anchor Disruption):** Anchors are direct geometric relationships; losing more than 50% under perturbation is considered a catastrophic failure of the spatial model.
  - **0.6 (Segmentation/Ordering):** These tests affect the internal "texture" of the text. A 40% survival rate is the minimum required to maintain statistical signatures like Markov properties.
  - **0.7 (Omission):** Natural languages and robust codes have high redundancy. Systems that collapse with <70% of their elements are considered too fragile to be plausible communication systems.

## 3. Synthesis and Equivalence Thresholds

### 3.1 Equivalence Threshold (0.30)
- **Used in:** `EquivalenceTest` (`src/phase3_synthesis/refinement/interface.py`)
- **Rationale:** A separation score of 0.30 represents the "near-chance" boundary where synthetic data becomes statistically indistinguishable from the real manuscript given the current feature set.

### 3.2 Improvement Threshold (0.10)
- **Used in:** `EquivalenceTest`
- **Rationale:** A reduction in separation of 0.10 is required to distinguish meaningful structural refinement from random noise in the phase3_synthesis process.

## 4. Model Sensitivity Rationales

Each explanation model has a hardcoded sensitivity profile used to calculate degradation under perturbation.

### 4.1 Constructed System Models (CS Series)
- **Procedural Generation (0.20-0.30):** Low sensitivity because mechanical algorithms lack semantic "fragility." Order (0.30) matters more than segmentation (0.20).
- **Glossolalia (0.35-0.40):** Moderate sensitivity mimicking natural language graphs. Reordering (0.40) is the primary failure mode.
- **Meaningful Construct (0.35-0.45):** Highest sensitivity in the CS class due to assumed idiosyncratic but "meaningful" structure. Omission (0.45) is most disruptive.

### 4.2 Visual Grammar Models (VG Series)
- **Adjacency Grammar (0.70 Anchor):** Extremely high sensitivity to anchor disruption (0.70) as it is the core claim of the model.
- **Containment Grammar (0.60 Anchor):** High sensitivity to container integrity. Omission (0.45) and anchor disruption (0.60) are key falsifiers.
- **Diagram Annotation (0.80 Anchor):** Critical dependence on diagram proximity. This model is designed to collapse almost immediately (0.80) if text-to-diagram links are broken.

## 5. Centralized Analysis Thresholds (`configs/phase2_analysis/thresholds.json`)

### 5.1 Mapping Stability
- `perturbation_strength=0.05`:
  Theoretical/conventional. Small boundary perturbation used to test local robustness.
- `constructed_system.ordering_collapse=0.5`:
  Theoretical. Below chance-level ordering survival implies collapse for rule-driven systems.
- `constructed_system.min_stable=0.6`:
  Conventional. Minimum robustness floor for practical stability.
- `visual_grammar.segmentation_collapse=0.4`:
  Empirical (Phase 2 stress behavior) with conservative margin.
- `visual_grammar.min_stable=0.5`:
  Conventional midpoint threshold.
- `hybrid_system.variance_limit=0.3`:
  Theoretical. Large spread across perturbations indicates unstable mixed phase5_mechanism.
- `standard_high_confidence=0.7`:
  Conventional high-confidence cutoff used across stress reporting.

### 5.2 Locality
- `radius_thresholds=[2.0,1.5,1.0]`:
  Empirical/conventional. Maps locality ratios to local/moderate/global regimes.
- `compositional_scores=[0.7,0.5,0.3]`:
  Conventional three-band score partition.
- `procedural_signature.repetition=0.15`:
  Empirical from control behavior where higher repetition flags mechanical generation.
- `procedural_signature.regularity=0.7`:
  Conventional high-regularity cutoff.
- `procedural_signature.combined=0.6`:
  Conventional combined indicator threshold.
- `pattern_type.min_radius=4`, `pattern_type.max_radius=8`, `pattern_type.score_threshold=0.5`:
  Theoretical defaults for local-vs-global grouping.
- `outcome.stable=0.6`, `outcome.collapsed=0.4`:
  Conventional stability bands.

### 5.3 Indistinguishability and Comparison
- `indistinguishability.separation_success=0.7`:
  Conventional strong-separation requirement for scrambled controls.
- `indistinguishability.separation_failure=0.3`:
  Conventional near-chance boundary for real-vs-synthetic separation.
- `comparator.significant_difference=0.05`:
  Conventional effect cutoff for "SURVIVES".
- `comparator.negligible_difference=0.02`:
  Conventional weak-effect cutoff for "PARTIAL".

### 5.4 Stability Analysis and Constraint Formalization
- `stability_analysis.representation_sensitivity.high=1.0`:
  Theoretical large-shift threshold.
- `stability_analysis.representation_sensitivity.moderate=0.5`:
  Conventional medium-shift threshold.
- `stability_analysis.representation_sensitivity.low=0.3`:
  Conventional small-shift threshold.
- `constraint_formalization.feature_importance_threshold=0.2`:
  Empirical/conventional minimum effect size for candidate constraints.
- `constraint_formalization.separation_threshold=0.3`:
  Conventional minimum real-vs-scrambled separation for formalization.
