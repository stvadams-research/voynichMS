# Execution Plan: Gap Closure and Residual Analysis

**Target:** Refinement of the "Implicit Constraint Lattice" model and infrastructure optimizations.
**Context:** Based on findings in `Gemini_Assessment.md`.
**Goal:** Address "in tension" results of Phase 10 and improve replication reliability.

---

## 1. Infrastructure: Data Integrity & Fast-Failure (Phase 0/1)

**Issue:** Long replication runs (~6h) can fail late due to missing or corrupted 7GB Yale scans.

- [x] **Task 1.1: Automated External Asset Validator**
    - **Location:** `scripts/phase0_data/verify_external_assets.py`
    - **Action:** Create a script that performs a non-destructive check (presence + file size + optional MD5 sample) of the Yale scans and Gutenberg corpora.
- [x] **Task 1.2: Replication Guardrail**
    - **Location:** `scripts/support_preparation/replicate_all.py`
    - **Action:** Integrate the validator at the very start of the execution chain. Fail immediately if assets are missing.

## 2. Mechanism: Higher-Order Lattice Refinement (Phase 5)

**Issue:** Method K shows systematic deviations toward natural language that the current lattice doesn't capture.

- [x] **Task 2.1: Context-Masking Simulation**
    - **Location:** `src/phase5_mechanism/parsimony/simulators.py` (`ImplicitLatticeSimulator`)
    - **Action:** Implement a "masking" rule where the lattice traversal is influenced by a secondary, low-entropy parameter (simulating a "key" or "mask" that persists across several tokens).
- [x] **Task 2.2: Parameter Sweep for Residual Matching**
    - **Location:** `src/phase5_mechanism/workflow/parameter_inference.py`
    - **Action:** Update the inferrer to specifically target the feature-correlation signatures identified in Phase 10 Method K.
    - **Success Metric:** Reduce Method K's |z|-scores from >2.0 to <1.0 in synthetic controls.

## 3. Admissibility: Performance & Targeted Retest (Phase 10)

**Issue:** Phase 10 is a major bottleneck; Method J structure is unexplained.

- [x] **Task 3.1: Selective Stage Runner**
    - **Location:** `src/phase10_admissibility/stage1_pipeline.py`
    - **Action:** Add a `--methods` flag to allow running only J and K during iterative model refinement.
- [x] **Task 3.2: Positional Subsequence Deep-Dive (Method J)**
    - **Location:** `src/phase10_admissibility/stage1_pipeline.py`
    - **Action:** Test whether Method J's anomalies (z > 30) disappear when the "masking" rules from Task 2.1 are applied.
    - **Hypothesis:** If Task 2.1 fixes Method J, we have identified a second-order "masking" rule in the manuscript's production.

## 4. Stroke Topology: Multi-Scale Cross-Validation (Phase 11)

**Issue:** Phase 11 results are currently siloed from the global mechanism (Phase 5).

- [x] **Task 4.1: Fractal Lattice Test**
    - **Location:** `src/phase11_stroke/analysis/`
    - **Action:** Apply the "Lattice vs. DAG" discrimination test from Phase 5G to the **stroke-level** transitions.
- [x] **Task 4.2: Hierarchical Transition Correlation**
    - **Location:** `src/phase11_stroke/analysis/`
    - **Action:** Measure the correlation between token-level lattice density and stroke-level transition complexity.
    - **Goal:** Determine if the "machine" operates identically at the sub-glyph and word scales.

## 5. Synthesis: Closing the Narrative (Phase 9)

- [x] **Task 5.1: Update "Closure Status" in Publication**
    - **Location:** `planning/support_preparation/content/06_conclusions.md` (Note: Updated in 11_discussion.md as per content structure)
    - **Action:** If Tasks 2.1 and 3.2 succeed, update the narrative from `in_tension` to `refined_closure`. 
    - **Document:** How "masking" explains the linguistic residuals without requiring actual language.

---

## Success Criteria for Completion

1. **Phase 10 (Methods J/K):** Synthetic controls now fall within the 95% confidence interval of the real manuscript features.
2. **Replication:** A fresh `replicate_all.py` run passes all verification checks in <5 hours with guaranteed asset presence.
3. **Publication:** The final generated report identifies a **single, hierarchical mechanism** that accounts for both the macro-lattice and the micro-residuals.
