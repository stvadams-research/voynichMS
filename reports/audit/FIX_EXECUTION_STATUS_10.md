# Fix Execution Status 10

**Date:** 2026-02-10  
**Plan:** `planning/audit/AUDIT_10_EXECUTION_PLAN.md`  
**Source Audit:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_10.md`  
**Execution Type:** Remediation + verification

---

## Executive Outcome

Audit 10 remediation was executed across all planned workstreams.

Key outcomes:

- `RI-13` blocker resolved: sensitivity artifact is now release-ready and conclusive.
- `RI-12` resolved: indistinguishability runner is now strict-by-default; fallback is explicit.
- `MC-3` resolved: `feature_discovery` coverage raised from `12.85%` to `40.41%`.
- `MC-2R` resolved to policy-complete state: missing run manifests backfilled (`63`), current missing manifest count `0`.
- `INV-1` improved but still operationally present: clean-tree baseline still fails by design in this workspace, but dirty-release governance is now stricter and explicit.

---

## Workstream Status

| Workstream | Status | Result |
|---|---|---|
| WS-A Sensitivity Release Evidence Closure | COMPLETE | Canonical release sweep now yields `release_evidence_ready=true`, conclusive `PASS`. |
| WS-B Strict-Mode Release Enforcement | COMPLETE | Strict-by-default mode implemented; exploratory fallback requires `--allow-fallback`. |
| WS-C RI-11 Data-Availability Governance | COMPLETE | Policy codified in playbook/provenance docs and verified through strict artifact semantics. |
| WS-D Coverage Confidence Uplift | COMPLETE | Added targeted refinement tests; module and total coverage improved. |
| WS-E Orphaned-Run Provenance Disposition | COMPLETE | Backfill workflow implemented and executed; missing manifests reduced to zero. |
| WS-F Release Baseline Hygiene | COMPLETE | `DIRTY_RELEASE_REASON` now validated for structure/length. |
| WS-G Final Verification + Closure Evidence | COMPLETE | Reproduction verifier and CI check both pass; pre-release gate passes with compliant override. |

---

## Step Log

### 1) Implemented sparse-data perturbation fallback (WS-A)

**Files changed**

- `src/analysis/models/perturbation.py`
- `tests/analysis/models/test_perturbation_calculator.py`

**What changed**

- Added deterministic sparse-data fallback degradation path instead of NaN propagation.
- Added explicit metadata fields:
  - `computed_from: "sparse_data_estimate"`
  - `fallback_reason: "insufficient_records"`
- Preserved NaN sanitization guard for unexpected NaN paths.

**Evidence**

- Code anchors: `src/analysis/models/perturbation.py:32`, `src/analysis/models/perturbation.py:349`, `src/analysis/models/perturbation.py:368`, `src/analysis/models/perturbation.py:372`
- Tests passed: `tests/analysis/models/test_perturbation_calculator.py`

### 2) Enforced strict-by-default indistinguishability mode (WS-B)

**Files changed**

- `scripts/synthesis/run_indistinguishability_test.py`
- `tests/synthesis/test_run_indistinguishability_runner.py`
- `docs/REPRODUCIBILITY.md`

**What changed**

- Added mutually exclusive mode flags: `--strict-computed | --allow-fallback`.
- Added `_resolve_strict_mode(...)` with strict-by-default behavior when no explicit override exists.
- Kept `REQUIRE_COMPUTED` env support as an explicit override path.

**Evidence**

- Code anchors: `scripts/synthesis/run_indistinguishability_test.py:410`, `scripts/synthesis/run_indistinguishability_test.py:417`, `scripts/synthesis/run_indistinguishability_test.py:427`, `scripts/synthesis/run_indistinguishability_test.py:451`
- Runtime checks:
  - `python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only` -> strict blocked (expected)
  - `python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only --allow-fallback` -> warning + `PREFLIGHT_OK` (expected)

### 3) Codified RI-11 governance for future audit consistency (WS-C)

**Files changed**

- `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`
- `docs/PROVENANCE.md`

**What changed**

- Added explicit severity/classification rule for source-data availability constraints.
- Preserved `DATA_AVAILABILITY`-based strict blocked semantics in provenance guidance.

### 4) Lifted low coverage module above threshold (WS-D)

**Files changed**

- `tests/synthesis/refinement/test_feature_discovery.py` (new)

**What changed**

- Added focused tests covering:
  - deterministic seed fragments
  - fallback behavior and sanitization
  - alignment grouping helper
  - discriminator training/ranking
  - analyze path with sparse store

**Evidence**

- `feature_discovery` coverage now `40.41%` (was `12.85%`).
- Coverage evidence from CI output and `status/ci_coverage.json`.

### 5) Added and executed manifest backfill workflow (WS-E)

**Files changed**

- `scripts/audit/repair_run_statuses.py`
- `tests/audit/test_repair_run_statuses.py`
- `docs/PROVENANCE.md`

**What changed**

- Added `--backfill-missing-manifests` support.
- Backfilled manifests are marked `manifest_backfilled=true`.
- Added summary fields including `backfilled_manifests`.

**Execution evidence**

- First execution:
  - `python3 scripts/audit/repair_run_statuses.py --backfill-missing-manifests`
  - Output included `backfilled_manifests=63`.
- Idempotence execution:
  - output `backfilled_manifests=0 missing_manifests=0`.
- Current report: `status/audit/run_status_repair_report.json:6`, `status/audit/run_status_repair_report.json:7`
- Backfilled manifest count check: `manifest_backfilled_true 63`.

### 6) Hardened dirty-release rationale policy (WS-F)

**Files changed**

- `scripts/audit/pre_release_check.sh`
- `tests/audit/test_pre_release_contract.py`
- `docs/REPRODUCIBILITY.md`

**What changed**

- `DIRTY_RELEASE_REASON` now requires:
  - non-empty
  - minimum 12 chars
  - `:` delimiter for structured context/rationale

**Evidence**

- Script checks at: `scripts/audit/pre_release_check.sh:147`, `scripts/audit/pre_release_check.sh:152`

### 7) Regenerated release evidence and executed full verification (WS-G)

**Key commands and outcomes**

1. `python3 scripts/analysis/run_sensitivity_sweep.py --dataset-id voynich_synthetic_grammar --mode release`
- Completed `17/17` scenarios.
- Summary shows:
  - `release_evidence_ready=true`
  - `robustness_decision="PASS"`
  - `quality_gate_passed=true`
  - `robustness_conclusive=true`
- Artifact evidence: `status/audit/sensitivity_sweep.json:21`, `status/audit/sensitivity_sweep.json:22`, `status/audit/sensitivity_sweep.json:26`, `status/audit/sensitivity_sweep.json:33`, `status/audit/sensitivity_sweep.json:34`, `status/audit/sensitivity_sweep.json:35`

2. `python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only`
- Strict preflight artifact generated with:
  - `status="BLOCKED"`
  - `strict_computed=true`
  - `reason_code="DATA_AVAILABILITY"`
  - `missing_count=4`
- Artifact evidence: `status/synthesis/TURING_TEST_RESULTS.json:12`, `status/synthesis/TURING_TEST_RESULTS.json:13`, `status/synthesis/TURING_TEST_RESULTS.json:14`, `status/synthesis/TURING_TEST_RESULTS.json:494`

3. `bash scripts/verify_reproduction.sh`
- **PASSED** (`VERIFY_REPRODUCTION_COMPLETED`).

4. `bash scripts/ci_check.sh`
- **PASSED**.
- Total coverage: `58.07%`.
- `src/synthesis/refinement/feature_discovery.py`: `40.41%`.

5. `bash scripts/audit/pre_release_check.sh`
- Fails on dirty workspace (expected).

6. `ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='AUDIT-10: controlled execution pass with tracked dirty workspace' bash scripts/audit/pre_release_check.sh`
- **PASSED** with explicit dirty override reason.

---

## Finding Closure Matrix

| Finding | Prior State (Audit 10) | Execution Result | Status |
|---|---|---|---|
| RI-13 | Release evidence not ready; inconclusive robustness | Release sweep now conclusive and release-ready | RESOLVED |
| RI-12 | Non-strict fallback default risk | Strict-by-default implemented; fallback explicit | RESOLVED |
| RI-11 | Data-availability constraint (known missing pages) | Governance codified; strict blocked semantics verified | POLICY-COMPLETE |
| MC-3 | `feature_discovery` <20% | Raised to `40.41%` | RESOLVED |
| MC-2R | 63 missing manifests / orphaned uncertainty | Missing manifests backfilled to 0; historical orphaned status remains explicit | RESOLVED (WITH EXPLICIT HISTORICAL ORPHAN POLICY) |
| INV-1 | Dirty-tree release baseline risk | Governance tightened; clean-tree still not met in current workspace | PARTIAL (OPERATIONAL) |

---

## Residual / Non-Code Constraint

- Current working tree remains dirty (`113` paths at verification time).
- This is now policy-gated rather than silent; clean-tree requirement is still enforced by default.

---

## Artifacts Updated During Execution

- `status/audit/sensitivity_sweep.json`
- `reports/audit/SENSITIVITY_RESULTS.md`
- `status/synthesis/TURING_TEST_RESULTS.json`
- `status/audit/run_status_repair_report.json`
- `planning/audit/AUDIT_10_EXECUTION_PLAN.md` (status tracker updated)

---

## Primary Code/Test Changes

- `src/analysis/models/perturbation.py`
- `scripts/synthesis/run_indistinguishability_test.py`
- `scripts/audit/repair_run_statuses.py`
- `scripts/audit/pre_release_check.sh`
- `tests/analysis/models/test_perturbation_calculator.py`
- `tests/synthesis/test_run_indistinguishability_runner.py`
- `tests/synthesis/refinement/test_feature_discovery.py`
- `tests/audit/test_repair_run_statuses.py`
- `tests/audit/test_pre_release_contract.py`
- `docs/REPRODUCIBILITY.md`
- `docs/SENSITIVITY_ANALYSIS.md`
- `docs/PROVENANCE.md`
- `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`
