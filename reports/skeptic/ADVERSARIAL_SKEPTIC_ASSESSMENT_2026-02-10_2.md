# Adversarial Skeptic Assessment Report (Pass 2)

**Date:** 2026-02-10  
**Playbook Executed:** `planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md`  
**Assessment Type:** Documentation and methodological stress test only (no code fixes)

---

## 1. Execution Evidence (This Run)

The following checks were executed for this pass:

- `ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='SK-M4: skeptic reassessment on intentional working tree' bash scripts/audit/pre_release_check.sh` -> **FAILED**
  - Failure cause: sensitivity artifact missing policy-required `dataset_policy_pass=true` condition.
  - Gate requirement is enforced in `scripts/audit/pre_release_check.sh:40` through `scripts/audit/pre_release_check.sh:48`.

- `bash scripts/verify_reproduction.sh` -> **FAILED**
  - Failure cause: sensitivity artifact missing/invalid `dataset_policy_pass=true`.
  - Requirement is enforced in `scripts/verify_reproduction.sh:147` through `scripts/verify_reproduction.sh:155`.

- `bash scripts/ci_check.sh` -> **FAILED**
  - Policy checks passed through SK-M4 (`claim boundaries`, `control comparability`, `closure conditionality`, `comparative uncertainty`, `report coherence`, `provenance uncertainty`).
  - Failure occurred in pytest contract:
    - `tests/audit/test_provenance_contract.py:13` through `tests/audit/test_provenance_contract.py:22`
    - Missing provenance-writer contract for:
      - `scripts/comparative/run_proximity_uncertainty.py:1` through `scripts/comparative/run_proximity_uncertainty.py:67`

- Runtime provenance spot-check:
  - `data/voynich.db` `runs` table currently reports:
    - `orphaned=63`
    - `success=135`

---

## 2. Overall Skeptic Verdict

This pass shows real hardening in claim-scope calibration and explicit uncertainty governance (notably SK-M3 and SK-M4), but **release readiness is currently blocked by operational evidence-contract regressions**.

Primary reason: core gates now fail on sensitivity-policy and provenance-contract integrity, which gives a hostile skeptic a concrete reproducibility/process attack.

---

## 3. Attack Vector Scorecard

| Attack Vector | Status | Risk |
|---|---|---|
| AV1. "You defined language out of existence" | Partially Defended | Medium |
| AV2. "Your controls are not comparable" | Partially Defended | High |
| AV3. "Statistics cannot detect meaning" | Partially Defended | Medium |
| AV4. "You ignored the images" | Partially Defended | High |
| AV5. "You stopped too early" | Partially Defended | Medium |
| AV6. "Comparative analysis is subjective" | Partially Defended | Medium |
| AV7. "You are really saying it is a hoax" | Partially Defended | Medium |
| Meta: Motivated reasoning | Partially Defended | Medium |
| Meta: Overreach | Partially Defended | High |

---

## 4. Detailed Findings (Prioritized)

### SK-C1 (Critical): Sensitivity evidence contract is internally inconsistent with release/verify gate policy.

- Current sensitivity artifact still claims strong release posture:
  - `release_evidence_ready=true` in `status/audit/sensitivity_sweep.json:35`
  - `robustness_decision=PASS` in `status/audit/sensitivity_sweep.json:26`
  - Small profile and warning-heavy context remain:
    - `dataset_pages=18` in `status/audit/sensitivity_sweep.json:30`
    - `dataset_tokens=216` in `status/audit/sensitivity_sweep.json:31`
    - `total_warning_count=918` in `status/audit/sensitivity_sweep.json:24`
    - `caveats=[]` in `status/audit/sensitivity_sweep.json:27`
- Public summary echoes this strong framing with no caveat text:
  - `reports/audit/SENSITIVITY_RESULTS.md:9`
  - `reports/audit/SENSITIVITY_RESULTS.md:23`
  - `reports/audit/SENSITIVITY_RESULTS.md:26`
- But gate policy now requires fields not present/valid in this artifact:
  - `dataset_policy_pass` and `warning_policy_pass` checks:
    - `scripts/audit/pre_release_check.sh:40` through `scripts/audit/pre_release_check.sh:48`
    - `scripts/verify_reproduction.sh:147` through `scripts/verify_reproduction.sh:155`

**Skeptic leverage:** "Your release artifact says PASS, but your own release and reproduction gates reject it."

---

### SK-C2 (Critical): Provenance-runner contract fails in CI, reopening process-integrity attack surface.

- Provenance contract enforces that non-exempt `run_*.py` scripts include provenance writer integration:
  - `tests/audit/test_provenance_contract.py:13` through `tests/audit/test_provenance_contract.py:22`
- CI failed on:
  - `scripts/comparative/run_proximity_uncertainty.py`
- The failing script currently outputs JSON but does not show `ProvenanceWriter` usage:
  - `scripts/comparative/run_proximity_uncertainty.py:1` through `scripts/comparative/run_proximity_uncertainty.py:67`

**Skeptic leverage:** "Your provenance policy says one thing; your runner contract currently violates it."

---

### SK-H3 (High): Control comparability is policy-guarded but still unresolved due data-availability block.

- Control-comparability artifact remains blocked:
  - `status/synthesis/CONTROL_COMPARABILITY_STATUS.json:12` (`NON_COMPARABLE_BLOCKED`)
  - `status/synthesis/CONTROL_COMPARABILITY_STATUS.json:13` (`DATA_AVAILABILITY`)
- Structural anti-leakage controls are explicitly documented and machine-reported:
  - leakage false + metric partition:
    - `status/synthesis/CONTROL_COMPARABILITY_STATUS.json:16`
    - `status/synthesis/CONTROL_COMPARABILITY_STATUS.json:21`
    - `status/synthesis/CONTROL_COMPARABILITY_STATUS.json:26`
  - policy framing:
    - `docs/GENERATOR_MATCHING.md:4`
    - `docs/GENERATOR_MATCHING.md:20`
    - `docs/METHODS_REFERENCE.md:99` through `docs/METHODS_REFERENCE.md:100`

**Skeptic leverage:** "You improved leakage controls, but comparability is still blocked rather than conclusively settled."

---

### SK-H1 (High): Multimodal challenge is better bounded but remains underpowered.

- Coupling status remains non-conclusive:
  - `results/mechanism/anchor_coupling_confirmatory.json:13` (`INCONCLUSIVE_UNDERPOWERED`)
  - `results/mechanism/anchor_coupling_confirmatory.json:15` (no conclusive claim allowed)
- Reports now explicitly prevent over-interpretation:
  - `results/reports/PHASE_5H_RESULTS.md:47`
  - `results/reports/PHASE_5I_RESULTS.md:51`
  - `results/reports/PHASE_5I_RESULTS.md:54`

**Skeptic leverage:** "You now acknowledge ambiguity correctly, but the image-text case is still not decisively closed."

---

### SK-M2 (Medium): Comparative uncertainty is explicitly managed, but remains non-conclusive.

- Uncertainty artifact now clearly bounds claim strength:
  - `results/human/phase_7c_uncertainty.json:19` (`INCONCLUSIVE_UNCERTAINTY`)
  - `results/human/phase_7c_uncertainty.json:21` (provisional allowed claim)
  - `results/human/phase_7c_uncertainty.json:24`
  - `results/human/phase_7c_uncertainty.json:25`
- Comparative reports are uncertainty-qualified:
  - `reports/comparative/PROXIMITY_ANALYSIS.md:24`
  - `reports/comparative/PHASE_B_SYNTHESIS.md:8` through `reports/comparative/PHASE_B_SYNTHESIS.md:21`

**Skeptic leverage:** "Claims are better calibrated, but nearest-neighbor confidence remains unresolved."

---

### SK-H2 / SK-M1 (Medium): Closure and non-claim language is materially improved.

- Boundary and non-claim structure is now explicit:
  - `README.md:33`
  - `README.md:47`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:46`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md:55`
- Conditional reopening language is explicit:
  - `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md:17`
  - `reports/comparative/PHASE_B_SYNTHESIS.md:38`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:80`
  - `docs/REOPENING_CRITERIA.md:5`

Residual issue:

- Absolute-risk rhetoric is reduced, but closure remains assertive enough that skeptics can still challenge scope if operational gates fail.

---

### SK-M3 (Resolved): Prior internal Phase 4 status contradiction appears remediated.

- Phase 4 report now states full completion and explicitly states no contradictory pending blocks:
  - `results/reports/PHASE_4_RESULTS.md:4`
  - `results/reports/PHASE_4_RESULTS.md:169`
- Coherence markers are present across linked docs:
  - `results/reports/PHASE_4_RESULTS.md:157`
  - `results/reports/PHASE_4_5_METHOD_CONDITION_MAP.md:52`

**Assessment update:** Prior SK-M3 contradiction is not reproduced in this pass.

---

### SK-M4 (Partially Resolved): Historical provenance uncertainty is now explicit and bounded, not eliminated.

- New provenance confidence framing is explicit:
  - `README.md:56`
  - `README.md:61`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:65`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md:74`
  - `docs/PROVENANCE.md:120`
- Canonical provenance-health artifact reports:
  - `PROVENANCE_QUALIFIED` with orphaned rows still present:
    - `status/audit/provenance_health_status.json` (current status snapshot)
    - runtime DB spot-check: `orphaned=63`, `success=135`

Residual coherence note:

- One register snapshot is now stale relative to current runtime counts:
  - `reports/skeptic/SK_M4_PROVENANCE_REGISTER.md:13` still shows `success=133`.

**Skeptic leverage:** "Uncertainty is managed better, but historical provenance remains qualified and some summaries drift."

---

## 5. What Held Up Well Under Skeptic Pressure

1. **Claim-boundary and closure-conditionality calibration improved materially.**  
   Evidence: `README.md:33`, `README.md:47`, `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md:17`, `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:34`.

2. **Multimodal and comparative claims are now explicitly evidence-bounded.**  
   Evidence: `results/mechanism/anchor_coupling_confirmatory.json:13`, `results/human/phase_7c_uncertainty.json:19`, `reports/comparative/PHASE_B_SYNTHESIS.md:21`.

3. **SK-M3 coherence remediation appears durable in current artifacts.**  
   Evidence: `results/reports/PHASE_4_RESULTS.md:169`, `results/reports/PHASE_4_5_METHOD_CONDITION_MAP.md:52`.

4. **SK-M4 provenance governance is now formalized and machine-checkable.**  
   Evidence: `docs/HISTORICAL_PROVENANCE_POLICY.md`, `configs/skeptic/sk_m4_provenance_policy.json`, `status/audit/provenance_health_status.json`.

---

## 6. Skeptic Success Criteria Check

Against the playbook’s success criteria, a competent skeptic can currently still claim:

- Operational release confidence is inconsistent (artifact says PASS while gates fail).
- Provenance contract enforcement is not fully closed (CI provenance contract failure).
- Multimodal and control-comparability conclusions remain bounded/non-conclusive rather than decisively resolved.

**Result:** Process and framing improved, but this pass is **not release-hardened** against a hostile expert skeptic due active gate failures.

---

## 7. Final Assessment Statement

This second pass shows meaningful improvements in epistemic scope control (especially SK-M3 and SK-M4). However, the current run fails three top-level validation gates, and those failures provide a direct credibility path for adversarial critique.

At this point, the strongest skeptic attack is no longer primarily rhetorical overreach; it is **evidence-contract inconsistency between generated artifacts and enforced release/CI policy**.
