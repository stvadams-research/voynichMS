# Phase 14H: Lattice Foundation Strengthening

**Date:** 2026-02-21
**Status:** IN PROGRESS

## Context

The lattice model explains 43.44% of token transitions (strict ±1 drift). The single largest unexplained category is "wrong window" (dist 2-10) at **42.45% (14,690 tokens)** — larger than the admissible category itself. STATUS.md Section 8 lists 6 open questions. Three are high-ROI to close now, before further convergence work (Phase 19 achieved only +0.15pp over baseline, confirming the foundation needs strengthening first).

This is **analytical/model validation work**, not data consistency. It belongs under Phase 14 as the next sub-phase (14H).

---

## Sprint 1: Failure Taxonomy Deep-Dive (Highest ROI)

**Script:** `scripts/phase14_machine/run_14z4_failure_taxonomy.py`
**Output:** `results/data/phase14_machine/failure_taxonomy.json`

Build a complete per-token failure record for all 34,605 tokens. The current `failure_diagnosis.json` has only per-section aggregates. `noise_register.json` has per-token records but caps at 1,000 entries and lacks distance measurements.

### Tasks

**1.1 Per-token record generation**
Extend `run_14v_failure_diagnosis.py` distance loop (lines 169-198) to emit a record for every token:
- `word`, `folio_id`, `line_index`, `token_position`, `section`, `hand`
- `actual_distance` (to nearest window containing the word)
- `category` (admissible / extended_drift / wrong_window / extreme_jump / not_in_palette)
- `prev_word`, `next_word`

Use `load_lines_with_metadata()` from `run_14x_mask_inference.py` for folio metadata.

**1.2 Mask-recoverability cross-reference**
Load per-line oracle offsets from `mask_inference.json` → `line_schedule`. For each wrong-window token, re-score using `score_line_with_offset()` with the oracle offset. Add `admissible_under_oracle` (bool) and `oracle_offset` (int) fields.

**1.3 Distance distribution analysis**
Histogram of distances within 2-10 range. Test for bimodality (Hartigan's dip test or KDE inspection). Smooth = random drift; bimodal = two distinct mechanisms.

**1.4 Bigram-predictable drift**
Compute `H(actual_distance | prev_word)` vs `H(actual_distance)`. Information gain pattern from `run_15d_selection_drivers.py`.

**1.5 Consistent offset families**
Group wrong-window tokens by signed distance. If specific offsets dominate (e.g., always +3), suggests additional mask states.

**1.6 Cross-transcription noise check**
For each wrong-window token position in ZL, check if same position fails in VT/IT/RF. Uses `load_canonical_lines(store, source_id=...)`. Fails only in ZL = likely transcription artifact. Fails in all = structural.

**1.7 Section-correlated failure patterns**
Per-section distance histograms. Do low-admissibility sections (Astro 27.7%) show different failure profiles than high ones (Biological 53.2%)?

### Reuse
- `score_line_with_offset()`: `run_14x_mask_inference.py:68`
- `load_lines_with_metadata()`: `run_14x_mask_inference.py` (extended in Phase 18)
- `load_palette()`: `run_14x_mask_inference.py:47`
- `SECTIONS`, `get_section()`, `get_hand()`: `run_14x_mask_inference.py:52-83`
- `measure_admissibility()`: `run_14z3_cross_transcription.py:52`
- `ProvenanceWriter.save_results()`: `src/phase1_foundation/core/provenance.py`

### Acceptance
- Per-token JSON with all 34,605 records and all fields
- Mask-recoverable count and percentage of wrong-window tokens
- Distance histogram with bimodality test
- Information gain of bigram context on drift distance
- Cross-transcription agreement rate (structural vs noise)
- Per-section distance distributions

---

## Sprint 2: Multi-Split Holdout Validation

**Script:** `scripts/phase14_machine/run_14z5_multisplit_holdout.py`
**Output:** `results/data/phase14_machine/multisplit_holdout.json`

### Tasks

**2.1 Seven leave-one-section-out splits**
For each of 7 sections: train lattice on remaining 6 via `GlobalPaletteSolver`, test on held-out section. Report admissibility (strict + drift), z-score, and chance baseline.

Pattern: `run_14g_holdout_validation.py` (single split) → generalize to all 7.

**2.2 Copy-Reset comparison per split**
Build Copy-Reset model on training lines per `run_14u_copyreset_holdout.py`. Score on held-out section. Report admissibility and z-score.

**2.3 Summary table**
7 rows (one per held-out section). Columns: section, train_tokens, test_tokens, lattice_drift_adm, lattice_z, copyreset_adm, copyreset_z, lattice_wins.

Aggregate: mean z-score, # splits where lattice beats Copy-Reset.

### Reuse
- `get_section_lines()`: `run_14g_holdout_validation.py:42-91`
- `binomial_z_score()`: `run_14g_holdout_validation.py:94-101`
- `GlobalPaletteSolver`: `src/phase14_machine/palette_solver.py`
- `build_copy_reset_model()`: `run_14u_copyreset_holdout.py:108-133`

### Acceptance
- All 7 splits produce valid z-scores
- Lattice z > 3σ in at least 5 of 7 splits
- Small sections (Cosmo, Herbal B) flagged if degenerate
- JSON artifact with full provenance

### Risk
Cosmo (1,727 tokens, 2 folios) and Herbal B (1,164 tokens) are small test sets. Results may have wide CIs. Flag but do not exclude.

---

## Sprint 3: MDL Elbow Analysis

**Script:** `scripts/phase14_machine/run_14z6_mdl_elbow.py`
**Output:** `results/data/phase14_machine/mdl_elbow.json`

### Tasks

**3.1 Dense sweep with corrected MDL**
Use frequency-conditional L(model) from `run_14z_lattice_compression.py` (not the double-counted original). Sweep at 20 K values: [2, 3, 5, 7, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60, 75, 100, 150, 200, 350, 500].

For each K: train via `GlobalPaletteSolver` (solve once, re-cluster at each K), compute corrected L(model) + L(data|model), compute admissibility.

**3.2 Knee-point detection**
Two methods: second-derivative of L(total) vs K, and Kneedle algorithm. Report optimal K.

**3.3 Penalty quantification**
`L_total(K=50) - L_total(K=optimal)` in bits and BPT delta. If penalty is small (<0.5 BPT), K=50 is justified. If large, flag for STATUS.md update.

**3.4 Admissibility-at-optimum**
Report admissibility at optimal K vs K=50. Document the tradeoff (fewer windows = higher admissibility but less specific model).

### Reuse
- `GlobalPaletteSolver`: `src/phase14_machine/palette_solver.py`
- `entropy()` helper: `run_14z_lattice_compression.py:52-62`
- Frequency bucketing pattern: `run_14z_lattice_compression.py:272-307`
- `EvaluationEngine.calculate_admissibility()`: `src/phase14_machine/evaluation_engine.py:44-142`

### Acceptance
- 20-point sweep with corrected MDL
- Knee-point from two independent methods
- K=50 penalty quantified
- If optimal K ≠ 50 by >20%, flag prominently

---

## Sprint 4: CI Cleanup + Governance Updates

### Tasks

**4.1 Fix remaining ruff errors**
Run `ruff check . --fix`, then manually review any remaining. Verify `ruff check .` returns 0.

**4.2 Update CANONICAL_EVALUATION.md**
Add Sections 17-19 for Sprint 1-3 results (failure taxonomy, multi-split holdout, MDL elbow). Update Section 16 conclusion.

**4.3 Update STATUS.md**
Close 3 open questions in Section 8: minimality, failure taxonomy, holdout robustness. Update Section 10 "where you stand."

**4.4 Update claim_artifact_map.md**
Add claims 80+ for Phase 14H findings. Update verification count.

---

## Dependency Graph

```
Sprint 1 (Failure Taxonomy) ──────┐
Sprint 2 (Multi-Split Holdout) ───┤── Sprint 4 (Governance)
Sprint 3 (MDL Elbow) ─────────────┘
```

Sprints 1, 2, 3 are **fully independent** and can execute in parallel.
Sprint 4 depends on all three completing.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| 1 | `scripts/phase14_machine/run_14z4_failure_taxonomy.py` | Script |
| 1 | `results/data/phase14_machine/failure_taxonomy.json` | Artifact |
| 2 | `scripts/phase14_machine/run_14z5_multisplit_holdout.py` | Script |
| 2 | `results/data/phase14_machine/multisplit_holdout.json` | Artifact |
| 3 | `scripts/phase14_machine/run_14z6_mdl_elbow.py` | Script |
| 3 | `results/data/phase14_machine/mdl_elbow.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| 4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add Sections 17-19 |
| 4 | `STATUS.md` | Close 3 open questions, update framing |
| 4 | `governance/claim_artifact_map.md` | Add claims 80+ |

## Verification

After all sprints:
1. `ruff check .` returns 0 errors
2. `python -m pytest tests/` — all tests pass
3. All 3 new JSON artifacts exist with valid provenance headers
4. STATUS.md Section 8 has 3 fewer open questions
5. Run each new script independently to confirm reproducibility
