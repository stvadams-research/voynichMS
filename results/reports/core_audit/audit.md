# COMPREHENSIVE CODE AND LOGIC AUDIT REPORT

**Date:** 2026-02-08  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Objective:** Identify any errors, logic gaps, or biases that may have led to false conclusions.

---

## 1. Audit Summary

A comprehensive audit of the Phase 1 through Phase 5K codebase, results, and documentation was conducted. The audit focused on the integrity of "Computed" results, the validity of hypothesis elimination, and the robustness of the final "Implicit Constraint Lattice" lead.

**Conclusion:** The project's primary conclusions—that the manuscript is a non-semantic procedural artifact and that it exhibits global deterministic stiffness—are **fundamentally robust**. However, several specific metrics from Phase 2 were found to be influenced by hardcoded "targets" or simulated logic, which may have exaggerated the precision of early findings.

---

## 2. Findings: Phase 2 Analysis (Integrity Risk)

### 2.1 Mapping Stability (0.02)
- **Status:** **VERIFIED (Calculated)**
- **Audit Detail:** While some synthesis modules (`feature_discovery.py`) contained hardcoded return values of 0.02 for non-scrambled data, the authoritative `MappingStabilityTest` in `src/phase2_analysis/stress_tests/mapping_stability.py` performs a real calculation based on glyph-to-word boundary perturbations.
- **Risk:** The hardcoded values in synthesis modules created a "mirrored" expectation that could have misled investigators if they relied on the synthesis logs rather than the analysis logs.

### 2.2 Information Density (z=5.68)
- **Status:** **VERIFIED (Calculated)**
- **Audit Detail:** The z-score of 5.68 is computed in `InformationPreservationTest` by comparing real-data Shannon entropy against shuffled controls. The script `run_baseline_assessment.py` used 5.68 as a target for generator matching, which is a valid benchmarking technique but carries a risk of circular validation if the real data is not re-computed independently.

---

## 3. Findings: Phase 5 Identifiability (High Robustness)

### 3.1 Path Forcing (86% Consistency)
- **Status:** **ROBUST**
- **Audit Detail:** The `PathCollisionTester` logic was traced. It computes real bigram successor consistency across the entire 233k token corpus. The 86% figure is a direct empirical measurement from the `voynich_real` dataset. This is the strongest evidence for a static-object traversal mechanism.

### 3.2 Positional Forcing (65% Predictive Lift)
- **Status:** **ROBUST**
- **Audit Detail:** Verified via `results/phase5_mechanism/dependency_scope/pilot_5j_results.json`. The predictive lift from conditioning on line-position is 65.61%. This is a massive effect size that is not replicable by simple local DAG simulators (which showed only ~10% lift).

---

## 4. Findings: Structural & Logical Flaws

### 4.1 Data Leakage / Circularity
- **Observation:** The "Generator Matching" process in Phase 3 and 4 often used Phase 2 metrics as optimization targets.
- **Impact:** This ensured that synthetic data *matched* the real manuscript's anomalies, but it also means that passing an "indistinguishability test" (Phase 3.3) only proves that the generator is as anomalous as the original, not that the mechanism is identical.

### 4.2 Simulated Logic Persistence
- **Observation:** `src/phase1_foundation/metrics/library.py` still contains `_calculate_simulated` methods.
- **Impact:** While `REQUIRE_COMPUTED=1` is enforced in the pipeline, the existence of these methods creates a technical debt and a risk of "silent fallback" if configuration is mismanaged.

---

## 5. Final Assessment

| Finding | Impact | Validity |
|---------|--------|----------|
| **Language Falsification** | High | **UNSHAKEN**. The mapping collapse (0.02) is a real property of the EVA transcription under boundary shift. |
| **Mechanical Sufficiency** | High | **UNSHAKEN**. Generators matched on Phase 2 metrics are sufficient to explain the z=5.68 anomaly. |
| **Implicit Lattice Lead** | Medium | **PROBABLE**. The 65% positional lift proves global feature dependence, but the "Lattice" is a model class, not a specific historical object. |

**Final Statement:** The audit confirms that no critical errors were found that would flip the project's primary conclusions. The Voynich Manuscript remains best explained as a **Single Global Machine** using a **High-Skew Deterministic Traversal of an Implicit Lattice**.

---

## 6. Remediation (2026-02-09)

All code-level issues from sections 2.1, 2.2, and 4.2 have been addressed. Summary of changes (10 files, -604 / +100 lines):

### 6.1 Simulated Logic Removal (Section 4.2) — RESOLVED

All `_calculate_simulated`, `_compute_simulated`, and `_run_simulated` methods have been removed across:

| File | Change |
|------|--------|
| `phase1_foundation/metrics/library.py` | Removed dead `_calculate_simulated` from RepetitionRate and ClusterTightness. Removed `use_real_computation` guard. |
| `phase2_analysis/models/perturbation.py` | Replaced `_calculate_simulated` fallbacks with `_insufficient_data()` returning NaN + warning log. Removed `use_real_computation` guard. |
| `phase3_synthesis/refinement/feature_discovery.py` | Removed `_compute_simulated` (80+ lines of hardcoded values incl. 0.02). All `_compute_simulated_value` calls replaced with NaN + warning. Removed `use_real_computation` guard. |
| `phase2_analysis/stress_tests/mapping_stability.py` | Removed 4 hardcoded simulated return values (0.625, 0.70, 0.65, 0.30). Removed `use_real_computation` guard. |
| `phase2_analysis/stress_tests/locality.py` | Removed 6 simulated return values. Removed `use_real_computation` guard. |
| `phase2_analysis/stress_tests/information_preservation.py` | Removed simulated density/redundancy fallback. Removed `use_real_computation` guard. |
| `phase1_foundation/hypotheses/destructive.py` | Removed 4 large `_run_simulated` methods (~250 lines). Removed `use_real_computation` guard. |
| `phase1_foundation/hypotheses/library.py` | Removed `_run_simulated` method. Removed `use_real_computation` guard. |
| `phase3_synthesis/profile_extractor.py` | Removed `use_real_computation` guard; retained `store is None` guard (legitimate runtime fallback). |

### 6.2 Hardcoded Target Removal (Section 2.2) — RESOLVED

`scripts/phase3_synthesis/run_baseline_assessment.py`: Replaced hardcoded `target_z = 5.68` and `target_rep = 0.90` with dynamic computation from the `voynich_real` dataset. Info density and locality targets are now explicitly `None` with `status: requires_control_dataset`.

### 6.3 Hardcoded Feature Values (Section 2.1) — RESOLVED

The 0.02 value in `feature_discovery.py` (and all other hardcoded feature bases) have been removed. Missing-data cases now return NaN with a warning log instead of plausible-looking hardcoded values.

### 6.4 Data Leakage / Circularity (Section 4.1) — NOT A CODE FIX

This is a methodological observation, not a code defect. The generator matching process using Phase 2 metrics as optimization targets is by design. The audit correctly notes that passing an indistinguishability test proves the generator is *as anomalous* as the original, not that the mechanism is identical. This limitation is inherent to the methodology and is already documented in the project's conclusions.

### 6.5 Remaining `use_real_computation` Infrastructure

The `use_real_computation()` function and `ComputationTracker` in `config.py` are retained as infrastructure. No production code paths reference `use_real_computation` anymore; all computation is now unconditionally real. The infrastructure remains available for future testing scenarios.

---
**Audit COMPLETE. Remediation COMPLETE.**
