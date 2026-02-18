# Phase 10 Results

Generated: 2026-02-18T13:15:44.034118+00:00
Aggregate class: **mixed_results_tension**
Closure status: **in_tension**

## Method Outcomes

- Method H: `closure_strengthened`
- Method J: `closure_weakened`
- Method K: `closure_weakened`
- Method G: `indeterminate`
- Method I: `closure_strengthened`
- Method F: `indeterminate`

## Aggregate Interpretation

- Baseline closure statement: `structurally indistinguishable under tested methods`
- Aggregate reason: Results are mixed across methods; closure is neither defeated nor upgradable and must be stated with explicit tensions.
- Mixed-results rule applied: no by-fiat resolution; tensions are recorded explicitly.

## Urgent Designation Meaning

- Priority gate: `urgent`
- Gate reason: Method F is prioritized because Stage 1/2 includes non-strengthening signals (weakened or indeterminate outcomes).
- Meaning: Urgent is a scheduling/compute-priority designation for Method F. It means Stage 1/2 had at least one non-strengthening signal and deep reverse search should not be deferred. It is not itself evidence that closure is defeated.
- Trigger rule: Rule trigger: urgent when not (G and I both closure_strengthened) or when Stage 1 contains closure_weakened findings.

## Stage 5 High-ROI Addendum (2026-02-18)

- Run ID: `5f85586d-01fc-30c0-61f8-0f34e003c82a`
- Method F robustness gate: `pass=True` across `12` confirmatory runs (`0` weakened-family runs, `0` stable-natural violations).
- Method J strict gate (stays weakened): `True`
- Method K strict gate (stays weakened): `False`
- Resolution class: `partial_resolution_inconclusive`
- Upgrade rule satisfied: `False`

## Stage 5b K Adjudication Addendum (2026-02-18)

- Run ID: `6c7b700e-f2f5-0988-1f2c-7975d8014d77`
- Focal-depth check (seed 77, 300 runs): `pass=True` (`decision=closure_weakened`, correlation `0.4114`).
- Seed-band check (8 seeds, 150 runs each): `pass_rate=0.875` against threshold `0.750`.
- Final adjudication: Method K `closure_weakened_supported`.
- Interpretation: the strict 3-seed Stage 5 miss was a narrow-threshold instability; broader registered adjudication retained K as weakened.

## Artifacts

- Stage 4 synthesis artifact: `results/data/phase10_admissibility/stage4_synthesis.json`
- Stage 4 status tracker: `results/data/phase10_admissibility/stage4_execution_status.json`
- Stage 1 summary: `results/data/phase10_admissibility/stage1_summary.json`
- Stage 1b replication: `results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json`
- Stage 2 summary: `results/data/phase10_admissibility/stage2_summary.json`
- Stage 3 summary: `results/data/phase10_admissibility/stage3_summary.json`
- Stage 5 Method F matrix: `results/data/phase10_admissibility/stage5_method_f_matrix.json`
- Stage 5 J/K strict recalibration: `results/data/phase10_admissibility/stage5_jk_recalibration.json`
- Stage 5 summary: `results/data/phase10_admissibility/stage5_high_roi_summary.json`
- Stage 5 report: `results/reports/phase10_admissibility/PHASE_10_STAGE5_HIGH_ROI.md`
- Stage 5b K adjudication summary: `results/data/phase10_admissibility/stage5b_k_adjudication_summary.json`
- Stage 5b K adjudication report: `results/reports/phase10_admissibility/PHASE_10_STAGE5B_K_ADJUDICATION.md`
