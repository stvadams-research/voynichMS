# Phase 14G: Comprehensive Strengthening Program

**Objective:** Address all identified model weaknesses, credibility threats, and
validation gaps across 6 sprints.

**Date:** 2026-02-21
**Status:** COMPLETE

---

## Sprint 1: Fix Phase 16 Report (Credibility)

**Problem:** ERGONOMIC_VERIFICATION.md claimed rho=0.2334 (p<0.0001) but actual
data shows rho=-0.0003 (p=0.99). Also claimed 68.33% efficiency when actual is
81.50%.

- [x] **1.1:** Rewrote `results/reports/phase16_physical/ERGONOMIC_VERIFICATION.md`
  with actual values from JSON artifacts (rho=-0.0003, p=0.9926, efficiency=81.50%).
  Reframed narrative: ergonomic coupling is NULL, geometric optimization is real.
- [x] **1.2:** Updated `planning/phase16_physical_grounding/phase_16_execution_plan.md`
  — fixed all stale values, marked ergonomic correlation as NULL RESULT.
- [x] **1.3:** Verified `grep -r "0.2334" results/ planning/` returns zero hits
  in reports and planning. (Data files contain 0.2334 as legitimate numeric values
  in unrelated contexts — confirmed safe.)

**Outcome:** Credibility issue resolved. All report values now match computed data.

---

## Sprint 2: Lattice Compression / MDL Analysis

**Problem:** Lattice L(model)=154,340 bits dominates MDL. Copy-Reset needs only
20 bits. The current computation double-counts (lattice_map + window_contents,
but window_contents is derivable from lattice_map).

- [x] **2.1:** Created `scripts/phase14_machine/run_14z_lattice_compression.py`
  — five compression schemes: naive, entropy-optimal, character-feature,
  stem-based, frequency-conditional.
- [x] **2.2:** Run script, analyze results
- [x] **2.3:** Update CANONICAL_EVALUATION.md with compression findings (Section 12)

**Results:**

| Method | L(model) bits | BPT |
|:---|---:|---:|
| Showdown (double-counted) | 154,340 | 15.73 |
| Naive (log₂50 per word) | 43,554 | 12.53 |
| Entropy-optimal (Huffman) | 40,930 | 12.45 |
| **Frequency-conditional** | **38,029** | **12.37** |
| Character-feature | 392,983 | 22.62 |

**Outcome:** Double-counting confirmed. Frequency-conditional encoding achieves 75%
compression (154K → 38K bits). Lattice BPT drops from 15.73 to 12.37. Gap to
Copy-Reset reduced from 4.83 to 1.47 BPT. High-frequency words cluster tightly
(H=0.575 bits) while hapax spread (H=5.377 bits).

**Artifact:** `results/data/phase14_machine/lattice_compression.json`

---

## Sprint 3: Mask Rotation Generative Model

**Problem:** Oracle mask inference gives +14.3pp but is post-hoc. Need
predictive rules using observable metadata.

- [x] **3.1:** Created `scripts/phase14_machine/run_14z2_mask_prediction.py`
  — tests 6 prediction rules (global_mode, per_section, per_quire, per_hand,
  per_page, prev_line_carry)
- [x] **3.2:** Run script, compute capture rates
- [x] **3.3:** Update CANONICAL_EVALUATION.md (Section 13)

**Results:**

| Rule | Admissibility | Oracle Capture |
|:---|---:|---:|
| Global mode (offset=17) | 45.91% | 44.2% |
| Per-hand | 45.91% | 44.2% |
| Per-section | 45.28% | 39.8% |
| Per-page | 45.32% | 40.1% |
| Per-quire | 45.24% | 39.5% |
| Prev-line carry | 43.04% | 24.2% |
| Oracle (ceiling) | 53.91% | 100.0% |

**Outcome:** Global mode (single offset=17) captures 44.2% of oracle gain with
one parameter. 6 of 7 sections share mode offset 17; only Astro uses 0.
Per-section/quire/hand rules do not improve over global mode.

**Artifact:** `results/data/phase14_machine/mask_prediction.json`

---

## Sprint 4: Cross-Transcription Validation

**Problem:** All analysis uses ZL only. Need independence validation across
5 EVA transcription sources (GC, VT, IT, RF, FG).

- [x] **4.1:** Created `scripts/phase14_machine/run_14z3_cross_transcription.py`
  — vocab overlap, admissibility ratio, permutation test
- [x] **4.2:** Run script, analyze results
- [x] **4.3:** Update CANONICAL_EVALUATION.md (Section 14)

**Results:**

| Source | Vocab Overlap | Admissibility | Ratio | Z-Score |
|:---|---:|---:|---:|---:|
| VT | 65.9% | 49.97% | 1.150 | 89.0 |
| IT | 65.8% | 49.32% | 1.135 | 88.2 |
| RF | 69.3% | 47.51% | 1.094 | 86.7 |
| GC | 0.7% | 21.93% | 0.505 | 0.28 |
| FG | 0.03% | 89.5%* | — | -0.39 |

*FG has only 19 clamped tokens (non-EVA alphabet).

**Outcome:** STRONG validation. 3 independent EVA transcriptions (VT, IT, RF)
show admissibility ratios 1.09–1.15 with z-scores > 86. Lattice structure is
transcription-independent. GC and FG use non-EVA alphabets (<1% overlap).

**Artifact:** `results/data/phase14_machine/cross_transcription.json`

---

## Sprint 5: Within-Window Selection Analysis

**Problem:** Phase 15 found 21.49% selection skew, Phase 16 proved NOT ergonomic.
What drives the bias?

- [x] **5.1:** Created `scripts/phase15_rule_extraction/run_15d_selection_drivers.py`
  — tests 5 hypotheses: positional bias, bigram context, suffix affinity,
  frequency bias, recency bias
- [x] **5.2:** Run script, rank drivers by information gain
- [x] **5.3:** Update CANONICAL_EVALUATION.md (Section 15) and governance docs

**Results:** ALL 5 hypotheses significant:

| Hypothesis | Bits Explained | Key Finding |
|:---|---:|:---|
| **Bigram context** | **2.432** | H(w|window,prev) = 4.74 vs H(w|window) = 7.17 |
| Positional bias | 0.637 | Mean relative position = 0.247 (top-of-window pref) |
| Recency bias | 0.216 | Recently-used words +10.8pp more likely to recur |
| Suffix affinity | 0.163 | 2.62x excess suffix match rate |
| Frequency bias | 0.123 | Spearman rho = -0.247 (common words selected more) |

**Outcome:** Bigram context is the dominant driver (2.43 bits). The scribe's
within-window choices are substantially constrained by local context, consistent
with a production protocol that prescribes bigram-level sequences.

**Artifact:** `results/data/phase15_selection/selection_drivers.json`

---

## Sprint 6: Phase 17 Completion & Governance Cleanup

- [x] **6.1:** Updated Phase 17 execution plan checkboxes and Latin capacity note
- [x] **6.2:** Latin capacity bound computed: 7.53 bpw × 12,519 = 94,268 bits ≈
  22,992 Latin chars ≈ 4-5 Vulgate chapters (documented in Phase 17 plan)
- [x] **6.3:** Updated claim_artifact_map.md with claims 71-79 (Phase 14G section)
  and verification count (68 → 77 fully verifiable)
- [x] **6.4:** Updated CANONICAL_EVALUATION.md with Sections 12-15 and revised
  Formal Conclusion (Section 16)
- [x] **6.5:** Full test suite (851 pass) + lint clean on all new scripts
- [x] **6.6:** This execution plan saved with actual results

---

## Execution Order (Completed)

```
Sprint 1 (COMPLETE) ─┐
                      ├── Sprint 3 (COMPLETE) ──┐
Sprint 2 (COMPLETE) ──┘                         ├── Sprint 5 (COMPLETE) ── Sprint 6 (COMPLETE)
                      ┌── Sprint 4 (COMPLETE) ──┘
                      └── (parallel with 3)
```

---

## Files Summary

**New files:**
- `scripts/phase14_machine/run_14z_lattice_compression.py`
- `scripts/phase14_machine/run_14z2_mask_prediction.py`
- `scripts/phase14_machine/run_14z3_cross_transcription.py`
- `scripts/phase15_rule_extraction/run_15d_selection_drivers.py`

**Modified files:**
- `results/reports/phase16_physical/ERGONOMIC_VERIFICATION.md` (Sprint 1)
- `planning/phase16_physical_grounding/phase_16_execution_plan.md` (Sprint 1)
- `results/reports/phase14_machine/CANONICAL_EVALUATION.md` (Sprint 6: Sections 12-16)
- `governance/claim_artifact_map.md` (Sprint 6: Claims 71-79)
- `planning/phase17_finality/phase_17_execution_plan.md` (Sprint 6)

**Generated artifacts:**
- `results/data/phase14_machine/lattice_compression.json`
- `results/data/phase14_machine/mask_prediction.json`
- `results/data/phase14_machine/cross_transcription.json`
- `results/data/phase15_selection/selection_drivers.json`

**PHASE 14G COMPLETE.**
