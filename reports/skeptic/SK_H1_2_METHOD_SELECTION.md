# SK-H1.2 Method Selection Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_2_EXECUTION_PLAN.md`  
Scope: WS-H1.2-B and WS-H1.2-D method-lane selection with anti-tuning constraints.

## Selection Rule (Pre-Registered)

Method selection was constrained to an adequacy-first policy:

1. Prefer lanes that satisfy adequacy thresholds without custom post-hoc exclusions.
2. Among adequacy-passing lanes, prefer lower anchor-density distortion and better token balance.
3. Do not select by desired claim direction.
4. Perform stability checks across seeds/line caps after selecting the lane.

Policy baseline: `configs/skeptic/sk_h1_multimodal_policy.json`

## Candidate Matrix

Coverage + coupling sweep summary: `/tmp/h1_2_sweep/summary.json`

| Candidate | Anchor Ratio | Token Balance Ratio | Adequacy Pass | Coupling Status | Notes |
|---|---|---|---|---|---|
| `geometric_v1_t001` | 0.4284 | 0.7494 | `True` | `CONCLUSIVE_NO_COUPLING` | Lowest threshold; balanced lane. |
| `geometric_v1_t005` | 0.4284 | 0.7494 | `True` | `CONCLUSIVE_NO_COUPLING` | Same empirical behavior as `t001`. |
| `geometric_v1_t010` | 0.4481 | 0.8120 | `True` | `INCONCLUSIVE_UNDERPOWERED` | Inferential ambiguity despite adequacy pass. |
| `geometric_v1_t015` | 0.7231 | 0.3830 | `True` | `INCONCLUSIVE_UNDERPOWERED` | High anchor skew; less balanced lane. |

## Selected Lane

Selected lane: `geometric_v1_t001`  
Selection rationale:

- Meets adequacy thresholds with matched large cohorts.
- Preserves better anchored/unanchored balance than higher-threshold lanes.
- Avoids high-skew geometry seen in `t015`.
- Provides conservative baseline for subsequent stability envelope testing.

Configuration updates applied:

- `configs/skeptic/sk_h1_multimodal_policy.json`
  - `anchor_method_name`: `geometric_v1_t001`
  - `sampling.max_lines_per_cohort`: `1600`

## Stability Result and Decision

Stability artifacts: `/tmp/h1_2_stability/*.json` and `results/mechanism/by_run/anchor_coupling_confirmatory.<run_id>.json`

- Conclusive no-coupling outcomes observed for:
  - `s42_l800`, `s42_l1200`, `s42_l1600`, `s2718_l1200`
- Inconclusive outcomes observed for:
  - `s314_l1200`, `s314_l1600`, `s2718_l1600`

Decision:

- Keep selected method lane as adequacy-optimal.
- Treat SK-H1.2 endpoint as qualified non-conclusive due seed-sensitive inferential ambiguity across stability envelope.

## Anti-Tuning Evidence

1. Candidate lane was selected before stability envelope interpretation.
2. Final narrative/report outcome follows mixed stability evidence, not a single favorable run.
3. Confirmatory artifact remains fail-closed (`INCONCLUSIVE_UNDERPOWERED`) under current selected publication run:
   - `results/mechanism/anchor_coupling_confirmatory.json`
