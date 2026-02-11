# PHASE_7B_EXECUTION_PLAN.md

**Project:** Voynich Manuscript – Post-Structural Inquiry  
**Phase:** 7B  
**Phase Name:** Codicological and Material Constraints  
**Status:** PLANNED  
**Evidence Type:** Physical manuscript structure and production coupling  

---

## 1. Purpose of Phase 7B

Phase 7B evaluates whether the Voynich Manuscript’s formally identified production phase5_mechanism is **coupled to the manuscript as a physical object**.

After Phases 5 and 6 established that the text is a unified, indifferent formal system, and Phase 7A established disciplined but phase7_human execution, Phase 7B asks:

> Does the formal system adapt to, depend on, or ignore the material and codicological structure of the manuscript?

This phase introduces **physical layout, material sequencing, and scribal evidence** as constraints.

---

## 2. Core Questions

Phase 7B addresses the following questions:

1. Was the text generated **in situ** on the pages, or copied from an external source?
2. Does the production phase5_mechanism respond to:
   - page boundaries,
   - quire structure,
   - layout constraints,
   - scribal hand changes?
3. Are there detectable **mode shifts** in production aligned with physical features?

---

## 3. What Phase 7B Is Not

Phase 7B does NOT:
- interpret illustrations or diagrams semantically,
- infer symbolic meaning from layout,
- identify author or cultural origin,
- assume language or encoding.

All phase2_analysis is structural and physical.

---

## 4. Competing Hypotheses

### H7B.1 – In-Situ Generation
Text was generated directly onto the manuscript pages, with the formal system operating **in awareness of page geometry and material constraints**.

Predictions:
- Line behavior adapts near page edges.
- Quire boundaries affect statistical signatures.
- Layout irregularities correlate with text properties.

---

### H7B.2 – External Generation and Copying
Text was generated externally (e.g., from tables, diagrams, or lists) and then copied into the manuscript with minimal adaptation.

Predictions:
- Text properties are invariant to page geometry.
- Quire and page boundaries show no systematic effect.
- Layout constraints do not influence generation behavior.

---

## 5. Design Principles

### 5.1 Mechanism frozen
All tests assume the Implicit Constraint Lattice and execution properties established in Phases 5 and 6.

No alternative generators are introduced.

---

### 5.2 Geometry as constraint, not meaning
Illustrations, margins, and layout are treated as **geometric anchors**, not symbolic content.

---

### 5.3 Boundary-first testing
Physical boundaries are treated as natural intervention points for detecting coupling.

---

## 6. Test Families and Metrics

### 6.1 Page Boundary Adaptation Test
**Objective:** Detect whether generation behavior changes near page ends.

**Metrics:**
- Line length variance vs distance from page bottom
- Token complexity near boundaries
- Successor entropy near final lines

**Kill rule (H7B.2):**
If no statistically significant boundary effect exists, in-situ adaptation is weakened.

---

### 6.2 Quire Boundary Discontinuity Test
**Objective:** Test whether text properties shift across quire boundaries.

**Metrics:**
- Distributional change of line metrics across quires
- Reset strength at quire starts
- Vocabulary introduction rates

**Kill rule (H7B.2):**
If quire boundaries are indistinguishable from random breaks, material coupling is weakened.

---

### 6.3 Scribal Hand Coupling Test
**Objective:** Determine whether different scribal hands alter execution behavior.

**Metrics:**
- Line-level entropy and determinism by hand
- Correction density by hand
- Stroke complexity by hand

**Kill rule (H7B.2):**
If execution signatures remain invariant across hands, the phase5_mechanism is independent of individual scribes.

---

### 6.4 Layout Obstruction Test
**Objective:** Evaluate whether text adapts to irregular layouts (diagrams, labels, tight spaces).

**Metrics:**
- Token truncation or elongation near obstructions
- Deviations in successor patterns near diagrams
- Local entropy shifts

**Kill rule (H7B.2):**
If layout irregularities do not induce measurable adaptation, copying from an external source is favored.

---

## 7. Control Comparisons

### 7.1 Required controls
- Synthetic lattice output written into constrained layouts
- Externally generated text copied into arbitrary page geometries
- Randomized layout baselines

### 7.2 Matching constraints
Controls must match:
- line count,
- line length distribution,
- vocabulary size,
- positional conditioning.

---

## 8. Execution Order

1. Annotate manuscript with page, quire, hand, and layout metadata  
2. Compute baseline metrics ignoring physical structure  
3. Introduce boundary-aware stratification  
4. Apply hypothesis kill rules  

No adaptive threshold tuning during execution.

---

## 9. Decision Framework

### Outcome A: Strong Material Coupling
- Boundary-adaptive behavior detected
- Quire or layout effects present
- Scribal hand influences execution

**Interpretation:**  
Supports in-situ generation with awareness of material context.

---

### Outcome B: Weak or No Material Coupling
- Text properties invariant to physical structure
- No quire or layout signatures
- Scribal independence

**Interpretation:**  
Supports external generation and subsequent copying.

---

## 10. Phase 7B Deliverables

### Code
- `src/phase_7b/page_boundary_tests.py`
- `src/phase_7b/quire_analysis.py`
- `src/phase_7b/scribe_coupling.py`

### Data
- `results/phase_7b/phase_7b_results.json`

### Report
- `reports/PHASE_7B_RESULTS.md`

---

## 11. Phase 7B Termination Statement

Phase 7B terminates when codicological and material constraints are evaluated against the frozen phase5_mechanism, and the degree of coupling between text generation and physical manuscript structure is decisively classified.

Phase 7B does not infer purpose; it constrains production mode.
