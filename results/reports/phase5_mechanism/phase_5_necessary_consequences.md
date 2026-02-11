# PHASE 5 NECESSARY CONSEQUENCES AND KILL RULES

**Project:** Voynich Manuscript – Identifiability Phase  
**Objective:** Pre-register the measurable properties that must be present for a mechanism class to remain admissible.

---

## 1. Class: Bounded Pool Reuse

### Consequence ID: C5.POOL.1 (Pool Exhaustion Dynamics)
- **Statement:** If tokens are drawn from a bounded pool, the rate of "novel" token introduction must follow a pool-exhaustion curve (high initial novelty, rapid decay to a replenishment baseline).
- **Observable proxy:** Cumulative vocabulary vs. token count (Heap's Law deviation).
- **Null model:** Open-vocabulary natural language (stable power-law growth).
- **Kill rule:** If the novelty rate does not show a statistically significant decay below the matched-language baseline, the bounded-pool class is eliminated.

### Consequence ID: C5.POOL.2 (Windowed TTR Stability)
- **Statement:** The Type-Token Ratio (TTR) within small locality windows must be lower than in globally matched natural language.
- **Observable proxy:** Mean TTR in a 50-token rolling window.
- **Kill rule:** If mean windowed TTR exceeds the matched-natural-language baseline, the class is eliminated.

---

## 2. Class: Table or Grille Selection

### Consequence ID: C5.TABLE.1 (Successor Set Sharpness)
- **Statement:** Table-based traversal forces a limited set of possible successors for any given state (row/column), creating abrupt constraints.
- **Observable proxy:** Entropy of the successor distribution per token, compared to its frequency.
- **Null model:** Stochastic Markov grammar.
- **Kill rule:** If successor distributions are indistinguishable from matched-stochastic-grammar controls, the hidden-state table model is eliminated.

### Consequence ID: C5.TABLE.2 (Hidden-State Recoverability)
- **Statement:** If a 2D table was used, there must exist a latent low-cardinality state model that predicts token transitions better than a standard Markov model.
- **Observable proxy:** Predictive lift of a latent-state model (e.g., HMM) vs. bigram baseline.
- **Kill rule:** If predictive lift is < 5% over matched-grammar controls, the class is eliminated.

---

## 3. Class: Copying with Systematic Mutation

### Consequence ID: C5.COPY.1 (Variant Family Clustering)
- **Statement:** Scribal copying produces "families" of near-identical tokens within local neighborhoods.
- **Observable proxy:** Count of token pairs within distance $D$ having edit distance $\le 1$.
- **Null model:** Pool-reuse without copying.
- **Kill rule:** If the frequency of near-duplicate neighbors does not exceed the matched-pool baseline, the copying model is eliminated.

---

## 4. Class: Multi-Stage Pipeline

### Consequence ID: C5.PIPE.1 (Residual Structural Fingerprinting)
- **Statement:** The final stage of a pipeline cannot fully mask the signatures of the primary stage. Remaining structure must be non-random.
- **Observable proxy:** Statistical significance of residuals after fitting the best single-stage survivor model.
- **Kill rule:** If the best single-stage model accounts for all measurable structure (Residual z < 2.0), the multi-stage class is eliminated as underdetermined or unnecessary.

---
**Status:** Necessary consequences registered.  
**Next:** Build matched comparator suite.
