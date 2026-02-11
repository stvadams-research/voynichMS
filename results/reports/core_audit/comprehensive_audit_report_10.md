# Comprehensive Code Audit Report 10

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no remediation changes in this pass)

---

## Executive Summary

Tenth-pass assessment was rerun end-to-end with fresh static and runtime evidence.

Primary outcomes:

- Release-gate false-pass behavior remains fixed (checks fail closed).
- Current release evidence is still not publishable: sensitivity robustness remains `INCONCLUSIVE` and `release_evidence_ready=false`.
- RI-11 criteria update remains in effect: strict indistinguishability blockage is treated as a source-data availability constraint (lost/unavailable pages), not a pure code defect.
- Split-folio normalization issue from prior pass is now resolved in current behavior: strict/non-strict preflight now reports missing `4/18` pages (not inflated counts).

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 0 | No immediate conclusion-invalidating defect observed in this pass |
| High | 1 | Release-evidence readiness blocker remains |
| Medium | 5 | Reproducibility and publication-readiness risks remain |
| Low | 0 | No low-priority-only findings recorded |

---

## Audit Scope and Evidence

Playbook Phases 0-5 were rerun with direct command execution and source inspection.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader; print('loader_import_ok')"`
- Determinism replay for Test A (two `scripts/phase3_synthesis/run_test_a.py` runs with same seed; canonical `results` compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/core_audit/pre_release_check.sh`
- `ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='Audit10 assessment' bash scripts/core_audit/pre_release_check.sh`
- `bash scripts/verify_reproduction.sh`
- `bash scripts/ci_check.sh`
- `python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py`
- Static scans via `find`, `rg`, `git status --short`, and SQLite queries against `data/voynich.db`

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True`; keys `['10','20','30']` |
| Full pytest + coverage | Pass | Total coverage `56.08%` |
| Pre-release baseline | Fail | Fails release-evidence gate (`release_evidence_ready=true` required) |
| Pre-release with dirty override | Fail | Still fails release-evidence gate |
| Reproduction verifier | Fail | Fails sensitivity integrity check (`release_evidence_ready=true` required) |
| CI check | Fail | Fails through verifier failure |
| Non-strict indistinguishability preflight | Pass-with-warning | Missing pages warning, `PREFLIGHT_OK` |
| Strict indistinguishability preflight | Fail (blocked) | `status=BLOCKED`, `reason_code=DATA_AVAILABILITY`, missing `4/18` pages |
| Strict indistinguishability full run | Fail (blocked) | Same strict preflight block |

No source-code fixes were applied as part of this assessment run.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 49 | `find scripts -name '*.py'` |
| `tests` Python files | 52 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 43 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 4 | `find scripts -name '*.sh'` |
| `core_status/by_run` files | 0 | `find core_status/by_run -type f` |
| working tree changes | 109 | `git status --short | wc -l` |

Top-level source distribution:

- `foundation 55`
- `analysis 22`
- `mechanism 21`
- `synthesis 13`
- `inference 6`
- `functional 6`
- `human 5`
- `comparative 1`

### 0.2 Inventory findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Medium | Worktree remains non-clean (`109` modified/untracked paths). | `scripts/core_audit/pre_release_check.sh:136`, `scripts/core_audit/pre_release_check.sh:149` |
| INV-2 | Resolved | Playbook-required audit log exists. | `scripts/core_audit/pre_release_check.sh:6`, `scripts/core_audit/pre_release_check.sh:11` |
| INV-3 | Resolved | Legacy `core_status/by_run` verification artifacts are absent in current workspace state. | `scripts/core_audit/pre_release_check.sh:113` |

---

## Phase 1: Results Integrity Audit

### 1.1 High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-13 | **High** | Release-evidence sensitivity artifact remains non-conclusive and non-ready, blocking verifier/CI/release gates. | `core_status/core_audit/sensitivity_sweep.json:21`, `core_status/core_audit/sensitivity_sweep.json:22`, `core_status/core_audit/sensitivity_sweep.json:26`, `core_status/core_audit/sensitivity_sweep.json:39`; gate enforcement: `scripts/core_audit/pre_release_check.sh:26`, `scripts/core_audit/pre_release_check.sh:42`, `scripts/core_audit/pre_release_check.sh:47`, `scripts/core_audit/pre_release_check.sh:52`; verifier enforcement: `scripts/verify_reproduction.sh:129`, `scripts/verify_reproduction.sh:153`, `scripts/verify_reproduction.sh:157`, `scripts/verify_reproduction.sh:161` |

### 1.2 Medium findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-11 (criteria retained) | **Medium** | Strict indistinguishability remains blocked by unavailable/lost source pages (`f91r`, `f91v`, `f92r`, `f92v`) and is treated as a scoped data-availability constraint, not a pure implementation defect. | `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.82412819-f2cf-88b3-b74b-01ec27e4bb05.json:12`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.82412819-f2cf-88b3-b74b-01ec27e4bb05.json:14`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.82412819-f2cf-88b3-b74b-01ec27e4bb05.json:15`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.82412819-f2cf-88b3-b74b-01ec27e4bb05.json:488`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.82412819-f2cf-88b3-b74b-01ec27e4bb05.json:494`; policy docs: `governance/governance/REPRODUCIBILITY.md:135`, `governance/governance/REPRODUCIBILITY.md:136`, `governance/governance/REPRODUCIBILITY.md:137`, `governance/PROVENANCE.md:84`, `governance/PROVENANCE.md:87` |
| RI-12 | Medium | Non-strict fallback path is still default unless strict mode is explicitly enabled (`REQUIRE_COMPUTED=1` or `--strict-computed`). | strict mode derivation: `scripts/phase3_synthesis/run_indistinguishability_test.py:420`; CLI flag: `scripts/phase3_synthesis/run_indistinguishability_test.py:406`, `scripts/phase3_synthesis/run_indistinguishability_test.py:413`; non-strict artifact: `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.f4bd9cb2-ea8b-fea0-b2af-34ca44178fdd.json:13` |
| MC-3 | Medium | Aggregate coverage exceeds threshold (`56.08%`), but one synthesis module remains below 20% (`feature_discovery.py` at `12.85%`), leaving low test confidence in that path. | `core_status/ci_coverage.json:1` (totals and per-file summaries), full run evidence from `bash scripts/ci_check.sh` output |
| MC-2R | Medium | Historical run provenance uncertainty persists: SQLite `runs` table still contains `63` `orphaned` rows and filesystem manifest check still shows `63` missing `runs/<id>/run.json`. | SQLite queries on `data/voynich.db` (`SELECT status, COUNT(*) ...` and manifest presence check); policy framing: `governance/PROVENANCE.md:96`, `governance/PROVENANCE.md:101`, `governance/PROVENANCE.md:104` |
| INV-1 | Medium | Release-cut baseline remains non-clean (`109` working-tree changes). | `git status --short | wc -l`; gate path: `scripts/core_audit/pre_release_check.sh:136`, `scripts/core_audit/pre_release_check.sh:149` |

### 1.3 Resolved/Improved since Audit 9

| Prior ID | Current state | Evidence |
|---|---|---|
| RI-14 (split-folio overcount) | **Resolved** | Preflight now canonicalizes split folios and reports missing `4/18` pages instead of inflated counts. | normalization logic: `scripts/phase3_synthesis/run_indistinguishability_test.py:129`, `scripts/phase3_synthesis/run_indistinguishability_test.py:133`, `scripts/phase3_synthesis/run_indistinguishability_test.py:144`, `scripts/phase3_synthesis/run_indistinguishability_test.py:147`; artifact fields: `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.f4bd9cb2-ea8b-fea0-b2af-34ca44178fdd.json:260`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.f4bd9cb2-ea8b-fea0-b2af-34ca44178fdd.json:486`, `core_status/phase3_synthesis/by_run/TURING_TEST_RESULTS.f4bd9cb2-ea8b-fea0-b2af-34ca44178fdd.json:492` |
| DOC-5 (RI-11 policy documentation gap) | **Resolved** | RI-11 policy treatment is now explicitly documented in reproducibility and provenance docs. | `governance/governance/REPRODUCIBILITY.md:135`, `governance/governance/REPRODUCIBILITY.md:136`, `governance/governance/REPRODUCIBILITY.md:137`; `governance/PROVENANCE.md:84`, `governance/PROVENANCE.md:87`, `governance/PROVENANCE.md:88`, `governance/PROVENANCE.md:89` |
| MC-3 partial | **Improved** | Coverage increased from prior pass baseline to `56.08%`; under-20 modules reduced to one. | `core_status/ci_coverage.json:1`; pytest/CI outputs from this pass |
| RI-10 (gate false-pass semantics) | **Still resolved** | Release checks remain fail-closed when sensitivity is not release-ready/conclusive/quality-passing. | `scripts/core_audit/pre_release_check.sh:37`, `scripts/core_audit/pre_release_check.sh:42`, `scripts/core_audit/pre_release_check.sh:47`, `scripts/core_audit/pre_release_check.sh:52`; `scripts/verify_reproduction.sh:144`, `scripts/verify_reproduction.sh:153`, `scripts/verify_reproduction.sh:157`, `scripts/verify_reproduction.sh:161` |

---

## Phase 2: Method Correctness and Internal Consistency

### Key observations

- Determinism contract remains stable for Test A replay (`results_equal=True`).
- Sensitivity release gates are correctly wired and fail closed when robustness is inconclusive.
- Strict indistinguishability behavior is explicit and policy-aligned (`BLOCKED` + `DATA_AVAILABILITY`) under current corpus availability.

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-3 | Resolved | Preflight now uses normalized page-ID handling for split folios, reducing naming/identity drift in strict checks. | `scripts/phase3_synthesis/run_indistinguishability_test.py:69`, `scripts/phase3_synthesis/run_indistinguishability_test.py:129`, `scripts/phase3_synthesis/run_indistinguishability_test.py:144` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | Improved | Strict mode commands and release-evidence constraints remain documented in reproducibility guide. | `governance/governance/REPRODUCIBILITY.md:90`, `governance/governance/REPRODUCIBILITY.md:94`, `governance/governance/REPRODUCIBILITY.md:101`, `governance/governance/REPRODUCIBILITY.md:135` |
| DOC-5 | Resolved | RI-11 data-availability interpretation is now explicitly encoded in release-facing docs. | `governance/governance/REPRODUCIBILITY.md:136`, `governance/governance/REPRODUCIBILITY.md:137`; `governance/PROVENANCE.md:87`, `governance/PROVENANCE.md:88`, `governance/PROVENANCE.md:89` |

---

## Phase 5: External-Critique Simulation

### Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Are release-evidence checks strict enough to prevent accidental pass? | Yes. Current scripts fail closed when sensitivity evidence is inconclusive/non-ready/non-quality-passing. |
| Why does strict indistinguishability fail? | Because four required pages are unavailable/lost in source corpus; strict policy correctly reports `BLOCKED` with `DATA_AVAILABILITY`. |
| Is missing-page accounting still inflated by split folios? | No. Current preflight canonicalization now reports `4/18` missing pages with normalized available-page tracking. |
| Is the project reproducible today? | Core determinism/tests pass, but full release verification still fails due sensitivity evidence state. |

---

## Consolidated Findings Register (Prioritized)

1. **RI-13 (High):** Sensitivity evidence remains non-conclusive/non-ready; release verification cannot pass.
2. **RI-11 (Medium, criteria retained):** Strict mode remains blocked by known source-data availability limits (lost/unavailable pages).
3. **RI-12 (Medium):** Non-strict fallback remains default unless strict mode is explicitly enforced.
4. **MC-3 (Medium):** Coverage threshold is met, but one synthesis module remains <20% coverage (`feature_discovery.py`).
5. **MC-2R (Medium):** Historical orphaned-run uncertainty remains explicit but unresolved.
6. **INV-1 (Medium):** Large dirty worktree (`109` paths) persists for release-cut baseline.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (tenth pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Blocking items before release confidence

- Produce a conclusive sensitivity artifact (`release_evidence_ready=true`, quality gate pass, conclusive robustness).
- Decide whether strict mode should be mandatory by default for release-path reproducibility commands.
- Decide and document disposition strategy for historical orphaned runs before publication freeze.
- Establish a clean release-cut working tree baseline.
