# Phase 5B Execution Plan: Constraint Topology and Latent State Geometry

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 5B  
**Phase Name:** Constraint Geometry  
**Goal Type:** Structural mechanism refinement and identifiability deepening  
**Primary Goal:** Characterize the topology, locality, and dimensionality of the constraints governing token succession and reuse in the Voynich Manuscript, in order to further narrow admissible production mechanisms without assuming semantics.

---

## 1. Phase 5B Purpose and Core Question

### 1.1 Core question
What is the geometric and dynamical structure of the constraints that govern token succession and reuse in the Voynich Manuscript, and which classes of mechanisms are compatible with that structure?

### 1.2 Why Phase 5B exists
Phase 5 established that:
- Production mechanisms are identifiable using text-internal evidence.
- Voynich exhibits stronger successor constraints than naive pool models.
- Voynich exhibits less local repetition than copying-driven models.

These results invalidate coarse mechanism classes and force refinement.  
Phase 5B exists to replace broad labels such as “table” with measurable constraint properties.

### 1.3 What Phase 5B is not
- Not a semantic analysis.
- Not a historical reconstruction.
- Not a new hypothesis fishing expedition.
- Not a continuation of Phase 4-style proxy testing.

Phase 5B studies constraint geometry, not meaning.

### 1.4 Success criteria
Phase 5B is successful if it produces:
- A measurable description of Voynich constraint topology.
- Bounds on latent state dimensionality and transition sparsity.
- Clear elimination or refinement of table, pool, and pipeline sub-classes.
- A reduced and better-defined set of admissible mechanism families.

---

## 2. Phase 5B Design Principles

### 2.1 Geometry over labels
All analysis targets structural properties such as:
- state count
- transition sharpness
- locality and reset behavior

Mechanism labels are secondary and may be revised.

### 2.2 Latent-state agnosticism
Latent states are treated as abstract constraints, not semantic categories.

No assumption is made that states correspond to meaning, words, or symbols.

### 2.3 Perturbation robustness
All inferred structures must be stable under:
- resampling
- mild noise injection
- alternative but equivalent sectionings

Unstable structures are not admissible evidence.

### 2.4 Matched comparator enforcement
All conclusions must be supported by comparison to:
- matched non-semantic generators
- adversarial hybrids designed to spoof simple signatures

---

## 3. Constraint Topology Concepts

Phase 5B formalizes constraint geometry along four axes.

### 3.1 State dimensionality
How many latent states are required to explain successor constraints?

Low-dimensional:
- consistent with tables or grids

High-dimensional:
- consistent with pools or stochastic grammars

### 3.2 Transition sparsity
How sharply do states constrain successors?

Measured via:
- conditional entropy
- successor set size
- transition graph sparsity

### 3.3 Locality and reset behavior
Do constraints:
- persist globally
- reset at boundaries (line, page, quire)
- drift gradually

### 3.4 Constraint heterogeneity
Are constraints uniform across tokens, or concentrated in:
- positional tokens
- specific glyph classes
- structural regions

---

## 4. Signature Test Families

Phase 5B introduces second-order tests that refine Phase 5 signatures.

### 4.1 Latent state recoverability tests

**Objective:**  
Determine whether a small, stable latent state space predicts successor sets better than matched controls.

**Methods may include:**
- Hidden Markov style inference with bounded state counts
- Spectral or matrix factorization methods on transition matrices
- Minimum-description-length model selection

**Key evaluations:**
- predictive gain versus matched generators
- stability of inferred states across perturbations
- sensitivity to assumed state count

**Elimination criteria:**
- No low-dimensional model outperforms matched non-table generators
- Inferred states are unstable or non-reproducible

---

### 4.2 Constraint locality and reset tests

**Objective:**  
Determine whether constraint regimes persist globally or reset at structural boundaries.

**Candidate boundaries:**
- line
- paragraph
- page
- quire or section

**Tests may include:**
- windowed successor entropy tracking
- regime change detection
- boundary-conditioned transition matrices

**Elimination criteria:**
- No statistically meaningful reset or regime shift beyond chance
- Apparent resets fully explained by token frequency drift

---

### 4.3 Constraint sharpness profiling

**Objective:**  
Measure where and how strongly successor constraints apply.

**Tests may include:**
- per-token successor entropy distributions
- clustering of low-entropy tokens
- positional entropy gradients

**Elimination criteria:**
- Constraint sharpness uniformly weak or uniformly strong in a way matched generators can reproduce
- No identifiable structural asymmetries

---

### 4.4 Global versus local constraint decomposition

**Objective:**  
Determine whether constraints decompose into:
- a small number of global rules
- many weak local rules
- layered constraints consistent with pipelines

**Tests may include:**
- residual analysis after fitting best single-layer models
- additive versus multiplicative constraint models
- variance explained by successive layers

**Elimination criteria:**
- Single-layer models fully explain constraints
- No evidence of layered structure beyond overfitting noise

---

## 5. Comparator and Generator Requirements

### 5.1 Refined generator suite
Extend Phase 5 generators to include:
- structured tables with varying geometry
- state-switching table hybrids
- large-pool generators tuned to match entropy but not topology

### 5.2 Adversarial spoofing generators
Explicitly design generators to:
- match successor entropy
- match pool size
- break latent-state stability

These test whether observed geometry is robust or superficial.

Deliverable:
- `src/mechanism/generators/constraint_geometry/`
- `docs/GENERATOR_MATCHING_5B.md`

---

## 6. Run Structure and Provenance

### 6.1 Canonical run manifest additions
In addition to Phase 5 fields, Phase 5B runs must record:
- inferred state count ranges
- stability scores under perturbation
- comparator model performance

### 6.2 Folder structure (consistent with program conventions)

- `src/mechanism/constraint_geometry/`
- `analysis/mechanism/constraint_geometry/`
- `configs/mechanism/constraint_geometry/`
- `runs/mechanism/<run_id>/`
- `results/mechanism/constraint_geometry/`
- `reports/`

---

## 7. Evaluation and Outcomes

### 7.1 Outcome categories
Each refined mechanism family is assigned one of:
- **Eliminated:** incompatible with observed constraint geometry
- **Refined admissible:** compatible but with narrowed parameter space
- **Observationally equivalent:** indistinguishable from one or more families
- **Underdetermined:** insufficient resolution to test key properties

### 7.2 Required summary tables
- Constraint property comparison table
- State dimensionality bounds per corpus
- Generator family survival matrix

---

## 8. Phase 5B Outputs

### 8.1 Required reports
- `reports/PHASE_5B_CONSTRAINT_GEOMETRY.md`
- `reports/PHASE_5B_RESULTS.md`
- `reports/PHASE_5B_REFINED_CLASSES.md`
- `reports/PHASE_5B_CONCLUSIONS.md`

### 8.2 Required artifacts
- State recovery plots
- Entropy and sparsity profiles
- Perturbation robustness summaries

---

## 9. Interpretation Boundary

Phase 5B is allowed to conclude:
- The dimensionality and topology of constraints in the Voynich Manuscript
- Which refined mechanism families remain admissible
- Which classes are eliminated by constraint geometry alone

Phase 5B is not allowed to conclude:
- That any mechanism is historically true
- That semantics is present or absent
- That constraints encode meaning

---

## 10. Phase 5B Termination Statement

Phase 5B characterizes the topology and geometry of structural constraints governing the Voynich Manuscript. By refining admissible mechanism families based on latent state behavior, constraint sharpness, and locality, Phase 5B further narrows the space of explanations without invoking semantics. Progress beyond this phase requires either external anchoring evidence or a shift in inferential target.

---

## 11. Immediate Next Actions

1) Select latent state recovery methods and pre-register limits  
2) Extend generator suite with geometry-matched variants  
3) Implement constraint locality and sharpness tests  
4) Run a second pilot focused on latent state stability  
5) Review whether mechanism families collapse further or fork into equivalence classes
