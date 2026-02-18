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

## Artifacts

- Stage 4 synthesis artifact: `results/data/phase10_admissibility/stage4_synthesis.json`
- Stage 4 status tracker: `results/data/phase10_admissibility/stage4_execution_status.json`
- Stage 1 summary: `results/data/phase10_admissibility/stage1_summary.json`
- Stage 1b replication: `results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json`
- Stage 2 summary: `results/data/phase10_admissibility/stage2_summary.json`
- Stage 3 summary: `results/data/phase10_admissibility/stage3_summary.json`
