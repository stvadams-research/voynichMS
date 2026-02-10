# SK-H3.3 Residual Register

Date: 2026-02-10  
Scope: Pass-3 SK-H3 residual closure from `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`  
Plan: `planning/skeptic/SKEPTIC_H3_3_EXECUTION_PLAN.md`

## Baseline Freeze

Canonical baseline artifacts:

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`

Baseline blocker state:

- `status=NON_COMPARABLE_BLOCKED`
- `reason_code=DATA_AVAILABILITY`
- `evidence_scope=available_subset`
- `full_data_closure_eligible=false`
- `missing_count=4`

## Approved Lost-Page Source Note

This register is the canonical source note for the SK-H3 approved lost-page policy binding.

Approved lost pages:

- `f91r`
- `f91v`
- `f92r`
- `f92v`

Policy binding:

- `configs/skeptic/sk_h3_data_availability_policy.json`
- `approved_lost_pages_policy_version=2026-02-10-h3.3`
- `approved_lost_pages_source_note_path=reports/skeptic/SK_H3_3_RESIDUAL_REGISTER.md`

## Residual Matrix

| Residual ID | Description | Control | Closure Test |
|---|---|---|---|
| H3.3-R1 | Data-availability block is policy-valid but must remain machine-checkable and drift-resistant. | Irrecoverability metadata + source-reference pinning | `python3 scripts/skeptic/check_control_data_availability.py --mode release` |
| H3.3-R2 | Available-subset lane needed explicit quality thresholds and transition reason codes. | `available_subset_diagnostics` + `AVAILABLE_SUBSET_QUALIFIED` / `AVAILABLE_SUBSET_UNDERPOWERED` | `python3 scripts/skeptic/check_control_comparability.py --mode release` |
| H3.3-R3 | Gate scripts could accept semantically divergent artifacts without explicit parity checks. | SK-H3 semantic parity checks in pre-release/verify/CI | `bash scripts/ci_check.sh` (SK-H3 stage), contract tests |
| H3.3-R4 | Human-readable claims could overstate subset evidence beyond artifact entitlement. | Allowed/disallowed claim catalog + doc updates | SK-H3 doc marker checks via policy checkers |
| H3.3-R5 | Gate-health dependency snapshots lacked explicit SK-H3 semantics. | Include SK-H3 dependency snapshot in gate-health artifact | `python3 scripts/audit/build_release_gate_health_status.py` |

## Allowed vs Disallowed Claims

Allowed claim classes:

- "Full-dataset comparability remains blocked by data availability."
- "Available-subset evidence is bounded and non-conclusive."
- "Available-subset evidence is underpowered" (only when `AVAILABLE_SUBSET_UNDERPOWERED`).

Disallowed claim classes:

- "Control comparability is conclusive for full dataset" while `evidence_scope=available_subset`.
- Any claim implying `full_data_closure_eligible=true` when missing pages remain.
- Any claim that omits active `DATA_AVAILABILITY` blocker status.

