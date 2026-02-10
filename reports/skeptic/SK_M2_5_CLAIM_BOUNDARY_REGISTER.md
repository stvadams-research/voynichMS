# SK-M2.5 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M2_5_EXECUTION_PLAN.md`

## Canonical Evidence Source

- `results/human/phase_7c_uncertainty.json`

Current lane:

- `status=INCONCLUSIVE_UNCERTAINTY`
- `reason_code=TOP2_IDENTITY_FLIP_DOMINANT`
- `m2_5_closure_lane=M2_5_BOUNDED`

## Allowed and Disallowed Claims by M2.5 Lane

### `M2_5_ALIGNED`

Allowed:

- robust comparative confidence claims tied to confirmed-threshold support.

Disallowed:

- omitting uncertainty provenance references from comparative conclusions.

### `M2_5_QUALIFIED`

Allowed:

- directional comparative claims with explicit uncertainty caveats and reopenability.

Disallowed:

- deterministic nearest-neighbor certainty language.

### `M2_5_BOUNDED` (Current Lane)

Allowed:

- "Comparative signal is directionally suggestive but non-conclusive."
- "Nearest-neighbor identity remains perturbation-sensitive."
- "Interpretation is uncertainty-qualified and gated by `results/human/phase_7c_uncertainty.json`."

Disallowed:

- "Nearest-neighbor is confirmed/settled."
- "Comparative uncertainty is resolved."
- "Further uncertainty analysis is unnecessary."

### `M2_5_BLOCKED`

Allowed:

- explicit process-blocked statements (contract/parity incomplete).

Disallowed:

- treating blocked process state as substantive comparative conclusion.

### `M2_5_INCONCLUSIVE`

Allowed:

- provisional status statements pending evidence completion.

Disallowed:

- lane-entitled claims without deterministic lane assignment.

## Missing-Folio Non-Blocker Rule (SK-M2)

- Missing-folio objections route to SK-H3 by default.
- They are non-blocking for SK-M2 unless objective comparative-input validity failure is demonstrated.
- `M2_5_BLOCKED` based on missing folios requires objective linkage evidence in `m2_5_data_availability_linkage`.

## Required Comparative Surfaces

- `reports/comparative/PROXIMITY_ANALYSIS.md`
- `reports/comparative/PHASE_B_SYNTHESIS.md`
- `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`
- `reports/comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md`
- `docs/COMPARATIVE_UNCERTAINTY_POLICY.md`
