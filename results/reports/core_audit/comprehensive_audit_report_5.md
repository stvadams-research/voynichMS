# Comprehensive Code Audit Report 5

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no fixes applied)

---

## Executive Summary

This fifth-pass assessment was rerun from the playbook with fresh command evidence.

Compared to prior audits, deterministic replay and CI checks now pass. The main unresolved blocker has shifted from core execution determinism to **sensitivity-analysis validity and interpretation quality**.

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 1 | Invalidates a core methodological claim |
| High | 6 | Materially weakens release defensibility |
| Medium | 9 | Important correctness/reproducibility risks |
| Low | 2 | Hygiene/clarity gaps |

---

## Audit Scope and Evidence

Playbook phases 0 through 5 were rerun with static and runtime checks.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader; print('loader_import_ok')"`
- `python3 scripts/phase3_synthesis/run_test_a.py --seed 4242 --output /tmp/audit5_test_a_1.json` (run twice; canonical payload compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/verify_reproduction.sh`
- `bash scripts/ci_check.sh`
- inventory and static scans with `find`, `rg`, `git status --short`, and direct source inspection

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True` for same seed |
| Full pytest + coverage | Pass | Total coverage `40%` |
| Reproduction verifier | Pass | Warnings still emitted by cluster-tightness fallback path |
| CI check | Pass | CI coverage gate run reports `34.30%` |

No remediation changes were made for this audit.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 48 | `find scripts -name '*.py'` |
| `tests` Python files | 26 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 17 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 2 | `find scripts -name '*.sh'` |

Top-level source distribution:

- `src/phase1_foundation`: 55
- `src/phase2_analysis`: 22
- `src/phase5_mechanism`: 21
- `src/phase3_synthesis`: 13
- `src/phase4_inference`: 6
- `src/phase6_functional`: 6
- `src/phase7_human`: 5
- `src/phase8_comparative`: 1

### 0.2 Inventory findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Medium | Worktree is not release-clean (59 modified/untracked paths), which complicates reproducible freeze/baseline claims. | `git status --short` |
| INV-2 | Medium | `core_status/` artifacts are not ignored and appear as recurring untracked output noise. | `.gitignore:37`, `.gitignore:38`, `.gitignore:39`; `git status --short` (`?? core_status/`) |

---

## Phase 1: Results Integrity Audit

### 1.1 Critical and High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-1 | **Critical** | Sensitivity sweep evaluates dataset `"real"` instead of canonical `"voynich_real"`, driving invalid/insufficient-data paths. | `scripts/phase2_analysis/run_sensitivity_sweep.py:73`, `scripts/phase2_analysis/run_sensitivity_sweep.py:74`; DB check: `has_real 0`, `has_voynich_real 1` |
| RI-2 | **High** | Robustness PASS is degenerate: all scenarios show `Surviving=0` and `Falsified=6`, so stability is measured on collapsed outputs. | `reports/core_audit/SENSITIVITY_RESULTS.md:15` through `reports/core_audit/SENSITIVITY_RESULTS.md:31` |
| RI-3 | **High** | Perturbation warnings are intentionally suppressed during sweep, reducing visibility into invalid-run conditions. | `scripts/phase2_analysis/run_sensitivity_sweep.py:50` |
| RI-4 | **High** | Documentation states robustness PASS without disclosing all-model collapse caveat, which overstates conclusion strength. | `governance/SENSITIVITY_ANALYSIS.md:15` through `governance/SENSITIVITY_ANALYSIS.md:18`; compare `reports/core_audit/SENSITIVITY_RESULTS.md:15` through `reports/core_audit/SENSITIVITY_RESULTS.md:31` |

### 1.2 Medium and Low findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| RI-5 | Medium | Sensitivity runner writes core_status/report artifacts outside provenance envelope format used by most run scripts. | `scripts/phase2_analysis/run_sensitivity_sweep.py:225`; `scripts/phase2_analysis/run_sensitivity_sweep.py:156` |
| RI-6 | Medium | Sensitivity runner mutates `configs/phase6_functional/model_params.json` in place per scenario, with drift risk on interrupted runs. | `scripts/phase2_analysis/run_sensitivity_sweep.py:189`; restore in `scripts/phase2_analysis/run_sensitivity_sweep.py:202` |
| RI-7 | Medium | Fixture contains non-standard JSON token `NaN`; strict JSON parsers may reject it. | `tests/fixtures/cluster_tightness_baseline.json:13` |
| RI-8 | Low | Residual `"NOT COMPUTED"` display fallback remains in baseline assessment output formatting. | `scripts/phase3_synthesis/run_baseline_assessment.py:205` |

---

## Phase 2: Method Correctness and Internal Consistency

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| MC-1 | **High** | CI gate tests only `tests/phase1_foundation`, `tests/phase2_analysis`, `tests/core_audit`, excluding present suites (`integration`, `human`, `mechanism`, `synthesis`). | `scripts/ci_check.sh:23` through `scripts/ci_check.sh:25`; test dirs under `tests/` |
| MC-2 | **High** | Coverage remains low in critical modules despite global pass (`40%` full-suite, many core files still 0%). | Full pytest coverage output; examples: `src/phase2_analysis/models/*`, `src/phase1_foundation/cli/main.py`, `src/phase1_foundation/qc/*` |
| MC-3 | Medium | CI coverage (`34.30%`) diverges materially from full-suite coverage (`40%`) because CI runs a subset of suites. | `bash scripts/ci_check.sh` vs `python3 -m pytest ... tests` |
| MC-4 | Medium | Provenance migration is incomplete in `run_*.py` inventory: 6 runner scripts do not reference `ProvenanceWriter` (`run_phase_2_1.py`, `run_phase_2_3.py`, `run_phase_2_4.py`, `run_phase_3.py`, `run_phase_3_1.py`, `run_sensitivity_sweep.py`). | `rg` inventory over `scripts/**/run_*.py` |

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-1 | Medium | Artifact contracts remain mixed: provenance-heavy runner outputs coexist with ad hoc core_audit/sensitivity status files. | `scripts/phase2_analysis/run_sensitivity_sweep.py`, `core_status/core_audit/sensitivity_sweep.json`, `reports/core_audit/SENSITIVITY_RESULTS.md` |
| ST-2 | Low | Output lifecycle policy is still inconsistent (`runs/` ignored, `core_status/` not ignored). | `.gitignore:37`, `.gitignore:38`, `.gitignore:39` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | **High** | Sensitivity summary framing is not aligned with scenario-level evidence quality; missing explicit caveat for all-scenario zero survivors. | `governance/SENSITIVITY_ANALYSIS.md:15` through `governance/SENSITIVITY_ANALYSIS.md:18`; `reports/core_audit/SENSITIVITY_RESULTS.md:15` through `reports/core_audit/SENSITIVITY_RESULTS.md:31` |
| DOC-2 | Medium | Sensitivity report lacks explicit data-quality caveats section (missing-data/fallback-rate context). | `reports/core_audit/SENSITIVITY_RESULTS.md` |

---

## Phase 5: External-Critique Simulation and Clean-Room Re-Execution

### 5.1 Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Where are assumptions stated? | Mostly documented, but sensitivity-run assumptions still include implicit data-target mismatch (`real` vs `voynich_real`). |
| Which parameters matter most? | Thresholds, sensitivities, and dimension weights are explicit in sweep script/config. |
| What happens if they change? | Current evidence indicates top-model/anomaly labels stay fixed, but all runs are uniformly falsified (`0` survivors), weakening interpretation. |
| How do we know this is not tuned? | Determinism is now demonstrated, but robustness claims remain vulnerable until sensitivity data-targeting and caveats are corrected. |
| What evidence is negative/null? | Scenario table clearly reports all-model falsification; this negative evidence is present but under-emphasized in summary docs. |

### 5.2 Clean-room command outcomes

| Check | Result | Notes |
|---|---|---|
| `python3 -c "... import foundation.configs.loader ..."` | Pass | Import succeeds (`loader_import_ok`). |
| `run_test_a.py` replay with same seed | Pass | Canonical `results` payload identical across two runs. |
| `python3 -m pytest --cov=src ... -q tests` | Pass | Coverage `40%`. |
| `bash scripts/verify_reproduction.sh` | Pass | Includes warning: cluster-tightness bbox fallback with insufficient regions. |
| `bash scripts/ci_check.sh` | Pass | CI coverage gate currently enforced on suite subset (`34.30%`). |

---

## Consolidated Findings Register (Prioritized)

1. **RI-1 (Critical):** sensitivity sweep runs against invalid dataset ID (`real`), not `voynich_real`.
2. **RI-2 + RI-4 + DOC-1 (High):** robustness PASS messaging is stronger than the underlying scenario evidence supports.
3. **MC-1 + MC-2 (High):** CI gate scope and critical-module coverage remain insufficient for release confidence.
4. **RI-5 + RI-6 (Medium):** sensitivity artifacts/provenance and config-mutation strategy remain fragile.
5. **INV-1 + INV-2 (Medium):** release baseline hygiene is still noisy (dirty tree + unignored status artifacts).

---

## Release Readiness Verdict

**Assessment Complete:** Yes (fifth pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Remaining blockers before release confidence

- Correct sensitivity data targeting and regenerate sweep evidence.
- Align sensitivity summary language with scenario-level evidence quality.
- Expand mandatory CI suite coverage and improve critical-module tests.
- Freeze a clean release baseline and artifact policy.
