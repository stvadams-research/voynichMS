# SK-H1.4 Claim Boundary Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_4_EXECUTION_PLAN.md`  
Assessment source: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## Purpose

Bind public SK-H1 language to deterministic H1.4 lane semantics so robustness-mixed outcomes cannot be narrated as fully robust closure.

## Lane-Bound Taxonomy

| Lane | Preconditions | Allowed Claim | Disallowed Claim |
|---|---|---|---|
| `H1_4_ALIGNED` | canonical lane conclusive + robustness class robust by matrix thresholds | "Multimodal no-coupling conclusion is robust across registered lanes." | Any statement that still frames robustness as mixed/fragile. |
| `H1_4_QUALIFIED` | canonical lane conclusive + robustness class mixed/fragile with complete controls | "Canonical no-coupling signal is present, but robustness remains qualified across registered lanes." | Any unqualified global no-coupling claim across all lanes. |
| `H1_4_BLOCKED` | lane/class/coherence mismatch across artifacts/checkers/reports | "SK-H1 remains unresolved due multimodal robustness governance inconsistency." | Any closure claim (`ALIGNED` or `QUALIFIED`). |
| `H1_4_INCONCLUSIVE` | incomplete evidence for lane assignment | "SK-H1.4 status is provisional pending complete robustness evidence." | Any conclusive claim. |

## Current Lane for This Cycle

Current canonical lane and class:

- `h1_4_closure_lane=H1_4_QUALIFIED`
- `robustness.robustness_class=MIXED`

Required qualifier phrase in report surfaces:

- "robustness remains qualified across registered lanes"

## Required Artifact Anchors Before Claims

1. `results/mechanism/anchor_coupling_confirmatory.json`:
   - `results.status`
   - `results.h1_4_closure_lane`
   - `results.h1_4_residual_reason`
   - `results.h1_4_reopen_conditions`
   - `results.robustness.robustness_class`
2. `configs/skeptic/sk_h1_multimodal_status_policy.json`:
   - lane/class allowed values
   - lane-scoped marker requirements
3. Report markers for qualified lane:
   - `results/reports/PHASE_5I_RESULTS.md`
   - `reports/human/PHASE_7B_RESULTS.md`

## Reopen Conditions

This boundary may be upgraded only if one trigger is met:

1. `registered lane matrix reaches robust class without inferential ambiguity`
2. `policy thresholds are revised with documented rationale and rerun evidence`

Absent those triggers, repeated reassessment must preserve `H1_4_QUALIFIED` claim limits.
