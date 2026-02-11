# SK-C1.2 Execution Status

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_C1_2_EXECUTION_PLAN.md`  
Scope: Sensitivity artifact/report contract coherence and gate alignment (`SK-C1`, pass-2)

## Outcome

`C1_2_QUALIFIED`

- Contract integrity between sensitivity JSON/report and gate expectations is now machine-enforced.
- Release evidence is still non-compliant in current canonical artifact because current run is iterative/synthetic and policy-failing by design.

## Implemented Workstreams

### WS-C1.2-A Baseline/Root Cause

- Added root-cause register: `reports/core_skeptic/SK_C1_2_CONTRACT_REGISTER.md`.
- Classified mismatch as stale/legacy artifact-report state plus missing machine-checkable contract gate.

### WS-C1.2-B Schema Hardening

- Added contract policy: `configs/core_audit/sensitivity_artifact_contract.json`.
- Added checker: `scripts/core_audit/check_sensitivity_artifact_contract.py`.
- Added summary metadata fields in runner output:
  - `schema_version`
  - `policy_version`
  - `generated_utc`
  - `generated_by`

### WS-C1.2-C Readiness Logic Reconciliation

- Added explicit fail-reason list: `release_readiness_failures`.
- Enforced fail-closed readiness logic from explicit prerequisites.
- Kept warning-bearing caveat requirements strict and deduplicated caveat output.

### WS-C1.2-D Report/Artifact Synchronization

- Regenerated canonical artifacts from current runner:
  - `core_status/core_audit/sensitivity_sweep.json`
  - `reports/core_audit/SENSITIVITY_RESULTS.md`
- Current report now mirrors artifact values and caveat burden.

### WS-C1.2-E Gate/Test Contract Locking

- Wired checker into gate paths:
  - `scripts/ci_check.sh` (`--mode ci`)
  - `scripts/core_audit/pre_release_check.sh` (`--mode release`)
  - `scripts/verify_reproduction.sh` (`--mode release`)
- Added/updated tests:
  - `tests/core_audit/test_sensitivity_artifact_contract.py`
  - `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py`
  - `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py`
  - `tests/core_audit/test_pre_release_contract.py`
  - `tests/core_audit/test_verify_reproduction_contract.py`
  - `tests/core_audit/test_ci_check_contract.py`

### WS-C1.2-F Docs/Audit Traceability

- Updated docs:
  - `governance/SENSITIVITY_ANALYSIS.md`
  - `governance/governance/REPRODUCIBILITY.md`
- Updated plan status table in:
  - `planning/core_skeptic/SKEPTIC_C1_2_EXECUTION_PLAN.md`

## Verification Evidence

Commands run:

- `python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke --quick`
- `python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode ci`
- `python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release`
- `python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_guardrails.py tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py tests/core_audit/test_sensitivity_artifact_contract.py tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py tests/core_audit/test_ci_check_contract.py`

Observed results:

- Contract checker (`ci`): **PASS**.
- Contract checker (`release`): **FAIL (expected)** with explicit reasons:
  - non-release execution mode,
  - release readiness false,
  - dataset/warning policy failures,
  - quality/robustness gates not satisfied,
  - non-empty readiness failure list.
- Targeted SK-C1.2 test suites: **PASS** (`26 passed`).

## Current Canonical Sensitivity State

From `core_status/core_audit/sensitivity_sweep.json`:

- `execution_mode=iterative`
- `dataset_policy_pass=false`
- `warning_policy_pass=false`
- `release_evidence_ready=false`
- `release_readiness_failures` populated with explicit fail reasons
- `total_warning_count=270`
- non-empty `caveats`

This is contract-coherent and policy-qualified, not release-ready evidence.

## Residual Work (Outside SK-C1.2 Contract Integrity)

- Generate full release-mode sensitivity evidence on approved release dataset:
  - `python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real`
- Re-run release/repro gates after that evidence generation.

