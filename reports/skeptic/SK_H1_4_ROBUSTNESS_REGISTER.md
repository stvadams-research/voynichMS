# SK-H1.4 Robustness Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_4_EXECUTION_PLAN.md`  
Assessment source: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## Baseline Freeze

Canonical artifact:

- `results/mechanism/anchor_coupling_confirmatory.json`

Baseline tuple (frozen):

- `run_id=ef7fffef-968d-30d6-f34d-f4efadff6f7e`
- `timestamp=2026-02-10T19:54:04.882999+00:00`
- `status=CONCLUSIVE_NO_COUPLING`
- `status_reason=adequacy_and_inference_support_no_coupling`
- `adequacy.pass=true`
- `inference.decision=NO_COUPLING`
- `h1_4_closure_lane=H1_4_QUALIFIED`
- `h1_4_residual_reason=registered_lane_fragility`

## Registered Robustness Matrix Snapshot

Source policy: `configs/skeptic/sk_h1_multimodal_policy.json`

- `matrix_id=SK_H1_4_MATRIX_2026-02-10`
- `matrix_version=2026-02-10-h1.4`
- `publication_lane_id=publication-default`
- `allowed_robustness_classes=[ROBUST, MIXED, FRAGILE]`

Canonical robustness summary:

- `robustness_class=MIXED`
- `expected_lane_count=3`
- `observed_lane_count=3`
- `conclusive_lane_count=1`
- `ambiguity_lane_count=1`
- `underpowered_lane_count=1`
- `blocked_lane_count=0`
- `agreement_ratio=0.333333`
- `matching_status_count=1`

## Lane Outcomes Considered

| Lane ID | Purpose | Run ID | Timestamp | Status | Status Reason |
|---|---|---|---|---|---|
| `publication-default` | canonical publication lane | `19609a70-a8b4-5b57-eaff-4f70c128acb5` | `2026-02-10T19:53:03.181292+00:00` | `CONCLUSIVE_NO_COUPLING` | `adequacy_and_inference_support_no_coupling` |
| `stability-probe-seed-2718` | seed robustness probe | `cd893dae-7211-fa59-02b5-99d7068a7f7e` | `2026-02-10T19:53:27.743213+00:00` | `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | `inferential_ambiguity` |
| `adequacy-floor` | adequacy floor probe | `869b6f8d-90d8-e75c-0269-ecd69c0c7b86` | `2026-02-10T19:53:54.097031+00:00` | `INCONCLUSIVE_UNDERPOWERED` | `adequacy_thresholds_not_met` |

Canonical publication artifact was restored after lane probes:

- `results/mechanism/anchor_coupling_confirmatory.json`
- `run_id=ef7fffef-968d-30d6-f34d-f4efadff6f7e`

## Residual Vectors and Controls

| Residual ID | Residual | Control | Verification Command |
|---|---|---|---|
| H1.4-R1 | Seed-lane fragility enables over-broad claim reuse. | Deterministic lane mapping (`H1_4_QUALIFIED` for canonical conclusive + mixed robustness). | `python3 scripts/skeptic/check_multimodal_coupling.py --mode release` |
| H1.4-R2 | Publication lane could be swapped post hoc. | Matrix publication lane pinning (`publication-default`) in policy + checker. | `python3 scripts/skeptic/check_multimodal_coupling.py --mode ci` |
| H1.4-R3 | Legacy runs can be misread as current-policy regression. | Legacy reconciliation index and explicit pre/post-hardening classification. | `rg -n "SK_H1_4_LEGACY_RECONCILIATION|H1_4_" reports/skeptic` |
| H1.4-R4 | Report wording can overstate robustness despite mixed matrix. | H1.4 lane-bound marker checks in status policy and checker. | `python3 scripts/skeptic/check_multimodal_coupling.py --mode release` |
| H1.4-R5 | SK-C1 release blockers can mask SK-H1 evidence in gate summaries. | Gate-health dependency snapshot includes multimodal H1.4 fields. | `python3 scripts/audit/build_release_gate_health_status.py` |

## Disconfirmability Triggers (Reopen Conditions)

The current H1.4 decision must be revisited only if at least one trigger occurs:

1. `registered lane matrix reaches robust class without inferential ambiguity`
2. `policy thresholds are revised with documented rationale and rerun evidence`

Absent those triggers, repeating the same assessment on unchanged evidence should not reopen SK-H1 as unresolved.
