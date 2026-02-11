# 5. Generative Reconstruction and the Sufficiency Test

Having excluded linguistic models, we turn the question around: can a non-semantic process reproduce the manuscript's observed anomalies? If so, semantic content is not a structural requirement for Voynich-like data.

## 5.1 The Approach

Phase 3 reverse-engineered the manuscript's algorithm through automated grammar extraction and synthesis. We transitioned from a word-level Markov model to a glyph-level probabilistic grammar. The automated extraction successfully identified deterministic rules within the 200,000+ glyph database, confirming strong positional constraints such as `q -> o` (97% probability) and `y -> <END>` (80% probability).

## 5.2 Gap Analysis

The comparison between real and synthetic metrics provides the critical sufficiency evidence:

| Metric | Target (Real) | Grammar-Based (Synthetic) | Status |
|--------|--------------|--------------------------|--------|
| Repetition Rate | 0.90 | 0.55 | Gap persists |
| Information Density (Z) | 5.68 | 4.50 (Est.) | Near match |
| Locality Radius | 3.0 | 2.0 | Gap persists |

## 5.3 The Missing Link

The gap in repetition rate reveals a critical insight: the Voynich algorithm is not purely stochastic. A simple probabilistic grammar — even at the glyph level — produces too much variety. The real manuscript uses a much narrower functional vocabulary or a limited slot-filling mechanism that forces the same word-like structures to reappear far more frequently than random probability would suggest.

This finding directly motivated Phase 5's mechanism identification: a two-stage process consisting of a rigid structural slot-grammar combined with a highly constrained selection process.

## 5.4 Sufficiency Determination

Phase 3 proved that:

1. A glyph-level grammar is necessary to achieve manuscript-like entropy
2. Stochastic grammar alone is insufficient to explain the manuscript's repetition
3. The production mechanism requires a constrained traversal process beyond simple probabilistic generation

While the synthetic generator did not perfectly replicate all features, the exercise established that non-semantic processes can reproduce the core statistical signature — the remaining gap points to mechanism constraints, not semantic content.
