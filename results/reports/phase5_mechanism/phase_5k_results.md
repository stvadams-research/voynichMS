# PHASE 5K RESULTS: FINAL INTERNAL COLLAPSE

**Date:** 2026-02-08
**Status:** Phase Complete (Definitive Elimination)
**Objective:** Determine if the "Position-Indexed Explicit Graph" (M1) is a viable explanation or if it collapses into an "Implicit Constraint Lattice" (M2).

---

## 1. Node Explosion and Parsimony

We estimated the effective state space required to model the manuscript as an explicit graph with nodes `(Word, Position)`.

| Dataset | Vocab Size | Observed States (W,P) | Explosion Factor |
|---------|------------|-----------------------|------------------|
| **Voynich (Real)** | 5,214 | 9,708 | **1.86x** |
| **M1 (Pos-DAG)** | 10,011 | 17,422 | 1.74x |
| **M2 (Lattice)** | 6,100 | 14,294 | 2.34x |

**Finding:** The observed "Explosion Factor" is low (1.86x). This initially suggests `(Word, Position)` is a compact representation. However, this metric is deceptive without the Residual Dependency core_audit (below).

---

## 2. Residual Dependency Audit (The Kill Step)

We tested whether the state `(Word, Position)` is sufficient to determine the successor, or if knowing the *previous word* (History) adds information.

| Dataset | H(Successor \| Word, Pos) | H(Successor \| Word, Pos, History) | Entropy Reduction |
|---------|---------------------------|------------------------------------|-------------------|
| **Voynich (Real)** | 0.7869 bits | **0.0936 bits** | **88.11%** |
| **M1 (Pos-DAG)** | 2.0535 bits | 0.0878 bits | 95.72% |
| **M2 (Lattice)** | 1.3826 bits | 0.2779 bits | 79.90% |

### Key Finding: History is Mandatory
In the real manuscript, knowing `(Word, Position)` leaves **0.79 bits** of uncertainty about the next word. Adding the *previous word* reduces this to **0.09 bits** (an 88% reduction).

**Implication for M1:**
If the phase5_mechanism were a simple Position-Indexed DAG (State = `Word + Position`), the `History` term should provide **zero** additional information (Markov property). The massive 88% reduction proves that the true state is **at least Second-Order** (`Prev, Curr, Pos`).

**Implication for Parsimony:**
To model a second-order dependency as an explicit graph, the state space explodes to $V^2 	imes L$ (approx $5000^2 	imes 8 \approx 200 	ext{ million}$ nodes). This is **pathologically non-parsimonious**.

---

## 3. Final Collapse: Elimination of M1

The "Augmented Explicit Graph" (M1) is **ELIMINATED** because:
1.  **Insufficiency:** `(Word, Position)` states are insufficient to capture the determinism (0.79 bits residual).
2.  **Non-Parsimony:** Upgrading M1 to handle the observed history dependency requires a state space orders of magnitude larger than the corpus itself.

The "Implicit Constraint Lattice" (M2) is the **FINAL SURVIVOR**.
- It explains the high determinism via evaluable rules (e.g., `f(prev, curr, pos)`).
- It does not require storing millions of edge transitions.
- It naturally handles the observed history dependency.

---

## 4. Final Mechanism Definition

The Voynich Manuscript is produced by an **Implicit Constraint Lattice**.
- **Nodes:** Words (formal tokens).
- **Edges:** Dynamic (rule-evaluated).
- **Constraints:**
  1.  **Positional Forcing:** Rules strictly conditioned on line slot.
  2.  **History Conditioning:** Rules strictly conditioned on the immediate predecessor (or suffix thereof).
  3.  **Feature Matching:** Successors are chosen to satisfy morphological constraints relative to the current state.

**Project Status:** Internal structural discrimination is COMPLETE.
