# PHASE 5B: CONSTRAINT GEOMETRY FRAMEWORK

**Project:** Voynich Manuscript – Identifiability Phase (Refinement)  
**Objective:** Characterize the topology and dimensionality of the constraints governing token succession.

---

## 1. Dimensionality and Latent States

We characterize the "internal degrees of freedom" required to explain successor constraints.

- **State Cardinality ($K$):** The number of inferred latent states.
  - Low ($K < 50$): Consistent with mechanical tables or small-grid traversals.
  - High ($K > 500$): Consistent with open-vocabulary languages or large stochastic grammars.
- **Predictive Lift:** The increase in successor predictability when assuming $K$ hidden states versus a simple bigram model.

---

## 2. Transition Sparsity and Sharpness

We measure how "abruptly" the system restricts the possible next tokens.

- **Successor Entropy Distribution:** The distribution of Shannon entropy across all token types.
- **State Sparsity:** The ratio of observed transitions to the total possible state-to-token mappings.
- **Constraint Asymmetry:** Identification of specific tokens (e.g., positional markers) that act as "bottlenecks" or "reset points" in the generation process.

---

## 3. Locality and Reset Dynamics

We evaluate the temporal/linear stability of the constraint regimes.

- **Regime Persistence:** The distance over which a latent state remains predictive.
- **Boundary Resets:** Statistical evidence of constraint resets at line, page, or quire boundaries.
- **Reset Signature:** Comparison of transition matrices immediately before and after structural boundaries.

---

## 4. Pre-Registered Test Methods

1.  **HMM-Inference (Latent State Recovery):** Use Hidden Markov Models with varying $K$ to measure the elbow point of predictive gain.
2.  **Windowed Entropy Tracking:** Calculate successor entropy in sliding windows to detect regime shifts.
3.  **Boundary-Conditioned Transition Analysis:** Compare inter-line and intra-line transition matrices.

---
**Status:** Framework registered.  
**Next:** Implement latent state recovery and reset tests.
