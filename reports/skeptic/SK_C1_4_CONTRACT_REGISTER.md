# SK-C1.4 Contract Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_C1_4_EXECUTION_PLAN.md`  
Source assessment: `reports/skepitic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## 1) Baseline Failure Tuple (Pass-4 Freeze)

SK-C1 pass-4 blocker was a single release-path contract failure class:

- Missing canonical release sensitivity artifact:
  - `status/audit/sensitivity_sweep_release.json`
- Resulting release gate failures:
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
  - `scripts/ci_check.sh` (`--mode release` sensitivity contract stage)

## 2) Producer -> Checker -> Gate -> Health Dependency Map

1. Producer:
   - `scripts/analysis/run_sensitivity_sweep.py --mode release`
2. Canonical artifacts:
   - `status/audit/sensitivity_sweep_release.json`
   - `reports/audit/SENSITIVITY_RESULTS_RELEASE.md`
3. Contract checker:
   - `scripts/audit/check_sensitivity_artifact_contract.py --mode release`
4. Gate scripts:
   - `scripts/audit/pre_release_check.sh`
   - `scripts/verify_reproduction.sh`
   - `scripts/ci_check.sh`
5. Gate-health synthesis:
   - `scripts/audit/build_release_gate_health_status.py`
   - `status/audit/release_gate_health_status.json`

## 3) Canonical Path and Policy Register

Release-path canonical sensitivity files:

- Release preflight status:
  - `status/audit/sensitivity_release_preflight.json`
- Release progress heartbeat:
  - `status/audit/sensitivity_progress.json`
- Release checkpoint/resume state:
  - `status/audit/sensitivity_checkpoint.json`
- Release contract artifact:
  - `status/audit/sensitivity_sweep_release.json`
- Release report:
  - `reports/audit/SENSITIVITY_RESULTS_RELEASE.md`

Non-release/iterative files remain non-authoritative for release claims:

- `status/audit/sensitivity_sweep.json`
- `reports/audit/SENSITIVITY_RESULTS.md`

## 4) SK-C1.4 Reason-Code Coherence Register

Primary gate-block reason codes:

- `SENSITIVITY_RELEASE_CONTRACT_BLOCKED`
- `SENSITIVITY_RELEASE_ARTIFACT_MISSING`
- `SENSITIVITY_RELEASE_REPORT_MISSING`
- `SENSITIVITY_RELEASE_PREFLIGHT_MISSING`
- `SENSITIVITY_RELEASE_PREFLIGHT_BLOCKED`
- `SENSITIVITY_PREFLIGHT_<REASON_CODE>` passthrough for preflight blockers

Operational dependency snapshot fields now include:

- `sensitivity_preflight_path`
- `sensitivity_preflight_status`
- `sensitivity_preflight_reason_codes`
- `sensitivity_preflight_generated_utc`

## 5) SK-C1.4 Verification Snapshot

Commands executed:

- `python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only`
- `python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release`
- `python3 scripts/audit/build_release_gate_health_status.py`

Observed post-change behavior:

- Release preflight succeeds with explicit artifact and reason-code payload.
- Release contract checker now reports:
  - missing artifact,
  - latest preflight status,
  - canonical preflight and release remediation commands.
- Gate health now records sensitivity subreason:
  - `SENSITIVITY_RELEASE_ARTIFACT_MISSING`
  and includes preflight dependency snapshot.

## 6) Anti-Regression Lock Points

Code and tests locking SK-C1.4 behavior:

- Runner:
  - `scripts/analysis/run_sensitivity_sweep.py`
- Release checker:
  - `scripts/audit/check_sensitivity_artifact_contract.py`
- Gate integrations:
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
  - `scripts/ci_check.sh`
- Gate-health reason coherence:
  - `scripts/audit/build_release_gate_health_status.py`
- Targeted tests:
  - `tests/analysis/test_sensitivity_sweep_end_to_end.py`
  - `tests/audit/test_sensitivity_artifact_contract.py`
  - `tests/audit/test_pre_release_contract.py`
  - `tests/audit/test_verify_reproduction_contract.py`
  - `tests/audit/test_ci_check_contract.py`
  - `tests/audit/test_release_gate_health_status_builder.py`
