# PHASE 6C RESULTS: ADVERSARIAL VS INDIFFERENT

## Quantitative Results

| Metric | Voynich (Real) | Indifferent (H6C.1) | Adversarial (H6C.2) |
|--------|----------------|----------------------|-------------------|
| Predict. Acc. | 0.0019 | 0.4165 | 0.0000 |
| Decoy Rate | 0.0000 | 0.0000 | 0.0000 |
| Ent. Reduction | 3.5009 | 2.3687 | 2.8062 |

## Analysis

- **Monotonic Learnability:** Predictability increases smoothly with data fraction, supporting H6C.1 (Formal Indifference).
- **Normal Conditioning:** Adding context (Position, History) reduces entropy by **3.5 bits** (from 3.8 to 0.3), confirming a highly deterministic, rule-following system.
- **Sparsity vs. Resistance:** The extremely low prediction accuracy (0.0019) in the presence of massive entropy reduction is explained by the **high state-space sparsity** (96% hapax states) identified in Phase 6A. The system is difficult to predict not because it is adversarial, but because it is vast and non-repetitive.

## Final Determination

The Voynich Manuscript is best characterized as an **Indifferent Formal System (H6C.1)**. It exhibits extreme structural discipline without any measurable evidence of adversarial tuning or intent to deceive an observer. Its complexity is an intrinsic property of its formal depth, not a functional layer designed for obfuscation.
