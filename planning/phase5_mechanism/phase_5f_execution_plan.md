# Phase 5F Execution Plan: Entry-Point Selection and Path Parameterization

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5F  
**Phase Name:** Entry-Point Identifiability  
**Goal Type:** Path-instance inference under fixed deterministic traversal  
**Primary Goal:** Infer how entry points and minimal path parameters are selected for each line when traversing a large deterministic structure, and determine whether those selections are independent, structured, or externally anchored, without invoking semantics.

---

## 1. Phase 5F Purpose and Core Question

### 1.1 Core question
Given a fixed global traversal rule over a large deterministic object, how are per-line entry points and minimal parameters selected, and what structure governs their distribution across the manuscript?

### 1.2 Why Phase 5F exists
Phase 5E established that:
- Successor forcing is global and deterministic.
- Lines are paths through a static structure.
- Line boundaries reset traversal state but not rules.

What remains unknown is the **selection mechanism** that chooses where and how each line enters the structure.

### 1.3 What Phase 5F is not
- Not a decoding attempt.
- Not a semantic or linguistic analysis.
- Not a claim about historical intent.
- Not a test of alternative traversal rules.

Phase 5F assumes the traversal rule is fixed and studies only path instantiation.

### 1.4 Success criteria
Phase 5F is successful if it produces:
- A constrained model of entry-point selection.
- Bounds on the number and nature of path parameters.
- Evidence for independence, coupling, or anchoring of entry points.
- Elimination of entry mechanisms incompatible with observed path statistics.

---

## 2. Phase 5F Design Principles

### 2.1 Fixed traversal, variable entry
Traversal dynamics identified in Phase 5E are treated as invariant.
All variability is attributed to entry-point and parameter selection.

### 2.2 Line-level independence as null
The default hypothesis is that entry points are independently sampled per line.
Departures from independence must be demonstrated.

### 2.3 Minimal parameterization
Prefer the smallest parameter set that explains observed diversity.
Any extra parameter must be justified by a necessary consequence.

### 2.4 Text-internal evidence only
No appeal to illustrations, herbal sections, or external metadata unless explicitly tested as an anchor.

---

## 3. Entry-Point Abstraction

### 3.1 Definition
An entry point is the initial state of a traversal instance for a line, consisting of:
- Starting node or position in the large object.
- Optional traversal parameters that affect the path deterministically.

### 3.2 Candidate parameter types
- Start position index.
- Direction or orientation.
- Step size or skip pattern.
- Layer or sheet selection, if applicable.

These parameters must reset fully at each line.

---

## 4. Entry-Point Hypothesis Classes

### 4.1 Uniform Independent Entry
- Entry points sampled uniformly from the object.
- No coupling between adjacent lines.

**Vulnerability:** May fail to explain clustering or repetition patterns.

### 4.2 Locally Coupled Entry
- Entry points weakly correlated across adjacent lines.
- Coupling decays rapidly with distance.

**Vulnerability:** Risks violating Phase 5B reset signatures.

### 4.3 Section-Anchored Entry
- Entry points drawn from restricted subsets per page or section.
- Anchors may be layout-driven but not semantic.

**Vulnerability:** Over-predicts block-level regularities.

### 4.4 Parameter-Driven Entry
- Entry determined by a small parameter vector rather than a raw position.
- Many paths share parameters but start at different nodes.

**Vulnerability:** Risk of hidden state persistence.

Deliverable:
- `reports/PHASE_5F_ENTRY_CLASSES.md`

---

## 5. Necessary Consequences at the Entry Level

### 5.1 Universal entry consequence
**C5F.UNIV.1 (Reset Compliance)**  
- Entry-point parameters must show no predictive carryover across line boundaries beyond chance.

**Kill rule:** Any model showing significant inter-line parameter persistence is eliminated.

### 5.2 Independence consequences
**C5F.IND.1 (Adjacency Independence)**  
- Entry-point similarity between adjacent lines must not exceed shuffled controls unless anchored.

**Kill rule:** Excess similarity without anchoring evidence eliminates independent-entry models.

### 5.3 Anchoring consequences
**C5F.ANCH.1 (Block Consistency)**  
- If entry is anchored, parameter distributions must be stable within blocks and shift at block boundaries.

**Kill rule:** Absence of block-level shifts eliminates anchored-entry models.

### 5.4 Parameter economy
**C5F.PARM.1 (Minimality)**  
- The number of free parameters must be small relative to the number of distinct observed paths.

**Kill rule:** Models requiring many parameters per line are eliminated as non-explanatory.

Deliverable:
- `reports/PHASE_5F_NECESSARY_CONSEQUENCES.md`

---

## 6. Signature Tests and Analyses

### 6.1 Entry-point clustering analysis
**Objective:**  
Detect clustering of inferred entry points across lines.

**Methods may include:**
- Distance metrics on inferred path prefixes.
- Hierarchical clustering with permutation baselines.

**Kill criteria:**  
Observed clustering inconsistent with candidate entry class.

---

### 6.2 Parameter inference and identifiability
**Objective:**  
Infer minimal parameter sets explaining observed path diversity.

**Methods may include:**
- Prefix-tree compression analysis.
- Description-length minimization over parameterized paths.

**Kill criteria:**  
Parameter sets unstable or overly large.

---

### 6.3 Block and layout alignment tests
**Objective:**  
Test whether entry-point distributions align with structural blocks such as pages or sections.

**Kill criteria:**  
Apparent alignment explainable by chance or global frequency effects.

---

### 6.4 Coverage and reuse profiling
**Objective:**  
Measure how much of the object is covered by observed paths and how often entry points recur.

**Kill criteria:**  
Coverage patterns incompatible with candidate selection mechanisms.

---

## 7. Generator and Comparator Suite

### 7.1 Entry simulators
For each entry class:
- A minimal simulator with fixed traversal.
- A relaxed variant.
- An adversarial variant that attempts to spoof clustering.

### 7.2 Matching requirements
Simulators must match Voynich on:
- Line length distribution.
- Path prefix diversity.
- Global frequency profile.

Deliverables:
- `src/phase5_mechanism/entry_selection/`
- `governance/ENTRY_SIMULATOR_SPEC.md`

---

## 8. Run Structure and Provenance

### 8.1 Canonical run manifest additions
Each run must record:
- Entry class ID.
- Parameter definitions and counts.
- Inferred versus simulated distributions.
- Consequence satisfaction and eliminations.

### 8.2 Folder structure

- `src/phase5_mechanism/entry_selection/`
- `phase2_analysis/phase5_mechanism/entry_selection/`
- `configs/phase5_mechanism/entry_selection/`
- `runs/phase5_mechanism/<run_id>/`
- `results/phase5_mechanism/entry_selection/`
- `reports/`

---

## 9. Evaluation and Outcome Labels

### 9.1 Entry mechanism outcomes
Each entry class receives one label:
- **Eliminated:** incompatible with observed entry statistics.
- **Sufficient:** explains observed path instantiation with minimal parameters.
- **Equivalent:** indistinguishable from another class.
- **Underdetermined:** insufficient resolution to decide.

### 9.2 Equivalence handling
If equivalence remains:
- Document what additional evidence would separate candidates.
- Classify evidence as text-internal or external.

Deliverable:
- `reports/PHASE_5F_EQUIVALENCE.md`

---

## 10. Interpretation Boundary

Phase 5F is allowed to conclude:
- How entry points and parameters are selected.
- Whether selection is independent, coupled, or anchored.
- The minimal parameterization required for path diversity.

Phase 5F is not allowed to conclude:
- That entry choices encode meaning.
- That the mechanism reflects language or code.
- That the object was historically intended for communication.

---

## 11. Phase 5F Termination Statement

Phase 5F identifies the mechanism by which traversal instances are initiated for each line in the Voynich Manuscript. By constraining entry-point selection and parameterization under a fixed deterministic traversal, Phase 5F further narrows admissible explanations without invoking semantics. Progress beyond this phase requires either external anchoring evidence or a shift from text-internal inference.

---

## 12. Immediate Next Actions

1) Freeze entry mechanism classes  
2) Pre-register entry-level necessary consequences  
3) Implement entry simulators with fixed traversal  
4) Infer path prefixes and entry parameters from real data  
5) Run clustering, independence, and coverage tests  
6) Decide whether entry mechanisms collapse or remain equivalent
