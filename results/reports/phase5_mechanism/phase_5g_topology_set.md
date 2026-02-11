# PHASE 5G TOPOLOGY SET: LARGE-OBJECT CANDIDATES

**Project:** Voynich Manuscript – Topology Collapse  
**Objective:** Define the frozen set of topological models to be tested for non-equivalence.

---

## 1. Topological Classes

All models are instantiated with a target vocabulary size of >3,000 nodes to match Phase 5F entry-diversity estimates.

### 1.1 Rectangular Grid ($M 	imes N$)
- **Configuration:** $60 	imes 60$ grid (3,600 nodes).
- **Adjacency:** Orthogonal and diagonal (8-neighbor).
- **Traversal:** Fixed displacement rule ($dx=+1, dy=0$).

### 1.2 Layered Tables (Sheet Stack)
- **Configuration:** 10 sheets of $20 	imes 20$ grids (4,000 nodes total).
- **Adjacency:** Within-sheet grid adjacency.
- **Traversal:** Select sheet $k$, follow fixed walk.

### 1.3 Directed Acyclic Graph (DAG)
- **Configuration:** 4,000 nodes with stratified layer structure.
- **Connectivity:** Each node has exactly one deterministic successor (determined by a fixed rule).
- **Traversal:** Follow the only available edge.

### 1.4 Constraint Lattice
- **Configuration:** Abstract state space defined by 3-glyph "slot rules."
- **Mechanism:** $NextWord = f(CurrentWord, Position)$.
- **Traversal:** Implicit path-finding.

---
**Status:** Topology set frozen.  
**Next:** Pre-register necessary consequences and implement simulators.
