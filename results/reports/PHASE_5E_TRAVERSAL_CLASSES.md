# PHASE 5E TRAVERSAL DYNAMICS CLASSES

**Project:** Voynich Manuscript – Large-Object Traversal  
**Objective:** Define the rules governing how a scribe moves through a large deterministic structure.

---

## 1. Fixed Deterministic Walk
- **Definition:** Given a starting position (entry point), the entire sequence of the line is pre-ordained.
- **Rule:** $Pos_{n+1} = f(Pos_n)$.
- **Implication:** The scribe only needs to choose the start; the rest is a mechanical "unrolling."

## 2. Parameterized Deterministic Walk
- **Definition:** Each line starts with a small set of parameters (e.g., direction, skip rate) that determines the path.
- **Rule:** $Pos_{n+1} = f(Pos_n, 	heta)$.
- **Implication:** Allows multiple distinct lines to pass through the same node in different ways.

## 3. Rule-Evaluated Successor Selection
- **Definition:** The next node is chosen by evaluating a fixed global rule against the current state (e.g., "Find the next word that ends with the last glyph of the current word").
- **Rule:** $Pos_{n+1} = argmin_{v \in Adj(u)} Cost(v, State)$.
- **Implication:** The structure is emergent rather than explicit.

---
**Status:** Traversal classes frozen.  
**Next:** Pre-register necessary consequences.
