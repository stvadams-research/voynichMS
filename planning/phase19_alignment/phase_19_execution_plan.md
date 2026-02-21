# Phase 19: Generated-to-Actual Convergence Plan

**Date:** 2026-02-21
**Status:** EXECUTED (2026-02-21)
**Scope:** Reduce the gap between folio-conditioned generated output and the actual folio text while preserving lattice validity and epistemic honesty.

## Execution Progress (2026-02-21)

- [x] P0 complete: benchmark manifest and scoring package implemented
- [x] P1 complete: frozen baseline report generated
- [x] P2 complete: line-conditioned constrained decoder implemented and evaluated
- [x] P3 complete: retrieval-plus-edit baseline and hybrid selector evaluated
- [x] P4 complete: workbench alignment diagnostics + docs + final convergence report generated

### Snapshot

- Holdout composite mean (`test` split):
- `phase18_baseline`: 0.2548
- `line_conditioned_decoder`: 0.2559
- `retrieval_edit`: 0.2563

---

## 1. Objective

Move from "structurally valid generation" to "measurably closer reconstruction" at the folio/line level.

Phase 19 is focused on one question:

> Given a folio id, how much can we improve generated-to-actual agreement without violating known lattice constraints or overstating what this means?

### 1.1 Priority Decision

There is no higher-ROI phase that must come first. The only required pre-work is measurement and normalization discipline, which is included as P0 tasks in this phase.

---

## 2. Baseline (Starting Point)

1. Phase 18 Page Generator is complete and operational in `tools/workbench/`.
2. Generation is folio-conditioned (schedule + line-count controls) and validator-compatible.
3. Current system optimizes structural admissibility, not lexical match to a specific folio.
4. Existing global metrics indicate structural capture is meaningful but incomplete:
   - strict admissibility around the current ~45-54% range depending on mask policy,
   - substantial residual mismatch remains.

**Implication:** We now need an explicit match objective and a reproducible evaluation harness.

---

## 3. Phase 19 Hard Gates

1. A frozen, reproducible folio-level benchmark and scorecard exists before model changes.
2. All model comparisons are done on holdout folios (no leakage).
3. At least one new method beats current Phase 18 generator baseline on primary match metrics while maintaining validator compatibility.
4. Reporting clearly distinguishes:
   - structural improvement,
   - lexical reconstruction improvement,
   - unresolved residual.

---

## 4. Deliverables

| ID | Deliverable | Path | Priority |
|---|---|---|---|
| D1 | Folio match benchmark manifest (train/val/test splits, line alignments, metadata) | `results/data/phase19_alignment/folio_match_benchmark.json` | P0 |
| D2 | Canonical scoring package (exact match, edit distance, n-gram divergence, marker/affix fidelity) | `scripts/phase19_alignment/score_alignment.py` | P0 |
| D3 | Frozen baseline report for current generator and simple controls | `results/reports/phase19_alignment/BASELINE_ALIGNMENT_REPORT.md` | P1 |
| D4 | Line-conditioned constrained decoder prototype | `scripts/phase19_alignment/run_19a_line_conditioned_decoder.py` | P2 |
| D5 | Retrieval-plus-edit baseline under lattice constraints | `scripts/phase19_alignment/run_19b_retrieval_edit.py` | P2 |
| D6 | Comparative evaluation artifact (all methods, all splits, confidence intervals) | `results/data/phase19_alignment/alignment_eval.json` | P3 |
| D7 | Workbench diagnostics extension for per-folio match scoring | `tools/workbench/js/views/page_generator_view.js` + docs | P3 |
| D8 | Final claim-safe phase report | `results/reports/phase19_alignment/PHASE19_CONVERGENCE_REPORT.md` | P3 |

---

## 5. ROI-Prioritized Execution Plan

## P0: Measurement Discipline First (Mandatory)

### P0.1 Define primary and secondary metrics

Primary metrics:
1. `ExactTokenRate` (position-aware exact token agreement).
2. `NormalizedEditDistance` (line-level and folio-level).
3. `AffixMarkerFidelity` (`<%>`, `<$>`, IVTFF marker class correctness).

Secondary metrics:
1. `NgramDivergence` (1/2/3-gram JS divergence).
2. `LineCountError`.
3. `ValidatorPassRate` (syntax and lattice modes).

### P0.2 Build benchmark splits and freeze them

1. Create deterministic train/val/test folio splits (by folio id, not by line).
2. Add section-balanced and stress splits (hard folios, sparse sections).
3. Save split manifest + hash to artifact.

### P0.3 Transliteration normalization bridge for scoring

1. Define canonical scoring-normalization rules (lossless where possible).
2. Separate rendering normalization from modeling normalization.
3. Add unit tests for all normalizer edge cases.

Acceptance:
1. Benchmark artifact versioned and hash-stable.
2. Same inputs always yield identical scores.
3. All methods will be scored through one shared evaluator.

---

## P1: Establish Strong Baselines

### P1.1 Current Phase 18 generator baseline

1. Run baseline on all splits with fixed seeds and parameter sweep.
2. Record best-achievable baseline frontier, not single-point cherry picks.

### P1.2 Non-trivial controls

1. Retrieval-only baseline (nearest historical lines by folio/section/line-index context).
2. N-gram language baseline under admissibility filtering.
3. Copy-reset style control for lexical overlap sanity checks.

Acceptance:
1. Baseline report includes confidence intervals and variance by section.
2. A single frozen "beat-this" baseline is defined for Phase 19 progression.

---

## P2: Constrained Model Improvements

### P2.1 Line-conditioned decoder

Condition generation on:
1. folio id / section / side,
2. line index and local line neighborhood,
3. schedule offset source,
4. marker/affix state,
5. short prior context.

### P2.2 Constrained decoding strategy

1. Replace pure sampling with beam search under lattice/IVTFF constraints.
2. Optimize directly for alignment score while enforcing validity constraints.

### P2.3 Calibration and uncertainty

1. Output top-k candidate lines/pages.
2. Score and select best candidate under frozen evaluator.

Acceptance:
1. Improvement over frozen baseline on holdout set in at least 2 primary metrics.
2. No regression >1.0pp in validator compatibility.

---

## P3: Hybrid Retrieval + Edit Path (High ROI)

### P3.1 Contextual retrieval

1. Retrieve candidate lines from matched context buckets.
2. Use section/marker/line-position priors to narrow candidates.

### P3.2 Lattice-constrained editing

1. Apply minimal edits to retrieved candidates subject to admissibility constraints.
2. Enforce marker/affix consistency rules.

### P3.3 Mixture-of-experts selector

1. Compare decoder and retrieval-edit outputs under the same scorecard.
2. Select best per-line/per-page candidate.

Acceptance:
1. Hybrid system beats both component methods on composite score.
2. Gains hold across at least 3 independent split seeds.

---

## P4: Integration, Reporting, and Claim Discipline

### P4.1 Workbench integration (analysis mode)

1. Add per-run match score panel (Generated vs Actual) in Page Generator.
2. Show score breakdown and uncertainty bands.
3. Keep generation and evaluation toggleable.

### P4.2 Documentation and governance

1. Add `tools/workbench/docs/phase19_alignment.md`.
2. Update claim map only for validated, reproducible gains.
3. Add explicit non-semantic interpretation guardrails.

Acceptance:
1. End-to-end reproducible command path exists.
2. Report includes both wins and unresolved residual categories.

---

## 6. Acceptance Matrix

| Gate | Pass Condition |
|---|---|
| G1 Benchmark Integrity | Split manifest is deterministic, versioned, and reused across all experiments |
| G2 Baseline Rigor | Phase 18 baseline + controls are published with CIs and section breakdown |
| G3 Holdout Improvement | At least one Phase 19 method beats frozen baseline on >=2 primary metrics on holdout folios |
| G4 Constraint Safety | Syntax/lattice validation remains stable (no material regression) |
| G5 Reproducibility | Re-running pipeline with same seed/splits reproduces same summary metrics |
| G6 Claim Discipline | Final report explicitly separates structural fit, lexical fit, and unexplained residual |

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Metric gaming | False sense of progress | Use multi-metric scorecard and publish full metric vector |
| Data leakage across lines/folios | Inflated results | Split by folio, lock manifest, audit leak checks |
| Overfitting sparse sections | Fragile gains | Section-balanced eval and hierarchical smoothing |
| Transliteration artifacts mistaken for model gains | Misleading improvement | Normalize before scoring; include affix/marker fidelity separately |
| Overclaiming "decoding" | Credibility loss | Explicit non-goals + claim review gate |

---

## 8. Non-Goals (Phase 19)

1. No claim of semantic decipherment.
2. No claim of exact historical reconstruction.
3. No replacement of the Phase 14/18 lattice foundation.
4. No publication-level conclusion that residual mismatch is solved unless metrics justify it.

---

## 9. Execution Order

```
P0 Measurement and benchmark freeze
  -> P1 Baseline and controls
    -> P2 Constrained decoder
    -> P3 Retrieval-edit hybrid (parallel with late P2)
      -> P4 Integration + report + claim governance
```

---

## 10. Exit Criteria

Phase 19 is complete when:

1. The project has a reproducible benchmark for generated-to-actual convergence.
2. At least one method materially improves holdout lexical/line-level match over the frozen Phase 18 baseline.
3. The final report states exactly what improved, what did not, and what remains unexplained.
