# SK-M2.5 Baseline Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_M2_5_EXECUTION_PLAN.md`  
Source assessment: `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`

## Pass-5 Finding Freeze

Assessment finding frozen for this remediation cycle:

- `SK-M2 (Medium): Comparative uncertainty remains bounded and explicitly inconclusive.`

## Canonical Baseline Snapshot

Source: `results/phase7_human/phase_7c_uncertainty.json`

- `status`: `INCONCLUSIVE_UNCERTAINTY`
- `reason_code`: `TOP2_IDENTITY_FLIP_DOMINANT`
- `m2_4_closure_lane`: `M2_4_BOUNDED`
- `m2_4_residual_reason`: `top2_identity_flip_rate_remains_dominant`
- `m2_5_closure_lane`: `M2_5_BOUNDED`
- `m2_5_residual_reason`: `top2_identity_flip_rate_remains_dominant`
- `nearest_neighbor`: `Lullian Wheels`
- `nearest_neighbor_stability`: `0.4565`
- `jackknife_nearest_neighbor_stability`: `0.8333`
- `rank_stability`: `0.4565`
- `nearest_neighbor_probability_margin`: `0.0670`
- `top2_gap.ci95_lower`: `0.0263`
- `top2_set_stability`: `0.5580`
- `top2_identity_flip_rate`: `0.4420`
- `m2_5_data_availability_linkage.missing_folio_blocking_claimed`: `false`
- `m2_5_data_availability_linkage.objective_comparative_validity_failure`: `false`

## Contradiction and Defect Classification

| ID | Observation | Classification | Current Disposition |
|---|---|---|---|
| M2.5-CX1 | Pass-4 artifact had `m2_4_residual_reason=null`. | Fixable SK-M2 contract defect | Resolved in producer + checker + gate scripts. |
| M2.5-CX2 | No deterministic `m2_5_*` lane/residual/reopen fields in canonical artifact. | Fixable SK-M2 contract defect | Resolved in producer + policy + checker + tests. |
| M2.5-CX3 | `TOP2_IDENTITY_FLIP_DOMINANT` persists (`top2_set_stability=0.558`, `rank_stability=0.4565`). | Non-fixable within current evidence and registered matrix policy | Explicitly bounded via `M2_5_BOUNDED`; reopen only on objective trigger changes. |
| M2.5-CX4 | Missing-folio objections repeatedly reused without comparative-validity linkage. | Non-fixable external constraint misuse (SK-H3 class) | Enforced non-blocking SK-M2 boundary unless objective linkage is present. |

## Blocker Taxonomy (Pass-5)

Fixable blockers remediated in this pass:

1. Null/ambiguous residual-reason contract for SK-M2 lanes.
2. Missing SK-M2.5 deterministic closure metadata.
3. Missing checker-level guard against unsupported folio-based SK-M2 blocking.
4. Missing SK-M2 dependency projection in release gate-health snapshot.

Non-fixable or out-of-scope blockers remaining:

1. Comparative instability itself (`TOP2_IDENTITY_FLIP_DOMINANT`) remains empirically present in canonical metrics.
2. SK-C1 release sensitivity evidence artifact remains absent (`core_status/core_audit/sensitivity_sweep_release.json`), causing release-path failures independent of SK-M2 semantics.
