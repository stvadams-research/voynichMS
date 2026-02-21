# SK-H2.4 Gate Dependency Matrix

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_H2_4_EXECUTION_PLAN.md`

## Purpose

Map all public closure/claim surfaces to gate-health entitlement dependencies and checker coverage.

## Canonical Dependency Source

- `core_status/core_audit/release_gate_health_status.json`

Current lane/class snapshot:

- `h2_4_closure_lane=H2_4_QUALIFIED`
- `allowed_claim_class=QUALIFIED`
- `allowed_closure_class=CONDITIONAL_CLOSURE_QUALIFIED`

## Surface Coverage Matrix

| Surface | Claim Type | Primary Checker(s) | Required Gate Fields | Current Dependency Status | Coverage |
|---|---|---|---|---|---|
| `README.md` | project-level claim scope | `check_claim_boundaries.py`, `check_claim_entitlement_coherence.py` | `status`, `allowed_claim_class`, `h2_4_closure_lane`, freshness timestamp | degraded, qualified only | Covered |
| `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` | closure statement | `check_claim_boundaries.py`, `check_closure_conditionality.py`, `check_claim_entitlement_coherence.py` | `status`, `allowed_claim_class`, `allowed_closure_class`, `h2_4_closure_lane` | degraded, conditional closure qualified | Covered |
| `results/reports/phase3_synthesis/final_phase_3_3_report.md` | mechanism closure summary | `check_claim_boundaries.py`, `check_closure_conditionality.py`, `check_claim_entitlement_coherence.py` | same as above | degraded, conditional closure qualified | Covered |
| `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md` | comparative closure boundary | `check_claim_boundaries.py`, `check_closure_conditionality.py`, `check_claim_entitlement_coherence.py` | same as above + degraded-state marker | degraded, contingent language required | Covered |
| `reports/phase8_comparative/PHASE_B_SYNTHESIS.md` | comparative synthesis claim | `check_claim_boundaries.py`, `check_closure_conditionality.py`, `check_claim_entitlement_coherence.py` | same as above + degraded-state marker | degraded, contingent language required | Covered |
| `governance/REOPENING_CRITERIA.md` | canonical reopen policy | `check_closure_conditionality.py` | lane-consistent reopening semantics | bounded with SK-H2.4 triggers | Covered |
| `governance/CLOSURE_CONDITIONALITY_POLICY.md` | closure policy contract | `check_closure_conditionality.py` | lane-to-closure-class mapping | aligned with H2.4 | Covered |

## Coverage-Gap Check (Pass 4)

No uncovered public closure surfaces were found among files cited by pass-4 SK-H2 references.

Residual dependency still open:

- SK-C1 release sensitivity evidence contract remains unresolved (`SENSITIVITY_RELEASE_CONTRACT_BLOCKED`).

## Anti-Drift Controls

1. H2/M1 policies both enforce freshness on the same gate-health artifact.
2. Coherence script verifies lane and claim/closure classes across both policies.
3. CI/pre-release/verify scripts invoke the coherence checker in-mode.
