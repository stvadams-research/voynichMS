# SK-H3.2 Data-Availability Register

Date: 2026-02-10  
Scope: Residual closure for `SK-H3` from `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`

## Baseline Snapshot

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
  - `status=NON_COMPARABLE_BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - `leakage_detected=false`
- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`
  - `status=BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - strict preflight missing pages: `f91r`, `f91v`, `f92r`, `f92v`

## Root-Cause Matrix

| Cause ID | Type | Evidence | Impact | Remediation Track |
|---|---|---|---|---|
| H3.2-R1 | Source-data availability constraint | Strict preflight lists 4 missing pharmaceutical pages | Full-dataset comparability closure cannot be claimed | Add canonical data-availability policy and status artifact |
| H3.2-R2 | Governance gap (not method leakage) | Existing SK-H3 checks prove metric partition and `leakage_detected=false` | Skeptic can claim unresolved closure semantics despite anti-leakage controls | Enforce blocked-vs-subset semantics in checker and gates |
| H3.2-R3 | Artifact semantics drift risk | Prior status artifacts lacked required `evidence_scope` and closure eligibility fields | Reports/gates could diverge on what is blocked vs qualified | Require machine-checked scope fields and cross-artifact consistency |

## Canonical Missing-Page Register

Approved lost pages for this dataset scope:

- `f91r`
- `f91v`
- `f92r`
- `f92v`

Policy source:

- `configs/core_skeptic/sk_h3_data_availability_policy.json`

Canonical status artifact:

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`

## Current Closure Posture

- Full-data closure: blocked (`reason_code=DATA_AVAILABILITY`)
- Available-subset lane: allowed as bounded evidence only (`evidence_scope=available_subset`)
- Allowed claim form: non-conclusive for full dataset unless missing-page constraint is removed
