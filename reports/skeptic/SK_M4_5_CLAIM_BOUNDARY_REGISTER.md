# SK-M4.5 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M4_5_EXECUTION_PLAN.md`

## Canonical Evidence Source

- `status/audit/provenance_health_status.json`
- `status/audit/provenance_register_sync_status.json`
- `reports/skeptic/SK_M4_PROVENANCE_REGISTER.md`

Current lane:

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `m4_5_historical_lane=M4_5_BOUNDED`

## Allowed and Disallowed Claims by M4.5 Lane

### `M4_5_ALIGNED`

Allowed:

- historical provenance confidence is aligned under current thresholds and coupling checks.

Disallowed:

- omitting provenance source artifact references in closure-facing claims.

### `M4_5_QUALIFIED`

Allowed:

- qualified provenance confidence with explicit recoverable residual caveats.

Disallowed:

- deterministic certainty language that omits recoverable residual scope.

### `M4_5_BOUNDED` (Current Lane)

Allowed:

- "Historical provenance confidence remains bounded by irrecoverable source constraints."
- "Run-status parity and synchronization are in-sync, but historical certainty is qualified."
- "Claims are constrained to `status/audit/provenance_health_status.json` and reopen criteria."

Disallowed:

- "Historical provenance is fully aligned / fully complete."
- "No residual provenance uncertainty remains."
- "Missing folio objections are resolved as SK-M4 blockers" without objective linkage evidence.

### `M4_5_BLOCKED`

Allowed:

- process-blocked statements tied to explicit contract/parity/freshness failures.

Disallowed:

- treating blocked process state as substantive historical-confidence resolution.

### `M4_5_INCONCLUSIVE`

Allowed:

- provisional status statements pending complete evidence.

Disallowed:

- lane-entitled claims without deterministic lane assignment.

## Missing-Folio Non-Blocker Rule (SK-M4)

- Missing folio objections route to SK-H3 by default.
- SK-M4 folio blocking is only valid when `m4_5_data_availability_linkage.objective_provenance_contract_incompleteness=true`.
- Approved irrecoverable-loss classification (`approved_irrecoverable_loss_classification=true`) is bounded context, not standalone SK-M4 block.

## Required SK-M4 Surfaces

- `README.md`
- `docs/PROVENANCE.md`
- `docs/HISTORICAL_PROVENANCE_POLICY.md`
- `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
- `results/reports/FINAL_PHASE_3_3_REPORT.md`
- `reports/skeptic/SK_M4_PROVENANCE_REGISTER.md`
