# SK-C1.5 Contract Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_C1_5_EXECUTION_PLAN.md`  
Source assessment: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`

## 1) Pass-5 Failure Tuple (Frozen)

SK-C1 pass-5 remained blocked on one deterministic class:

- Missing release artifact/report pair:
  - `status/audit/sensitivity_sweep_release.json`
  - `reports/audit/SENSITIVITY_RESULTS_RELEASE.md`
- With preflight already passing:
  - `status/audit/sensitivity_release_preflight.json` (`status=PREFLIGHT_OK`)

## 2) Producer -> Checker -> Gate -> Health Dependency Map

1. Producer:  
   `scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real`
2. Runtime state artifacts:
   - `status/audit/sensitivity_progress.json`
   - `status/audit/sensitivity_checkpoint.json`
   - `status/audit/sensitivity_release_run_status.json`
3. Release contract artifacts:
   - `status/audit/sensitivity_sweep_release.json`
   - `reports/audit/SENSITIVITY_RESULTS_RELEASE.md`
4. Contract checker:
   - `scripts/audit/check_sensitivity_artifact_contract.py --mode release`
5. Gate-health synthesizer:
   - `scripts/audit/build_release_gate_health_status.py`
   - `status/audit/release_gate_health_status.json`

## 3) SK-C1 Scope Boundary (Non-Blocking External Constraints)

SK-C1 evaluates release sensitivity contract integrity only.

- H3 approved irrecoverable folio/page loss is not an SK-C1 blocker when policy-pinned.
- SK-C1 gating depends only on sensitivity release producer/checker/runtime artifacts.

Reference: `planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md` (`Irrecoverable Source-Data Criteria`).

## 4) SK-C1.5 Reason-Code Register

Primary SK-C1.5 diagnostics now include:

- `preflight_ok_but_release_artifact_missing`
- `SENSITIVITY_PREFLIGHT_OK_ARTIFACT_MISSING`
- `SENSITIVITY_RELEASE_RUN_STATUS_MISSING`
- `SENSITIVITY_RELEASE_RUN_FAILED`
- `SENSITIVITY_RELEASE_RUN_STALE`

Runtime run-status contract states:

- `STARTED`
- `RUNNING`
- `COMPLETED`
- `FAILED`

## 5) Verification Snapshot (Execution Pass)

Executed:

- `python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only`
- `python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release`
- `python3 scripts/audit/build_release_gate_health_status.py`

Observed:

- Checker now emits explicit preflight-vs-artifact class when preflight is OK but release artifact is absent.
- Checker emits explicit release run-status diagnostics (`missing`, `FAILED`, or stale-heartbeat class).
- Gate-health now captures run-status dependency snapshot fields and sensitivity subreasons tied to SK-C1 runtime state.

## 6) Current Blocker Classification

Current SK-C1.5 lane: `C1_5_BLOCKED`.

Reason:

- canonical release artifact/report are still absent after interrupted release attempts, despite passing preflight and improved runtime observability.
