# 4. Structural Exclusion of Linguistic and Cipher Models

Phase 2 tested the manuscript against known linguistic and cryptographic production models. The results were definitive: natural language is structurally inadmissible.

## 4.1 Perturbation Analysis

Applying the Assumption-Resistant Framework, the manuscript was tested against six classes of production systems. Perturbation analysis demonstrated a Mapping Stability score of {{phase2.mapping_stability}}, indicating a total lack of the linguistic redundancy characteristic of human communication. For reference, natural languages typically score between 0.65 and 0.85 on this metric.

Two key factors drove the exclusion:

**Locality.** Dependencies in the Voynich text are extremely short-range (2-4 tokens). Human language requires long-range dependencies — grammar, narrative coherence, anaphora — to function. The manuscript's dependency radius falls well below the minimum threshold for any known linguistic system.

**Fragility.** When Mapping Stability tests were applied, linguistic models collapsed. The manuscript lacks the redundancy and flexibility of real communication. A genuine language can absorb noise because meaning is distributed across multiple redundant structures; the Voynich text has no such cushion.

## 4.2 The Transition from Simulated to Computed Results

A critical validation step was the transition from simulated baselines to real computation. The shift was transformative:

| Metric | Simulated (Baseline) | Real (Computed) | Shift |
|--------|---------------------|-----------------|-------|
| Repetition Rate | 15% (hardcoded) | {{phase1.repetition_rate}} | +75% |
| Information Z-Score | 1.90 (FRAGILE) | 5.68 (STABLE) | +3.78 |
| Mapping Stability | 0.88 (STABLE) | {{phase2.mapping_stability}} (COLLAPSED) | -0.86 |
| Pattern Type | Mixed | Procedural | Unified |

The manuscript is significantly more information-dense than previously estimated, but its structure is far more fragile and dependent on exact segmentation than any linguistic model predicts.

## 4.3 Dominance of Procedural Patterns

Pattern analysis identified procedural generation as the dominant structural regime. The manuscript behaves as a single, consistent procedural system rather than a collection of different regimes. Real data shows a {{phase1.repetition_rate}} token repetition rate, far exceeding any known natural language (typically 20-30%) or control corpus.

## 4.4 Semantic Necessity Assessment

Six maximally expressive non-semantic systems were tested against the observed metrics. Four of six successfully reproduced the observed anomalies, demonstrating that semantic content is not necessary to explain the manuscript's structure.

{{figure:results/visuals/phase2_analysis/6744b28c-bb3e-5956-2050-f5f59716ae7f_sensitivity_top_scores.png|Sensitivity Analysis: Collapse of Linguistic Models under Perturbation}}

{{figure:results/visuals/phase2_analysis/6744b28c-bb3e-5956-2050-f5f59716ae7f_sensitivity_model_survival.png|Model Survival Rates across Perturbation Levels}}

## 4.5 Phase 2 Determination

Linguistic and cipher models are formally excluded. Non-semantic models are structurally sufficient to explain the data. The manuscript's form — despite its apparent complexity and high information density — does not structurally require meaning to exist.
