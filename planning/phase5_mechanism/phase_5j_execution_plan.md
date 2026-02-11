# Phase 5J Execution Plan: Dependency Scope and Constraint Locality

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5J  
**Phase Name:** Dependency Scope Identifiability  
**Goal Type:** Final internal discrimination within a single deterministic mechanism  
**Primary Goal:** Determine whether successor determinism in the Voynich Manuscript is governed by **purely local transition rules** (explicit high-connectivity graph / DAG-like) or by **feature- or state-conditioned constraints** (implicit lattice / rule-evaluated system), using text-internal evidence only.

---

## 0. Phase Position and Rationale

### 0.1 Why Phase 5J exists
After Phases 5G and 5I, the project has established:

- A single global deterministic mechanism
- Independent per-line entry
- Large state space (>3,000 effective nodes)
- High successor forcing and convergence
- Structural invariance across sections

Exactly **one internal ambiguity remains**:

> Where do the constraints live?

Phase 5J is the last admissible internal step before formal closure.

---

## 1. Phase 5J Core Question

### 1.1 Core question
Does successor forcing depend **only on the current word/token** (local transition), or does it depend on **properties of the word, position, or accumulated path state** (global or feature-conditioned constraint)?

### 1.2 Competing hypotheses

**H1: Local Transition Model (Explicit Graph / DAG-like)**  
- Successor is fully determined by the current node.
- Identical words always imply identical successor sets, regardless of context.

**H2: Feature-Conditioned Model (Implicit Constraint Lattice)**  
- Successor depends on evaluable properties of the current word and/or path state.
- Identical words can diverge in successor behavior when features differ.

---

## 2. Design Principles

### 2.1 Minimal sufficiency
Assume local dependency unless additional scope is empirically required.

### 2.2 Scope over fit
The objective is not higher predictive accuracy per se, but identification of **dependency scope**.

### 2.3 Feature neutrality
Features are treated as formal properties only:
- glyph composition
- length
- affix structure
- positional class

No semantic interpretation is permitted.

### 2.4 Adversarial equivalence testing
Every test must be paired with adversarial controls designed to spoof the competing hypothesis.

---

## 3. Pre-Registered Necessary Consequences and Kill Rules

### 3.1 C5J.LOC.1 (Context Sufficiency)
**Statement:**  
If constraints are local, conditioning on features beyond the current word should not significantly increase successor predictability.

**Observable proxy:**  
Predictive lift of feature-augmented successor models over node-only models.

**Kill rule:**  
If feature-conditioned models produce statistically significant and robust predictive lift beyond adversarial DAG controls, H1 is eliminated.

---

### 3.2 C5J.GLOB.1 (Feature Sensitivity)
**Statement:**  
If constraints are global, successor identity must correlate with measurable word features even when the current word is held constant.

**Observable proxy:**  
Mutual Information between successor identity and feature vectors conditioned on current word.

**Kill rule:**  
If MI collapses to shuffled-control levels under conditioning, H2 is eliminated.

---

### 3.3 C5J.HIST.1 (Path Dependence)
**Statement:**  
If path history matters, identical words appearing at different line positions or prefix histories must diverge in successor behavior.

**Observable proxy:**  
Successor divergence rate for identical words across distinct prefix contexts.

**Kill rule:**  
If divergence is indistinguishable from noise, history-dependent models are eliminated.

---

## 4. Signature Test Families

### 4.1 Node-only vs feature-conditioned prediction
**Objective:**  
Compare successor prediction under:
- node-only models
- node + feature models
- node + position models
- node + prefix-depth models

**Evaluation:**  
Cross-validated predictive lift relative to matched adversarial generators.

---

### 4.2 Equivalence class splitting
**Objective:**  
Test whether tokens that are identical as nodes split into distinct successor classes when conditioned on features.

**Metrics:**
- Conditional entropy reduction
- Successor-set partition purity

---

### 4.3 Prefix-history perturbation
**Objective:**  
Hold the current word fixed while perturbing earlier prefixes.

**Metrics:**
- Successor stability under prefix swaps
- Context sensitivity curves

---

### 4.4 Adversarial compilation tests
**Objective:**  
Attempt to compile feature-conditioned rules into explicit graphs.

**Metrics:**
- Node explosion factor
- Predictive fidelity loss
- Overfitting thresholds

---

## 5. Generator and Comparator Suite

### 5.1 Dependency simulators
Implement minimal generators for:
- Pure local-transition (DAG-like)
- Feature-conditioned lattice-like
- Hybrid adversarial controls

Traversal and entry rules fixed across all simulators.

### 5.2 Matching requirements
Simulators must match Voynich on:
- successor forcing rate
- convergence
- coverage skew
- line-level entropy

---

## 6. Run Structure and Provenance

### 6.1 Run manifest additions
Each Phase 5J run records:
- dependency hypothesis
- feature set definition
- conditioning scope
- predictive lift metrics
- consequence pass/fail status

### 6.2 Folder structure

- `src/phase5_mechanism/dependency_scope/`
- `phase2_analysis/phase5_mechanism/dependency_scope/`
- `configs/phase5_mechanism/dependency_scope/`
- `runs/phase5_mechanism/<run_id>/`
- `results/phase5_mechanism/dependency_scope/`
- `reports/`

---

## 7. Outcome Classification

### 7.1 Possible outcomes
Each hypothesis receives exactly one label:

- **Eliminated**
- **Sufficient**
- **Equivalent**
- **Non-identifiable**

### 7.2 Resolution logic
- If one hypothesis is eliminated, Phase 5J collapses the mechanism class.
- If both remain, Phase 5J establishes a formal identifiability boundary.

---

## 8. Interpretation Boundary

Phase 5J may conclude:
- Whether successor constraints are local or feature-conditioned
- Whether dependency scope is identifiable from text alone

Phase 5J may not conclude:
- Anything about semantics, meaning, or language
- Anything about historical intent or purpose

---

## 9. Phase 5J Termination Statement

Phase 5J evaluates the dependency scope of successor constraints in the Voynich Manuscript. By discriminating between local transition rules and feature-conditioned constraints, Phase 5J determines whether the remaining admissible internal models can be collapsed using text-internal evidence alone, or whether an irreducible identifiability boundary has been reached.

---

## 10. Immediate Next Actions

1) Freeze feature sets and dependency hypotheses  
2) Implement node-only and feature-conditioned predictors  
3) Build adversarial simulators  
4) Execute predictive lift and divergence tests  
5) Apply kill rules  
6) Transition to Phase 6 (Formal Identification or Formal Closure)
