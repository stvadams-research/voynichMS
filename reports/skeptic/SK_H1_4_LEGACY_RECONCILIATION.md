# SK-H1.4 Legacy Reconciliation

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_4_EXECUTION_PLAN.md`

## Purpose

Prevent pre-H1.4 by-run artifacts from being misinterpreted as regressions against current H1.4 semantics.

## By-Run Inventory Split

Source directory: `results/mechanism/by_run/`

- Total confirmatory by-run artifacts: `21`
- Pre-H1.4 artifacts (no `h1_4_closure_lane` / `robustness` block): `17`
- H1.4-governed artifacts (with lane + robustness fields): `4`

### Pre-H1.4 Status Distribution

| Status | Count |
|---|---:|
| `CONCLUSIVE_NO_COUPLING` | 8 |
| `INCONCLUSIVE_UNDERPOWERED` | 7 |
| `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | 1 |
| `BLOCKED_DATA_GEOMETRY` | 1 |

### H1.4 Artifact Set

| Run ID | Status | Status Reason | H1.4 Lane | Robustness Class |
|---|---|---|---|---|
| `19609a70-a8b4-5b57-eaff-4f70c128acb5` | `CONCLUSIVE_NO_COUPLING` | `adequacy_and_inference_support_no_coupling` | `H1_4_QUALIFIED` | `MIXED` |
| `cd893dae-7211-fa59-02b5-99d7068a7f7e` | `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | `inferential_ambiguity` | `H1_4_INCONCLUSIVE` | `MIXED` |
| `869b6f8d-90d8-e75c-0269-ecd69c0c7b86` | `INCONCLUSIVE_UNDERPOWERED` | `adequacy_thresholds_not_met` | `H1_4_INCONCLUSIVE` | `MIXED` |
| `ef7fffef-968d-30d6-f34d-f4efadff6f7e` | `CONCLUSIVE_NO_COUPLING` | `adequacy_and_inference_support_no_coupling` | `H1_4_QUALIFIED` | `MIXED` |

## Reconciliation Rules

1. Pre-H1.4 runs remain valid historical evidence, but they are not authoritative for H1.4 lane assignment.
2. Official SK-H1.4 classification must use artifacts that include both:
   - `results.h1_4_closure_lane`
   - `results.robustness`
3. Canonical publication claim for this cycle is bound to:
   - `results/mechanism/anchor_coupling_confirmatory.json`
   - `run_id=ef7fffef-968d-30d6-f34d-f4efadff6f7e`
4. Legacy runs can inform trend context, but cannot override current matrix policy and lane mapping.

## Operational Interpretation

- Historical heterogeneity is expected and documented.
- H1.4 does not erase prior runs; it adds deterministic semantics for present-tense claims.
- Reassessment should reference this register before classifying a repeated SK-H1 residual as a new semantic failure.
