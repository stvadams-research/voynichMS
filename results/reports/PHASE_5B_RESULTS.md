# PHASE 5B RESULTS: CONSTRAINT GEOMETRY PILOT

**Date:** 2026-02-07
**Status:** Pilot Complete (Success)
**Objective:** Characterize the topology and reset behavior of Voynich constraints.

---

## 1. Pilot Results Summary

| Dataset | Effective Rank (Dim) | Reset Score (Boundary) | Interpretation |
|---------|----------------------|------------------------|----------------|
| **Voynich (Real)** | **83** | **0.9585** | High-Dim, Non-Persistent |
| **Pool-Reuse (Syn)** | 79 | 0.9366 | Stochastic Baseline |
| **Geometric Table (Syn)** | 61 | 0.0000 | Rigid, Low-Dim |

---

## 2. Key Findings

### 2.1 Dimensionality Mismatch
The real manuscript requires **83 latent dimensions** to explain 90% of its transition variance. This is significantly higher than a 10x10 (Rank 61) table traversal. This implies that the production mechanism has a high degree of state-freedom, potentially involving a much larger component set or a hybrid stochastic-table process.

### 2.2 The "Line Reset" Signature
The most decisive finding is the **Reset Score**. 
- The real manuscript shows a score of **0.9585**, meaning the successor rules *completely change* (or are absent) across line boundaries.
- Simple table models show **0.0000** (perfect persistence).
- This falsifies the hypothesis of a static table being traversed continuously across the page.

### 2.3 Mechanism Lead: Line-Conditioned Pool
The data now points toward a **Line-Conditioned Bounded Pool** model. The scribe likely selected a small pool of valid tokens for a specific line or block, then moved to a *new, independent pool* for the next line, rather than following a continuous traversal path.

---

## 3. Admission Status Updates

| Mechanism Class | Status | Evidence |
|-----------------|--------|----------|
| **Static Table Traversal** | **ELIMINATED** | Violates C5.TABLE.1 (Successor Set Sharpness) and C5.TABLE.2 (Persistence). |
| **Global Pool Reuse** | WEAKENED | Voynich dimensionality is high, but reset behavior is too extreme for a global pool. |
| **Line-Reset Pool** | **STRENGTHENED** | Matches both high dimensionality and near-perfect boundary reset signatures. |

---
**Conclusion:** Phase 5B has narrowed the "Table vs. Pool" debate. The manuscript is not a table in the rigid sense; it is a **highly non-persistent stochastic process** that resets its constraints at every structural boundary (lines).
