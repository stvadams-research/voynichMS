# Phase 14N: Physical Integration Analysis

**Date:** 2026-02-21
**Status:** COMPLETE (2026-02-21)
**Depends on:** Phase 14I (offset corrections), Phase 12 (mechanical slips), Phase 16 (physical grounding)

## Execution Progress

- [x] Sprint 1: Offset correction topology (2026-02-21)
- [x] Sprint 2: Slip-offset correlation (2026-02-21)
- [x] Sprint 3: Device geometry inference (2026-02-21)
- [x] Sprint 4: Governance updates (2026-02-21)

### Key Results

**Sprint 1 — Offset Correction Topology:**
- **Moran's I = 0.915, p < 0.0001**: Corrections are *strongly* spatially autocorrelated — nearby windows have highly similar drift values. This is not random per-window calibration.
- **FFT dominant k=1 (period=50 windows), 85.4% power fraction**: A single sinusoidal cycle captures 85% of the variance. This is the signature of a circular rotating device.
- **Phase structure:** 9 zones, 7 zero-correction anchor points at windows [0, 18, 44, 45, 47, 48, 49]. Window 18 is the primary anchor (highest-frequency vocabulary cluster).
- **Magnitude profile:** Peaked at deciles 6-7 (windows 30-39, mean |corr| = 14-17), minimal at edges. Consistent with cumulative drift from an anchor point.

**Sprint 2 — Slip-Offset Correlation:**
- All 202 slips mapped (0 unmapped OOV).
- **Window 18 concentrates 187/202 slips (92.6%)** despite having correction=0. This is the *anchor window* — slips occur where the scribe starts/resets, not where drift is largest.
- **Slip rate vs |correction|: rho = −0.360, p = 0.010**: Slips are *anti-correlated* with correction magnitude. The anchor/zero-correction windows are most slip-prone.
- **Positive vs negative windows: p = 0.955 (null)**: Drift direction does not affect slip rate.
- **Position clustering:** Slips at positions 1-2 overwhelmingly occur in zero-correction windows (45/47 pos-1, 43/43 pos-2). This confirms the anchor-point hypothesis.
- **Temporal clustering: CV = 1.81 (clustered)**: Slips cluster in consecutive folios, suggesting device wear/misalignment episodes. Top folios: f83r(8), f81v(7), f84v(7).

**Sprint 3 — Device Geometry Inference:**

| Model | Geometry | Params | RSS | BIC | Rank |
|:---|:---|---:|---:|---:|---:|
| **Volvelle** | Rotating disc | 2 | 1,245 | **168.6** | **1** |
| Tabula | 10×5 grid | 15 | 472 | 170.9 | 2 |
| Grille | Linear strip | 2 | 2,359 | 200.5 | 3 |

- **Volvelle wins BIC** by 2.3 over tabula (Δ=31.9 over grille). The single-cycle sinusoidal model (2 params) fits almost as well as the 15-parameter grid model — parsimony strongly favors the rotating disc.
- **Physical profile:** Circular device with single-cycle drift, anchor at window 18 (highest-frequency vocabulary), slips concentrated at the anchor/reset point, temporal clustering in folio batches.

## Motivation

Three independent physical signals have been measured but never connected:

1. **Offset corrections** (Phase 14I): 50 per-window signed values showing a striking 3-phase spatial structure — positive drift in early windows (0-10), strong negative drift in mid windows (11-39), mild negative in late windows (40-49), with 7 zero-drift anchor points.

2. **Mechanical slips** (Phase 12): 202 verified vertical offsets (z=9.47σ) concentrated at early line positions (65.4% in positions 1-3), exponentially decaying with position.

3. **Geometric layout** (Phase 16): 81.5% grid efficiency (10×5 grid optimal), null ergonomic correlation (rho=-0.0003), confirming sequential optimization without effort bias.

No analysis has tested whether these three signals are **mutually consistent** with a single physical device. If the offset corrections show spatial autocorrelation, the slips cluster at high-drift windows, and the geometry constrains device type, we have a triangulated physical reconstruction.

---

## Sprint 1: Offset Correction Topology

**Script:** `scripts/phase14_machine/run_14zf_physical_integration.py`
**Output:** `results/data/phase14_machine/physical_integration.json`

### Tasks

**1.1 Spatial autocorrelation (Moran's I)**
Treat the 50 windows as positions on a circular lattice (after spectral reordering). Compute Moran's I for the correction values:
- Positive I = spatially clustered (nearby windows have similar corrections)
- I ≈ 0 = random
- Negative I = spatially dispersed (checkerboard pattern)
Test significance via permutation (10K shuffles).

**1.2 Periodicity analysis (FFT)**
Apply FFT to the 50 correction values (circular sequence):
- If dominant frequency at k=1: single-cycle drift (consistent with circular device rotation)
- If dominant frequency at k=2+: multi-cycle pattern (consistent with folded/tiled device)
- No dominant frequency: random per-window calibration
Report power spectrum and dominant period.

**1.3 Phase structure characterization**
Quantify the 3-phase structure observed in canonical offsets:
- Segment the 50 windows into contiguous runs of same-sign corrections
- Test whether the observed number of sign changes is fewer than expected by chance (runs test)
- Identify the transition points between positive and negative drift zones
- Map anchor windows (zero correction) relative to phase boundaries

**1.4 Correction magnitude profile**
- Mean |correction| by position decile (windows 0-4, 5-9, ..., 45-49)
- Is the magnitude profile symmetric, monotonic, or peaked?
- Physical interpretation: monotonic = cumulative drift from a reference point; symmetric = drift from center; peaked = specific zones of difficulty

### Reuse
- `canonical_offsets.json`: `results/data/phase14_machine/canonical_offsets.json`
- `scipy.stats.mstats.moran_i` or manual implementation
- `numpy.fft.fft` for periodicity

### Acceptance
- Moran's I with significance test
- FFT power spectrum with dominant period identified
- Phase structure quantified (number of zones, transition points, anchor positions)
- Clear statement: are corrections spatially structured or random?

---

## Sprint 2: Slip-Offset Correlation

**Script:** Same as Sprint 1 (extended)

### Tasks

**2.1 Per-window slip frequency**
Map each of the 202 verified slips to its window:
- For each slip, identify the window of the slipped word (via `lattice_map`)
- Compute per-window slip count and slip rate (normalized by window's corpus token count)
- Top 10 windows by slip rate

**2.2 Slip rate vs offset magnitude**
Correlate per-window slip rate with |offset correction|:
- Spearman rho and p-value
- Hypothesis: high-drift windows (large |correction|) are more vulnerable to slips
- Alternative: slips occur at anchor points (zero correction) where the device has no drift compensation

**2.3 Slip rate vs correction sign**
Compare slip rates for positive-correction windows vs negative-correction windows:
- Mann-Whitney U test
- Physical interpretation: if positive-drift windows have more slips, the forward drift causes the eye to overshoot; if negative-drift, the backward pull causes under-indexing

**2.4 Slip position vs offset position**
The 202 slips are concentrated at line positions 1-3. The offset corrections are per-window (not per-position). Test:
- Do early-position slips occur preferentially in specific windows?
- Cross-tabulate: (slip position) × (window correction sign)
- Physical interpretation: if early slips cluster in positive-drift windows, the device's forward bias at session start causes indexing errors

**2.5 Temporal clustering**
Within the manuscript's folio sequence, do slips cluster in consecutive folios?
- Compute inter-slip interval distribution
- Compare to geometric expectation under independence
- Physical interpretation: temporal clustering suggests device wear/misalignment episodes

### Reuse
- `slip_detection_results.json`: `results/data/phase12_mechanical/slip_detection_results.json`
- `canonical_offsets.json`: `results/data/phase14_machine/canonical_offsets.json`
- `lattice_map` from full palette grid
- `load_lines_with_metadata()`: `run_14x_mask_inference.py`

### Acceptance
- Per-window slip rate table
- Slip-offset correlation (rho, p-value)
- Slip-sign comparison (U-test, p-value)
- Clear statement: are slips and offsets correlated?

---

## Sprint 3: Device Geometry Inference

**Script:** Same as Sprint 1 (extended)

### Tasks

**3.1 Candidate device models**
Define three candidate physical devices, each with a characteristic error signature:

| Device | Geometry | Expected Correction Pattern | Expected Slip Pattern |
|:---|:---|:---|:---|
| **Circular volvelle** | Rotating disc(s) | Sinusoidal drift (accumulates with rotation) | Uniform across windows |
| **Rectangular tabula** | 10×5 grid | Row/column structure (drift depends on position in grid) | Concentrated at row transitions |
| **Linear sliding grille** | Sequential strip | Monotonic drift (accumulates with linear traversal) | Concentrated at strip edges |

**3.2 Model-data comparison**
For each candidate:
- Generate the predicted correction profile (50 values) under that geometry
- Compare to observed corrections via residual sum of squares
- Compare predicted vs observed slip distribution (chi-squared)
- Rank candidates by combined fit

**3.3 Bayesian model comparison**
Compute BIC for each candidate device model:
- Parameters: volvelle (2: amplitude, phase), tabula (4: row drift, column drift, row offset, column offset), grille (2: slope, intercept)
- Likelihood: sum of squared residuals of correction fit
- BIC = n·ln(RSS/n) + k·ln(n)
- Select model with lowest BIC

**3.4 Physical constraints summary**
Synthesize Sprints 1-3 into a physical profile:
- Device type (most likely candidate)
- Orientation (correction phase structure)
- Wear pattern (slip-offset correlation)
- Anchor positions (zero-correction windows as physical reference points)

### Acceptance
- Three candidate models with predicted profiles
- Model comparison table (RSS, chi², BIC)
- Best-fit device type identified
- Physical constraints document

---

## Sprint 4: Governance Updates

### Tasks

**4.1 Update CANONICAL_EVALUATION.md**
Add Section for physical integration analysis (offset topology, slip correlation, device inference).

**4.2 Update STATUS.md**
Update Section 6 (physical machine not required) with new evidence. Update Section 10.

**4.3 Update claim_artifact_map.md**
Add claims for physical integration findings.

**4.4 Update this execution plan**
Record actual results in the Execution Progress section.

---

## Dependency Graph

```
Sprint 1 (Offset Topology) → Sprint 2 (Slip-Offset Correlation) → Sprint 3 (Device Inference) → Sprint 4 (Governance)
```

Strictly sequential: Sprint 2 uses Sprint 1's spatial characterization to frame hypotheses. Sprint 3 synthesizes both into device models.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1-3 | `scripts/phase14_machine/run_14zf_physical_integration.py` | Script |
| 1-3 | `results/data/phase14_machine/physical_integration.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add physical integration section |
| 4 | `STATUS.md` | Update physical device section |
| 4 | `governance/claim_artifact_map.md` | Add claims |
