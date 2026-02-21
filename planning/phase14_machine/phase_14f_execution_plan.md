# Phase 14F: Model Improvements, Hybrid MDL & Documentation

**Objective:** Close remaining model gaps (section variation, mask states, MDL
parsimony) and formally document ZL as the canonical transcription standard.

**Date:** 2026-02-21
**Status:** COMPLETE

---

## Sprint 0: Documentation — ZL as Canonical Standard

**Goal:** Make explicit that all analysis uses the Zandbergen-Landini (ZL)
transcription in EVA lowercase encoding.

- [x] **0.1:** Updated `governance/methods_reference.md` — added Section 0:
  Transcription Standard with loader path, sanitization rules, source URL,
  citation, and explicit note that 6 other sources (including Currier/D'Imperio)
  are isolated from the canonical pipeline.
- [x] **0.2:** Updated `governance/config_reference.md` — added Transcription
  Source section noting `DEFAULT_SOURCE_ID = "zandbergen_landini"` is not
  configurable by design.
- [x] **0.3:** Updated `ARCHITECTURE.md` — added Key Design Decision #6
  documenting the canonical transcription chain.
- [x] **0.4:** Updated `README.md` — added transcription standard note in Quick
  Start section.

**Outcome:** ZL provenance is now documented in 4 governance/architecture files.

---

## Sprint 1: Section-Aware Lattice Model

**Goal:** Test whether section-specific spectral reordering can close the 25.5pp
admissibility gap (Biological 53.2% vs Astro 27.7%).

**Approach:** Per-section 50x50 transition matrices → section-specific Fiedler
reorderings → route each line through its section's ordering.

- [x] **1.1:** Created `scripts/phase14_machine/run_14y_section_lattice.py`
- [x] **1.2:** Ran section-aware routing experiment
- [x] **1.3:** Analyzed results

**Outcome: NULL RESULT.** Section-specific reordering **hurts** global
admissibility by -8.0pp (43.4% → 35.5%). No individual section improved except
Herbal B (+0.9pp, within noise).

| Section | Global Ordering | Section Ordering | Delta |
|:---|---:|---:|---:|
| Stars (10,096 tok) | 41.8% | 35.2% | -6.6pp |
| Herbal A (8,664 tok) | 37.0% | 32.9% | -4.1pp |
| Biological (6,012 tok) | 56.9% | 56.8% | -0.0pp |
| Pharma (2,836 tok) | 50.3% | 45.2% | -5.1pp |
| Astro (2,665 tok) | 29.8% | 20.9% | -9.0pp |
| Cosmo (1,422 tok) | 58.2% | 51.9% | -6.3pp |
| Herbal B (1,157 tok) | 31.9% | 32.8% | +0.9pp |

**Interpretation:** The scribe uses the same traversal pattern across all
sections. The 25.5pp section gap is driven by vocabulary distribution (sections
with more common tokens concentrated in fewer windows score higher), not by
different tool configurations per section. This rules out "section-specific tool
settings" as an explanation for section variation.

**Artifact:** `results/data/phase14_machine/section_lattice.json`

---

## Sprint 2: Emulator Upgrade — Full-Range Mask States

**Goal:** Fix the 12-state mask limitation in the emulator to match empirical
finding that 48 of 50 mask offsets are used.

- [x] **2.1:** Updated `src/phase14_machine/high_fidelity_emulator.py`:
  - `set_mask()`: `state % 12` → `state % self.num_windows`
  - `generate_mirror_corpus()`: `randint(0, 11)` → `randint(0, self.num_windows - 1)`
- [x] **2.2:** Re-ran `run_14c_mirror_corpus.py`
- [x] **2.3:** Re-ran `run_14h_baseline_showdown.py`

**Outcome:** Mirror corpus entropy fit stable at **87.61%** (was 87.60%).
Minimal impact — both 12-state and 50-state uniform sampling produce similar
diversity because even 12 states cover enough of the window space for the
generation process. The fix is architecturally correct (emulator now matches
empirical data) even though metrics barely moved.

---

## Sprint 3: Hybrid Copy-Reset + Lattice Model

**Goal:** Build a hybrid model that combines Copy-Reset's within-line repetition
capture with the Lattice's cross-section structural signal.

**Approach:** Probability mixture model:
```
P(w) = p_copy * P_copy(w) + p_lattice * P_lattice(w) + p_emit * P_unigram(w)
```

- [x] **3.1:** Added `hybrid_cr_lattice_mdl()` to `run_14h_baseline_showdown.py`
  - First attempt (sequential cost model): 15.9975 BPT — WORSE than lattice
    (sequential approach steals cheap tokens from lattice accounting)
  - Second attempt (probability mixture): **15.4920 BPT** — properly improves
    over lattice
- [x] **3.2:** Ran comparison

**Outcome: PARTIAL SUCCESS.** The hybrid improves L(data|model) by 8K bits
(381K vs 390K for pure lattice), confirming that Copy-Reset's repetition signal
and the Lattice's structural signal are **complementary**. However, the 154K
model cost (encoding 7,717 window assignments) dominates, so the hybrid (15.49
BPT) still cannot beat Copy-Reset's minimal 2-parameter model (10.90 BPT).

| Model | L(model) | L(data\|model) | L(total) | BPT |
|:---|---:|---:|---:|---:|
| **Copy-Reset** | **20** | **377,229** | **377,249** | **10.90** |
| Hybrid (CR+Lattice) | 154,380 | 381,719 | 536,099 | 15.49 |
| Lattice (Ours) | 154,340 | 389,950 | 544,290 | 15.73 |
| Table-Grille | 238,090 | 405,146 | 643,236 | 18.59 |
| Markov-O2 | 250,400 | 431,676 | 682,076 | 19.71 |

**Key insight:** The Lattice's value is not parsimony — it's **holdout
generalization** (10.81% vs Copy-Reset's 3.71% across sections). The hybrid
preserves this while slightly improving absolute fit.

---

## Sprint 4: Update Reports & Governance

- [x] **4.1:** Updated `CANONICAL_EVALUATION.md`:
  - Section 5: Added Hybrid row to MDL baseline table
  - Section 9: Updated mask inference to reflect emulator fix
  - Added Section 11: Section-Aware Routing (Null Result)
  - Updated Section 12 (Formal Conclusion) with synthesis
- [x] **4.2:** Updated `governance/claim_artifact_map.md`:
  - Added Claim 62d: Hybrid BPT 15.49
  - Added Claim 62e: Section-aware routing null result -8.0pp
  - Verification count: 66 → 68
- [x] **4.3:** Tests — 851/851 pass
- [x] **4.4:** Lint — clean on all changed files

---

## Verification Summary

| Criterion | Expected | Actual | Status |
|:---|:---|:---|:---|
| Section-aware > 43.44% globally | Improvement | -8.0pp (NULL) | Informative null |
| Hybrid BPT < 15.73 | < 15.73 | 15.49 | PASS |
| Mirror entropy fit ≥ 87.6% | ≥ 87.6% | 87.61% | PASS |
| Tests pass | 851 | 851 | PASS |
| Lint clean | 0 errors | 0 errors | PASS |
| ZL documented in governance | Present | 4 files | PASS |

---

## Files Summary

**New files:**
- `scripts/phase14_machine/run_14y_section_lattice.py`

**Modified files:**
- `governance/methods_reference.md` (Sprint 0: Section 0 added)
- `governance/config_reference.md` (Sprint 0: Transcription Source section)
- `ARCHITECTURE.md` (Sprint 0: Key Design Decision #6)
- `README.md` (Sprint 0: transcription standard note)
- `src/phase14_machine/high_fidelity_emulator.py` (Sprint 2: full-range mask)
- `scripts/phase14_machine/run_14h_baseline_showdown.py` (Sprint 3: hybrid MDL)
- `results/reports/phase14_machine/CANONICAL_EVALUATION.md` (Sprint 4)
- `governance/claim_artifact_map.md` (Sprint 4)

**Generated/regenerated artifacts:**
- `results/data/phase14_machine/section_lattice.json` (new)
- `results/data/phase14_machine/mirror_corpus_validation.json` (re-run)
- `results/data/phase14_machine/baseline_comparison.json` (re-run)

**PHASE 14F COMPLETE.**
