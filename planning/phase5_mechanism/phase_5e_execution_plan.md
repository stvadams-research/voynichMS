# Phase 5E Execution Plan: Large-Object Topology and Traversal Dynamics

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5E  
**Phase Name:** Large-Object Traversal Identifiability  
**Goal Type:** Structural topology and traversal-rule identification  
**Primary Goal:** Identify which classes of large deterministic structures, combined with line-initial traversal rules, are sufficient to reproduce the Voynich Manuscript’s global diversity, local rigidity, deterministic succession, and per-line reset behavior, without invoking semantics.

---

## 1. Phase 5E Purpose and Core Question

### 1.1 Core question
What topological classes of large deterministic objects, together with what traversal dynamics, can account for the observed Voynich signature of high global entropy, low line-level entropy, strict determinism, and complete line-boundary resets?

### 1.2 Why Phase 5E exists
Phase 5D established that:
- Line generation is deterministic and non-repeating.
- Slot-based grammars with small vocabularies are eliminated.
- Global option space is large, but local choice is highly constrained.
- The remaining viable class is traversal of a large, pre-defined structure.

Phase 5E exists to replace the phrase “large-object traversal” with a formally defined, testable family of structures and traversal rules.

### 1.3 What Phase 5E is not
- Not an interpretation of symbols or meaning.
- Not a decoding or decipherment attempt.
- Not a historical reconstruction.
- Not a claim that any specific object actually existed.

Phase 5E studies *structural possibility*, not historical fact.

### 1.4 Success criteria
Phase 5E is successful if it produces:
- A finite, explicit set of admissible object topologies.
- A finite, explicit set of admissible traversal dynamics.
- Elimination of topology–traversal pairs incompatible with observed constraints.
- A reduced equivalence class, or proof of observational equivalence.

---

## 2. Phase 5E Design Principles

### 2.1 Topology–traversal separation
Object topology and traversal rules are treated as separate degrees of freedom.
No traversal is evaluated without an explicit underlying structure.

### 2.2 Determinism and reset enforcement
All traversal dynamics must:
- Be deterministic once parameters are fixed.
- Reset completely at line boundaries.
- Forbid reuse of nodes or labels within a line, unless explicitly tested.

### 2.3 Scale consistency
Candidate structures must plausibly support:
- Hundreds of valid tokens per effective position.
- Thousands of distinct paths across the manuscript.
- Stable global frequency profiles.

### 2.4 Minimal sufficiency
Any additional complexity beyond what is required to match observed data eliminates the candidate.

---

## 3. Candidate Large-Object Topology Classes

Phase 5E begins by freezing a finite set of topological families.

### 3.1 Rectangular or Ragged Grids
- Nodes arranged in rows and columns.
- Adjacency defined geometrically.
- Traversal corresponds to moving across rows, columns, or diagonals.

**Strengths:** Natural explanation for successor forcing.  
**Vulnerabilities:** May over-impose regularity or symmetry.

---

### 3.2 Layered Tables or Sheets
- Multiple tables stacked or indexed.
- Traversal involves selecting a layer, then following a deterministic rule within it.

**Strengths:** Supports large option spaces with local rigidity.  
**Vulnerabilities:** Risk of hidden persistence across lines.

---

### 3.3 Directed Acyclic Graphs (DAGs)
- Nodes represent components.
- Edges encode allowed deterministic successors.
- Paths correspond to lines.

**Strengths:** High expressive power with strict determinism.  
**Vulnerabilities:** Hard to constrain without overfitting.

---

### 3.4 Constraint Lattices
- Objects defined implicitly by constraint satisfaction rather than explicit adjacency.
- Traversal corresponds to resolving constraints in a fixed order.

**Strengths:** Explains large global diversity with local forcing.  
**Vulnerabilities:** Risk of indistinguishability from generic rule systems.

Deliverable:
- `reports/PHASE_5E_TOPOLOGY_CLASSES.md`

---

## 4. Traversal Dynamics Families

Traversal rules determine how a path is chosen through the object.

### 4.1 Fixed Deterministic Walk
- Given an entry point, the path is fully determined.
- No branching once traversal begins.

### 4.2 Parameterized Deterministic Walk
- A small set of line-initial parameters selects among deterministic paths.
- Parameters are resampled per line.

### 4.3 Rule-Evaluated Successor Selection
- At each step, the next node is chosen by evaluating a fixed rule against the current state.

Deliverable:
- `reports/PHASE_5E_TRAVERSAL_CLASSES.md`

---

## 5. Necessary Consequences at the Topology–Traversal Level

Phase 5E defines **topology–traversal necessary consequences**.

### 5.1 Global–local entropy split
- Topology must permit high global successor entropy.
- Traversal must enforce low conditional entropy within a path.

### 5.2 Path collision behavior
- Identical local contexts should force identical successors more often than chance.
- Collision rates must match observed successor consistency.

### 5.3 Reset compatibility
- No traversal state may persist across lines.
- Entry-point selection must be sufficient to explain line-to-line variation.

### 5.4 Frequency emergence
- Global token frequency profiles must emerge naturally from traversal statistics, not be imposed ad hoc.

Deliverable:
- `reports/PHASE_5E_NECESSARY_CONSEQUENCES.md`

---

## 6. Signature Tests and Analyses

### 6.1 Path determinism testing
**Objective:**  
Measure how often identical local contexts force identical continuations.

**Kill criteria:**  
Observed determinism incompatible with candidate topology or traversal rule.

---

### 6.2 Entry-point sensitivity analysis
**Objective:**  
Test whether small changes in starting conditions plausibly generate observed line diversity.

**Kill criteria:**  
Candidate requires implausibly many entry points or parameters.

---

### 6.3 Collision and divergence profiling
**Objective:**  
Measure where paths converge or diverge across lines.

**Kill criteria:**  
Collision patterns inconsistent with observed successor statistics.

---

### 6.4 Over-regularity detection
**Objective:**  
Ensure candidates are not too rigid compared to real data variability.

**Kill criteria:**  
Candidate produces positional or frequency regularities absent in Voynich.

---

## 7. Generator and Comparator Suite

### 7.1 Topology simulators
For each topology–traversal pair:
- One minimal simulator
- One relaxed variant
- One adversarial variant

### 7.2 Matching requirements
All simulators must be matched to Voynich on:
- token inventory size
- line length distribution
- global frequency profile

Deliverables:
- `src/phase5_mechanism/large_object/`
- `governance/LARGE_OBJECT_SIMULATOR_SPEC.md`

---

## 8. Run Structure and Provenance

### 8.1 Canonical run manifest additions
Each run must record:
- topology class ID
- traversal rule ID
- entry-point parameterization
- sufficiency outcome
- violated or satisfied consequences

### 8.2 Folder structure

- `src/phase5_mechanism/large_object/`
- `phase2_analysis/phase5_mechanism/large_object/`
- `configs/phase5_mechanism/large_object/`
- `runs/phase5_mechanism/<run_id>/`
- `results/phase5_mechanism/large_object/`
- `reports/`

---

## 9. Evaluation and Outcome Labels

### 9.1 Topology–traversal outcomes
Each topology–traversal pair is labeled as:
- **Eliminated:** incompatible with observed constraints
- **Sufficient:** reproduces all tested signatures
- **Equivalent:** indistinguishable from another pair
- **Underdetermined:** insufficient resolution to test key consequences

### 9.2 Equivalence handling
If equivalence remains:
- Document what additional evidence would separate candidates.
- Classify evidence as text-internal or external.

Deliverable:
- `reports/PHASE_5E_EQUIVALENCE.md`

---

## 10. Interpretation Boundary

Phase 5E is allowed to conclude:
- What classes of large deterministic structures are compatible with the Voynich Manuscript.
- What traversal dynamics are required.
- Whether topology–traversal identifiability is achievable with text alone.

Phase 5E is not allowed to conclude:
- That any structure encodes meaning.
- That the object was historically real or conceptual.
- That the traversal corresponds to language or code.

---

## 11. Phase 5E Termination Statement

Phase 5E evaluates large-object topologies and traversal dynamics as candidates for the Voynich Manuscript’s deterministic line-level production mechanism. By eliminating incompatible structures and identifying equivalence classes among survivors, Phase 5E further constrains the space of admissible explanations without invoking semantics. Progress beyond this phase requires either externa
