# Phase 14M: Frequency-Stratified Lattice Refinement

**Date:** 2026-02-21
**Status:** COMPLETE (2026-02-21)
**Depends on:** Phase 14L (residual characterization), Phase 14I (offset corrections)

## Execution Progress

- [x] Sprint 1 frequency-weighted lattice built and evaluated (2026-02-21)
- [x] Sprint 2 tier-specific corrections (gate passed, negligible improvement) (2026-02-21)
- [x] Sprint 3 OOV recovery and consolidation (2026-02-21)
- [x] Sprint 4 governance updates (2026-02-21)

### Key Results

**The canonical lattice dominates all fresh builds.** The iteratively refined canonical lattice (64.4% corrected admissibility) vastly outperforms both fresh uniform (40.0%) and fresh frequency-weighted (40.8%) builds. The canonical lattice's advantage comes from its multi-phase optimization history, not edge weighting.

**Frequency weighting significantly improves fresh builds:**

| Metric | Uniform (fresh) | Freq-Weighted | Delta |
|:---|---:|---:|---:|
| CV mean corrected admissibility | 36.2% | **49.9%** | **+13.7pp** |
| All 7 folds positive | — | yes | — |

**Per-tier effects (full corpus, fresh builds):**

| Tier | Canonical | Uniform | Freq-Wt | FW-Uni Delta |
|:---|---:|---:|---:|---:|
| Common (>100) | **97.9%** | 65.0% | 46.0% | -19.1pp |
| Medium (10-100) | **76.8%** | 41.9% | 60.2% | **+18.3pp** |
| Rare (<10) | **34.2%** | 22.7% | 28.1% | +5.4pp |
| Hapax (=1) | 5.8% | 5.4% | 3.9% | -1.6pp |

Frequency weighting trades common-word performance for massive medium-tier gains (+18.3pp). The canonical lattice dominates ALL tiers — its iterative refinement captures frequency information implicitly.

**Sprint 2 results — negligible:**
- Tier-specific corrections: +0.1pp medium, +0.9pp rare (not meaningful)
- Weighted mode: -0.6pp vs plain mode (14/50 windows differ)
- Conclusion: correction learning is already frequency-optimal

**Sprint 3 results — OOV recovery is productive:**
- Suffix-based recovery: **72.2%** (1,418/1,964 OOV transitions)
- Nearest-neighbor recovery: 31.0% (608/1,964)
- Suffix recovery adds **+4.81pp** to consolidated rate
- Consolidated best model: 42.9% (freq-weighted + suffix OOV)

**Null hypothesis assessment:** The null hypothesis ("frequency weighting has no effect because the layout already captures frequency via edge density") is **REJECTED for fresh builds** (+13.7pp CV) but **CONFIRMED for the canonical lattice** (which already implicitly captures frequency through its iterative optimization history).

**Diagnosis:** The canonical lattice should remain the production model. Frequency weighting is valuable for cold-start lattice building but cannot replace iterative refinement. OOV suffix recovery (72.2%) is the one genuinely actionable finding — it could be integrated into the canonical pipeline for a +4.81pp gain.

## Motivation

Phase 14L proved that **vocabulary frequency is the dominant factor** in the ~40% residual: common words fail at 6.9%, medium at 35.1%, rare at 84.5%, hapax at 97.8%. Yet the entire pipeline — palette solver, offset corrections, evaluation — treats all tokens equally. Every transition edge weighs 1.0 regardless of whether it represents a common bigram (daiin→chedy, thousands of observations) or a hapax transition (one observation).

This phase tests whether frequency-aware modeling can close the gap, focusing on medium-frequency words (35.1% failure rate, 8,683 transitions) as the highest-ROI tier: enough data to optimize, enough failures to reduce.

**Null hypothesis:** Frequency weighting has no significant effect because the current lattice already optimally places common words by virtue of their edge density in the force-directed layout.

---

## Sprint 1: Frequency-Weighted Palette Solver

**Script:** `scripts/phase14_machine/run_14ze_frequency_lattice.py`
**Output:** `results/data/phase14_machine/frequency_lattice.json`

### Tasks

**1.1 Frequency-weighted edge construction**
Modify the palette solver's `ingest_data()` logic (without modifying the class itself — wrap externally):
- Count each (u, v) bigram pair's frequency in the corpus
- Weight transition edges by `log2(1 + bigram_count)` instead of uniform 1.0
- Slip edges remain at 10.0 (already high-confidence)
- Build graph with weighted edges, then solve/cluster/reorder as normal

**1.2 Frequency-stratified admissibility evaluation**
For each model variant, report admissibility broken down by frequency tier:
- Common (>100 occ.): target — maintain <10% failure
- Medium (10-100): target — reduce from 35.1%
- Rare (<10): informational only (insufficient data to optimize)
- Hapax: informational only

**1.3 A/B comparison: uniform vs frequency-weighted**
Generate both lattices from identical data. Compare:
- Overall admissibility (strict ±1)
- Per-tier admissibility
- Window composition changes (do frequent words cluster differently?)
- Token displacement (how many words change windows?)

**1.4 Frequency-weighted offset corrections**
Learn offset corrections on the frequency-weighted lattice. Compare:
- Corrected admissibility (uniform lattice + corrections) vs (freq lattice + corrections)
- Per-tier improvement

### Reuse
- `GlobalPaletteSolver`: `src/phase14_machine/palette_solver.py` (use externally, don't modify)
- `learn_offset_corrections()`: `run_14z8_bigram_conditioned.py`
- `score_with_correction()`: `run_14z8_bigram_conditioned.py`
- `load_palette()`, `load_lines_with_metadata()`: `run_14x_mask_inference.py`
- `signed_circular_offset()`: `run_14z7_bigram_transitions.py`

### Acceptance
- Per-tier admissibility table for both model variants
- Medium-tier improvement quantified (primary outcome metric)
- Clear A/B comparison with statistical test (binomial z-score for medium-tier)
- If medium-tier improves by <2pp: frequency weighting at the layout level is not productive

---

## Sprint 2: Frequency-Stratified Offset Corrections (Gated)

**Gate:** Sprint 1 must show that the frequency-weighted lattice changes window assignments for ≥10% of medium-frequency words. If the layout is effectively unchanged, this sprint is skipped (the layout already implicitly captures frequency via edge density).

**Script:** Same as Sprint 1 (extended)
**Output:** Same JSON (extended)

### Tasks

**2.1 Tier-specific offset corrections**
Instead of learning one global set of 50 corrections, learn separate corrections per frequency tier:
- Common tier: learn corrections from common-word transitions only
- Medium tier: learn corrections from medium-word transitions only
- Apply the appropriate correction based on the target word's tier
- Fallback: if a tier has <5 observations for a window, use the global correction

**2.2 Weighted mode estimation**
Replace the unweighted mode in `learn_offset_corrections()` with a frequency-weighted mode:
- For each window, compute offsets weighted by bigram frequency
- `weighted_mode = argmax(sum of bigram frequencies per offset value)`
- Compare: does weighted mode differ from unweighted mode?

**2.3 Cross-validated evaluation**
7-fold leave-one-section-out validation of:
- Global corrections (baseline, from Phase 14I)
- Frequency-weighted corrections (this sprint)
- Tier-specific corrections (this sprint)
Report mean delta and z-score per variant.

### Acceptance
- At least one frequency-aware correction variant improves cross-validated admissibility by ≥1pp
- Per-tier improvement table
- If no variant improves by ≥1pp: the offset learning is already frequency-optimal

---

## Sprint 3: OOV Recovery & Consolidated Evaluation

**Script:** Same as Sprint 1 (extended)
**Output:** Same JSON (extended)

### Tasks

**3.1 OOV window prediction via suffix mapping**
For the ~6.7% of failures from OOV tokens (not in palette):
- Build a suffix→window distribution from in-palette words
- For each OOV word, predict its window from the suffix class most common in that suffix's windows
- Score: how many previously-OOV transitions become admissible?

**3.2 Nearest-neighbor OOV recovery**
Alternative approach: for each OOV word, find the most similar in-palette word (edit distance ≤ 2) and inherit its window assignment.
- Score against suffix-based approach
- Report recovery rate

**3.3 Consolidated model evaluation**
Combine the best components from Sprints 1-3 into a single "best available" model:
- Best lattice variant (uniform or frequency-weighted)
- Best correction variant (global, weighted, or tier-specific)
- Best OOV recovery (suffix or nearest-neighbor)
- Report final admissibility by tier with full provenance

**3.4 Diminishing returns assessment**
Quantify: given 14L's diagnosis, how much of the residual is *theoretically* addressable?
- Upper bound: if all medium-tier failures are eliminated → overall improvement
- Practical bound: observed improvement from this phase
- Irreducible floor estimate

### Acceptance
- OOV recovery rate quantified
- Consolidated "best model" admissibility
- Clear statement: how much of the residual was recovered by frequency-aware modeling?
- Diminishing returns assessment with recommendation for further work

---

## Sprint 4: Governance Updates

### Tasks

**4.1 Update CANONICAL_EVALUATION.md**
Add Section 26: Frequency-Stratified Lattice Refinement.

**4.2 Update STATUS.md**
Update Section 4 (gap diagnosis) and Section 10 with Phase 14M results.

**4.3 Update claim_artifact_map.md**
Add claims for frequency-stratified findings.

**4.4 Update this execution plan**
Record actual results in the Execution Progress section.

---

## Dependency Graph

```
Sprint 1 (Frequency-Weighted Lattice) → Sprint 2 (Gated: Tier-Specific Corrections)
                                      ↘
                                        Sprint 3 (OOV Recovery + Consolidation) → Sprint 4 (Governance)
```

Sprint 2 depends on Sprint 1's gate. Sprint 3 can start after Sprint 1 (OOV recovery is independent of Sprint 2). Sprint 4 depends on all prior sprints.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1-3 | `scripts/phase14_machine/run_14ze_frequency_lattice.py` | Script |
| 1-3 | `results/data/phase14_machine/frequency_lattice.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add Section 26 |
| 4 | `STATUS.md` | Update gap diagnosis |
| 4 | `governance/claim_artifact_map.md` | Add claims |
