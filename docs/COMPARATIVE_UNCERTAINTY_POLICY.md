# Comparative Uncertainty Policy (SK-M2)

## Purpose

This policy constrains comparative-distance claims so nearest-neighbor and
structural-isolation conclusions are uncertainty-qualified.

Machine-readable policy:

- `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`

Automated checker:

- `scripts/skeptic/check_comparative_uncertainty.py`

## Status Taxonomy

- `STABILITY_CONFIRMED`: distance uncertainty intervals and perturbation stability support a robust comparative claim.
- `DISTANCE_QUALIFIED`: directionality is supported, but rank/nearest-neighbor stability is moderate and caveats are required.
- `INCONCLUSIVE_UNCERTAINTY`: point estimates exist but uncertainty evidence is insufficient for robust comparative claims.
- `SUBJECTIVITY_RISK_BLOCKED`: policy violations or unqualified deterministic claims are present.

## Required Evidence

Comparative conclusions must cite:

1. Point estimates and 95% confidence intervals.
2. Nearest-neighbor stability under perturbation.
3. Jackknife stability under leave-one-dimension-out checks.
4. Rank-stability diagnostics (top-k set stability).
5. Nearest-neighbor probability margin and top-2 gap robustness.
6. Policy status and allowed-claim text from uncertainty artifact.

Primary artifact:

- `results/human/phase_7c_uncertainty.json`

Required artifact semantics include:

- `rank_stability`
- `rank_stability_components`
- `nearest_neighbor_probability_margin`
- `top2_gap` and `top2_gap_fragile`
- `metric_validity`

## Narrative Guardrails

1. Do not present nearest-neighbor outcomes as deterministic when stability is below policy threshold.
2. Public comparative prose must link to the uncertainty artifact.
3. Structural-isolation claims must be framed as uncertainty-qualified.
4. If status is `INCONCLUSIVE_UNCERTAINTY`, nearest-neighbor language must stay directional and caveated.

## Enforcement

- CI: `python3 scripts/skeptic/check_comparative_uncertainty.py --mode ci`
- Pre-release: `python3 scripts/skeptic/check_comparative_uncertainty.py --mode release`

## Verification

```bash
python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 scripts/skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/skeptic/check_comparative_uncertainty.py --mode release
```
