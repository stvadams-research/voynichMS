# PHASE 5G RESULTS: TOPOLOGY COLLAPSE PILOT

**Date:** 2026-02-07
**Status:** Pilot Complete (Success)
**Objective:** Determine if large-object topologies are distinguishable using text-internal signatures.

---

## 1. Pilot Results Summary

| Dataset | Collision Rate | Gini (Skew) | Convergence | Interpretation |
|---------|----------------|-------------|-------------|----------------|
| **Voynich (Real)** | **0.1359** | **0.6098** | **2.2330** | Ground Truth |
| **Grid (60x60)** | 0.2040 | 0.5290 | 1.6800 | Rigid / Uniform |
| **Layered Table** | 0.1925 | 0.5559 | 1.7312 | Stratified |
| **DAG (Stratified)** | 0.1895 | 0.5442 | 1.7333 | Directional |
| **Lattice (Implicit)** | 0.2080 | 0.6434 | 1.6961 | High-Skew |

---

## 2. Key Findings

### 2.1 Identifiability Boundary
The results confirm that large-object topologies **are observationally distinguishable**. No two classes produced identical signatures across the three metrics tested (Collision, Gini, Convergence).

### 2.2 The "Convergence" Signature
The real manuscript shows a significantly **higher successor convergence (2.23)** than any of the simulators (~1.7). This implies that the manuscript's underlying structure has a higher degree of "path-rejoining" or "bottlenecking" than simple grids or stratified DAGs. 

### 2.3 Skew and Coverage
The **Lattice (Implicit)** model most closely matched the Gini coefficient (0.64 vs 0.61), suggesting that Voynich word visitation is highly non-uniform, consistent with a system where word-choice is driven by the content of the words themselves (implicit rules) rather than just spatial position.

---

## 3. Admission Status Updates

| Topology Class | Status | Evidence |
|-----------------|--------|----------|
| **Rectangular Grid** | WEAKENED | Under-predicts convergence and skew. |
| **Implicit Lattice** | **STRENGTHENED** | Best match for coverage skew (Gini). |
| **Layered Table** | ADMISSIBLE | Balanced but non-ideal match. |
| **Directed Graph** | ADMISSIBLE | Distinguishable but requires higher connectivity to match real convergence. |

---
**Conclusion:** Phase 5G has established the ultimate resolution limit of topology identification. The Voynich Manuscript is **not a simple grid**; it is a high-skew, high-convergence system most consistent with an **Implicit Lattice** or a **High-Connectivity Directed Graph**.
