# SCORING_GUIDELINES.md
## Phase B: Comparative and Contextual Classification

This document defines the scoring scale (0–5) for the comparison dimensions.

---

### General Scale Definition

- **0: Absent / Negligible**
  - The property is not present or is indistinguishable from noise.
- **1: Low / Weak**
  - The property is detectable but inconsistent or very weak.
- **2: Moderate / Mixed**
  - The property is a secondary feature or highly variable.
- **3: Strong / Consistent**
  - The property is a primary feature and consistently observed.
- **4: Very Strong / Extreme**
  - The property dominates the artifact's structure.
- **5: Near-Total / Definitional**
  - The property is an invariant rule or the defining characteristic of the artifact.

---

### Dimension-Specific Guidance (Examples)

#### 1. Determinism
- **0:** Stochastic (random walk).
- **3:** High-order Markov chain (e.g., natural language).
- **5:** Rigid table lookup or mathematical sequence.

#### 2. State-Space Sparsity
- **0:** Saturated (every possible state visited multiple times).
- **3:** Power-law distribution (standard vocabulary use).
- **5:** Ultra-sparse (almost every state is a hapax).

#### 5. Reuse Suppression
- **0:** Highly repetitive (mantras, simple loops).
- **3:** Efficient (avoids repetition where redundant).
- **5:** Pathological (actively suppresses repetition despite cost).

#### 9. Layout Coupling
- **0:** Geometric indifference (fluid text flow).
- **3:** Margin awareness (standard justification).
- **5:** Geometric determination (text form is dictated by shape/diagram).
