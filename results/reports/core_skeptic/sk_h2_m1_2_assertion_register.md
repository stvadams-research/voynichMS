# SK-H2.2 / SK-M1.2 Assertion Register

**Date:** 2026-02-10  
**Source Finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md` (`SK-H2 / SK-M1`)  
**Purpose:** Map closure and non-claim assertions to operational gate-health entitlement dependencies.

---

## Operational Dependency Baseline

- Canonical gate-health source: `core_status/core_audit/release_gate_health_status.json`
- Gate families tracked:
  - `ci_check`
  - `pre_release_check`
  - `verify_reproduction`
- Entitlement model:
  - `GATE_HEALTH_OK` -> full framework-bounded claim class allowed.
  - `GATE_HEALTH_DEGRADED` -> claim/closure wording must remain qualified and operationally contingent.

---

## Assertion Inventory

| Assertion ID | Source | Assertion Class | Operational Dependencies | Residual Risk if Gates Fail | Status |
|---|---|---|---|---|---|
| H2M1-A1 | `README.md` | Project-level conclusion summary | `ci_check`, `pre_release_check`, `verify_reproduction` | Overreach framing risk if summary reads stronger than current gate posture | OPEN |
| H2M1-A2 | `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` | Framework closure statement | `pre_release_check`, `verify_reproduction` | "Stopped too early" challenge if closure line is interpreted as unconditional | OPEN |
| H2M1-A3 | `results/reports/phase3_synthesis/final_phase_3_3_report.md` | Mechanism closure summary | `pre_release_check`, `verify_reproduction` | "Solved in principle" language can outrun current operational evidence integrity | OPEN |
| H2M1-A4 | `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md` | Comparative closure boundary | `ci_check`, `verify_reproduction` | Boundary language can appear terminal under degraded gate health | OPEN |
| H2M1-A5 | `reports/phase8_comparative/PHASE_B_SYNTHESIS.md` | Comparative closure synthesis | `ci_check`, `verify_reproduction` | Conditional closure can still be read as high-confidence finality if not operationally tagged | OPEN |

---

## Entitlement Mapping Rules

1. If gate health is degraded, all tracked assertions must include:
   - explicit operational contingency marker,
   - pointer to `core_status/core_audit/release_gate_health_status.json`,
   - qualified closure/claim wording.
2. If gate health is healthy, framework-bounded conclusive-within-scope wording is allowed.
3. Entitlement downgrade reason codes must be surfaced in policy-check diagnostics.
