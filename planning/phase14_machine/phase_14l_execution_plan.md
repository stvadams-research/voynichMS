# Phase 14L: Residual Characterization

**Date:** 2026-02-21
**Status:** COMPLETE (2026-02-21)
**Depends on:** Phase 14I (per-window offset corrections), Phase 14H (failure taxonomy)

## Execution Progress

- [x] Sprint 1 positional analysis (2026-02-21)
- [x] Sprint 2 lexical analysis (2026-02-21)
- [x] Sprint 3 diagnostic synthesis (2026-02-21)
- [x] Sprint 4 governance updates (2026-02-21)

### Key Results

**Overall:** 29,460 transitions scored, 11,760 failures (39.9% failure rate).

**Frequency tier is THE dominant factor:**

| Tier | Total | Failures | Rate |
|:---|---:|---:|---:|
| Common (>100 occ.) | 11,634 | 798 | 6.9% |
| Medium (10-100) | 8,683 | 3,050 | 35.1% |
| Rare (<10) | 7,761 | 6,561 | 84.5% |
| Hapax (1 occ.) | 1,382 | 1,351 | 97.8% |

Low-frequency words account for **67.3% of all failures**.

**Secondary factors:**
- Section range: 17.0pp (Biological 32.4% → Astro 49.4%)
- Position gradient: 11.6pp (gentle)
- |Correction magnitude| vs failure: rho=0.43, p=0.002
- Burst clustering: mild (chi² p=0.004)
- Window size vs failure: null (rho=0.11, p=0.44)

**Diagnosis:** The residual is a sparse-data artifact, not a missing constraint family. ~30% potentially reducible (OOV + section corrections); ~70% is irreducible frequency effect.

**Governance:** CANONICAL_EVALUATION.md Section 25, STATUS.md Section 4+10 updated, claims #109-116 added.

## Motivation

After per-window offset correction, ~38% of token transitions remain unexplained. The failure taxonomy (Phase 14H) categorized these by distance but did not diagnose **why** specific tokens fail. Understanding the residual determines whether further modeling is productive or whether the remaining gap is fundamentally noise (transcription error, hapax legomena, irreducible randomness).

This phase asks: **what characterizes the tokens the model cannot reach?**

## Sprint 1: Positional and Sequential Analysis

**Script:** `scripts/phase14_machine/run_14zd_residual_characterization.py`
**Output:** `results/data/phase14_machine/residual_characterization.json`

### Tasks

**1.1 Position-within-line analysis**
For each token position (0, 1, 2, ..., up to max line length):
- Failure rate (corrected model)
- Compare to baseline failure rate
- Are line-initial or line-final tokens disproportionately failing?

**1.2 Sequential burst analysis**
Count consecutive failure runs (sequences of non-admissible tokens):
- Distribution of run lengths
- Expected run length under independence assumption
- Chi-squared test: are failures more clustered than random?
- If clustered: does burst position correlate with line position?

**1.3 Folio-level failure rates**
Per-folio failure rate. Are specific folios disproportionately responsible?
- Top 10 highest-failure folios
- Top 10 lowest-failure folios
- Correlation with folio properties (quire, section, hand)

**1.4 Line-length effect**
Failure rate vs line length (in tokens). Short lines may have different failure profiles than long lines.

### Reuse
- `load_lines_with_metadata()`: `run_14x_mask_inference.py`
- `load_palette()`: `run_14x_mask_inference.py`
- `SECTIONS`, `get_section()`: `run_14x_mask_inference.py`
- `signed_circular_offset()`: `run_14z7_bigram_transitions.py`
- `learn_offset_corrections()`: `run_14z8_bigram_conditioned.py`
- `GlobalPaletteSolver`: `src/phase14_machine/palette_solver.py`

### Acceptance
- Position-within-line failure curve (is it flat or structured?)
- Burst analysis with statistical test
- Folio-level failure map
- Clear answer: is the residual positionally structured or uniform?

---

## Sprint 2: Lexical Analysis

**Script:** Same as Sprint 1 (extended)

### Tasks

**2.1 Per-word failure rates**
For each word in the vocabulary:
- Count of times it appears as the "failing" token (not admissibly reached)
- Count of times it appears as the "predecessor" of a failing token
- Failure rate as target vs overall frequency
- Failure rate as predecessor vs overall frequency

**2.2 Top failure contributors**
- Top 50 words by absolute failure count (as target)
- Top 50 words by failure rate (as target, min 20 occurrences)
- Top 50 words as predecessor of failure
- Overlap analysis: are the same words failing and causing failures?

**2.3 Word-class analysis**
Group words by:
- Frequency tier (hapax, rare <10, medium 10-100, common >100)
- Suffix class (final character: -y, -n, -m, -l, etc.)
- Length (short ≤3, medium 4-5, long ≥6 characters)
Report failure rate by group. Does any word class dominate the residual?

**2.4 Window occupancy vs failure**
For each window:
- Number of words assigned
- Failure rate of words in that window
- Correlation between window size and failure rate
- Correlation between window mode offset and failure rate

### Acceptance
- Per-word failure table (full vocabulary)
- Top contributors identified
- Word-class failure profile (frequency, suffix, length)
- Window occupancy correlation

---

## Sprint 3: Diagnostic Synthesis

**Script:** Same as Sprint 1 (extended)

### Tasks

**3.1 Principal failure modes**
Synthesize Sprints 1-2 into a diagnostic taxonomy:
- **Positional failures**: Are they concentrated at specific line positions?
- **Lexical failures**: Are they driven by specific words or word classes?
- **Sequential failures**: Are they clustered in bursts?
- **Sectional failures**: Are they section-specific?

**3.2 Reducibility estimate**
Of the ~38% residual, estimate how much is:
- Transcription noise (cross-transcription disagreement from Phase 14H)
- Hapax/rare word effect (OOV + low-frequency tokens)
- Positional effect (if line-initial tokens are worse)
- Structurally irreducible (uniform, non-patterned)

**3.3 Recommendations**
Based on the diagnosis, recommend:
- Whether further lattice refinement is productive
- Whether the residual suggests a missing constraint family
- Whether the residual is consistent with transcription noise + randomness

### Acceptance
- Clear taxonomy of failure modes with quantified contributions
- Reducibility estimate (what fraction is noise vs signal?)
- Actionable recommendations

---

## Sprint 4: Governance Updates

### Tasks

**4.1 Update CANONICAL_EVALUATION.md**
Add Section for residual characterization.

**4.2 Update STATUS.md**
Update Section 4 (remaining gap) with diagnostic results. Update Section 10.

**4.3 Update claim_artifact_map.md**
Add claims for residual characterization findings.

---

## Dependency Graph

```
Sprint 1 (Positional) → Sprint 2 (Lexical) → Sprint 3 (Synthesis) → Sprint 4 (Governance)
                \              /
                 (can partially overlap)
```

Sprints 1 and 2 are conceptually independent but share a single script for efficiency. Sprint 3 synthesizes both.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1-3 | `scripts/phase14_machine/run_14zd_residual_characterization.py` | Script |
| 1-3 | `results/data/phase14_machine/residual_characterization.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add residual section |
| 4 | `STATUS.md` | Update gap diagnosis |
| 4 | `governance/claim_artifact_map.md` | Add claims |
