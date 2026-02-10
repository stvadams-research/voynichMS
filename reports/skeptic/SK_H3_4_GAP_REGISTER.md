# SK-H3.4 Gap Register

Date: 2026-02-10  
Scope: Pass-4 SK-H3 residual closure from `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
Plan: `planning/skeptic/SKEPTIC_H3_4_EXECUTION_PLAN.md`

## Baseline Freeze

Canonical artifacts:

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`

Baseline tuple (frozen):

- `status=NON_COMPARABLE_BLOCKED`
- `reason_code=DATA_AVAILABILITY`
- `evidence_scope=available_subset`
- `full_data_closure_eligible=false`
- `available_subset_status=COMPARABLE_QUALIFIED`
- `available_subset_reason_code=AVAILABLE_SUBSET_QUALIFIED`
- `available_subset_confidence=QUALIFIED`
- `missing_count=4`
- `approved_lost_pages_policy_version=2026-02-10-h3.4`
- `approved_lost_pages_source_note_path=reports/skeptic/SK_H3_4_GAP_REGISTER.md`
- `full_data_feasibility=irrecoverable`
- `full_data_closure_terminal_reason=approved_lost_pages_not_in_source_corpus`
- `h3_4_closure_lane=H3_4_QUALIFIED`

Baseline provenance tuple:

- `run_id=1f171d1a-045a-3aee-b8a7-b5d83c617784`
- `timestamp=2026-02-10T19:38:43.113791+00:00`

## Approved Lost Pages

Approved irrecoverable pages in scope:

- `f91r`
- `f91v`
- `f92r`
- `f92v`

Classification contract:

- `irrecoverability.recoverable=false`
- `irrecoverability.approved_lost=true`
- `irrecoverability.unexpected_missing=false`
- `irrecoverability.classification=APPROVED_LOST_IRRECOVERABLE`

## Residual-to-Control Matrix

| Residual ID | Residual | Control | Verification Command |
|---|---|---|---|
| H3.4-R1 | Full-data closure still blocked, must be terminally classified. | Feasibility fields (`full_data_feasibility`, terminal reason, reopen conditions, lane) and policy checks. | `python3 scripts/skeptic/check_control_data_availability.py --mode release` |
| H3.4-R2 | Available-subset claims can still be overinterpreted as full-data closure. | Lane-bounded claim register and doc synchronization. | `rg -n "H3_4_|available_subset|full_data_closure_eligible" docs reports/skeptic` |
| H3.4-R3 | Cross-artifact drift can reintroduce semantic contradictions. | Required parity checks for scope, feasibility, lane, and irrecoverability. | `python3 scripts/skeptic/check_control_comparability.py --mode release` |
| H3.4-R4 | Stale artifact pairings can mimic a valid lane state. | Freshness checks (`run_id` match, timestamp skew). | `python3 scripts/skeptic/check_control_data_availability.py --mode ci` |
| H3.4-R5 | Gate diagnostics can hide SK-H3 semantics behind other blockers. | Gate and gate-health SK-H3 parity/freshness diagnostics. | `python3 scripts/audit/build_release_gate_health_status.py` |

## Deterministic Lane Predicates

### Lane A (`H3_4_ALIGNED`) predicate

Required:

- `missing_count==0`
- `evidence_scope=full_dataset`
- `full_data_closure_eligible=true`
- `full_data_feasibility=feasible`

Current evaluation: **not satisfied**.

### Lane B (`H3_4_QUALIFIED`) predicate

Required:

- approved lost pages are policy-registered and irrecoverable,
- `reason_code=DATA_AVAILABILITY`,
- `evidence_scope=available_subset`,
- `full_data_closure_eligible=false`,
- `full_data_feasibility=irrecoverable`,
- `h3_4_closure_lane=H3_4_QUALIFIED`.

Current evaluation: **satisfied**.

### Blocked/Inconclusive predicate

If Lane A and Lane B both fail, classification must be `H3_4_BLOCKED` or `H3_4_INCONCLUSIVE`.

Current evaluation: **not applicable** (Lane B satisfied).
