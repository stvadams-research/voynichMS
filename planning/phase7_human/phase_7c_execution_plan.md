# PHASE 7B EXECUTION PLAN: CODICOLOGICAL CONSTRAINTS

**Project:** Voynich Manuscript – Human–Artifact Coupling  
**Phase:** 7B  
**Phase Name:** Codicological Constraints  
**Goal Type:** External coupling core_audit (physical manuscript vs formal system)  
**Primary Goal:** Determine whether the execution of the Voynich formal system is adaptively coupled to the physical structure of the manuscript (pages, quires, layout, scribal hands), or whether the manuscript functions as a largely neutral carrier.

---

## 1. Phase 7B Purpose and Core Question

### 1.1 Core Question
Does the Voynich production phase5_mechanism adapt to codicological constraints (page boundaries, quire structure, layout geometry, scribal hand), or is the formal system executed independently of the manuscript’s physical form?

### 1.2 Why Phase 7B Exists
Earlier phases established:
- A single global deterministic phase5_mechanism (Phase 5)
- Indifferent formal execution (Phase 6)
- Human but disciplined production (Phase 7A)

What remains unresolved is **where the control lives**:
- In the manuscript object itself, or
- In the scribe executing an abstract system

Phase 7B explicitly tests manuscript-level coupling.

### 1.3 What Phase 7B Is Not
- Not an phase2_analysis of illustration meaning
- Not a palaeographic classification project
- Not a semantic or historical interpretation

Phase 7B evaluates **structural responsiveness to physical constraints**, not content.

---

## 2. Design Principles

### 2.1 Carrier vs Controller Distinction
The manuscript may either:
- Actively constrain generation (controller), or
- Passively host generation (carrier)

Phase 7B is designed to distinguish these.

### 2.2 Orthogonality to Mechanism
All tests must:
- Assume the same underlying formal system
- Measure *modulation*, not rule change

If the phase5_mechanism changes, Phase 5 conclusions are violated.

---

## 3. Hypothesis Space

### H7B.1: In-Situ Adaptation
The scribe adapts execution dynamically to:
- Page boundaries
- Layout constraints
- Available space
- Illustration placement

Predicted signatures:
- Boundary-conditioned line shortening
- Layout-driven word compression
- Page-aware structural adjustments

### H7B.2: External Generation or Abstract Execution
The scribe executes an abstract formal system largely independent of:
- Page geometry
- Layout constraints
- Illustration proximity

Predicted signatures:
- Weak or absent boundary effects
- Stable structural statistics across pages
- Layout variance absorbed by scribal execution, not rule change

---

## 4. Test Families and Metrics

### 4.1 Page Boundary Adaptation Test

**Objective:**  
Detect whether line structure adapts near page ends.

**Metrics:**
- Correlation between line position (within page) and:
  - Line length
  - Mean word length
  - Token count

**Null Model:**  
Shuffled line order within pages.

**Kill Rule (H7B.1):**  
If boundary proximity significantly predicts compression beyond shuffled controls, H7B.2 is weakened.

---

### 4.2 Layout Variability Audit

**Objective:**  
Measure how much execution varies with layout geometry.

**Metrics:**
- Coefficient of variation of:
  - Line lengths per page
  - Word counts per line
- Comparison across pages with differing illustration density

**Interpretation:**
- High variability with stable internal constraints supports abstract execution.
- Systematic compression supports in-situ adaptation.

---

### 4.3 Quire Continuity Test

**Objective:**  
Test whether quires act as production units.

**Metrics:**
- Between-quire variance vs within-quire variance for:
  - Mean word length
  - TTR
  - Successor consistency

**Kill Rule:**  
If quire boundaries introduce abrupt statistical shifts, manuscript-level control is implicated.

---

### 4.4 Scribal Hand Coupling

**Objective:**  
Determine whether execution signatures correlate more strongly with scribal identity than with manuscript structure.

**Metrics:**
- TTR
- Repetition rate
- Error density
- Local entropy

**Comparison:**
- Hand A vs Hand B
- Same formal metrics, different agents

**Interpretation:**
- Strong hand dependence with weak layout dependence supports abstract system execution.

---

## 5. Execution Order

1. Page boundary correlation phase2_analysis
2. Layout variability profiling
3. Quire continuity phase2_analysis
4. Scribal hand comparison
5. Synthesis across all metrics

Each test is run independently and then integrated.

---

## 6. Decision Framework

### Outcomes

- **Supports H7B.1 (In-Situ Adaptation):**
  - Execution structure changes near boundaries
  - Layout geometry predicts token behavior

- **Supports H7B.2 (External Generation):**
  - Weak boundary effects
  - Strong scribal-agent effects
  - Global phase5_mechanism stability

### Phase 7B Success Criteria
Phase 7B is successful if it:
- Clearly locates control at either manuscript or agent level
- Eliminates at least one hypothesis class
- Does not require semantic assumptions

---

## 7. Artifacts and Deliverables

### Outputs
- `reports/PHASE_7B_RESULTS.md`
- Tables of boundary correlations
- Quire variance plots
- Scribal hand comparison summaries

### Provenance
- All runs tagged with RunID
- Corpus subsets frozen
- Metrics reproducible

---

## 8. Termination Statement

Phase 7B terminates when codicological coupling is either confirmed or falsified. The phase does not aim to explain *why* the manuscript exists, only whether its physical form actively constrains its formal execution.

---

**Next Phase:** Phase 7C – Cognitive Load and Decision Structure
