# Data Consistency & Gap Closure: Execution Plan

**Created:** 2026-02-21
**Scope:** Fix the data-layer inconsistency that undermines all Phase 12-17 results, restore the full palette, re-run the complete pipeline, and close the remaining methodological gaps.

---

## Problem Statement

Three interacting issues invalidate most current result files:

1. **Source inconsistency.** `run_14a` loads only Zandbergen-Landini (5,145 lines, 34,635 tokens, 9,840 clean unique). Every other script loads ALL 7 transcription sources (103,003 lines, 230,337 tokens, 38,800 unique). Scripts that validate the palette against "real data" are comparing a ZL-only model against a 7-source corpus.

2. **Sanitization inconsistency.** `run_14a` applies a `sanitize()` function that strips IVTFF markup (`<%>`, `<$>`, brackets, symbols). No other script does this. Tokens like `chotaiin<$>` in the validation data will never match `chotaiin` in the palette.

3. **Palette regression.** The last `run_14a` invocation omitted `--full`, dropping from ~7,711 mapped tokens to 1,986. The `replicate.py` master script also omits `--full`.

**Impact:** The reported 89% failure rate, 53.7% extreme jumps, and catastrophic trigram overgeneration are largely artifacts of data mismatch, not model weakness. Fixing this will produce dramatically different (and more honest) numbers.

---

## Sprint 1: Data Foundation (Centralize Source & Sanitization)

### 1.1 — Create shared data loading utility

**File:** `src/phase1_foundation/core/data_loading.py` (new)

Create a single canonical function that all scripts use:

```python
def load_canonical_lines(store, dataset_id="voynich_real",
                         source_id="zandbergen_landini",
                         sanitize=True) -> List[List[str]]:
    """Load tokenized lines from the canonical transcription source.

    All Phase 12+ scripts should use this function to ensure
    consistent data across the pipeline.
    """
```

This function:
- Calls `get_lines_from_store()` with `source_id`
- Applies the sanitization regex (moved from `run_14a`)
- Returns clean lines

**Also fix the sanitization regex itself:**
- Current regex leaves `:` artifacts (e.g., `lchoro:am`)
- Add `re.sub(r'[:\?]', '', t)` or handle `[o:a]` notation properly
- Document what the sanitization does and why

### 1.2 — Update all Phase 12-17 scripts to use `load_canonical_lines()`

**Scripts to update (19 total in Phase 12-14):**

| Script | Current Call | Change |
|--------|-------------|--------|
| `run_12a_slip_detection.py` | `get_lines_from_store(store, "voynich_real")` | `load_canonical_lines(store)` |
| `run_12e_prototype_validation.py` | same | same |
| `run_12f_skeptics_gate.py` | same | same |
| `run_14a_palette_solver.py` | has own sanitize() | use shared, remove local |
| `run_14b_state_discovery.py` | `get_lines_from_store(store, "voynich_real")` | `load_canonical_lines(store)` |
| `run_14c_mirror_corpus.py` | same | same |
| `run_14d_overgeneration_audit.py` | same | same |
| `run_14e_mdl_analysis.py` | same | same |
| `run_14f_noise_register.py` | same | same |
| `run_14h_baseline_showdown.py` | same | same |
| `run_14i_ablation_study.py` | same | same |
| `run_14j_sequence_audit.py` | same | same |
| `run_14l_canonical_metrics.py` | same | same |
| `run_14m_refined_mdl.py` | same | same |
| `run_14n_chance_calibration.py` | same | same |
| `run_14p_selection_bias.py` | same | same |
| `run_14q_residual_analysis.py` | same | same |
| `run_14r_minimality_sweep.py` | same | same |
| `run_14s_sectional_invariance.py` | same | same |

**Phase 15:**
| `run_15a_trace_instrumentation.py` | `get_lines_from_store(store, "voynich_real")` | `load_canonical_lines(store)` |

**Phase 13:**
| `export_slip_viz.py` | same | same |
| `run_final_fit_check.py` | same | same |

### 1.3 — Special case: `run_14g_holdout_validation.py`

This script queries by section (Herbal vs Biological) via direct SQLAlchemy. It needs its own section-aware variant of `load_canonical_lines()` that:
- Filters by `source_id="zandbergen_landini"`
- Applies sanitization
- Splits by folio range (Herbal: f1-f56, Biological: f75-f116)

Add a helper:
```python
def load_canonical_lines_by_section(store, section_folios, ...):
```

### 1.4 — Update `replicate.py`

```python
run_command("python3 scripts/phase14_machine/run_14a_palette_solver.py --full")
```

### 1.5 — Add unit test for data consistency

**File:** `tests/phase1_foundation/test_data_loading.py`

- Test that `load_canonical_lines()` returns only ZL tokens
- Test that sanitization removes all IVTFF markup
- Test that no tokens contain `<`, `>`, `[`, `]`, `{`, `}`, `*`, `$` after sanitization
- Test that colon notation (`[o:a]`) is handled correctly

---

## Sprint 2: Restore Full Palette & Re-run Pipeline

### 2.1 — Run 14a with --full

```bash
python scripts/phase14_machine/run_14a_palette_solver.py --full
```

Expected result: ~7,700+ tokens mapped (ZL clean vocabulary with --full).

### 2.2 — Re-run Phase 14 validation suite (14b-14o)

Run in order via replicate.py (now with --full). Expected impact:
- **Failure rate** should drop dramatically (from 89% to something much lower, since tokens now match)
- **Admissibility** should increase significantly
- **Entropy match** should improve
- **Overgeneration** trigram rate should improve

### 2.3 — Re-run Phase 14 extended analysis (14p-14t)

These depend on the palette and canonical data being consistent.

### 2.4 — Re-run Phase 15 (15a-15c)

The trace instrumentation (15a) loads lines and traces them through the lattice. With consistent data, the number of admissible decisions should change.

### 2.5 — Re-run Phase 16 (16a-16c)

Ergonomic costs and layout projection depend on the palette size.

### 2.6 — Re-run Phase 17 (17a-17b)

Bandwidth audit reads from 14P and 16B outputs.

### 2.7 — Verify run_id provenance

All result JSONs should now have valid `run_id` values (not `"none"`).

---

## Sprint 3: Close Methodological Gaps

### 3.1 — Copy-Reset holdout comparison

**New script:** `scripts/phase14_machine/run_14u_copyreset_holdout.py`

The baseline showdown (14h) shows Copy-Reset beats the Lattice on MDL (12.24 vs 14.50 BPT). The critical question: does Copy-Reset also generalize across sections?

Implementation:
1. Load Herbal section (training), Biological section (testing)
2. Build Copy-Reset model from Herbal: for each bigram (w1, w2), estimate P(w2 = w1) from training data
3. Measure "Copy-Reset admissibility" on Biological: what fraction of bigrams in test data are explained by the copy hypothesis?
4. Compare to Lattice holdout admissibility (currently 13.26% drift)
5. If Copy-Reset fails the holdout, the Lattice has unique generalization power despite worse MDL

### 3.2 — Formal slip permutation test

**New script:** `scripts/phase12_mechanical/run_12g_slip_permutation.py`

The 914 slips at "19.87x vs shuffle control" need a proper statistical test:
1. Load real manuscript lines
2. Count slips using existing detection logic
3. Run 10,000 permutations: shuffle line assignments (row index), re-run detection
4. Compute empirical p-value: fraction of permutations with >= observed slip count
5. Report p-value and 95% CI on slip rate

### 3.3 — Diagnose residual failures

**New script:** `scripts/phase14_machine/run_14v_failure_diagnosis.py`

After data consistency fixes, re-examine whatever failure rate remains:
1. Categorize failures by: (a) token not in palette at all, (b) token in palette but wrong window, (c) section/quire
2. Report per-section admissibility rates
3. Identify if failures cluster in specific manuscript regions
4. This tells us whether the lattice works everywhere or only in certain sections

### 3.4 — Trigram overgeneration analysis

After Sprint 2, re-examine the trigram unattested rate with consistent data. If it's still near 100%, investigate:
1. What fraction of real trigrams involve rare tokens (< 5 occurrences)?
2. Do the most common synthetic trigrams resemble real ones structurally?
3. Is the issue that trigrams are combinatorially sparse, or that the model's sequential behavior genuinely diverges?

If trigrams are just sparse (expected for 7,700+ vocabulary), the metric is uninformative and should be reframed. If they genuinely diverge, consider adding bigram transition weights to the emulator.

---

## Sprint 4: Reporting & Commit

### 4.1 — Update claim_artifact_map.md

Add/revise claims for:
- Data consistency methodology
- Corrected admissibility rates
- Corrected failure rates
- Copy-Reset holdout result
- Slip permutation p-value

### 4.2 — Update CANONICAL_EVALUATION.md

Regenerate with corrected numbers from the full pipeline run.

### 4.3 — Commit

Single commit covering:
- New `data_loading.py` utility
- All script updates for source consistency
- replicate.py --full fix
- New scripts (14u, 12g, 14v)
- All regenerated result JSONs
- Updated reports and claim map

---

## Execution Order

```
Sprint 1 (Data Foundation)
  1.1  Create load_canonical_lines()          [new file]
  1.2  Update 19 Phase 12-14 scripts          [mechanical edits]
  1.3  Update 14g holdout (section-aware)      [careful edit]
  1.4  Update replicate.py                     [one-line fix]
  1.5  Add data loading test                   [new test file]

Sprint 2 (Re-run Pipeline)
  2.1  Run 14a --full                          [~2 min]
  2.2  Run 14b-14o                             [~15 min total]
  2.3  Run 14p-14t                             [~5 min]
  2.4  Run 15a-15c                             [~3 min]
  2.5  Run 16a-16c                             [~2 min]
  2.6  Run 17a-17b                             [~1 min]
  2.7  Verify provenance                       [spot check]

Sprint 3 (Methodology)
  3.1  Copy-Reset holdout script               [new script + run]
  3.2  Slip permutation test                   [new script + run]
  3.3  Failure diagnosis                       [new script + run]
  3.4  Trigram analysis                         [analysis after Sprint 2]

Sprint 4 (Reporting)
  4.1  Update claim_artifact_map.md
  4.2  Regenerate CANONICAL_EVALUATION.md
  4.3  Commit
```

---

## Expected Outcome

After all sprints:
- **Every script** loads from the same canonical source (ZL) with the same sanitization
- **Full palette** (~7,700 tokens) used throughout
- **Failure rate** should drop from 89% to a meaningful number
- **Admissibility** should be significantly higher and interpretable
- **Copy-Reset holdout** answers "is the lattice uniquely explanatory?"
- **Slip p-value** is formally established
- **All results** have valid run_id provenance
- **The narrative** is grounded in consistent, reproducible data

---

## Risk: What If Results Get Worse?

With consistent data, some metrics might reveal uncomfortable truths:
- The lattice might explain a higher % of tokens but still have significant failures
- Copy-Reset might also pass the holdout (which would weaken the lattice's uniqueness claim)
- The 82% entropy fit might change

**This is fine.** Honest results on consistent data are infinitely more valuable than inflated results on mismatched data. Every number that changes is a number that was previously wrong.
