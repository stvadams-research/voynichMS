# Phase 19 Convergence Report

Generated: 2026-02-22T04:05:10.448157+00:00

## Outcome

- Best holdout method: `hybrid_oracle_selector`
- Baseline holdout composite: 0.2548
- Best holdout composite: 0.2570
- Absolute gain: +0.0023

## Holdout Ranking (Composite Mean)

| Rank | Method | Composite Mean |
|---|---|---:|
| 1 | hybrid_oracle_selector | 0.2570 |
| 2 | unigram_window_control | 0.2569 |
| 3 | retrieval_edit | 0.2563 |
| 4 | line_conditioned_decoder | 0.2559 |
| 5 | phase18_baseline | 0.2548 |

## Claim Discipline

- Improvements in this phase are lexical/structural alignment gains only.
- No semantic decipherment claim is made.
- Residual mismatch remains and is explicitly tracked in alignment metrics.

## Artifacts

- `results/data/phase19_alignment/alignment_eval.json`
- `results/reports/phase19_alignment/BASELINE_ALIGNMENT_REPORT.md`
- `results/data/phase19_alignment/line_conditioned_decoder.json`
- `results/data/phase19_alignment/retrieval_edit.json`
