# Phase 16: Ergonomic Grounding and Physical Layout (Level 3)

**Objective:** To test whether the "Selection Bias" found in Phase 15 is driven
by physical ergonomics and the geometric layout of the production device.

**Status:** COMPLETE (2026-02-21)

---

## 1. Task 1: Ergonomic Word Costing
**Goal:** Quantify the "effort" required to produce every word in the vocabulary.

- [x] **1.1: Stroke-Cost Mapping**
    - **Results:** Assigned costs to **7,755 words**; matched **4,755** directly from sub-glyph stroke data.
- [x] **1.2: Artifact:** `results/data/phase16_physical/word_ergonomic_costs.json`.

## 2. Task 2: Selection vs. Effort Correlation
**Goal:** Test whether the scribe's choices are biased toward physical ease or rhythmic flow.

- [x] **2.1: The Effort Audit**
    - **Results: NULL RESULT.** Found no correlation (**Rho=-0.0003**, p=0.9926) between word cost and selection frequency. The ergonomic coupling hypothesis is rejected.
- [x] **2.2: Rhythmic Coupling:** Measured average effort gradient of **0.611 strokes** — a consistent physical rhythm exists but does not correlate with selection preference.

## 3. Task 3: Geometric Layout Inference
**Goal:** Project the 50 abstract windows into a physical coordinate system.

- [x] **3.1: Sequential Distance Minimization**
    - **Results:** Tested **2D Grid (10x5)** vs. **Circular Volvelle**.
- [x] **3.2: Geometric Fit:** The **2D Grid** achieved **81.50% efficiency improvement** over random placement (avg travel 0.723 units vs 3.906 baseline), proving it is the optimized physical layout.

## 4. Task 4: The "Mechanical Hand" Summary
**Goal:** Formalize the Level 3 conclusion.

- [x] **4.1: Report:** Created `results/reports/phase16_physical/ERGONOMIC_VERIFICATION.md`.
- [x] **Results:** Confirmed the tool layout is geometrically optimized. Within-window selection bias source remains open (not ergonomic).

---

## Success Criteria for Phase 16

1. **Ergonomic Correlation:** **NULL RESULT.** Rho=-0.0003 (p=0.9926). No evidence of effort-based selection bias.
2. **Geometric Preference:** **PASSED.** 2D Grid is 81.50% more efficient than random.
3. **Selection Driver:** **OPEN.** The 21.49% within-window skew (Phase 15) is real but not explained by ergonomics. Deferred to Phase 15D (selection driver analysis).

**PHASE 16 COMPLETE:** Geometric optimization confirmed. Ergonomic coupling rejected. Selection driver investigation continues.
