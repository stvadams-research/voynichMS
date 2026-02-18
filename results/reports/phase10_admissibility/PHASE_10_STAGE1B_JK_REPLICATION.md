# Phase 10 Stage 1b Replication (Methods J/K)

Generated: 2026-02-18T06:17:13.581241+00:00
Run ID: 90be725c-7807-2223-e4a5-39cbeef6bc8b
Seeds: [42, 77, 101]

## Multi-Seed Direction Consensus

- Method J consensus direction: `closure_weakened`
- Method K consensus direction: `closure_weakened`
- Method J gate pass: `True`
- Method K gate pass: `True`

## Method J Ablation Outcome

- Edge rules removed for ablation: `line_initial_tokens, paragraph_initial_tokens`
- Gate definition: stable |z| > threshold non-edge anomalies must remain under folio-order permutation stability

## Method K Robustness Outcome

- Requires consistent outlier sign across seeds, correlated residuals, and persistent hard-to-close language-ward residual features
- Correlation all-pass: `True`

## Upgrade Gate Summary

- Method J stays weakened: `True`
- Method K stays weakened: `True`
- Priority recommendation: `10.2_then_10.3`

## Artifacts

- Canonical replication artifact: `results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json`
- Status tracker: `results/data/phase10_admissibility/stage1b_jk_replication_status.json`
