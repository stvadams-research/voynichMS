# SK-M2.4 Diagnostic Matrix

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_4_EXECUTION_PLAN.md`  
Matrix summary source: `/tmp/m2_4_sweep/summary.json`

## Threshold-Gap Diagnostics (Canonical Publication Lane)

Canonical lane: seed `42`, iterations `2000` (standard profile)

### Confirmed-Class Gaps

| Metric | Observed | Threshold | Gap (Observed - Threshold) | Pass |
|---|---:|---:|---:|---|
| nearest-neighbor stability | 0.4565 | 0.7500 | -0.2935 | No |
| jackknife stability | 0.8333 | 0.7500 | +0.0833 | Yes |
| rank stability | 0.4565 | 0.6500 | -0.1935 | No |
| nearest-neighbor margin | 0.0670 | 0.1000 | -0.0330 | No |
| top-2 gap CI lower | 0.0263 | 0.0500 | -0.0237 | No |

### Qualified-Class Gaps

| Metric | Observed | Threshold | Gap (Observed - Threshold) | Pass |
|---|---:|---:|---:|---|
| nearest-neighbor stability | 0.4565 | 0.5000 | -0.0435 | No |
| jackknife stability | 0.8333 | 0.7000 | +0.1333 | Yes |
| rank stability | 0.4565 | 0.5500 | -0.0935 | No |
| nearest-neighbor margin | 0.0670 | 0.0300 | +0.0370 | Yes |

### Fragility-Dominance Diagnostics

| Diagnostic | Observed | Floor / Trigger | Gap | Interpretation |
|---|---:|---:|---:|---|
| top-2 set stability | 0.5580 | 0.6000 (identity-flip dominant trigger) | -0.0420 | Identity instability trigger activated. |
| max(top-2 rank entropy) | 2.0820 | 1.5000 (high entropy trigger) | +0.5820 | Rank entropy remains high. |

## Registered Matrix 2.0 Sweep

Profiles:

- `smoke`: 400 iterations
- `standard`: 2000 iterations
- `release-depth`: 8000 iterations

Seeds: `42`, `314`, `2718`

### Lane Outcomes (9/9 lanes)

- status set: `INCONCLUSIVE_UNCERTAINTY`
- reason set: `TOP2_IDENTITY_FLIP_DOMINANT`
- lane set: `M2_4_BOUNDED`
- nearest-neighbor: `Lullian Wheels` in all lanes

### Metric Envelope Across All Lanes

| Metric | Min | Max | Mean |
|---|---:|---:|---:|
| nearest-neighbor stability | 0.3775 | 0.4575 | 0.4452 |
| rank stability | 0.4275 | 0.4630 | 0.4538 |
| nearest-neighbor margin | 0.0000 | 0.0704 | 0.0518 |
| top-2 gap CI lower | 0.0080 | 0.0393 | 0.0228 |
| top-2 identity flip rate | 0.4050 | 0.4538 | 0.4399 |

## Diagnostic Conclusion

SK-M2 remains bounded by recurrent top-2 identity volatility, not by missing fields or single-seed noise.

This supports `M2_4_BOUNDED` as the deterministic closure lane for the current evidence state.
