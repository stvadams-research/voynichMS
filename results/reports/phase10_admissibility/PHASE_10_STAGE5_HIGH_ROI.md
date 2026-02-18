# Phase 10 Stage 5 High-ROI Confirmatory Results

Generated: 2026-02-18T14:27:55.565721+00:00
Run ID: 5f85586d-01fc-30c0-61f8-0f34e003c82a

## Gate Outcomes

- Method F robustness gate pass: `True`
- Method J strict gate pass (stays weakened): `True`
- Method K strict gate pass (stays weakened): `False`
- Resolution class: `partial_resolution_inconclusive`

## Method F Matrix

- Robustness runs completed: `12`
- Runs with weakened family decisions: `0`
- Runs violating stable-natural cap: `0`

## Resolution Rule

- Pre-registered rule: closure upgrade is only eligible if Method F passes and both Method J and Method K fail strict weakened-status gates.
- Rule satisfied: `False`
- Recommendation: `One weakened method persists; collect an independent adjudicating test family.`

## Artifacts

- Method F matrix artifact: `results/data/phase10_admissibility/stage5_method_f_matrix.json`
- J/K strict artifact: `results/data/phase10_admissibility/stage5_jk_recalibration.json`
- Stage 5 summary artifact: `results/data/phase10_admissibility/stage5_high_roi_summary.json`
- Status tracker: `results/data/phase10_admissibility/stage5_high_roi_status.json`

## Stage 5b Follow-On (2026-02-18)

- Trigger: Method K strict gate miss in this Stage 5 run.
- Follow-on run ID: `6c7b700e-f2f5-0988-1f2c-7975d8014d77`
- Focal-depth result (seed 77, runs 300): `closure_weakened` with correlation `0.4114`.
- Seed-band result (8 seeds, 150 runs each): pass rate `0.875` (threshold `0.750`).
- Method K adjudication outcome: `closure_weakened_supported`.
- Follow-on report: `results/reports/phase10_admissibility/PHASE_10_STAGE5B_K_ADJUDICATION.md`
