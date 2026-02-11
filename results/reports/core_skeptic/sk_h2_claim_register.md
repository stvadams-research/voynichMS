# SK-H2 Claim Register

**Date:** 2026-02-10  
**Source Finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-H2`)

---

## Claim Inventory

| Claim ID | Source | Prior Risk Pattern | Evidence Anchor | Boundary Tag | Remediation Status |
|---|---|---|---|---|---|
| H2-C1 | `README.md` | Categorical "falsified" headline wording | `results/reports/phase3_synthesis/FINAL_REPORT_PHASE_3.md`, `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` | `CONCLUSIVE_WITHIN_SCOPE` | CALIBRATED |
| H2-C2 | `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` | Absolute closure phrase ("Exhaustive", "scientifically unjustified") | `results/reports/phase4_inference/PHASE_4_RESULTS.md`, reopening criteria in same doc | `QUALIFIED` | CALIBRATED |
| H2-C3 | `results/reports/FINAL_PHASE_3_3_REPORT.md` | Semantic absolutism ("semantically empty procedural system") | `results/reports/phase3_synthesis/FINAL_REPORT_PHASE_3.md`, `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` | `CONCLUSIVE_WITHIN_SCOPE` | CALIBRATED |

## Operational Entitlement Dependencies (H2.2)

- Canonical gate-health source: `core_status/core_audit/release_gate_health_status.json`
- Required gate set for full claim entitlement:
  - `ci_check`
  - `pre_release_check`
  - `verify_reproduction`
- Current assumption for this pass: `GATE_HEALTH_DEGRADED`
- Required downgrade behavior under degraded state:
  - claims remain qualified/reopenable,
  - docs include explicit operational contingency markers,
  - entitlement reason codes surfaced in checker diagnostics.

---

## Non-Claim Boundary References

- `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` (explicit "What this does not claim" section)
- `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` (reopening criteria + non-claim block)
- `results/reports/FINAL_PHASE_3_3_REPORT.md` (framework-bounded final determination + non-claim block)

---

## Policy Link

- `governance/CLAIM_BOUNDARY_POLICY.md`
- `configs/core_skeptic/sk_h2_claim_language_policy.json`
