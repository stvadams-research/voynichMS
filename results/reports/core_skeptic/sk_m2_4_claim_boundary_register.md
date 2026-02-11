# SK-M2.4 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_4_EXECUTION_PLAN.md`

## Canonical Evidence Source

- `results/phase7_human/phase_7c_uncertainty.json`

Current lane:

- `m2_4_closure_lane=M2_4_BOUNDED`
- `status=INCONCLUSIVE_UNCERTAINTY`
- `reason_code=TOP2_IDENTITY_FLIP_DOMINANT`

## Allowed and Disallowed Claims by Lane

### `M2_4_ALIGNED`

Allowed:

- robust phase8_comparative confidence claims tied to confirmed thresholds.

Disallowed:

- uncertainty caveats omitted from public phase8_comparative summaries.

### `M2_4_QUALIFIED`

Allowed:

- directional phase8_comparative statements with explicit caveats and reopenability.

Disallowed:

- deterministic nearest-neighbor certainty language.

### `M2_4_BOUNDED` (Current Lane)

Allowed:

- "Comparative signal is directionally suggestive but non-conclusive."
- "Nearest-neighbor identity remains perturbation-sensitive."
- "Interpretation is uncertainty-qualified and gated by `results/phase7_human/phase_7c_uncertainty.json`."

Disallowed:

- "Nearest-neighbor is confirmed/settled."
- "Comparative uncertainty is resolved."
- "Further uncertainty phase2_analysis is unnecessary."

## Required Marker Semantics in Tracked Comparative Reports

Tracked surfaces must remain synchronized to SK-M2.4 entitlement:

- `reports/phase8_comparative/PROXIMITY_ANALYSIS.md`
- `reports/phase8_comparative/PHASE_B_SYNTHESIS.md`
- `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md`
- `reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md`
- `governance/COMPARATIVE_UNCERTAINTY_POLICY.md`

Required SK-M2.4 markers include:

- `INCONCLUSIVE_UNCERTAINTY`
- `M2_4_BOUNDED`
- `phase_7c_uncertainty.json`
- uncertainty-qualified phase8_comparative language

## Reopen Boundary Conditions

The current `M2_4_BOUNDED` boundary should be reopened only if:

1. lane eligibility changes (`M2_4_QUALIFIED` or `M2_4_ALIGNED` candidate),
2. fragility diagnostics materially shift under registered matrix reruns,
3. checker-policy or narrative parity breaks.
