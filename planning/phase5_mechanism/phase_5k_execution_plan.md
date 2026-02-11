# Phase 5K Execution Plan: Parsimony Collapse and Residual Dependency Audit

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5K  
**Phase Name:** Final Internal Collapse  
**Goal Type:** Explanatory sufficiency and residual ambiguity elimination  
**Primary Goal:** Determine whether the remaining escape hatch for a position-indexed explicit graph (augmented DAG) is **explanatorily admissible**, or whether the Voynich production phase5_mechanism must be classified as an **implicit, feature-conditioned constraint system** (lattice-like), by applying parsimony and residual-dependency tests.

---

## 0. Phase Position and Rationale

### 0.1 Why Phase 5K exists
Phase 5J established that:

- Successor determinism depends strongly on **position-in-line**.
- Pure word-local transition models are falsified.
- Global, feature-conditioned constraints are required.

However, one theoretical alternative remains:

> A high-dimensional explicit graph where nodes encode `(word, position)` or equivalent state.

Phase 5K exists to test whether this alternative is:
- explanatory and parsimonious, or
- formally eliminable as a compiled surrogate of a lattice.

This phase is not about predictive accuracy, but **model legitimacy**.

---

## 1. Phase 5K Core Questions

### 1.1 Core question A: Parsimony
Can a position-indexed explicit graph explain the observed behavior **without pathological complexity**?

### 1.2 Core question B: Residual dependency
Beyond position, does any additional path history materially contribute to successor determinism?

---

## 2. Competing Model Classes

### 2.1 M1: Augmented Explicit Graph (Position-Indexed DAG)
- Nodes represent `(word, position)` or `(word, slot)`.
- Successor edges are fixed and deterministic.
- No rule evaluation at runtime.

### 2.2 M2: Implicit Constraint System (Lattice-like)
- Nodes represent words only.
- Successors are evaluated dynamically via constraints:
  - position
  - word features
- Global rule set reused across all lines.

---

## 3. Design Principles

### 3.1 Explanatory economy
Models are evaluated on:
- state count
- rule count
- reuse of structure
not just output fidelity.

### 3.2 Compilation awareness
A model that merely *compiles* another at extreme cost is not explanatory.

### 3.3 Minimal residual scope
Once position is accounted for, any remaining dependency must be justified.

---

## 4. Test Family A: Parsimony and Compilation Cost (Former 4.1)

### 4.1 Node Explosion Analysis
**Objective:**  
Quantify the effective state space required for a position-indexed DAG to match Voynich successor behavior.

**Procedure:**
- Construct explicit graphs with nodes `(word, position)`.
- Measure:
  - total node count
  - edge count
  - connected components
- Compare against:
  - observed vocabulary size
  - line-length distribution

**Metric:**  
Node Explosion Factor = |States_DAG| / |Words_Voynich|

**Kill rule (C5K.PAR.1):**  
If the node explosion factor exceeds an order-of-magnitude threshold (pre-registered, e.g. >10x) without increasing explanatory clarity, M1 is eliminated.

---

### 4.2 Rule Compression Comparison
**Objective:**  
Compare descriptive complexity between M1 and M2.

**Procedure:**
- Encode both hookup tables and rule sets.
- Measure:
  - parameter count
  - description length (MDL proxy)
  - reuse of components across positions

**Kill rule (C5K.PAR.2):**  
If M2 achieves equal or better fit with substantially fewer parameters, M1 is eliminated as non-parsimonious.

---

## 5. Test Family B: Residual Dependency Audit (Former 4.2)

### 5.1 History Conditioning Sweep
**Objective:**  
Test whether dependencies beyond position materially affect successor determinism.

**Procedure:**
- Compare conditional entropy under:
  - (word)
  - (word, position)
  - (word, position, prefix depth)
  - (word, position, previous word class)

**Metric:**  
Incremental entropy reduction per added conditioning variable.

**Kill rule (C5K.RES.1):**  
If added history variables reduce entropy by less than a pre-registered epsilon (e.g. <5%), history-dependent models are eliminated.

---

### 5.2 Prefix Perturbation Test
**Objective:**  
Test whether changing early prefixes alters successors once `(word, position)` is fixed.

**Procedure:**
- Swap prefixes across lines while holding current word and position constant.
- Measure successor divergence.

**Kill rule (C5K.RES.2):**  
If divergence is indistinguishable from shuffled controls, path-history dependence is eliminated.

---

## 6. Generator and Comparator Suite

### 6.1 Simulators
Implement:
- Position-indexed explicit DAG simulator
- Implicit lattice simulator
- Adversarial hybrids

All simulators must match:
- successor forcing
- convergence
- coverage skew
- line-level entropy

---

## 7. Run Structure and Provenance

### 7.1 Run records
Each Phase 5K run logs:
- model class (M1 or M2)
- state count
- parameter count
- entropy metrics
- kill-rule outcomes

### 7.2 Folder structure

- `src/phase5_mechanism/parsimony/`
- `phase2_analysis/phase5_mechanism/parsimony/`
- `configs/phase5_mechanism/parsimony/`
- `runs/phase5_mechanism/<run_id>/`
- `results/phase5_mechanism/parsimony/`
- `reports/`

---

## 8. Outcome Classification

Each model receives exactly one label:

- **Eliminated (Non-Parsimonious)**
- **Sufficient**
- **Equivalent (Compiled Form)**
- **Non-Identifiable**

---

## 9. Phase 5K Termination Conditions

Phase 5K terminates when:

- Parsimony thresholds are evaluated, and
- Residual dependency effects are quantified, and
- One of the following holds:
  - M1 eliminated in favor of M2
  - M1 shown to be a compiled but non-explanatory form of M2
  - Formal non-identifiability is demonstrated

---

## 10. Interpretation Boundary

Phase 5K may conclude:
- Whether the remaining explicit-graph alternative is explanatorily admissible
- Whether the phase5_mechanism must be classified as an implicit constraint system

Phase 5K may not conclude:
- Anything about semantics or meaning
- Anything about historical intent

---

## 11. Phase 5K Termination Statement

Phase 5K evaluates whether the remaining position-indexed explicit graph explanation for the Voynich Manuscript is structurally and explanatorily viable, or whether it collapses into a compiled surrogate of an implicit constraint lattice. By applying parsimony and residual dependency tests, Phase 5K determines whether final internal identification is possible or whether the project must conclude with a formal identifiability boundary.

---

## 12. Immediate Next Actions

1) Pre-register parsimony thresholds  
2) Implement position-indexed DAG construction  
3) Compute node explosion and description length metrics  
4) Run residual dependency sweeps  
5) Apply kill rules  
6) Transition to Phase 6 (Formal Identification or Formal Closure)
