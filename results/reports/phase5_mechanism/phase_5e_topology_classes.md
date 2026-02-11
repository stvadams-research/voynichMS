# PHASE 5E TOPOLOGY CLASSES: LARGE DETERMINISTIC STRUCTURES

**Project:** Voynich Manuscript – Large-Object Traversal  
**Objective:** Define the topological families of large objects capable of supporting deterministic line production.

---

## 1. Rectangular or Ragged Grids
- **Description:** Nodes arranged in a fixed grid ($M 	imes N$). Adjacency is based on row/column/diagonal proximity.
- **Mechanism:** Scribe moves a "grille" or follows a fixed displacement rule.
- **Strengths:** High local forcing; easy to implement with physical tools.
- **Vulnerabilities:** Over-imposes symmetry; might fail to match the sheer variety of Voynich word patterns.

## 2. Layered Tables or Sheets
- **Description:** A stack of grids. A line is produced by selecting a layer, then traversing it.
- **Mechanism:** $L = Traversal(Layer_k, Start_i)$. 
- **Strengths:** Explains how the global vocabulary can be large while each line is rigidly constrained.
- **Vulnerabilities:** Requires a phase5_mechanism for selecting the layer that doesn't leak into the text.

## 3. Directed Acyclic Graphs (DAGs)
- **Description:** A network of components where edges define the only allowed sequences.
- **Mechanism:** Each line is a path from a "Start" node to an "End" node.
- **Strengths:** Can represent complex grammatical rules deterministically.
- **Vulnerabilities:** High risk of overfitting; requires many nodes to match Voynich's global entropy.

## 4. Constraint Lattices
- **Description:** An abstract space where the next token is the only one satisfying a set of ordered constraints.
- **Mechanism:** $Word_{n+1} = Unique(Constraints(Word_n, Position))$.
- **Strengths:** Natural explanation for "Scale Paradox" (high global entropy, low local).
- **Vulnerabilities:** Mechanically complex for a 15th-century scribe.

---
**Status:** Topology classes frozen.  
**Next:** Define traversal dynamics.
