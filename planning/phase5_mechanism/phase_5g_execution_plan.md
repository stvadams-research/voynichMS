# Phase 5G Execution Plan: Topology Collapse and Non-Equivalence Testing

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5G  
**Phase Name:** Topology Collapse  
**Goal Type:** Structural non-equivalence testing among admissible large-object models  
**Primary Goal:** Determine whether the remaining admissible large-object topologies are structurally distinguishable using text-internal evidence alone, or whether they collapse into an irreducible equivalence class.

---

## 1. Phase 5G Purpose and Core Question

### 1.1 Core question
Given a fixed global deterministic traversal rule and independently selected per-line entry points, are the remaining large-object topology classes (grids, layered tables, DAGs, constraint lattices) observationally distinguishable using text-internal signatures, or are they provably equivalent at the level of observable output?

### 1.2 Why Phase 5G exists
Phase 5E and 5F established that:
- A global deterministic rule system governs successor relations.
- Lines are independent traversal instances with no carryover.
- Entry points are sampled independently from a very large space.
- Multiple topology classes remain admissible.

Phase 5G exists to collapse this remaining topology space as far as identifiability permits.

### 1.3 What Phase 5G is not
- Not an attempt to decide historical plausibility.
- Not a semantic or linguistic phase2_analysis.
- Not a search for meaning or decoding.
- Not a refinement of traversal rules.

Phase 5G holds traversal fixed and varies topology only.

### 1.4 Success criteria
Phase 5G is successful if it produces:
- Clear elimination of one or more topology classes, or
- A rigorous demonstration that multiple topologies are observationally equivalent under all admissible metrics, or
- A bounded statement of what additional evidence would be required to separate them.

---

## 2. Phase 5G Design Principles

### 2.1 Equivalence-aware evaluation
Failure to distinguish topologies is an acceptable and informative outcome.
Non-identifiability must be demonstrated, not assumed.

### 2.2 Traversal invariance
All topology tests assume:
- A fixed deterministic traversal rule.
- Independent per-line entry selection.
Traversal dynamics are not tuned per topology beyond necessity.

### 2.3 Text-internal sufficiency
Only statistics derivable from the manuscript text are admissible.
No appeal to illustrations, layout, or historical context.

### 2.4 Adversarial topology construction
For each topology class, construct adversarial instances designed to mimic others as closely as possible.

---

## 3. Topology Classes Under Test

Phase 5G evaluates the following frozen classes:

1) Rectangular or Ragged Grids  
2) Layered Tables or Sheets  
3) Directed Acyclic Graphs (DAGs)  
4) Constraint Lattices  

Each topology is instantiated at scales sufficient to support:
- >3,000 entry points
- High global entropy
- Deterministic successor forcing

Deliverable:
- `reports/PHASE_5G_TOPOLOGY_SET.md`

---

## 4. Observational Signature Families

Phase 5G introduces topology-sensitive signatures.

### 4.1 Path overlap geometry
**Question:**  
How often do distinct paths share long prefixes or suffixes?

**Rationale:**  
- Grids impose geometric overlap constraints.
- DAGs allow flexible convergence and divergence.
- Lattices may enforce constraint-driven overlap.

**Metrics:**
- Prefix collision length distribution
- Suffix convergence frequency
- Longest common subsequence statistics

**Elimination logic:**  
Topologies unable to reproduce observed overlap patterns are eliminated.

---

### 4.2 Reachability and coverage profiles
**Question:**  
How efficiently do paths cover the underlying object?

**Rationale:**  
- Uniform grids yield regular coverage.
- DAGs may produce skewed visitation.
- Layered tables may show stratified coverage.

**Metrics:**
- Node visitation frequency distribution
- Coverage growth as a function of line count
- Gini coefficient over node usage

**Elimination logic:**  
Topologies producing coverage dynamics incompatible with observed frequency emergence are eliminated.

---

### 4.3 Path reversibility and ambiguity
**Question:**  
Is traversal locally reversible or ambiguous?

**Rationale:**  
- Grids often allow reverse paths.
- DAGs may not.
- Constraint lattices may allow multiple resolutions.

**Metrics:**
- Backward determinism score
- Context-to-predecessor ambiguity
- Ratio of unique predecessors per node

**Elimination logic:**  
Topologies with reversibility profiles inconsistent with Voynich statistics are eliminated.

---

### 4.4 Symmetry and isotropy tests
**Question:**  
Does the output exhibit hidden directional or symmetry biases?

**Rationale:**  
- Grids impose axial symmetry.
- DAGs and lattices need not.

**Metrics:**
- Directional successor asymmetry
- Positional entropy gradients
- Mirror and rotation invariance tests on path fragments

**Elimination logic:**  
Topologies imposing detectable symmetry absent in the manuscript are eliminated.

---

## 5. Necessary Consequences at the Topology Level

Phase 5G formalizes topology-level kill rules.

### 5.1 C5G.COV.1 (Coverage Compatibility)
- Coverage growth and node visitation must match Voynich-derived estimates.
- Topologies requiring extreme skew or extreme uniformity are eliminated.

### 5.2 C5G.OVR.1 (Overlap Structure)
- Path overlap statistics must fall within the empirical envelope.
- Topologies with overlap tails too long or too short are eliminated.

### 5.3 C5G.SYM.1 (Symmetry Absence)
- No strong global symmetry may be detectable beyond shuffled controls.
- Symmetry-imposing topologies are eliminated.

Deliverable:
- `reports/PHASE_5G_NECESSARY_CONSEQUENCES.md`

---

## 6. Generator and Comparator Suite

### 6.1 Topology simulators
For each topology class:
- One canonical instance
- One adversarial instance designed to mimic competitors
- One minimal instance near the identifiability boundary

Traversal rule and entry selection fixed across all simulators.

### 6.2 Matching requirements
Simulators must match Voynich on:
- Line length distribution
- Entry-point entropy
- Successor forcing rate

Deliverables:
- `src/phase5_mechanism/topology_collapse/`
- `governance/TOPOLOGY_SIMULATOR_SPEC.md`

---

## 7. Run Structure and Provenance

### 7.1 Canonical run manifest additions
Each Phase 5G run must record:
- Topology class and instance ID
- Object size and connectivity
- Traversal rule hash
- Signature outcomes and eliminations

### 7.2 Folder structure

- `src/phase5_mechanism/topology_collapse/`
- `phase2_analysis/phase5_mechanism/topology_collapse/`
- `configs/phase5_mechanism/topology_collapse/`
- `runs/phase5_mechanism/<run_id>/`
- `results/phase5_mechanism/topology_collapse/`
- `reports/`

---

## 8. Evaluation and Outcome Labels

### 8.1 Topology outcomes
Each topology class receives one label:
- **Eliminated:** incompatible with text-internal signatures
- **Admissible:** compatible and distinguishable
- **Equivalent:** observationally indistinguishable from another class
- **Non-identifiable:** cannot be separated from multiple classes with text alone

### 8.2 Collapse criteria
Phase 5G is considered complete when:
- All topology classes are labeled, and
- Either at least one class is eliminated, or
- A formal equivalence class is documented.

Deliverable:
- `reports/PHASE_5G_EQUIVALENCE_AND_COLLAPSE.md`

---

## 9. Interpretation Boundary

Phase 5G is allowed to conclude:
- Which topology classes remain admissible.
- Which are eliminated by structural evidence.
- Whether topology is identifiable from text alone.

Phase 5G is not allowed to conclude:
- That any topology was historically used.
- That the structure encodes meaning.
- That the topology reflects subject matter.

---

## 10. Phase 5G Termination Statement

Phase 5G evaluates whether the remaining admissible large-object topologies underlying the Voynich Manuscript are structurally distinguishable using text-internal evidence alone. By eliminating incompatible topologies or demonstrating irreducible equivalence, Phase 5G determines the ultimate resolution limit of topology identification within the current inferential scope.

---

## 11. Immediate Next Actions

1) Freeze topology instances and sizes  
2) Pre-register topology-level necessary consequences  
3) Implement topology simulators with fixed traversal and entry rules  
4) Run overlap, coverage, symmetry, and reversibility analyses  
5) Assign elimination or equivalence labels  
6) Decide whether to proceed to external anchoring or formal closure
