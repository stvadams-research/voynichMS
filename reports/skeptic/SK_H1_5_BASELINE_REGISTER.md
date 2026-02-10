# SK-H1.5 Baseline Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_5_EXECUTION_PLAN.md`  
Assessment source: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`

## Baseline Freeze

Canonical artifact:

- `results/mechanism/anchor_coupling_confirmatory.json`

Frozen tuple:

- `run_id=a2c8da85-c0f5-874c-27d1-8455688f98a9`
- `timestamp=2026-02-10T21:46:19.944860+00:00`
- `status=CONCLUSIVE_NO_COUPLING`
- `status_reason=adequacy_and_inference_support_no_coupling`
- `h1_4_closure_lane=H1_4_QUALIFIED`
- `h1_4_residual_reason=registered_lane_fragility`
- `h1_5_closure_lane=H1_5_BOUNDED`
- `h1_5_residual_reason=diagnostic_lane_non_conclusive_bounded`

## Robustness Snapshot

- `robustness_class=MIXED`
- `entitlement_robustness_class=ROBUST`
- `agreement_ratio=0.333333`
- `entitlement_agreement_ratio=1.0`
- `expected_lane_count=3`
- `observed_lane_count=3`
- `expected_entitlement_lane_count=1`
- `observed_entitlement_lane_count=1`
- `observed_diagnostic_lane_count=1`
- `observed_stress_lane_count=1`
- `diagnostic_non_conclusive_lane_count=2`
- `robust_closure_reachable=true`
- `robust_closure_reachable_reason=entitlement_matrix_covered`

## Lane Outcomes (Registered Matrix)

| Lane ID | Lane Class | Purpose | Run ID | Status | Status Reason |
|---|---|---|---|---|---|
| `publication-default` | `entitlement` | canonical publication lane | `a2c8da85-c0f5-874c-27d1-8455688f98a9` | `CONCLUSIVE_NO_COUPLING` | `adequacy_and_inference_support_no_coupling` |
| `stability-probe-seed-2718` | `diagnostic` | seed robustness probe | `cd893dae-7211-fa59-02b5-99d7068a7f7e` | `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | `inferential_ambiguity` |
| `adequacy-floor` | `stress` | adequacy floor probe | `869b6f8d-90d8-e75c-0269-ecd69c0c7b86` | `INCONCLUSIVE_UNDERPOWERED` | `adequacy_thresholds_not_met` |

## Reopen Conditions

- H1.4 reopen conditions:
  - `registered lane matrix reaches robust class without inferential ambiguity`
  - `policy thresholds are revised with documented rationale and rerun evidence`
- H1.5 reopen conditions:
  - `entitlement lanes lose conclusive alignment under registered matrix`
  - `diagnostic/stress lanes introduce policy-incoherent contradiction`
  - `lane taxonomy or thresholds are revised with documented rationale and rerun evidence`
