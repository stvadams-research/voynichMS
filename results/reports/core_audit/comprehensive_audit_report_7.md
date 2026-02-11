# Comprehensive Code Audit Report 7

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no remediation changes in this pass)

---

## Executive Summary

Seventh-pass assessment was rerun with fresh static and runtime evidence.

Compared with Audit 6:

- Prior critical hardcoded-metric issue in `run_indistinguishability_test.py` is no longer present.
- Sensitivity artifacts are now canonical (`run_sensitivity_sweep`) and no longer legacy-tagged (`unknown_legacy` absent).
- `AUDIT_LOG.md` now exists (playbook output contract improved).
- A **new critical gate integrity issue** is present: `scripts/verify_reproduction.sh` can fail immediately and still return exit code `0`; `scripts/ci_check.sh` therefore reports success even when reproduction verification did not run.

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 1 | Can invalidate claimed verification success |
| High | 4 | Major result-trust or release-readiness blockers |
| Medium | 5 | Significant correctness/process clarity risks |
| Low | 1 | Hygiene noise |

---

## Audit Scope and Evidence

Playbook Phases 0-5 were rerun with direct command execution and source inspection.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import phase1_foundation.configs.loader; print('loader_import_ok')"`
- Determinism replay for Test A (`run_test_a.py` twice with same seed; canonical `results` compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/verify_reproduction.sh`
- `VIRTUAL_ENV="" bash scripts/verify_reproduction.sh` (workaround run to evaluate downstream behavior)
- `bash scripts/ci_check.sh`
- Timed subprocess execution of `scripts/phase3_synthesis/run_indistinguishability_test.py` (120s timeout wrapper)
- static scans via `find`, `rg`, `git status --short`, and metadata DB queries

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True` |
| Full pytest + coverage | Pass | Total coverage `50.35%` |
| Reproduction verifier (default invocation) | **Failing behavior** | Emits `VIRTUAL_ENV` unbound error but exits `0` |
| Reproduction verifier (`VIRTUAL_ENV=""`) | Pass | Completes determinism/spot-check/sensitivity checks |
| CI check | **False pass** | Prints `CI Check PASSED` despite verifier abort message |
| Indistinguishability runner timed execution | **Incomplete** | Did not finish within 120s; emitted fallback/simulated-profile warnings |

No source-code fixes were applied as part of this assessment run.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 49 | `find scripts -name '*.py'` |
| `tests` Python files | 39 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 30 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 3 | `find scripts -name '*.sh'` |

Top-level source distribution remains centered in:

- `src/phase1_foundation` (55)
- `src/phase2_analysis` (22)
- `src/phase5_mechanism` (21)
- `src/phase3_synthesis` (13)

### 0.2 Inventory findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Medium | Worktree remains non-clean (`83` modified/untracked paths), complicating release-baseline assertions. | `git status --short` |
| INV-2 | Resolved | Playbook-required `AUDIT_LOG.md` now exists. | `AUDIT_LOG.md` |
| INV-3 | Low | Transient status artifacts still accumulate and include historical stale provenance payloads. | `core_status/by_run/*`, e.g. `core_status/by_run/verify_1.2fe7df1c-9f94-805c-17fa-5ebe7dde7dae.json:6` |

---

## Phase 1: Results Integrity Audit

### 1.1 Critical/High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| MC-6 | **Critical** | Reproduction verification gate can fail immediately but still return success (`exit 0`), enabling false-positive CI/reproducibility claims. | Unbound var site: `scripts/verify_reproduction.sh:18`; strict shell mode: `scripts/verify_reproduction.sh:2`; observed behavior: `verify_exit:0` with error `VIRTUAL_ENV: unbound variable`; CI still reports pass after same error via verifier call at `scripts/ci_check.sh:78` |
| RI-8 | **High** | `run_indistinguishability_test.py` no longer hardcodes decision constants, but execution still depends on fallback/simulated profile paths and did not complete within 120s in timed assessment run. | Runner uses extractor path `scripts/phase3_synthesis/run_indistinguishability_test.py:93`; fallback infrastructure in `src/phase3_synthesis/profile_extractor.py:71`, `src/phase3_synthesis/profile_extractor.py:102`, `src/phase3_synthesis/profile_extractor.py:130`, `src/phase3_synthesis/profile_extractor.py:416`; timed run emitted fallback warnings and hit timeout |
| RI-9 | **High** | Published sensitivity evidence is canonical but not release-grade robustness evidence: latest artifact is a bounded single-scenario run (`--max-scenarios 1`) with 0 valid scenarios and `INCONCLUSIVE` decision. | `core_status/core_audit/sensitivity_sweep.json:13`, `core_status/core_audit/sensitivity_sweep.json:14`, `core_status/core_audit/sensitivity_sweep.json:24`, `core_status/core_audit/sensitivity_sweep.json:31`; `reports/core_audit/SENSITIVITY_RESULTS.md:7`, `reports/core_audit/SENSITIVITY_RESULTS.md:8`, `reports/core_audit/SENSITIVITY_RESULTS.md:13` |
| MC-2 | **High** | Metadata DB still contains substantial stale historical run rows (`status='running'`, `timestamp_end IS NULL`) with no corresponding `runs/<id>/run.json`, so backfill cannot reconcile them. | DB query in this core_audit: `running_total=63`, `with_run_json=0`, `missing_run_json=63`; repair scope in `scripts/core_audit/repair_run_statuses.py:45` |
| DOC-3 | **High** | Reproducibility docs instruct running verifier/CI commands as release checks, but current verifier behavior can silently fail while returning success. | Commands documented at `governance/governance/REPRODUCIBILITY.md:111` and `governance/governance/REPRODUCIBILITY.md:112`; verifier failure mode at `scripts/verify_reproduction.sh:18` with observed `exit 0` |

### 1.2 Medium findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| RI-6 | Medium | Fallback behavior remains available by default in phase3_synthesis profile extraction; strict computed mode remains opt-in. | `src/phase3_synthesis/profile_extractor.py:102`; `governance/governance/REPRODUCIBILITY.md:90` |
| MC-3 | Medium | Aggregate coverage improved to `50.35%`, but meaningful blind spots remain (6 files at `0%` and 12 files below `20%`). | `core_status/ci_coverage.json` summary (generated during this run); examples include `src/phase1_foundation/core/logging.py`, `src/phase1_foundation/storage/filesystem.py`, `src/phase1_foundation/qc/anomalies.py` |
| MC-5 | Medium | Verification breadth is better than Audit 6 (phase2_analysis spot-check + sensitivity artifact check), but current gate reliability is undermined by MC-6. | `scripts/verify_reproduction.sh:81`, `scripts/verify_reproduction.sh:92`, `scripts/verify_reproduction.sh:125` |
| ST-1 | Medium | Status artifact ecosystem is still mixed: new artifacts follow updated policy, while historical `core_status/by_run` payloads still embed stale `status: running`. | Policy target: `governance/PROVENANCE.md:45`; stale examples: `core_status/by_run/verify_1.2fe7df1c-9f94-805c-17fa-5ebe7dde7dae.json:6` |
| INV-1R | Medium | Release baseline remains hard to core_audit cleanly due large outstanding local diff while repeated core_audit/fix cycles continue. | `git status --short` count (`83`) |

### 1.3 Resolved/Improved since Audit 6

| Prior ID | Current state | Evidence |
|---|---|---|
| RI-1 (hardcoded indistinguishability constants) | Resolved | No hardcoded constants found (`real_z/syn_z/real_rad/syn_rad` absent); computed stress tests used in `scripts/phase3_synthesis/run_indistinguishability_test.py:151` and `scripts/phase3_synthesis/run_indistinguishability_test.py:168` |
| RI-2 / RI-3 (legacy sensitivity provenance) | Resolved | Canonical command present: `core_status/core_audit/sensitivity_sweep.json:9`; no `unknown_legacy`/legacy-reconcile markers in sensitivity artifacts/docs |
| INV-2 / DOC-2 (missing `AUDIT_LOG.md`) | Resolved | `AUDIT_LOG.md` exists |
| MC-1 (new artifact provenance status field) | Improved for new outputs | Provenance writer omits mutable status: `src/phase1_foundation/core/provenance.py:28`; new sensitivity snapshot has no provenance status field |

---

## Phase 2: Method Correctness and Internal Consistency

### Key observations

- Run persistence logic now includes completion callbacks (`src/phase1_foundation/runs/context.py:58`, `src/phase1_foundation/storage/metadata.py:499`), and recent rows are being persisted with final success/end timestamps.
- Historical DB rows remain stale where no run manifest is available for repair (MC-2).
- Coverage improved materially versus prior run, including previously critical modules:
  - `src/phase2_analysis/admissibility/manager.py`: 88%
  - `src/phase1_foundation/core/queries.py`: 65%
  - `src/phase1_foundation/cli/main.py`: 25%

Residual correctness risk is now concentrated in gate reliability (MC-6) and fallback-heavy phase3_synthesis execution (RI-8/RI-6).

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-1 | Medium | Historical vs current output contracts are mixed in retained artifacts (`core_status/by_run` includes pre-policy payloads). | `governance/PROVENANCE.md:45`, `core_status/by_run/verify_1.2fe7df1c-9f94-805c-17fa-5ebe7dde7dae.json:6` |
| ST-2 | Resolved | Prior stale narration drift in indistinguishability script was corrected (`2 pages` path and dynamic count message). | `scripts/phase3_synthesis/run_indistinguishability_test.py:101`, `scripts/phase3_synthesis/run_indistinguishability_test.py:133` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | Improved | Sensitivity docs now accurately state canonical-but-bounded run and caveats. | `governance/SENSITIVITY_ANALYSIS.md:12`, `governance/SENSITIVITY_ANALYSIS.md:21` |
| DOC-3 | High | Verification command guidance is currently unreliable because verifier can fail and still return success (MC-6). | `governance/governance/REPRODUCIBILITY.md:111`, `governance/governance/REPRODUCIBILITY.md:112`, `scripts/verify_reproduction.sh:18` |

---

## Phase 5: External-Critique Simulation

### Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Where are assumptions stated? | Better documented than prior pass (`governance/PROVENANCE.md`, `governance/SENSITIVITY_ANALYSIS.md`), but fallback behavior in phase3_synthesis remains active by default. |
| Which parameters matter most? | Disconfirmation thresholds, sensitivity scales, evaluation weights, and fallback/strict-mode toggles remain primary. |
| What happens if they change? | Sensitivity framework captures this conceptually, but latest published run is bounded to one scenario and is `INCONCLUSIVE`. |
| How do we know this is not tuned? | Determinism checks for Test A pass; however, verifier gate reliability bug (MC-6) undermines trust in automated reproducibility claims. |
| What evidence is negative/null? | Current sensitivity artifact explicitly reports zero valid scenarios and all-model falsification caveat (`INCONCLUSIVE`). |

---

## Consolidated Findings Register (Prioritized)

1. **MC-6 (Critical):** Reproduction verifier/CI gate can report success even when verification aborts immediately.
2. **RI-8 (High):** Indistinguishability runner still traverses fallback/simulated profile paths and did not complete in bounded runtime test.
3. **RI-9 (High):** Sensitivity evidence is canonical but bounded/inconclusive, not sufficient as release-grade robustness evidence.
4. **MC-2 (High):** Large set of stale historical run records remains unresolved due missing manifests.
5. **DOC-3 (High):** Reproducibility guidance currently points to a verifier path with silent-failure behavior.
6. **MC-3 / RI-6 (Medium):** Coverage and strict-mode/fallback policy improved but still leave non-trivial risk areas.
7. **INV-1 / INV-3 (Medium/Low):** Baseline cleanliness and transient artifact hygiene remain incomplete.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (seventh pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Blocking items before release confidence

- Fix verifier gate integrity so `scripts/verify_reproduction.sh` fails loudly and non-zero when prerequisites are missing, and ensure `scripts/ci_check.sh` cannot produce false pass output.
- Produce full sensitivity sweep evidence from canonical runner parameters representative of release claims (not bounded one-scenario smoke run).
- Resolve fallback/simulated-profile dependence in `run_indistinguishability_test.py` release path, or explicitly classify it as non-evidentiary.
- Define handling for irreparable historical `runs` rows lacking manifests (archive_legacy/purge/policy annotation).
- Establish a clean, intentional release diff baseline prior to final publication signoff.
