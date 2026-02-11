# 2. Methodology: The Assumption-Resistant Framework

## 2.1 Core Principles

The Assumption-Resistant Framework (ARF) is built on two epistemic commitments:

**Falsification over Confirmation.** For any hypothesis about the manuscript's production (e.g., "it is Italian," "it is a cipher"), we require it to survive perturbation analysis. If we scramble the text slightly and the hypothesis still holds — or if it collapses entirely — the hypothesis is structurally inadmissible. A robust explanation must degrade gracefully under noise, not survive only in pristine conditions.

**The Noise Floor.** If a non-semantic generator can produce the same statistical features as the manuscript, then those features cannot be used as proof of language. This is the "noise floor" principle: any metric that cannot distinguish the real manuscript from algorithmically generated text has no diagnostic power for semantic content.

## 2.2 Diagnostic Thresholds

The framework employs a suite of structural metrics, each with an empirically grounded threshold separating linguistic from non-linguistic production:

| Metric | Threshold | Voynich Value | Linguistic Expectation | Diagnostic Outcome |
|--------|-----------|---------------|------------------------|--------------------|
| Mapping Stability (S_stab) | > 0.60 | {{phase2.mapping_stability}} | 0.65 - 0.85 | {{phase2.mapping_stability_outcome}} |
| Token Repetition Rate | < 0.35 | {{phase1.repetition_rate}} | 0.20 - 0.30 | Excluded |
| Successor Consistency | < 0.10 | {{phase5.5e.successor_consistency}} | 0.02 - 0.08 | Excluded |
| Reset Score | < 0.40 | {{phase5.5b.reset_score}} | 0.10 - 0.30 | Excluded |

## 2.3 Admissibility Gates

Each research phase functions as an admissibility gate. A candidate production model must pass all gates to remain viable. The gates are ordered from broadest exclusion to finest discrimination:

1. **Distributional Gate** (Phase 1) — Does the candidate predict the observed token frequency distribution?
2. **Stability Gate** (Phase 2) — Does the candidate survive perturbation without structural collapse?
3. **Sufficiency Gate** (Phase 3) — Can a non-semantic process reproduce the same features?
4. **Inference Gate** (Phase 4) — Do diagnostic methods distinguish real data from controls?
5. **Mechanism Gate** (Phase 5) — What minimal state machine is forced by the evidence?
