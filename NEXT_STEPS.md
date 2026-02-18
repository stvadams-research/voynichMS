# Next Steps: Post-Phase-10 Priorities

Phase 10 is complete through Stage 4 synthesis.

Current aggregate state:
- `mixed_results_tension`
- closure status: `in_tension`
- strengthened: H, I
- weakened: J, K
- indeterminate: G, F

This list captures the highest-value follow-up work from that state.

## 1. Resolve Closure Tension (Highest Priority)

### A. Tighten Method J/K adjudication
- Add stricter preregistered thresholds for what qualifies as a stable weakened signal.
- Re-run J/K under independent null families and external corpora controls.
- Add a unified report lane that compares J/K weakened signals against F indeterminate outcomes.

### B. Expand Method F search diagnostics
- Add secondary stability criteria beyond perturbation pass-rate (e.g., cross-seed parameter neighborhoods).
- Add explicit negative controls where reverse decoders run on synthetic generator corpora.
- Track whether outlier classes recur across seeds and token windows.

## 2. Publication and Reproducibility

### A. Keep final Phase 10 reports canonical
- Use:
  - `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
  - `results/reports/phase10_admissibility/PHASE_10_CLOSURE_UPDATE.md`
- Ensure any summary elsewhere cites these two files directly.

### B. Add Phase 10 smoke-test path in CI
- Add a reduced Stage 2/3/4 smoke profile to validate pipeline contracts on PRs.
- Keep full-size Phase 10 runs as manual/overnight jobs.

## 3. Tooling and Data Hygiene

### A. Corpus expansion reproducibility
- Keep `tools/download_corpora.py` as the machine-only corpus-expansion path.
- Preserve checkpoint artifact:
  - `results/data/phase10_admissibility/corpus_expansion_status.json`

### B. Documentation synchronization
- Update top-level docs whenever Phase 10 status changes:
  - `README.md`
  - `governance/runbook.md`
  - `planning/phase10_admissibility/phase_10_execution_plan.md`
