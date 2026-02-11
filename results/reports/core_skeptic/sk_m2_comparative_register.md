# SK-M2 Comparative Register

**Date:** 2026-02-10  
**Source Finding:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md` (`SK-M2`)

---

## Comparative Claim Inventory

| Claim ID | Source | Prior Subjectivity-Risk Pattern | Uncertainty Linkage | Status |
|---|---|---|---|---|
| M2-C1 | `reports/phase8_comparative/PHASE_B_SYNTHESIS.md` | Nearest-neighbor claim presented as deterministic point estimate | `results/phase7_human/phase_7c_uncertainty.json` | CALIBRATED |
| M2-C2 | `reports/phase8_comparative/PROXIMITY_ANALYSIS.md` | Distance table had no CI or stability fields | `results/phase7_human/phase_7c_uncertainty.json` + CI/stability table | CALIBRATED |
| M2-C3 | `reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md` | Summary language implied closure with thin uncertainty visibility | Explicit uncertainty-qualified status block and artifact reference | CALIBRATED |
| M2-C4 | `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md` | Boundary language omitted comparative uncertainty constraint | Added uncertainty-qualified interpretation reference | CALIBRATED |

---

## Current SK-M2 Evidence State

- Primary uncertainty artifact: `results/phase7_human/phase_7c_uncertainty.json`
- Current status: `INCONCLUSIVE_UNCERTAINTY`
- Current reason code: `RANK_UNSTABLE_UNDER_PERTURBATION`
- Allowed claim class: directional/caveated comparative claim only

---

## Policy Linkage

- `governance/COMPARATIVE_UNCERTAINTY_POLICY.md`
- `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json`
- `scripts/core_skeptic/check_comparative_uncertainty.py`
