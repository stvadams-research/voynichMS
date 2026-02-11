# Fix Execution Status 8

**Date:** 2026-02-10  
**Source Plan:** `planning/core_audit/AUDIT_8_EXECUTION_PLAN.md`  
**Source Audit:** `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_8.md`

## 1) Scope and Outcome

This run executed the Audit 8 remediation plan and applied fixes across release-gate semantics, strict indistinguishability preflight behavior, coverage hardening for foundational modules, provenance artifact hygiene, release baseline controls, and documentation path alignment.

Overall status:

- `RI-10` closed: release gates no longer accept inconclusive sensitivity evidence.
- `RI-11`/`RI-12` partially closed: strict preflight and blocked-result reporting are implemented; strict run remains data-blocked.
- `MC-3` closed: prior 0%-coverage foundational modules now have direct tests and substantial coverage.
- `MC-2R`/`ST-1` improved: legacy verify artifact handling and checks are now explicit and scriptable.
- `INV-1` improved: dirty release override now requires explicit rationale.
- `DOC-4` closed via root-level reference file aliases.

## 2) Workstream Status

| Workstream | Status | Summary |
|---|---|---|
| WS-A Sensitivity Gate Semantics | COMPLETE | `release_evidence_ready` now requires full release sweep + conclusive robustness + quality-gate pass; verifier and pre-release gates enforce it. |
| WS-B Indistinguishability Strict Path | BLOCKED (data) | Added strict preflight mode and blocked-result artifacts; strict run still fails due missing `voynich_real` pharma pages. |
| WS-C Coverage Hardening | COMPLETE | Added targeted tests for six previously 0%-covered modules; total coverage increased to `52.28%`. |
| WS-D Provenance/Run-State Reconciliation | COMPLETE | Added legacy artifact checks to release gates and improved support_cleanup/report tooling behavior. |
| WS-E Release Baseline Hygiene | COMPLETE | `ALLOW_DIRTY_RELEASE=1` now requires `DIRTY_RELEASE_REASON`. |
| WS-F Documentation Contract Alignment | COMPLETE | Added root-level `governance/METHODS_REFERENCE.md`, `CONFIG_REFERENCE.md`, `governance/REPRODUCIBILITY.md` aliases to canonical `governance/` paths. |
| Final Verification + Audit 9 Prep | BLOCKED | Release gate correctly fails on current inconclusive sensitivity evidence; strict data prerequisites remain unsatisfied. |

## 3) Implemented Changes

### WS-A: Sensitivity gate semantics

Updated files:

- `scripts/phase2_analysis/run_sensitivity_sweep.py`
- `scripts/core_audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`
- `reports/core_audit/SENSITIVITY_RESULTS.md` (regenerated)
- `core_status/core_audit/sensitivity_sweep.json` (regenerated)
- `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py`
- `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py`
- `tests/core_audit/test_pre_release_contract.py`
- `tests/core_audit/test_verify_reproduction_contract.py`

Changes:

- Added explicit summary flags in sensitivity output:
  - `quality_gate_passed`
  - `robustness_conclusive`
- Redefined `release_evidence_ready` to require:
  - release mode,
  - full scenario execution,
  - quality-gate pass,
  - conclusive robustness (`PASS`/`FAIL`).
- Strengthened gate checks to fail on:
  - `robustness_decision == INCONCLUSIVE`,
  - missing/false `quality_gate_passed`,
  - missing/false `robustness_conclusive`.

Key references:

- `scripts/phase2_analysis/run_sensitivity_sweep.py:286`
- `scripts/phase2_analysis/run_sensitivity_sweep.py:383`
- `scripts/phase2_analysis/run_sensitivity_sweep.py:541`
- `scripts/core_audit/pre_release_check.sh:35`
- `scripts/verify_reproduction.sh:142`

### WS-B: Indistinguishability strict path

Updated files:

- `scripts/phase3_synthesis/run_indistinguishability_test.py`
- `tests/phase3_synthesis/test_run_indistinguishability_runner.py`
- `governance/governance/REPRODUCIBILITY.md`

Changes:

- Added structured preflight payload for real pharma-page prerequisites.
- Added strict blocked-result emission to `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` when strict preflight fails.
- Added CLI options:
  - `--preflight-only`
  - `--strict-computed`
- Preserved strict enforcement behavior (`REQUIRE_COMPUTED=1` still fail-fast).

Key references:

- `scripts/phase3_synthesis/run_indistinguishability_test.py:85`
- `scripts/phase3_synthesis/run_indistinguishability_test.py:126`
- `scripts/phase3_synthesis/run_indistinguishability_test.py:142`
- `scripts/phase3_synthesis/run_indistinguishability_test.py:347`

### WS-C: Coverage hardening

Updated files (new tests):

- `tests/phase1_foundation/core/test_logging_core.py`
- `tests/phase1_foundation/core/test_models.py`
- `tests/phase1_foundation/qc/test_anomalies.py`
- `tests/phase1_foundation/qc/test_checks.py`
- `tests/phase1_foundation/storage/test_filesystem.py`
- `tests/phase1_foundation/storage/test_interface.py`

Additional code fix discovered during test hardening:

- `src/phase1_foundation/storage/filesystem.py`

Changes:

- Added direct unit coverage for all six previously 0%-covered modules.
- Fixed atomic-write support_cleanup bug by assigning temp-file path before write call.

Key references:

- `src/phase1_foundation/storage/filesystem.py:64`

### WS-D: Provenance and artifact lifecycle

Updated files:

- `scripts/core_audit/cleanup_status_artifacts.sh`
- `scripts/core_audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`
- `governance/PROVENANCE.md`

Changes:

- Added `legacy-report` mode to support_cleanup script.
- Added accurate existence filtering in support_cleanup pattern handling (no false match counts for missing literal paths).
- Added release-gate checks that fail if `core_status/by_run/verify_*.json` include legacy `provenance.status` fields.

Key references:

- `scripts/core_audit/cleanup_status_artifacts.sh:10`
- `scripts/core_audit/cleanup_status_artifacts.sh:36`
- `scripts/core_audit/pre_release_check.sh:61`
- `scripts/verify_reproduction.sh:171`

### WS-E: Release baseline hygiene

Updated files:

- `scripts/core_audit/pre_release_check.sh`
- `governance/governance/REPRODUCIBILITY.md`

Changes:

- `ALLOW_DIRTY_RELEASE=1` now requires `DIRTY_RELEASE_REASON`.
- Pre-release output now includes explicit dirty-release rationale context.

Key references:

- `scripts/core_audit/pre_release_check.sh:95`
- `governance/governance/REPRODUCIBILITY.md:176`

### WS-F: Documentation contract alignment

Updated files:

- `governance/METHODS_REFERENCE.md` (new root alias)
- `CONFIG_REFERENCE.md` (new root alias)
- `governance/REPRODUCIBILITY.md` (new root alias)
- `governance/SENSITIVITY_ANALYSIS.md`
- `governance/governance/REPRODUCIBILITY.md`
- `AUDIT_LOG.md`

Changes:

- Added root-level reference aliases to satisfy playbook expected-output naming.
- Updated sensitivity docs to current quality-gated semantics and latest run snapshot.
- Logged Audit 8 remediation decisions and residual blockers in `AUDIT_LOG.md`.

## 4) Verification Evidence

### Command Results

1. Targeted remediation test batch:

```bash
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_guardrails.py tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py tests/phase3_synthesis/test_run_indistinguishability_runner.py tests/phase1_foundation/core/test_logging_core.py tests/phase1_foundation/core/test_models.py tests/phase1_foundation/qc/test_anomalies.py tests/phase1_foundation/qc/test_checks.py tests/phase1_foundation/storage/test_filesystem.py tests/phase1_foundation/storage/test_interface.py
```

Result: pass.

2. Canonical release-mode sweep rerun:

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --dataset-id voynich_synthetic_grammar --mode release
```

Result: pass, `17/17` scenarios; summary shows:

- `release_evidence_ready=False`
- `robustness_decision=INCONCLUSIVE`
- `quality_gate_passed=False`
- `robustness_conclusive=False`

3. Gate behavior validation:

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

Result: all fail closed (expected) on inconclusive sensitivity evidence.

4. Indistinguishability strict preflight:

```bash
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --strict-computed --preflight-only
```

Results:

- non-strict preflight: pass with warning and preflight artifact.
- strict preflight: fail-fast with explicit missing `10/18` pharma pages error.
- strict blocked result persisted in by-run artifact.

5. Full suite + coverage:

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
```

Result: pass; total coverage `52.28%`.

6. Coverage delta for prior 0%-coverage modules (`core_status/ci_coverage.json`):

- `src/phase1_foundation/core/logging.py`: `94.12%`
- `src/phase1_foundation/core/models.py`: `100.00%`
- `src/phase1_foundation/qc/anomalies.py`: `100.00%`
- `src/phase1_foundation/qc/checks.py`: `100.00%`
- `src/phase1_foundation/storage/filesystem.py`: `91.49%`
- `src/phase1_foundation/storage/interface.py`: `80.00%`

7. Run-status reconciliation utility:

```bash
python3 scripts/core_audit/repair_run_statuses.py
```

Result: `scanned=0 updated=0 reconciled=0 orphaned=0 missing_manifests=0` (no open running rows remained to reconcile).

8. Current DB run-state snapshot (`data/voynich.db`):

- `success: 95`
- `orphaned: 63`
- `running_end_null: 0`
- `orphaned_missing_run_json: 63`

9. Artifact support_cleanup verification:

```bash
bash scripts/core_audit/cleanup_status_artifacts.sh legacy-report
```

Result: `legacy_provenance_status_count=0`.

## 5) Finding Closure Matrix

| Finding ID | Status | Closure Evidence |
|---|---|---|
| `RI-10` | CLOSED | Gate semantics now require conclusive + quality-gated sensitivity evidence; inconclusive artifacts fail release checks. |
| `RI-11` | BLOCKED (data) | Strict preflight enforcement and blocked-result artifact implemented; strict run still fails due missing real pharma pages. |
| `RI-12` | PARTIAL | Strict mode now first-class (`--strict-computed`, `--preflight-only`) and integrated with verifier strict path; non-strict mode remains intentionally available outside release path. |
| `MC-3` | CLOSED | Six prior 0%-coverage modules now tested and covered (`80-100%`), aggregate coverage increased to `52.28%`. |
| `MC-2R` | IMPROVED | Historical orphaned state remains explicit (`orphaned=63`) with no open running-null rows. |
| `ST-1` | CLOSED (operational) | Legacy verify artifact status fields are now detectable/cleanable and release-gated. |
| `INV-1` | IMPROVED | Dirty release override requires explicit rationale (`DIRTY_RELEASE_REASON`). |
| `DOC-4` | CLOSED | Root-level doc aliases added to align with playbook expected output names. |

## 6) Residual Blockers

1. Strict computed indistinguishability (`RI-11`) remains blocked by dataset completeness:
- Missing `10/18` pharmaceutical pages in `voynich_real` (e.g., `f89r`..`f92v` shown in preflight diagnostics).

2. Release baseline remains blocked by current sensitivity evidence quality state:
- Full sweep executes, but robustness remains `INCONCLUSIVE` and release evidence is correctly flagged as not ready.

## 7) Final Notes

- Plan tracker statuses were updated in `planning/core_audit/AUDIT_8_EXECUTION_PLAN.md`.
- Audit execution notes were appended to `AUDIT_LOG.md` under Audit 8.
- This execution run intentionally focused on remediation; the next assessment pass should be produced separately as `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_9.md`.
