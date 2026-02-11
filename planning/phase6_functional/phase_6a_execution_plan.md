# PHASE_6A_EXECUTION_PLAN.md  
## Phase 6A — Formal-System Exhaustion and Completeness

**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 6A  
**Parent Phase:** Phase 6 — Functional Differentiation Under a Frozen Mechanism  
**Status:** Pre-registered execution plan  
**Intent:** Test whether the Voynich Manuscript is best explained as the execution, instantiation, or partial exhaustion of a formal deterministic system, rather than as a tool, generator, or adversarial artifact.

---

## 1. Phase 6A Position and Scope

### 1.1 Phase 6A question
Given the frozen mechanism identified in Phase 5 (implicit constraint lattice with deterministic traversal), does the manuscript exhibit structural signatures consistent with a **self-contained formal system executed for its own sake**?

Phase 6A evaluates whether the manuscript behaves like:
- an instantiated formal object,
- a constrained combinatorial exercise,
- or a disciplined execution of rules without optimization for reuse, access, or deception.

---

### 1.2 What Phase 6A does NOT assume
Phase 6A does **not** assume:
- semantics,
- communication intent,
- ritual or religious meaning,
- pedagogical purpose.

Phase 6A tests *formal properties only*.

---

## 2. Competing Functional Hypotheses

### H6A.1 — Formal-System Execution (Target Hypothesis)
The manuscript is the execution trace of a formal deterministic system where:
- correctness is defined internally,
- success is measured by rule adherence,
- output completeness or coverage is relevant.

### Competing hypotheses (held constant, not tested directly here)
- Operational Tool / Generator (Phase 6B)
- Adversarial / Epistemic Stress Artifact (Phase 6C)

Phase 6A does not attempt to prove H6A.1 true absolutely, only to test whether it is **structurally supported or weakened**.

---

## 3. Governing Design Principles (Phase 6A-Specific)

### 3.1 Coverage over efficiency
Formal-system execution is expected to prioritize:
- rule adherence,
- coverage,
- internal consistency,

over:
- efficiency,
- reuse,
- ergonomic optimization.

### 3.2 Internal sufficiency
All tests must rely on:
- text-internal structure,
- previously validated signatures,
- non-semantic metrics.

---

## 4. Signature Test Families

Phase 6A evaluates four independent but complementary signature families.

---

### 4.1 State-Space Coverage Analysis

**Objective:**  
Determine whether the manuscript exhibits patterns consistent with systematic exploration of a formal state space.

**Key questions:**
- Is the reachable state space densely or sparsely sampled?
- Are there large unused regions of the inferred lattice?
- Does traversal appear systematic rather than opportunistic?

**Metrics:**
- Visitation frequency distribution across inferred nodes
- Coverage ratio (visited vs theoretically reachable states)
- Tail behavior of low-frequency states

**Predictions under H6A.1:**
- Broad coverage with diminishing returns
- Long tail of rare but valid states
- No strong preference for “useful” or “central” regions

**Kill signal (weakening H6A.1):**
- Strong concentration on a small subset of states
- Evidence of access hubs optimized for reuse

---

### 4.2 Redundancy and Repetition Inefficiency

**Objective:**  
Assess whether the manuscript tolerates inefficiency consistent with formal execution.

**Key questions:**
- Are similar traversal paths repeated without apparent optimization?
- Is redundancy accepted rather than minimized?

**Metrics:**
- Path overlap rate beyond structural necessity
- Repetition distance distributions
- Redundant traversal detection

**Predictions under H6A.1:**
- Redundancy exists where rules permit it
- No pressure to minimize repetition beyond rule constraints

**Kill signal:**
- Systematic avoidance of redundancy
- Strong evidence of optimization for reuse or brevity

---

### 4.3 Error Typology and Correction Behavior

**Objective:**  
Characterize deviations from the inferred ruleset.

**Key questions:**
- Do deviations look like mechanical slips or conceptual corrections?
- Are corrections applied to restore rule compliance?

**Metrics:**
- Deviation classification (rule violation vs continuation error)
- Local vs global correction patterns
- Correction latency

**Predictions under H6A.1:**
- Errors are rare
- Errors resemble execution slips
- Corrections restore formal validity, not meaning

**Kill signal:**
- Corrections aimed at semantic coherence
- Adaptive changes that alter rule behavior

---

### 4.4 Completeness and Exhaustion Signatures

**Objective:**  
Test whether the manuscript trends toward completeness or exhaustion of some combinatorial regime.

**Key questions:**
- Do new patterns decrease over time?
- Is there evidence of approaching a terminal boundary?

**Metrics:**
- Novelty rate as a function of manuscript progression
- Late-stage entropy stabilization
- Diminishing introduction of new state combinations

**Predictions under H6A.1:**
- Declining novelty curve
- Stabilization of traversal behavior
- No abrupt stopping tied to external constraints

**Kill signal:**
- Persistent novelty without convergence
- Abrupt termination unrelated to system boundaries

---

## 5. Comparator and Control Strategy

### 5.1 Internal controls
- Segment-wise comparisons within the manuscript
- Early vs late manuscript behavior
- Section-independent aggregation

### 5.2 Synthetic comparators
- Formal-system simulators designed to:
  - exhaust state spaces,
  - tolerate redundancy,
  - prioritize rule coverage.

Comparators must match:
- global determinism,
- line reset behavior,
- entry independence.

---

## 6. Decision Framework

Phase 6A does not produce a binary verdict.

Instead, outcomes are classified as:

- **Supported:** Multiple signatures align with formal-system execution.
- **Weakened:** Some signatures contradict H6A.1.
- **Indeterminate:** Evidence insufficient to discriminate.

Explicit elimination of H6A.1 requires **multiple independent kill signals**.

---

## 7. Run Structure and Provenance

Each Phase 6A run records:
- RunID
- corpus hash
- inferred lattice parameters
- metric configurations
- output artifacts
- hypothesis impact summary

### Recommended directories
- `src/phase_6/formal_system/`
- `phase2_analysis/phase_6/formal_system/`
- `configs/phase_6a/`
- `runs/phase_6a/<run_id>/`
- `results/phase_6a/`

---

## 8. Phase 6A Termination Criteria

Phase 6A terminates when:
- all four signature families are evaluated,
- internal consistency checks pass,
- results are classified under the decision framework.

Phase 6A does **not** require a positive identification to terminate.

---

## 9. Phase 6A Output Artifacts

- `reports/PHASE_6A_RESULTS.md`
- `reports/PHASE_6A_INTERPRETATION.md`
- `results/phase_6a/coverage_tables.csv`
- `results/phase_6a/error_typology.csv`

---

## 10. Phase 6A Transition Logic

After Phase 6A:
- If H6A.1 is **supported**, proceed to Phase 6B with updated priors.
- If H6A.1 is **weakened or eliminated**, prioritize Phase 6B or 6C.
- If **indeterminate**, document boundary and proceed in parallel.

---

**Phase 6A Status:** Ready for execution  
**Next Planned Phase:** Phase 6B — Operational Tool / Generator Analysis
