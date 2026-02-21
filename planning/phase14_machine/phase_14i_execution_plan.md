# Phase 14I: Bigram-Conditioned Lattice & Open Questions

**Date:** 2026-02-21
**Status:** COMPLETE (2026-02-21)

## Execution Progress

- [x] Sprint 1 script written and executed (2026-02-21)
- [x] Sprint 2 script written and executed (2026-02-21)
- [x] Sprint 3 script written and executed (2026-02-21)
- [x] Sprint 4 governance updates (2026-02-21)

### Sprint 1 Results: Bigram Transition Profiling

**Info Gain Decomposition:**

| Conditioning | H(offset) | Info Gain |
|:---|---:|---:|
| None (unconditional) | 4.0903 | — |
| prev_window (50 params) | 2.8166 | 1.2737 |
| prev_word (all 6,536) | 1.7903 | 2.3001 |
| prev_word (≥5 obs, 772) | 2.3311 | 1.7592 |
| **Word beyond window** | — | **1.0263** |

Key findings:
- **1.03 bits** of word identity beyond window — richer model warranted
- **474/772** profiled prev_words have mode offset ≠ 0 (61.4%)
- **43/50** windows have mode offset ≠ 0 — systematic lattice drift
- Word-level fallback rate: 78.4% (most transitions lack sufficient word-level data)

**Theoretical Admissibility Ceilings:**

| Model | Admissible | Rate | Delta | Parameters |
|:---|---:|---:|---:|---:|
| Baseline (no correction) | 12,624 | 45.91% | — | 0 |
| Window-level mode | 17,700 | 64.37% | +18.46pp | 50 |
| Word-level mode | 14,413 | 52.42% | +6.51pp | 772 |

**Interpretation:** The window-level correction is the clear practical winner: +18.46pp with only 50 parameters and full coverage. The word-level correction adds only +6.51pp due to 78.4% fallback rate (most prev_words have < 5 observations). The ceiling of 64.37% is on training data — Sprint 2 cross-validation will determine the holdout improvement.

### Sprint 2 Results: Cross-Validated Bigram Conditioning

**Primary model (window_min5) — 7-fold leave-one-section-out:**

| Held Out | Test Tokens | Baseline | Corrected | Delta | Z-Score | Overfit Gap |
|:---|---:|---:|---:|---:|---:|---:|
| Herbal A | 8,826 | 19.9% | 36.8% | +16.9pp | 83.1σ | -4.0pp |
| Herbal B | 1,164 | 16.2% | 35.9% | +19.7pp | 29.5σ | -1.0pp |
| Astro | 2,869 | 15.0% | 34.3% | +19.3pp | 38.2σ | +0.5pp |
| Biological | 6,422 | 42.3% | 63.2% | +20.9pp | 152.1σ | -19.2pp |
| Cosmo | 1,727 | 21.3% | 32.0% | +10.7pp | 35.3σ | -4.5pp |
| Pharma | 3,501 | 15.4% | 23.2% | +7.8pp | 30.2σ | +2.3pp |
| Stars | 10,096 | 19.1% | 37.0% | +18.0pp | 99.0σ | -6.4pp |

- **Mean improvement: +16.17pp** (all 7/7 splits positive)
- **Mean z-score: 66.8σ** (all highly significant)
- **Mean overfit gap: -4.6pp** (negative = model performs BETTER on holdout)
- Window-level (50 params) consistently beats word-level (688+ params)
- min_obs threshold irrelevant for window-level (all 50 windows always have sufficient data)

**Model Comparison (mean across 7 splits):**

| Model | Mean Delta (pp) | Mean Z-Score | Params |
|:---|---:|---:|---:|
| window_min3 | +16.17 | 66.8σ | 50 |
| window_min5 | +16.17 | 66.8σ | 50 |
| word_min3 | +10.12 | 54.2σ | ~1,141 |
| word_min5 | +9.60 | 53.1σ | ~688 |
| word_min20 | +6.91 | 47.6σ | ~193 |

**Interpretation:** The per-window mode offset correction is a genuine structural finding. It improves admissibility by +16.17pp cross-validated with only 50 parameters — the simplest model wins. The negative overfitting gap means train-time corrections transfer well to unseen sections, confirming the structure is corpus-wide, not section-specific. This raises the effective admissibility ceiling from ~46% to ~62% (drift-corrected, holdout-validated).

### Sprint 3 Results: Closed Open Questions

**Q1: Higher-Order Overgeneration**

| N-gram | Real | Synthetic | Overgen. Ratio | Unattested Rate |
|:---|---:|---:|---:|---:|
| 2-gram | 24,088 | 579,933 | 24.1× | 100.0% |
| 3-gram | 22,806 | 499,819 | 21.9× | 100.0% |
| 4-gram | 18,808 | 400,187 | 21.3× | 100.0% |
| 5-gram | 15,126 | 300,196 | 19.9× | 100.0% |

Overgeneration decreases modestly at higher orders (24.1× → 19.9×) but remains ~20× at all levels. The lattice is a wide sequential gate: it permits ~20× more n-gram sequences than observed, and essentially zero synthetic n-grams match real ones.

**Q2: Per-Position Branching Factor**

| Position | Mean BF | Effective Bits |
|:---|---:|---:|
| 0 (line start) | 96.0 | 6.58 |
| 1 | 747.5 | 9.55 |
| 2-8 | ~890 | ~9.80 |
| 9+ | 878.1 | 9.78 |

Overall: **761.7 candidates/position = 9.57 effective bits**. Position 0 is constrained (window=0 fixed, 96 candidates). Positions 1+ quickly stabilize at ~890 candidates (~9.8 bits). Compare to 7.17 bits within-window selection from Phase 15D — the drift-inclusive branching is higher.

**Q3: MDL Gap Decomposition**

| Component | Lattice | Copy-Reset | Gap |
|:---|---:|---:|---:|
| L(model) | 38,029 | 77,180 | -39,151 |
| L(data\|model) | 317,965 | 348,377 | -30,411 |
| L(total) | 355,994 | 425,557 | -69,563 |
| BPT | 10.836 | 12.954 | -2.117 |

Under corrected encoding (frequency-conditional L(model)), the lattice actually **wins** MDL by 2.12 BPT. The previous "CR wins MDL" result was based on the double-counted lattice model cost (154K bits vs corrected 38K bits). The gap decomposes as 56.3% model overhead savings, 43.7% data encoding savings.

## Context

Phase 14H fully diagnosed the 46% wrong-window residual: it is structural (93.6%), context-dependent (1.31 bits bigram info gain), not mask-recoverable (2.8%), and follows a unimodal symmetric drift pattern. The diagnosis points directly to a **bigram-conditioned transition model** as the next improvement.

Additionally, STATUS.md Section 8 lists three remaining open questions (overgeneration bounding, branching factor, description length gap) that are analytical refinements ready to close.

This phase has two objectives:
- **Path A (Sprints 1-2):** Build and cross-validate a bigram-conditioned lattice model
- **Path B (Sprint 3):** Close the remaining open questions from STATUS.md Section 8

---

## Sprint 1: Bigram Transition Profiling

**Script:** `scripts/phase14_machine/run_14z7_bigram_transitions.py`
**Output:** `results/data/phase14_machine/bigram_transitions.json`

### Motivation

The current lattice is memoryless: word(n) → window(n+1), period. Phase 14H Sprint 1 showed 1.31 bits of information gain from prev_word on failure distance. Before building a correction model, we need to profile the transition patterns at both window-level and word-level granularity.

### Tasks

**1.1 Full transition record**
For all consecutive token pairs in the ZL corpus:
- `prev_word`, `curr_word`, `prev_window` = lattice_map[prev_word], `curr_window` = lattice_map[curr_word]
- `offset` = (curr_window - prev_window) mod 50 (signed, wrapped to [-25, +25])
- `admissible` = abs(offset) <= 1

Use `load_canonical_lines()` and the existing palette from `full_palette_grid.json`.

**1.2 Window-to-window transition matrix**
Build 50×50 matrix P(curr_window | prev_window). Visualize as heatmap. Compute entropy H(next_window | current_window) — how predictable is the next window from the current one?

**1.3 Word-level vs window-level info gain**
Compute three conditional entropies:
- H(offset) — unconditional offset entropy
- H(offset | prev_window) — conditioning on which window the prev word is in
- H(offset | prev_word) — conditioning on the specific prev word

If H(offset | prev_window) ≈ H(offset | prev_word), then all info gain is at the window level (simpler model, 50 parameters). If H(offset | prev_word) << H(offset | prev_window), then word identity carries extra signal (richer model, ~500+ parameters).

**1.4 Per-prev_word offset profiles**
For each prev_word with ≥5 consecutive-pair observations:
- Mode offset (most common observed offset)
- Offset entropy (how concentrated is the distribution)
- Count of observations
Group by: mode_offset = 0 (already well-predicted) vs mode_offset ≠ 0 (correctable).

**1.5 Per-prev_window offset profiles**
Same as 1.4 but aggregated at window level. For each of 50 windows:
- Mode offset, offset entropy, observation count
- Fraction of transitions that are admissible (distance ≤ 1)

**1.6 Theoretical ceiling computation**
Two ceilings:
- **Word-level correction:** For each prev_word, apply its mode offset as a correction. Count how many tokens become admissible under the shifted prediction.
- **Window-level correction:** For each prev_window, apply its mode offset. Count admissible tokens.

Both computed as: admissible = |actual_offset - mode_correction| ≤ 1.

Report improvement from baseline 43.44% and the gap between word-level and window-level ceilings.

### Reuse
- `load_canonical_lines()`: `src/phase1_foundation/core/data_loading.py`
- `entropy()`: `run_14z4_failure_taxonomy.py:248`
- `load_palette()` pattern: `run_14x_mask_inference.py:178`
- `ProvenanceWriter.save_results()`: `src/phase1_foundation/core/provenance.py`

### Acceptance
- Full transition record for ~34,000 consecutive pairs
- 50×50 transition matrix with entropy
- Three-level info gain comparison (unconditional / window / word)
- Per-prev_word and per-prev_window offset profiles
- Two theoretical ceilings with improvement deltas

---

## Sprint 2: Context-Conditioned Admissibility Evaluator

**Script:** `scripts/phase14_machine/run_14z8_bigram_conditioned.py`
**Output:** `results/data/phase14_machine/bigram_conditioned.json`

### Motivation

Sprint 1 provides the theoretical ceiling. Sprint 2 tests whether the improvement holds under cross-validation (not overfit to training data).

### Tasks

**2.1 Offset correction function**
Implement `apply_bigram_correction(tokens, lattice_map, offset_table, level)`:
- `level="window"`: offset_table maps prev_window → correction offset
- `level="word"`: offset_table maps prev_word → correction offset
- For each consecutive pair, predicted_window = (lattice_map[prev_word] + correction) % 50
- Admissible if |lattice_map[curr_word] - predicted_window| ≤ 1 (circular)
- Tokens with no entry in offset_table fall back to correction = 0 (unigram baseline)

**2.2 Training protocol**
Given training lines:
- For each consecutive pair (prev_word, curr_word) where both are in lattice_map:
  - Compute offset = lattice_map[curr_word] - lattice_map[prev_word] (circular)
  - Accumulate per prev_word (or prev_window)
- For each prev_word/window with ≥ min_obs observations, mode offset becomes the correction
- min_obs threshold sweep: [3, 5, 10, 20] to find optimal sparsity-accuracy tradeoff

**2.3 Seven-fold cross-validation**
Leave-one-section-out (same 7 sections as Phase 14H Sprint 2):
- Train offset table on 6 sections
- Score on held-out section
- Report: baseline admissibility, corrected admissibility, delta, z-score

Aggregate: mean improvement across 7 splits, # splits with positive improvement.

**2.4 Overfitting diagnostic**
For each split, report train admissibility vs test admissibility. If train >> test, the model overfits. Compare word-level vs window-level overfitting.

**2.5 Sparsity analysis**
What fraction of test tokens have a reliable correction (prev_word/window seen in training with ≥ min_obs)?
What fraction fall back to unigram? How does this change with min_obs threshold?

**2.6 Best model selection**
Report the best (level, min_obs) configuration by cross-validated admissibility improvement. Compare to the theoretical ceiling from Sprint 1.

### Reuse
- `get_section_lines()` pattern: `run_14g_holdout_validation.py:42-91`
- `binomial_z_score()`: `run_14g_holdout_validation.py:94-101`
- `load_canonical_lines()`: `src/phase1_foundation/core/data_loading.py`
- SECTIONS dict: `run_14x_mask_inference.py:52-83`

### Acceptance
- 7/7 splits produce valid results
- Word-level vs window-level comparison
- min_obs threshold sweep results
- Overfitting diagnostic (train vs test gap)
- Best model achieves statistically significant improvement over baseline (z > 3σ)
- JSON artifact with full provenance

### Risk
If theoretical ceiling from Sprint 1 shows only marginal improvement (< 5pp), Sprint 2 may show no significant cross-validated gain. In that case, document the null result — it means the 1.31 bits of bigram info gain translates to narrower offset distributions but not to more tokens crossing the admissibility threshold.

---

## Sprint 3: Close Remaining Open Questions

**Script:** `scripts/phase14_machine/run_14z9_open_questions.py`
**Output:** `results/data/phase14_machine/open_questions.json`

### Motivation

STATUS.md Section 8 has three remaining open questions. All are analytical refinements that can be closed with targeted computation.

### Tasks

**3.1 Higher-order overgeneration (4-gram, 5-gram)**
Extend `run_14d_overgeneration_audit.py` pattern:
- Generate 100K synthetic lines via HighFidelityVolvelle (seed=42)
- Compute n-gram unattested rates for n ∈ {2, 3, 4, 5}
- Real corpus n-grams from `load_canonical_lines()`
- Report: real count, synthetic count, unattested count, unattested rate per n
- Expected: overgeneration ratio should decrease at higher orders (more constrained)

**3.2 Per-position branching factor**
For each token in the real corpus at line position p:
- Current window = lattice_map[prev_word] (from preceding transition)
- Admissible next tokens = words in windows {current_window - 1, current_window, current_window + 1}
- Branching factor = |admissible next tokens|
- Report: mean, median, std branching factor by position (pos 0-9+)
- Also report: effective branching factor (log2 of mean) as bits of choice per position
- Compare to the 7.17 bits within-window / 4.74 bits bigram-conditioned from Phase 15D

**3.3 Description length gap decomposition**
Break down the 1.47 BPT gap between Lattice (12.37) and Copy-Reset (10.90):
- **Model overhead:** L(model) difference — lattice has 50×V parameters vs Copy-Reset's O(V)
- **Transition cost:** L(data|model) difference — lattice's window-based encoding vs CR's copy probability
- **Coverage gap:** Tokens the lattice handles that CR doesn't, and vice versa
- Use corrected MDL from `run_14z_lattice_compression.py` for lattice, Markov entropy for CR
- Decompose into: lattice_model_cost, lattice_data_cost, cr_model_cost, cr_data_cost

### Reuse
- `HighFidelityVolvelle`: `src/phase14_machine/high_fidelity_emulator.py`
- `get_ngrams()` pattern: `evaluation_engine.py:233-240`
- `load_canonical_lines()`: `src/phase1_foundation/core/data_loading.py`
- `entropy()`: standard helper
- MDL computation: `run_14z_lattice_compression.py`

### Acceptance
- N-gram overgeneration for n ∈ {2, 3, 4, 5} with rates
- Per-position branching factor distribution (positions 0-9+)
- MDL gap decomposed into model overhead vs data encoding
- All three STATUS.md open questions addressable from results

---

## Sprint 4: Governance Updates

### Tasks

**4.1 Update CANONICAL_EVALUATION.md**
Add Sections 20-22:
- Section 20: Bigram Transition Profiling (Sprint 1 results)
- Section 21: Context-Conditioned Admissibility (Sprint 2 results)
- Section 22: Closed Open Questions (Sprint 3 results)

**4.2 Update STATUS.md**
- Close remaining 3 open questions in Section 8 (overgeneration, branching factor, description length)
- Update Section 10 with Phase 14I accomplishments
- If bigram conditioning improves admissibility, update Section 1 with new rate

**4.3 Update claim_artifact_map.md**
Add claims for Phase 14I findings. Update verification count.

**4.4 Update execution plan**
Mark all sprints complete with actual results.

---

## Dependency Graph

```
Sprint 1 (Transition Profiling) ─── Sprint 2 (Conditioned Scoring) ──┐
Sprint 3 (Open Questions) ──────────────────────────────────────────-─┤── Sprint 4 (Governance)
                                                                      │
```

Sprint 1 → Sprint 2 is sequential (Sprint 2 needs Sprint 1's offset profiles).
Sprint 3 is independent of Sprints 1-2.
Sprint 4 depends on all three completing.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1 | `scripts/phase14_machine/run_14z7_bigram_transitions.py` | Script |
| 1 | `results/data/phase14_machine/bigram_transitions.json` | Artifact |
| 2 | `scripts/phase14_machine/run_14z8_bigram_conditioned.py` | Script |
| 2 | `results/data/phase14_machine/bigram_conditioned.json` | Artifact |
| 3 | `scripts/phase14_machine/run_14z9_open_questions.py` | Script |
| 3 | `results/data/phase14_machine/open_questions.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add Sections 20-22 |
| 4 | `STATUS.md` | Close 3 open questions, update framing |
| 4 | `governance/claim_artifact_map.md` | Add claims |

## Verification

After all sprints:
1. `ruff check .` returns 0 errors
2. `python -m pytest tests/` — all tests pass
3. All 3 new JSON artifacts exist with valid provenance headers
4. STATUS.md Section 8 has 0 remaining open questions
5. Run each new script independently to confirm reproducibility

### Verification Results (2026-02-21)

All 5 checks passed:
- `ruff check .` — 0 errors
- `pytest` — 859 passed
- All 3 artifacts exist: `bigram_transitions.json`, `bigram_conditioned.json`, `open_questions.json`
- STATUS.md Section 8: all 6 open questions closed
- All scripts ran independently and produced consistent results
