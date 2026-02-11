# SK-H3.4 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_H3_4_EXECUTION_PLAN.md`  
Assessment Source: `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## Purpose

This register binds SK-H3 public language to deterministic closure lanes so available-subset evidence cannot be promoted to full-dataset closure claims.

## Lane-Bound Taxonomy

| Lane | Preconditions | Allowed Claims | Disallowed Claims |
|---|---|---|---|
| `H3_4_ALIGNED` | full dataset available, no blocking data-availability reason, lane parity checks pass | "Control comparability is conclusive at full-dataset scope." | Any statement that still frames results as data-availability blocked. |
| `H3_4_QUALIFIED` | approved irrecoverable missing pages, `DATA_AVAILABILITY`, `evidence_scope=available_subset`, `full_data_closure_eligible=false` | "Full-dataset control comparability remains blocked by irrecoverable source gaps; available-subset evidence is bounded and non-conclusive." | Any statement claiming full-dataset closure, full-data eligibility, or absence of unresolved comparability constraints. |
| `H3_4_BLOCKED` | semantic/freshness/parity mismatch | "SK-H3 remains unresolved due governance inconsistency." | Any claim of closure quality (`ALIGNED` or `QUALIFIED`). |
| `H3_4_INCONCLUSIVE` | insufficient evidence for lane assignment | "SK-H3 status is provisional pending complete evidence." | Any conclusive control-comparability claim. |

## Required Artifact Anchors Before Claims

Before publishing SK-H3 claims, confirm all anchors:

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `results.h3_4_closure_lane`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `results.evidence_scope`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `results.full_data_closure_eligible`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `results.full_data_feasibility`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `results.full_data_closure_terminal_reason`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` -> matching parity fields
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` -> `results.irrecoverability.classification`

## Canonical Lane for Current Cycle

Current evidence-based lane:

- `H3_4_QUALIFIED`

Current bounded claim:

- "Full-dataset closure remains blocked by approved irrecoverable missing pages; available-subset comparability evidence is qualified and non-conclusive."

## Reopen Conditions

This claim boundary can be upgraded only if at least one objective trigger is satisfied:

- new primary source pages are added and strict preflight no longer reports approved-lost blocking pages, or
- approved-lost classification policy is updated with materially new external evidence and artifacts are regenerated under the updated policy.
