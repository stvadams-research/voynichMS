# SK-C1.2 Sensitivity Contract Register

Date: 2026-02-10  
Source plan: `planning/core_skeptic/SKEPTIC_C1_2_EXECUTION_PLAN.md`

## A1. Required field inventory (gate consumers)

The following fields are required by release/reproduction policy consumers:

- `execution_mode`
- `release_evidence_ready`
- `scenario_count_expected`
- `scenario_count_executed`
- `robustness_decision`
- `quality_gate_passed`
- `robustness_conclusive`
- `dataset_policy_pass`
- `warning_policy_pass`
- `warning_density_per_scenario`
- `total_warning_count`
- `caveats`

Consumer scripts:

- `scripts/core_audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`

## A2. Producer path map

Primary producer:

- `scripts/phase2_analysis/run_sensitivity_sweep.py`
  - summary producer: `_decide_robustness(...)` + `main(...)` summary enrichment
  - report producer: `_write_markdown_report(...)`

Contract checker introduced in SK-C1.2:

- `scripts/core_audit/check_sensitivity_artifact_contract.py`
- policy: `configs/core_audit/sensitivity_artifact_contract.json`

## A3. Root-cause classification

| Symptom | Classification | Evidence |
|---|---|---|
| `core_status/core_audit/sensitivity_sweep.json` lacked `dataset_policy_pass`, `warning_policy_pass`, `warning_density_per_scenario` while still claiming release readiness. | Stale artifact generated before current policy contract fields were enforced. | Historical artifact snapshot and gate failures in core_skeptic pass-2 assessment. |
| `reports/core_audit/SENSITIVITY_RESULTS.md` stated caveat-none despite warning-heavy run. | Report drift from canonical contract semantics (legacy output persisted). | Report text mismatch against warning burden and policy expectations. |
| Release/repro gates failed while artifact summary conveyed strong PASS framing. | Producer-consumer contract drift (artifact/report vs gate policy). | `pre_release_check.sh` and `verify_reproduction.sh` sensitivity checks. |

Final root-cause call:

- Primary: stale/legacy artifact and report state.
- Secondary: missing single machine-checkable contract gate for artifact+report coherence.

