# Comprehensive Code Audit Report 8

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no remediation changes in this pass)

---

## Executive Summary

Eighth-pass assessment was rerun with fresh static and runtime evidence.

Compared with Audit 7:

- Prior critical verifier false-pass issue is **resolved**.
- CI/verifier sentinel contract now behaves correctly end-to-end.
- Historical run-state drift is **partially improved** (`running + NULL end` is now `0`; stale rows are classified `orphaned`).
- Two major release-readiness blockers remain:
  - strict indistinguishability cannot run to completion with current real-data availability,
  - release checks can pass while sensitivity robustness remains explicitly `INCONCLUSIVE`.

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 0 | No immediate conclusion-invalidating defect observed in this pass |
| High | 2 | Major release-evidence reliability blockers |
| Medium | 5 | Reproducibility clarity and publication-readiness risks |
| Low | 0 | No low-priority-only findings recorded |

---

## Audit Scope and Evidence

Playbook Phases 0-5 were rerun with direct command execution and source inspection.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader; print('loader_import_ok')"`
- Determinism replay for Test A (`run_test_a.py` twice with same seed; canonical `results` compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/verify_reproduction.sh`
- `bash scripts/ci_check.sh`
- `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py`
- `bash scripts/core_audit/pre_release_check.sh`
- `ALLOW_DIRTY_RELEASE=1 bash scripts/core_audit/pre_release_check.sh`
- static scans via `find`, `rg`, `git status --short`, and SQLite queries against `data/voynich.db`

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True`; keys `['10','20','30']` |
| Full pytest + coverage | Pass | Total coverage `50%` (`50.35%`) |
| Reproduction verifier | Pass | Completion marker emitted; exit code `0` |
| CI check | Pass | Includes verifier sentinel enforcement |
| Strict indistinguishability run | **Fail** | Explicit preflight runtime error: missing `10/18` expected real pharma pages under `REQUIRE_COMPUTED=1` |
| Pre-release baseline check | Fail by default | Fails on dirty tree (`89` changes) |
| Pre-release baseline with override | Pass | `ALLOW_DIRTY_RELEASE=1` bypasses dirty-tree gate |

No source-code fixes were applied as part of this assessment run.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 49 | `find scripts -name '*.py'` |
| `tests` Python files | 41 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 32 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 4 | `find scripts -name '*.sh'` |
| `core_status/by_run` files | 20 | `find core_status/by_run -type f` |

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
| INV-1 | Medium | Worktree remains non-clean (`89` modified/untracked paths), and release gate fails without explicit override. | `scripts/core_audit/pre_release_check.sh:40`, `scripts/core_audit/pre_release_check.sh:45`; `git status --short` |
| INV-2 | Resolved | Playbook-required audit log exists. | `AUDIT_LOG.md` |

---

## Phase 1: Results Integrity Audit

### 1.1 High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-10 | **High** | Sensitivity evidence can be marked `release_evidence_ready=true` while robustness is explicitly `INCONCLUSIVE` and quality gates fail; release checks currently treat this as pass. | Robustness fields: `core_status/core_audit/sensitivity_sweep.json:23`, `core_status/core_audit/sensitivity_sweep.json:24`; release-ready flag: `core_status/core_audit/sensitivity_sweep.json:37`; report caveats: `reports/core_audit/SENSITIVITY_RESULTS.md:11`, `reports/core_audit/SENSITIVITY_RESULTS.md:16`, `reports/core_audit/SENSITIVITY_RESULTS.md:17`, `reports/core_audit/SENSITIVITY_RESULTS.md:22`, `reports/core_audit/SENSITIVITY_RESULTS.md:23`; gate logic checks only mode/release-ready/scenario-count: `scripts/core_audit/pre_release_check.sh:30`, `scripts/core_audit/pre_release_check.sh:35`; same contract in verifier: `scripts/verify_reproduction.sh:137`, `scripts/verify_reproduction.sh:149`; observed `pre_release_check` pass under `ALLOW_DIRTY_RELEASE=1` despite `INCONCLUSIVE` robustness |
| RI-11 | **High** | Strict release-evidentiary indistinguishability path is blocked by missing real-data prerequisites (`10/18` pages missing). | Strict preflight guard: `scripts/phase3_synthesis/run_indistinguishability_test.py:84`, `scripts/phase3_synthesis/run_indistinguishability_test.py:111`; strict command in reproducibility docs: `governance/governance/REPRODUCIBILITY.md:44`, `governance/governance/REPRODUCIBILITY.md:94`; observed runtime failure message with `REQUIRE_COMPUTED=1` |

### 1.2 Medium findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| RI-12 | Medium | Non-strict indistinguishability remains default (`REQUIRE_COMPUTED` opt-in), so fallback/simulated paths can still run unless caller enforces strict mode. | `scripts/phase3_synthesis/run_indistinguishability_test.py:125`, `scripts/phase3_synthesis/run_indistinguishability_test.py:114` |
| MC-3 | Medium | Coverage remains at `50%` with six modules at `0%` (`core/logging`, `core/models`, `qc/anomalies`, `qc/checks`, `storage/filesystem`, `storage/interface`). | `python3 -m pytest --cov=src ...` output from this run |
| MC-2R | Medium | Historical run provenance remains uncertain for old executions: `63` runs are now explicitly `orphaned` (no open `running` rows), and none have `runs/<id>/run.json`. | SQLite query on `data/voynich.db`: `success=89`, `orphaned=63`, `running_end_null=0`, `orphaned_missing_run_json=63`; policy note: `governance/PROVENANCE.md:88` |
| ST-1 | Medium | Legacy `core_status/by_run/verify_*.json` payloads still contain `provenance.status: running` (`20/20` files), which conflicts with current immutable-artifact policy language. | Example file: `core_status/by_run/verify_1.1291aeff-2f29-02e2-551d-1aa8b0ea6912.json:6`; policy: `governance/PROVENANCE.md:45`, `governance/PROVENANCE.md:49` |
| DOC-4 | Medium | Playbook expected outputs list root-level `governance/METHODS_REFERENCE.md`/`CONFIG_REFERENCE.md`/`governance/REPRODUCIBILITY.md`, while project currently uses `governance/` paths; contract is workable but naming/path mismatch remains for strict checklist interpretation. | Playbook contract: `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md` (Expected Outputs section); current files: `governance/governance/METHODS_REFERENCE.md`, `governance/CONFIG_REFERENCE.md`, `governance/governance/REPRODUCIBILITY.md` |

### 1.3 Resolved/Improved since Audit 7

| Prior ID | Current state | Evidence |
|---|---|---|
| MC-6 (verifier false pass) | **Resolved** | Verifier completion guard and trap-based fail-safe present: `scripts/verify_reproduction.sh:17`, `scripts/verify_reproduction.sh:18`, `scripts/verify_reproduction.sh:165`; CI sentinel enforcement present: `scripts/ci_check.sh:84`, `scripts/ci_check.sh:85`; both commands passed in this run |
| MC-2 (open `running` rows) | **Improved** | No `status='running' AND timestamp_end IS NULL` rows remain in `runs` table (`0`), historical uncertainty explicitly represented as `orphaned` |
| RI-9 partial (bounded sweep) | **Improved** | Sensitivity artifact now executes full release scenario count `17/17` with canonical command. | `core_status/core_audit/sensitivity_sweep.json:9`, `core_status/core_audit/sensitivity_sweep.json:35`, `core_status/core_audit/sensitivity_sweep.json:36`; `reports/core_audit/SENSITIVITY_RESULTS.md:8` |

---

## Phase 2: Method Correctness and Internal Consistency

### Key observations

- Determinism contract remains stable for Test A in this pass.
- CI/reproduction gate integrity materially improved and now matches documented sentinel contract.
- Strict evidentiary path for indistinguishability is now explicitly fail-fast (good behavior), but is currently blocked by missing real dataset pages.
- Sensitivity pipeline quality diagnostics are explicit and caveat-rich, but release gating semantics remain weaker than robustness semantics.

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-1 | Medium | Historical verify artifacts still encode legacy `provenance.status: running` state. | `core_status/by_run/verify_1.1291aeff-2f29-02e2-551d-1aa8b0ea6912.json:6` |
| ST-2 | Improved | Verifier/CI contracts now include explicit completion marker propagation and consumption. | `scripts/verify_reproduction.sh:166`; `scripts/ci_check.sh:85` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | Improved | Reproducibility documentation now describes verifier sentinel contract and strict-mode command. | `governance/governance/REPRODUCIBILITY.md:124`, `governance/governance/REPRODUCIBILITY.md:126`, `governance/governance/REPRODUCIBILITY.md:131` |
| DOC-4 | Medium | Expected-output filenames in playbook and actual docs pathing differ (`governance/` vs root-level names), which can cause checklist ambiguity. | `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`; `governance/governance/METHODS_REFERENCE.md`; `governance/CONFIG_REFERENCE.md`; `governance/governance/REPRODUCIBILITY.md` |

---

## Phase 5: External-Critique Simulation

### Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Where are assumptions stated? | Better documented in `governance/PROVENANCE.md`, `governance/SENSITIVITY_ANALYSIS.md`, and sensitivity report caveats. |
| Which parameters matter most? | Sensitivity thresholds, evaluation weights, and strict/fallback execution mode controls remain primary. |
| What happens if they change? | Full release-mode sensitivity sweep runs, but all scenarios remain invalid due insufficient-data conditions. |
| How do we know this is not tuned? | Determinism and CI/repro checks pass; however, strict indistinguishability cannot complete due missing real-data prerequisites. |
| What evidence is negative/null? | Sensitivity artifact explicitly reports `0` valid scenarios and `INCONCLUSIVE` robustness with caveats. |

---

## Consolidated Findings Register (Prioritized)

1. **RI-10 (High):** Release checks can pass while sensitivity robustness remains `INCONCLUSIVE` and quality gates fail.
2. **RI-11 (High):** Strict indistinguishability run is blocked by missing real-data prerequisites (`10/18` pages absent).
3. **RI-12 (Medium):** Non-strict fallback path remains default unless strict mode is explicitly enforced.
4. **MC-3 (Medium):** Coverage remains shallow in key modules (`50%` aggregate; six `0%` files).
5. **INV-1 (Medium):** Release baseline fails by default due large dirty worktree (`89` changes).
6. **MC-2R / ST-1 (Medium):** Historical artifact/run-state uncertainty remains explicit but unresolved (orphaned rows + legacy verify payloads).
7. **DOC-4 (Medium):** Playbook output filenames and actual doc paths are not aligned exactly.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (eighth pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Blocking items before release confidence

- Align release gating semantics with robustness semantics so a robustness-`INCONCLUSIVE` sensitivity artifact cannot be interpreted as release-ready evidence by automation.
- Satisfy strict real-profile prerequisites (or formally scope/label the strict indistinguishability check as currently blocked and non-evidentiary).
- Decide and document policy for historical orphaned runs and legacy verify artifacts (`core_status/by_run`) prior to publication freeze.
- Establish intentional clean release baseline (or explicitly accepted dirty cut policy with traceability).
