# Phase 14J: Second-Order Context Model

**Date:** 2026-02-21
**Status:** COMPLETE (2026-02-21) — Clean negative result
**Depends on:** Phase 14I (bigram-conditioned lattice)

## Execution Progress

- [x] Sprint 1 script written and executed (2026-02-21)
- [x] Sprint 2 SKIPPED — gate failed (+0.50pp < 2pp threshold)
- [x] Sprint 3 governance updates (2026-02-21)

### Sprint 1 Results: Second-Order Transition Analysis

**Sparsity:** Only 733/2,500 (29.3%) possible window pairs observed. Median 4.0 obs/pair.

**Info Gain Decomposition (trigram-based, 22,943 transitions):**

| Conditioning | H(offset) | Info Gain | Parameters |
|:---|---:|---:|---:|
| None (unconditional) | 4.0099 | — | 0 |
| curr_window | 2.8644 | 1.1455 | 50 |
| prev_window | 3.8815 | 0.1283 | 50 |
| **(prev_win, curr_win)** | **2.6099** | **1.3999** | **733** |
| **Pair beyond curr_window** | — | **0.2544** | — |

**Ceilings:**

| Model | Rate | Delta | Params |
|:---|---:|---:|---:|
| Baseline | 47.06% | — | 0 |
| 1st-order (curr_window) | 63.51% | +16.45pp | 50 |
| 2nd-order (min_obs=3) | 64.01% | +16.96pp | 476 |

**Pair mode divergence:** 70/327 pairs (21.4%) diverge from first-order, but only +0.50pp improvement.

**Gate decision:** FAIL. Ceiling improvement +0.50pp < 2pp threshold. Sprint 2 skipped.

**Key insight:** The lattice transition is essentially first-order Markov at the window level. curr_window captures 1.15 bits; adding prev_window adds only 0.25 bits. This is consistent with a physical tool where position (not history) determines the next transition.

## Motivation

Phase 14I discovered that per-window mode offset correction adds +16.17pp cross-validated admissibility with only 50 parameters. This is a **first-order** model: P(offset | prev_window). The info gain decomposition showed 1.03 bits of word identity beyond window identity — but word-level correction is impractical (78.4% fallback rate).

**The gap:** First-order window conditioning captures 1.27 bits of the 4.09-bit offset entropy. A **second-order** model — P(offset | prev_window, current_window) — may capture additional structure without the sparsity problems of word-level conditioning, since there are only 50×50 = 2,500 possible window pairs (vs 6,536 unique prev_words).

## Sprint 1: Second-Order Transition Analysis

**Script:** `scripts/phase14_machine/run_14za_second_order_transitions.py`
**Output:** `results/data/phase14_machine/second_order_transitions.json`

### Tasks

**1.1 Window-pair transition statistics**
Build a 50×50×50 tensor: count(prev_window, curr_window, next_window). From this derive:
- H(offset | prev_window, curr_window) — second-order conditional entropy
- I(offset; prev_window, curr_window) — second-order info gain
- Marginal: I(offset; curr_window | prev_window) — info gain of curr_window beyond prev_window

**1.2 Sparsity analysis**
Of 2,500 possible (prev_window, curr_window) pairs:
- How many are observed at all?
- How many have ≥5, ≥10, ≥20 observations?
- What fraction of total transitions do the well-observed pairs cover?

**1.3 Second-order mode offsets**
For each (prev_window, curr_window) pair with sufficient data:
- Compute mode offset (most common signed circular offset to next_window)
- Compare to first-order mode offset (from prev_window alone)
- Count how many pairs diverge from their first-order prediction

**1.4 Theoretical ceiling**
Apply second-order mode correction to all transitions:
- For pairs with ≥min_obs: use pair-specific mode offset
- Fallback to first-order (prev_window mode) for sparse pairs
- Report admissibility ceiling and parameter count at multiple min_obs thresholds

**1.5 Comparison table**
| Model | Info Gain | Ceiling | Parameters | Fallback Rate |
Rows: unconditional, first-order window, second-order window-pair, first-order word

### Reuse
- `signed_circular_offset()`: `run_14z7_bigram_transitions.py`
- `load_lines_with_metadata()`: `run_14x_mask_inference.py`
- `load_palette()`: `run_14x_mask_inference.py`
- `GlobalPaletteSolver`: `src/phase14_machine/palette_solver.py`
- `active_run()` / provenance: `src/phase1_foundation/runs/context.py`
- `ProvenanceWriter.save_results()`: `src/phase1_foundation/core/provenance.py`

### Acceptance
- Second-order info gain computed and compared to first-order
- Sparsity analysis with coverage at multiple thresholds
- Theoretical ceiling at multiple min_obs values
- Clear determination: does second-order warrant cross-validation (Sprint 2)?

---

## Sprint 2: Cross-Validated Second-Order Correction

**Script:** `scripts/phase14_machine/run_14zb_second_order_conditioned.py`
**Output:** `results/data/phase14_machine/second_order_conditioned.json`

**Gate:** Only execute if Sprint 1 shows second-order ceiling exceeds first-order ceiling by ≥2pp.

### Tasks

**2.1 Seven leave-one-section-out splits**
For each of 7 sections:
- Train fresh lattice on remaining 6 via `GlobalPaletteSolver`
- Learn second-order corrections on training data (with fallback to first-order)
- Score on held-out section
- Compare to first-order correction from Phase 14I

**2.2 Optimal min_obs sweep**
Test min_obs ∈ {3, 5, 10, 20} for the second-order pairs. Report mean delta, z-score, and overfit gap for each.

**2.3 Combined model**
Test a hierarchical model:
- Use second-order correction when pair has ≥min_obs observations
- Fall back to first-order when pair is sparse
- Report whether the combined model beats pure first-order

**2.4 Summary table**
| Model | Mean Delta | Mean Z | Overfit Gap | Params | All Positive |
Rows: first-order (baseline from 14I), second-order pure, second-order + fallback

### Reuse
- `train_lattice()`: `run_14z8_bigram_conditioned.py`
- `learn_offset_corrections()`: `run_14z8_bigram_conditioned.py` (extend for second-order)
- `score_with_correction()`: `run_14z8_bigram_conditioned.py` (extend for second-order)
- `get_section_lines()`: `run_14z5_multisplit_holdout.py`

### Acceptance
- All 7 splits produce valid z-scores
- Clear comparison: second-order vs first-order on holdout
- If second-order wins: quantify improvement and parameter cost
- If second-order loses or ties: document why (sparsity, overfitting)

---

## Sprint 3: Governance Updates

### Tasks

**3.1 Update CANONICAL_EVALUATION.md**
Add Section 23 (Second-Order Context Analysis) with Sprint 1-2 results.

**3.2 Update STATUS.md**
Update Section 1 admissibility numbers if second-order improves over first-order. Update Section 10 with Phase 14J accomplishments.

**3.3 Update claim_artifact_map.md**
Add claims for Phase 14J findings.

**3.4 Save execution plan**
Update this file with actual results.

---

## Dependency Graph

```
Sprint 1 (Analysis) → Sprint 2 (Cross-Validation, gated) → Sprint 3 (Governance)
```

Sprint 2 is gated on Sprint 1 results. If second-order ceiling is < first-order + 2pp, Sprint 2 is skipped and Sprint 3 documents the negative result.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1 | `scripts/phase14_machine/run_14za_second_order_transitions.py` | Script |
| 1 | `results/data/phase14_machine/second_order_transitions.json` | Artifact |
| 2 | `scripts/phase14_machine/run_14zb_second_order_conditioned.py` | Script |
| 2 | `results/data/phase14_machine/second_order_conditioned.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 3 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add Section 23 |
| 3 | `STATUS.md` | Update if improved |
| 3 | `governance/claim_artifact_map.md` | Add claims |
