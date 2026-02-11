# Fix Execution Status 9

**Date:** 2026-02-10  
**Source Plan:** `planning/core_audit/AUDIT_9_EXECUTION_PLAN.md`  
**Source Audit:** `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_9.md`

## 1) Scope and Outcome

This run executed the Audit 9 remediation plan with code, tests, and gate verification.

Overall outcome:

- `RI-14` / `ST-3` closed: strict preflight now normalizes split folio IDs and reports accurate missing pages.
- `RI-11` / `DOC-5` closed as policy+artifact contract: blocked strict preflight now emits machine-readable `reason_code=DATA_AVAILABILITY` with missing-page metadata.
- `RI-12` closed for release paths: verifier and pre-release checks now require strict preflight artifact semantics.
- `MC-3` improved materially: total coverage increased to `56.08%`; previously flagged modules rose above 20% except `feature_discovery`.
- `MC-2R` improved/verified: reconciliation utility remains stable and idempotent with tests.
- `INV-1` maintained/extended: release baseline checks now include strict preflight artifact policy validation.
- `RI-13` remains blocked: canonical full release sensitivity evidence is still not ready (`release_evidence_ready=false`).

## 2) Workstream Status

| Workstream | Status | Summary |
|---|---|---|
| WS-A Sensitivity Release Evidence Closure | BLOCKED | Canonical `voynich_real` release sweep attempts were non-responsive in this environment; active sensitivity artifact remains non-ready. |
| WS-B Indistinguishability Page-ID Normalization | COMPLETE | Added folio normalization (`f89r1` -> `f89r`) and updated preflight payloads. |
| WS-C RI-11 Policy Codification | COMPLETE | Added strict blocked reason-code semantics and documentation for data-availability constraints. |
| WS-D Strict-Mode Enforcement Hardening | COMPLETE | Verifier now always validates strict preflight outcomes; pre-release check enforces strict artifact policy. |
| WS-E Coverage Risk Reduction | IN PROGRESS | Added targeted tests and raised total coverage to `56.08%`; one sub-20 module remains (`feature_discovery`). |
| WS-F Orphaned-Run Provenance Resolution | COMPLETE | Added idempotence reconciliation test; runtime reconciliation confirms stable state. |
| WS-G Release Baseline Hygiene | COMPLETE | Baseline checks now include strict preflight artifact compliance (core_status/reason/missing metadata). |
| Final Verification + Audit 10 Prep | BLOCKED | Still blocked by WS-A unresolved sensitivity release-evidence state. |

## 3) Implemented Changes

### WS-B: Page-ID normalization and strict preflight payloads

Updated files:

- `scripts/phase3_synthesis/run_indistinguishability_test.py`
- `tests/phase3_synthesis/test_run_indistinguishability_runner.py`

Changes:

- Added split-folio normalization helper for preflight matching.
- Added normalized availability index and split-variant diagnostics in preflight payload.
- Added structured preflight exception with reason metadata.
- Added blocked-result `reason_code` and ensured strict preflight blocked artifacts include `preflight` details.

Result:

- Strict missing-page count reduced from `10/18` to `4/18` (remaining: `f91r`, `f91v`, `f92r`, `f92v`).

### WS-C / WS-D: Strict-mode release-path policy enforcement

Updated files:

- `scripts/verify_reproduction.sh`
- `scripts/core_audit/pre_release_check.sh`
- `tests/core_audit/test_verify_reproduction_contract.py`
- `tests/core_audit/test_pre_release_contract.py`
- `governance/governance/REPRODUCIBILITY.md`
- `governance/PROVENANCE.md`

Changes:

- `verify_reproduction.sh` now always validates strict preflight outcome and artifact semantics (`strict_computed`, `status`, `reason_code`, `missing_count`).
- `pre_release_check.sh` now requires policy-compliant strict preflight artifact (`PREFLIGHT_OK` or `BLOCKED` with `DATA_AVAILABILITY`).
- Documentation updated to codify the RI-11 criteria update as explicit data-availability scope policy.

### WS-E: Coverage risk reduction

New/updated tests:

- `tests/phase2_analysis/models/test_perturbation_calculator.py`
- `tests/phase2_analysis/anomaly/test_semantic_necessity_analyzer.py`
- `tests/phase3_synthesis/test_profile_extractor_simulated.py`
- `tests/phase3_synthesis/refinement/test_equivalence_retesting.py`
- `tests/phase3_synthesis/refinement/test_resynthesis.py`

Coverage effect:

- Total coverage increased from `52.28%` to `56.08%`.
- Previously flagged modules now above 20% except `src/phase3_synthesis/refinement/feature_discovery.py`.

### WS-F: Provenance reconciliation verification

Updated files:

- `tests/core_audit/test_repair_run_statuses.py`

Changes:

- Added idempotence test for `scripts/core_audit/repair_run_statuses.py`.
- Reconciliation command executed and confirmed stable state (`scanned=0 updated=0`).

### Plan status updates

Updated file:

- `planning/core_audit/AUDIT_9_EXECUTION_PLAN.md`

Changes:

- Workstream tracker updated from planning defaults to actual execution statuses and notes.

## 4) Verification Evidence

### Targeted remediation tests

```bash
python3 -m pytest -q \
  tests/phase3_synthesis/test_run_indistinguishability_runner.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_repair_run_statuses.py \
  tests/phase2_analysis/models/test_perturbation_calculator.py \
  tests/phase2_analysis/anomaly/test_semantic_necessity_analyzer.py \
  tests/phase3_synthesis/test_profile_extractor_simulated.py \
  tests/phase3_synthesis/refinement/test_equivalence_retesting.py \
  tests/phase3_synthesis/refinement/test_resynthesis.py
```

Result: pass.

### Strict preflight behavior (post-fix)

```bash
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
```

Results:

- non-strict preflight: `PREFLIGHT_OK` with warning, `missing_count=4`.
- strict preflight: fail-fast with blocked artifact and `reason_code=DATA_AVAILABILITY`.

### Release-path policy checks (validated under temporary release-ready sensitivity fixture)

```bash
bash scripts/verify_reproduction.sh
ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='Audit9 remediation validation' bash scripts/core_audit/pre_release_check.sh
```

Result:

- both checks pass policy logic when sensitivity artifact is release-ready.
- strict preflight blocked-data path is accepted only with approved reason code and metadata.

### Full suite and coverage

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
```

Result: pass, total coverage `56.08%`.

Sub-20 module count from `core_status/ci_coverage.json` after run:

- `1` remaining (`src/phase3_synthesis/refinement/feature_discovery.py: 12.85%`).

### Baseline gate behavior with real current artifact

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

Result: all fail closed on sensitivity non-readiness (`release_evidence_ready=false`), which is expected and policy-correct.

### Reconciliation utility

```bash
python3 scripts/core_audit/repair_run_statuses.py
```

Result: `scanned=0 updated=0 reconciled=0 orphaned=0 missing_manifests=0`.

## 5) Finding Closure Matrix

| Finding ID | Status | Closure Evidence |
|---|---|---|
| `RI-13` | BLOCKED | Sensitivity release artifact remains non-ready; gate behavior is correct but blocker persists. |
| `RI-14` | CLOSED | Split-folio normalization implemented; strict missing pages reduced to true unresolved set (`4/18`). |
| `RI-11` | CLOSED (policy) | Data-availability constraint codified and enforced through `reason_code=DATA_AVAILABILITY`. |
| `RI-12` | CLOSED | Release-path scripts now enforce strict preflight artifact semantics by default. |
| `MC-3` | IMPROVED | Total coverage `56.08%`; only one module remains below 20%. |
| `MC-2R` | IMPROVED | Reconciliation behavior verified and idempotence test added. |
| `INV-1` | IMPROVED | Baseline gate includes stricter policy checks and retains dirty-release rationale controls. |
| `DOC-5` | CLOSED | RI-11 criteria update language added to reproducibility/provenance docs. |
| `ST-3` | CLOSED | Naming/identity drift in preflight matching corrected via canonical normalization. |

## 6) Residual Blockers

1. **WS-A / `RI-13`**: canonical sensitivity release evidence is still unresolved.
   - Active artifact (`core_status/core_audit/sensitivity_sweep.json`) remains non-ready (`release_evidence_ready=false`).
   - Multiple full `voynich_real` sweep attempts were non-responsive in this environment and did not produce a completed artifact update.

2. **Coverage residual (`MC-3`)**:
   - `src/phase3_synthesis/refinement/feature_discovery.py` remains at `12.85%`.

## 7) Final Notes

- Plan tracker statuses were updated in `planning/core_audit/AUDIT_9_EXECUTION_PLAN.md`.
- This run executed remediation work; it did not perform a fresh assessment write-up for Audit 10.
- Next deliverable after resolving WS-A blocker: `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_10.md`.
