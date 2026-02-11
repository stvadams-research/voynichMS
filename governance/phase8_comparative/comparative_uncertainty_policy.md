# Comparative Uncertainty Policy (SK-M2 / SK-M2.5)

## Purpose

This policy constrains phase8_comparative-distance claims so nearest-neighbor and
structural-isolation conclusions are uncertainty-qualified, lane-entitled, and
reopenable under explicit criteria.

Machine-readable policy:

- `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json`

Automated checker:

- `scripts/core_skeptic/check_comparative_uncertainty.py`

## Status Taxonomy

- `STABILITY_CONFIRMED`: uncertainty diagnostics support robust phase8_comparative claims.
- `DISTANCE_QUALIFIED`: directional phase8_comparative claims are supported with caveats.
- `INCONCLUSIVE_UNCERTAINTY`: phase8_comparative claims remain bounded and non-conclusive.

## M2.5 Closure Lanes

- `M2_5_ALIGNED`: `STABILITY_CONFIRMED` with full confirmed-threshold support.
- `M2_5_QUALIFIED`: `DISTANCE_QUALIFIED` with bounded directional entitlement.
- `M2_5_BOUNDED`: `INCONCLUSIVE_UNCERTAINTY` with complete diagnostics and non-overreach boundaries.
- `M2_5_BLOCKED`: uncertainty contract fields or parity requirements are not satisfied.
- `M2_5_INCONCLUSIVE`: evidence is not sufficient to classify the lane deterministically.

## Required Evidence

Comparative conclusions must cite:

1. Point estimates and 95% confidence intervals.
2. Nearest-neighbor stability under perturbation.
3. Jackknife stability under leave-one-dimension-out checks.
4. Rank-stability diagnostics (top-k set stability).
5. Nearest-neighbor probability margin and top-2 gap robustness.
6. Lane, residual reason, and reopen triggers from the uncertainty artifact.

Primary artifact:

- `results/phase7_human/phase_7c_uncertainty.json`

Required artifact semantics include:

- `rank_stability`
- `rank_stability_components`
- `nearest_neighbor_probability_margin`
- `top2_gap` and `top2_gap_fragile`
- `fragility_diagnostics`
- `m2_4_closure_lane`, `m2_4_residual_reason`, `m2_4_reopen_triggers` (compatibility)
- `m2_5_closure_lane`, `m2_5_residual_reason`, `m2_5_reopen_triggers`
- `m2_5_data_availability_linkage`
- `metric_validity`

## Narrative Guardrails

1. Do not present nearest-neighbor outcomes as deterministic when stability is below policy floors.
2. Public phase8_comparative prose must link to the uncertainty artifact.
3. Structural-isolation claims must remain uncertainty-qualified.
4. If status is `INCONCLUSIVE_UNCERTAINTY`, nearest-neighbor language must stay directional and caveated.
5. If lane is `M2_5_BOUNDED`, language must explicitly state that confidence remains non-conclusive and reopenable.

## Missing-Folio Boundary

- Missing-folio objections map to SK-H3 by default.
- missing-folio objections are non-blocking for SK-M2 unless objective phase8_comparative-input validity failure is demonstrated.
- If blocked-lane language references missing folios, the uncertainty artifact must include explicit objective linkage evidence in `m2_5_data_availability_linkage`.

## Enforcement

- CI: `python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode ci`
- Pre-release: `python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release`

## Verification

```bash
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release
```
