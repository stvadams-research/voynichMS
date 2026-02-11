# SK-C2.2 Execution Status

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_C2_2_EXECUTION_PLAN.md`  
Scope: Runner-level provenance contract alignment for `SK-C2` (pass-2)

## Outcome

`C2_2_ALIGNED`

- Provenance runner contract is now policy-backed and machine-checked.
- Comparative uncertainty runner is explicitly modeled as delegated provenance and passes contract checks.
- CI/release/repro scripts now execute provenance runner contract checks directly.

## Implemented Workstreams

### WS-C2.2-A Baseline/Root Cause

- Added root-cause register:
  - `reports/core_skeptic/SK_C2_2_PROVENANCE_REGISTER.md`
- Classified SK-C2 as checker-model gap (string-only assumption) plus missing centralized policy/checker.

### WS-C2.2-B Runner Remediation

- Updated runner:
  - `scripts/phase8_comparative/run_proximity_uncertainty.py`
- Added explicit delegated provenance contract metadata in runner summary:
  - `provenance_contract_mode=delegated`
  - `provenance_delegated_to=src/phase8_comparative/mapping.py::run_analysis`
- Added envelope assertion (`provenance` + `results`) after run execution.

### WS-C2.2-C Policy/Checker Hardening

- Added policy:
  - `configs/core_audit/provenance_runner_contract.json`
- Added checker:
  - `scripts/core_audit/check_provenance_runner_contract.py`
- Replaced brittle provenance contract test logic with policy/checker-based enforcement:
  - `tests/core_audit/test_provenance_contract.py`
- Added checker-specific tests:
  - `tests/core_audit/test_provenance_runner_contract_checker.py`

### WS-C2.2-D Gate/Test Locking

- Integrated runner contract checker into:
  - `scripts/ci_check.sh` (`--mode ci`)
  - `scripts/core_audit/pre_release_check.sh` (`--mode release`)
  - `scripts/verify_reproduction.sh` (`--mode release`)
- Updated gate contract tests:
  - `tests/core_audit/test_ci_check_contract.py`
  - `tests/core_audit/test_pre_release_contract.py`
  - `tests/core_audit/test_verify_reproduction_contract.py`

### WS-C2.2-E Docs/Audit Traceability

- Updated:
  - `governance/PROVENANCE.md`
  - `governance/governance/REPRODUCIBILITY.md`
- Updated plan tracker:
  - `planning/core_skeptic/SKEPTIC_C2_2_EXECUTION_PLAN.md`

## Verification Evidence

Commands run:

- `python3 -m pytest -q tests/core_audit/test_provenance_contract.py`
- `python3 scripts/core_audit/check_provenance_runner_contract.py --mode ci`
- `python3 scripts/core_audit/check_provenance_runner_contract.py --mode release`
- `python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42`
- `python3 - <<'PY' ...` envelope check for `results/phase7_human/phase_7c_uncertainty.json`
- `python3 -m pytest -q tests/core_audit/test_provenance_contract.py tests/core_audit/test_provenance_runner_contract_checker.py tests/core_audit/test_ci_check_contract.py tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py`

Observed results:

- `tests/core_audit/test_provenance_contract.py`: **PASS**.
- `check_provenance_runner_contract.py --mode ci`: **PASS**.
- `check_provenance_runner_contract.py --mode release`: **PASS**.
- Comparative runner output includes delegated provenance contract metadata and writes provenance envelope.
- Targeted core_audit test suite: **PASS** (`15 passed`).

## Current SK-C2 State

- Prior CI blocker (`run_proximity_uncertainty.py` missing literal writer in runner) is remediated by policy-backed delegated provenance model.
- Runner-level provenance contract enforcement is now centralized and deterministic.
- SK-C2 pass-2 critical contract issue is closed in this execution scope.

## Residual

- This execution addresses SK-C2 contract consistency only; it does not alter SK-C1 sensitivity release evidence readiness or higher-level claim-scope items.

