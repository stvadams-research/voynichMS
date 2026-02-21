# Support Cleanup 5: Holistic Critical Assessment and ROI Execution Plan

**Date:** 2026-02-21
**Status:** COMPLETE
**Objective:** Identify the highest-ROI work to improve correctness, reproducibility, credibility, and maintainability across code, tests, results, claims, and project structure.

## Executive Summary

The project had strong conceptual architecture but the operational state was **not publication-grade** due to three high-impact failures:

1. ~~**Replication path is broken at syntax level** in multiple runner scripts.~~ **FIXED**
2. ~~**Verification surfaces disagree** (tests, docs, claim map, and orchestration are out of sync).~~ **FIXED**
3. ~~**Traceability claims are overstated** relative to actual artifact/key integrity.~~ **FIXED**

All P0, P1, and P2 items have been resolved. Documentation coherence sweep completed.

## Assessment Scorecard (Updated)

| Area | Before | After | What Changed |
|---|---|---|---|
| Code execution reliability | D | **B+** | All 8 syntax errors fixed; master runner updated to 17 phases; `assemble_draft.py` removed; return code checks added |
| Test health & coverage fidelity | C- | **B+** | 5 missing test dirs added to `testpaths`; `from src.` imports fixed; 851 tests pass (up from 818 collected) |
| Results/claims traceability | D | **B+** | 8 claim map entries corrected (4 missing files, 4 wrong key paths); verification count updated to 77 |
| Documentation coherence | D | **B** | README, replicateResults, ARCHITECTURE, PROJECT_CLOSURE_SUMMARY, MECHANICAL_ARCHITECTURE all updated to 17 phases; 914→202 normalized in 4 reports; FINAL_FIDELITY_CALIBRATION.md deprecated |
| Packaging/dependency integrity | C- | **B+** | 5 missing runtime deps added; `phase12_mechanical*` and `phase14_machine*` added to package discovery |
| Architectural direction | B | **B+** | Unchanged — already strong |

## Evidence Snapshot (Before → After)

1. ~~Master replication fails immediately~~ → **FIXED:** `replicate_all.py` now lists all 17 phases, includes phases 9/15/16, removed nonexistent `assemble_draft.py`, improved Phase 0 error messaging
2. ~~Syntax errors in 8 scripts~~ → **FIXED:** 27 string literal fixes across 8 files; `python3 -m compileall -q scripts/` returns clean
3. ~~Test failures by missing deps~~ → **FIXED:** `networkx`, `scikit-learn`, `scipy`, `pandas`, `python-Levenshtein` added to `pyproject.toml` and `requirements.txt`
4. ~~Test collection fails with `from src...` imports~~ → **FIXED:** 4 test files updated to use package imports; 5 test dirs added to `testpaths`
5. Coverage: 64.28% (unchanged — P3.2 deferred)
6. Static quality debt: (unchanged — P3.1 deferred; ruff lint errors are mostly style, not syntax)
7. ~~Claim map integrity drift~~ → **FIXED:** 8 entries corrected (claims #1, #45-49, #52, #62c)
8. ~~914 vs 202 contradiction~~ → **FIXED:** 5 occurrences corrected across 4 documents

---

## P0: Restore Core Reproducibility Surface — COMPLETE

### P0.1 Fix syntax-breaking scripts and add parse gate — DONE
- **Actions taken:** Fixed 27 split string literals across 8 files. All `print(f"<newline>...")` replaced with `print(f"\n...")`.
- **Verification:** `python3 -m compileall -q scripts/` returns clean.
- **Files:** `verify_external_assets.py`, 6 `replicate.py` files (phases 6-9, 12-13), `phase17/replicate.py`

### P0.2 Fix master replication orchestration logic — DONE
- **Actions taken:**
  - Header updated: "14 phases" → "17 phases"
  - Phase list: added phases 9, 15, 16 (created `replicate.py` for phases 15 and 16)
  - Removed nonexistent `assemble_draft.py` call
  - Added return code check for publication generation
  - Phase 0 error message now says "Asset Verification Failed" (not just "Missing Assets")
  - Success message: "17 Phase Reports" (not "14")
- **Verification:** `python3 -c "import ast; ast.parse(open('scripts/support_preparation/replicate_all.py').read())"` succeeds
- **Files:** `replicate_all.py`, new `scripts/phase15_rule_extraction/replicate.py`, new `scripts/phase16_physical_grounding/replicate.py`

### P0.3 Repair test collection integrity — DONE
- **Actions taken:**
  - Added 5 dirs to `testpaths`: `phase12_mechanical`, `phase14_machine`, `phase15_selection`, `phase16_physical`, `phase17_finality`
  - Fixed `from src.` → package imports in 4 test files (1 phase12, 3 phase14)
- **Verification:** `pytest` now collects 851 tests (was 818). All pass.
- **Files:** `pyproject.toml`, `test_slip_detection.py`, `test_evaluation_engine.py`, `test_strict_admissibility.py`, `test_emulator.py`

---

## P1: Repair Claim/Artifact Truth Surface — COMPLETE

### P1.1 Reconcile claim map with actual artifacts and keys — DONE
- **Actions taken:** Corrected 8 entries:
  - Claim #1: `results/data/phase3_synthesis/test_a_results.json` → `core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json`, key `repetition_rate.target`
  - Claims #45-46: `stage5b_k_adjudication.json` → `stage5b_k_adjudication_summary.json`, keys corrected
  - Claim #47: key `results.method_f.confirmatory_runs` → `results.method_f_gate.run_count`
  - Claim #48: key `results.partial_rho` → `results.observed_partial_rho`
  - Claim #49: key `results.boundary_mi` → `results.B1_boundary_mi`
  - Claim #52: `cross_section_analysis.json` → `matrix_alignment.json`, key `results.structural_similarity.structural_correlation`
  - Claim #62c: `window_reordering.json` → `reordered_palette.json`, key `results.final_extreme_jump`
- **Note:** Machine-check CI gate (P1.1 stretch goal) deferred to future sprint.
- **Files:** `governance/claim_artifact_map.md`

### P1.2 Normalize canonical slip count — DONE
- **Actions taken:** Replaced "914" with "202 (ZL-only canonical data)" in 4 documents (5 occurrences total):
  - `results/reports/phase12_mechanical/MECHANICAL_ARCHITECTURE.md` (2 occurrences)
  - `results/reports/phase13_demonstration/EVIDENCE_GALLERY.md` (1)
  - `results/reports/phase14_machine/FINAL_FIDELITY_CALIBRATION.md` (1)
  - `governance/PROJECT_CLOSURE_SUMMARY.md` (1)
- Also fixed: "19.87x" signal ratio → "z=9.47σ" in MECHANICAL_ARCHITECTURE.md
- Also fixed: "three-state volvelle" → "Lattice-Modulated Window System (50 windows, 12+ mask states)"
- **Verification:** `grep -rn "914" results/reports/ governance/` returns only the historical note in claim_artifact_map.md

---

## P2: Dependency and Packaging Coherence — COMPLETE

### P2.1 Align runtime dependencies — DONE
- **Actions taken:** Added 5 missing runtime deps to both `pyproject.toml` and `requirements.txt`:
  - `scipy>=1.12`, `pandas>=2.2`, `scikit-learn>=1.4`, `networkx>=3.2`, `python-Levenshtein>=0.25`
- **Files:** `pyproject.toml`, `requirements.txt`

### P2.2 Align package discovery with source tree — DONE
- **Actions taken:** Added `phase12_mechanical*` and `phase14_machine*` to `[tool.setuptools.packages.find] include`
- **Files:** `pyproject.toml`

---

## P3: Documentation Coherence Sweep — COMPLETE

### P3.0 Documentation coherence sweep
- **Actions taken:** Fixed stale phase counts, metrics, and claims across 8 documents:

| Document | Fixes |
|---|---|
| `README.md` | Status: 17 phases; removed "100% statistical fit"; metrics: 43.44% admissibility, 12.37/10.90 BPT; added Phase 15/16 key findings; phase flag `[1-17]`; "all 17 phases" |
| `replicateResults.md` | "17 research phases"; added Phases 12-17 reproduction sections; publication loop covers all phases; claim table expanded with 16 new rows; "79 claims" |
| `ARCHITECTURE.md` | System diagram extended to Phase 17; "Phases 2-17"; execution chain extended; scripts/ listing updated |
| `PROJECT_CLOSURE_SUMMARY.md` | "20x" → z=9.47σ (1.89x ratio); "3-state" → 12-state LMWS; added Phase 15/16/17 findings section |
| `FINAL_FIDELITY_CALIBRATION.md` | Added deprecation notice directing to CANONICAL_EVALUATION.md |
| `MECHANICAL_ARCHITECTURE.md` | "19.87x" → z=9.47σ; "89 clusters" → data reference; "three-state volvelle" → LMWS |

---

## P3.1/P3.2: Quality Gate Hardening — DEFERRED

- Lint enforcement rollout and targeted coverage improvements are deferred to a future sprint.
- Current state: `ruff check` reports ~4,300 style issues (mostly formatting, not correctness).
- Recommended: fail CI on syntax/import errors first, then ratchet.

---

## Definition of Done — ACHIEVED

- [x] Master replication entrypoint is executable and truthful about what it runs.
- [x] Test suite collection is clean for all intended phase test directories (851 tests, 0 collection errors).
- [x] Claim map paths and keys match actual artifacts (8 corrections applied).
- [x] No unresolved contradictory headline metrics across core docs.
- [x] Dependency/package manifests reflect real runtime import surface.
- [x] Documentation consistently references 17 phases and current canonical metrics.

---

## Files Modified

| Category | Files |
|---|---|
| Syntax fixes (P0.1) | 8 scripts (verify_external_assets.py, 6 replicate.py, phase17 replicate.py) |
| Master runner (P0.2) | `replicate_all.py` |
| New replicate scripts (P0.2) | `scripts/phase15_rule_extraction/replicate.py`, `scripts/phase16_physical_grounding/replicate.py` |
| Test config (P0.3) | `pyproject.toml` (testpaths) |
| Test imports (P0.3) | 4 test files (phase12/14) |
| Claim map (P1.1) | `governance/claim_artifact_map.md` |
| Slip count (P1.2) | 4 report/governance files |
| Dependencies (P2) | `pyproject.toml`, `requirements.txt` |
| Documentation (P3) | `README.md`, `replicateResults.md`, `ARCHITECTURE.md`, `PROJECT_CLOSURE_SUMMARY.md`, `FINAL_FIDELITY_CALIBRATION.md`, `MECHANICAL_ARCHITECTURE.md` |
