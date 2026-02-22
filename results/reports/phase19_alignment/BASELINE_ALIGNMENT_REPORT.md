# Phase 19 Baseline Alignment Report

Generated: 2026-02-22T04:05:10.448157+00:00

## Scope

Frozen baseline evaluation for Phase 18 page generation against holdout folios, with control comparisons.

## Holdout Split

- Test folios: 44
- Split hash: `4a4dcb9905962463b3fd67566066196e769381c44da5204588380c4c45c82b26`

## Test Metrics

| Method | Composite (mean) | Exact Token Rate (mean) | Normalized Edit Distance (mean) | Ngram JSD Avg (mean) |
|---|---:|---:|---:|---:|
| Phase18 Baseline | 0.2548 | 0.0000 | 0.9908 | 0.9856 |
| Unigram Window Control | 0.2569 | 0.0023 | 0.9881 | 0.9802 |

## Notes

- This report freezes baseline/control performance before Phase 19 method claims.
- Confidence intervals and per-folio rows are available in `alignment_eval.json`.
