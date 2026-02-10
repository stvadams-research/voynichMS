# Comprehensive Code Audit Report 9

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no remediation changes in this pass)

---

## Executive Summary

Ninth-pass assessment was rerun end-to-end with fresh static and runtime evidence.

Primary outcomes:

- Release-gate false-pass behavior from earlier audits remains fixed.
- Current release evidence is still not publishable: sensitivity robustness is `INCONCLUSIVE` and `release_evidence_ready=false`.
- **RI-11 criteria updated in this pass:** strict indistinguishability blockage is now treated as a **source-data availability constraint** (lost/unavailable pages), not a pure code defect.
- A separate implementation-level issue remains: strict preflight uses exact page IDs and over-counts missing pages when source uses split folios (`f89r1`, `f89r2`, etc.).

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 0 | No immediate conclusion-invalidating defect observed in this pass |
| High | 1 | Release-evidence readiness blocker |
| Medium | 6 | Reproducibility, criteria, and publication-readiness risks |
| Low | 0 | No low-priority-only findings recorded |

---

## Audit Scope and Evidence

Playbook Phases 0-5 were rerun with direct command execution and source inspection.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader; print('loader_import_ok')"`
- Determinism replay for Test A (`scripts/synthesis/run_test_a.py` twice with same seed; canonical `results` compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/audit/pre_release_check.sh`
- `ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='Audit9 assessment' bash scripts/audit/pre_release_check.sh`
- `bash scripts/verify_reproduction.sh`
- `bash scripts/ci_check.sh`
- `python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only`
- `REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py`
- static scans via `find`, `rg`, `git status --short`, and SQLite queries against `data/voynich.db`

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True`; keys `['10','20','30']` |
| Full pytest + coverage | Pass | Total coverage `52.28%` |
| Pre-release baseline | Fail | Fails release-evidence gate (`release_evidence_ready=true` required) |
| Pre-release with dirty override | Fail | Still fails release-evidence gate |
| Reproduction verifier | Fail | Fails sensitivity integrity check (`release_evidence_ready=true` required) |
| CI check | Fail | Fails through verifier failure |
| Non-strict indistinguishability preflight | Pass-with-warning | Missing pages warning, `PREFLIGHT_OK` |
| Strict indistinguishability preflight | Fail | RuntimeError: missing expected pharmaceutical pages |
| Strict indistinguishability full run | Fail | Same preflight RuntimeError |

No source-code fixes were applied as part of this assessment run.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 49 | `find scripts -name '*.py'` |
| `tests` Python files | 47 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 38 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 4 | `find scripts -name '*.sh'` |
| `status/by_run` files | 0 | `find status/by_run -type f` |
| working tree changes | 102 | `git status --short | wc -l` |

Top-level source distribution:

- `foundation 55`
- `analysis 22`
- `mechanism 21`
- `synthesis 13`
- `functional 6`
- `inference 6`
- `human 5`
- `comparative 1`

### 0.2 Inventory findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Medium | Worktree remains non-clean (`102` modified/untracked paths). | `scripts/audit/pre_release_check.sh:86`, `scripts/audit/pre_release_check.sh:89` |
| INV-2 | Resolved | Playbook-required audit log exists. | `AUDIT_LOG.md` |

---

## Phase 1: Results Integrity Audit

### 1.1 High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-13 | **High** | Release-evidence sensitivity artifact is explicitly non-conclusive and non-ready, blocking verifier/CI/release gates. | `status/audit/sensitivity_sweep.json:21`, `status/audit/sensitivity_sweep.json:22`, `status/audit/sensitivity_sweep.json:26`, `status/audit/sensitivity_sweep.json:39`; `reports/audit/SENSITIVITY_RESULTS.md:9`, `reports/audit/SENSITIVITY_RESULTS.md:11`, `reports/audit/SENSITIVITY_RESULTS.md:16`, `reports/audit/SENSITIVITY_RESULTS.md:17`, `reports/audit/SENSITIVITY_RESULTS.md:18`; gate enforcement: `scripts/audit/pre_release_check.sh:35`, `scripts/audit/pre_release_check.sh:42`, `scripts/audit/pre_release_check.sh:47`, `scripts/audit/pre_release_check.sh:52`; verifier enforcement: `scripts/verify_reproduction.sh:142`, `scripts/verify_reproduction.sh:153`, `scripts/verify_reproduction.sh:157`, `scripts/verify_reproduction.sh:161` |

### 1.2 Medium findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-11 (criteria update) | **Medium** | Strict indistinguishability failure is reclassified as a source-data availability constraint (lost/unavailable pages), not a pure code defect. Exact strict command still fails by design under current corpus availability. | strict failure artifact: `status/synthesis/by_run/TURING_TEST_RESULTS.75bd9894-f1d9-6826-4212-382b4a9c6d85.json:14`; strict raise path: `scripts/synthesis/run_indistinguishability_test.py:118`, `scripts/synthesis/run_indistinguishability_test.py:119`; expected section page contract: `src/synthesis/profile_extractor.py:63`, `src/synthesis/profile_extractor.py:69`; profile doc context: `src/synthesis/profile_extractor.py:4` |
| RI-14 | Medium | Preflight exact-page matching overstates missing pages (`10/18`) because split folio IDs in source (`f89r1`, `f89r2`, etc.) are not canonicalized before comparison. | expected vs available vs missing lists: `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:16`, `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:36`, `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:260`, `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:272`; exact matching logic: `scripts/synthesis/run_indistinguishability_test.py:100` |
| RI-12 | Medium | Non-strict fallback path remains the default unless strict mode is explicitly enabled (`REQUIRE_COMPUTED=1` or `--strict-computed`). | strict mode derivation: `scripts/synthesis/run_indistinguishability_test.py:366`; non-strict run state: `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:13` |
| MC-3 | Medium | Aggregate coverage is above minimum (`52.28%`) but six substantive modules remain below 20%, indicating low test confidence in several synthesis/anomaly paths. | `status/ci_coverage.json` totals and file summaries (generated by `scripts/ci_check.sh`) |
| MC-2R | Medium | Historical run provenance uncertainty persists: `63` rows remain `orphaned` and all `63` lack corresponding `run.json` artifact entries. | SQLite audit query against `data/voynich.db`; policy framing: `docs/PROVENANCE.md:90`, `docs/PROVENANCE.md:95` |
| INV-1 | Medium | Release-cut baseline is not currently clean (`102` working-tree changes). | `scripts/audit/pre_release_check.sh:86`, `scripts/audit/pre_release_check.sh:88`; `git status --short | wc -l` |

### 1.3 Resolved/Improved since Audit 8

| Prior ID | Current state | Evidence |
|---|---|---|
| RI-10 (gate false-pass semantics) | **Resolved** | Release checks now fail closed when sensitivity is not release-ready/conclusive/quality-passing. | `scripts/audit/pre_release_check.sh:35`, `scripts/audit/pre_release_check.sh:42`, `scripts/audit/pre_release_check.sh:47`, `scripts/audit/pre_release_check.sh:52`; `scripts/verify_reproduction.sh:142`, `scripts/verify_reproduction.sh:153`, `scripts/verify_reproduction.sh:157`, `scripts/verify_reproduction.sh:161` |
| ST-1 (legacy verify artifacts under `status/by_run`) | **Resolved in current workspace state** | `find status/by_run -type f` returned `0` files; pre-release legacy-artifact check is active: `scripts/audit/pre_release_check.sh:65`, `scripts/audit/pre_release_check.sh:76` |
| MC-3 partial | **Improved** | Coverage increased from prior pass baseline to `52.28%`; zero-covered module count now `0`. | `status/ci_coverage.json` |

---

## Phase 2: Method Correctness and Internal Consistency

### Key observations

- Determinism contract remains stable for Test A replay.
- Sensitivity release gates are correctly wired and now fail closed when robustness is inconclusive.
- Strict indistinguishability logic is explicit and fail-fast, but current preflight criteria conflate unavailable folios with non-canonical split-folio IDs.

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-3 | Medium | Pharmaceutical preflight assumes canonical page IDs while corpus stores mixed canonical + split IDs, creating naming/identity drift at runtime checks. | `scripts/synthesis/run_indistinguishability_test.py:88`, `scripts/synthesis/run_indistinguishability_test.py:100`; `status/synthesis/by_run/TURING_TEST_RESULTS.f258c848-e3e5-dd11-16b5-d5f21898cfcf.json:235` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | Improved | Strict mode commands and release-evidence constraints are documented in reproducibility guide. | `docs/REPRODUCIBILITY.md:94`, `docs/REPRODUCIBILITY.md:100`, `docs/REPRODUCIBILITY.md:133` |
| DOC-5 | Medium | Documentation does not yet encode the newly requested RI-11 criteria interpretation (lost/unavailable source pages) as an explicit audit/release policy decision. | `docs/REPRODUCIBILITY.md`, `docs/PROVENANCE.md` |

---

## Phase 5: External-Critique Simulation

### Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Are release-evidence checks strict enough to prevent accidental pass? | Yes, current scripts fail closed when sensitivity evidence is inconclusive. |
| Why does strict indistinguishability fail? | Because required page set is not fully available in source corpus under current criteria; this pass reclassifies that as data-availability scope, not hidden tuning. |
| Is the missing-page count itself reliable? | Not fully; current preflight over-counts missing folios due split-ID mismatch. |
| Is the project reproducible today? | Core determinism/tests pass, but full release verification fails due sensitivity evidence state. |

---

## RI-11 Criteria Update (Applied in Audit 9)

Audit 8 treated RI-11 as a high code-level blocker. For Audit 9, criteria are updated per stakeholder instruction:

- Missing pharmaceutical pages that are lost/unavailable in source data are treated as **scope constraints**, not coding defects.
- This reclassifies RI-11 from **High** to **Medium**.
- A separate code/data-contract issue remains (RI-14): exact ID matching inflates missing count by not normalizing split folios.

---

## Consolidated Findings Register (Prioritized)

1. **RI-13 (High):** Sensitivity evidence remains non-conclusive/non-ready; release verification cannot pass.
2. **RI-14 (Medium):** Indistinguishability preflight over-counts missing pages due non-canonical ID matching.
3. **RI-11 (Medium, reclassified):** Strict mode blocked by known source-data availability limits (lost/unavailable pages).
4. **RI-12 (Medium):** Non-strict fallback remains default unless strict mode is explicitly enforced.
5. **MC-3 (Medium):** Coverage floor met, but multiple critical synthesis/anomaly modules remain <20% coverage.
6. **MC-2R (Medium):** Historical orphaned-run uncertainty remains explicit but unresolved.
7. **INV-1 (Medium):** Large dirty worktree (`102` paths) persists for release-cut baseline.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (ninth pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Blocking items before release confidence

- Produce a conclusive sensitivity artifact (`release_evidence_ready=true`, quality gate pass, conclusive robustness).
- Finalize and document RI-11 policy language (source-data-availability scope) in release-facing docs/checklists.
- Resolve preflight page-ID normalization mismatch so missing-page accounting reflects corpus reality.
- Decide and document disposition strategy for historical orphaned runs before publication freeze.
