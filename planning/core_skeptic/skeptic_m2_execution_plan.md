# Execution Plan: Skeptic Comparative-Uncertainty Hardening (SK-M2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-M2` (listed as Medium in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and execution report reflect implementation outcomes.

---

## 1) Objective

Address `SK-M2` by making comparative-distance claims uncertainty-aware and perturbation-tested so nearest-neighbor and structural-isolation statements are no longer presented as deterministic point claims.

This plan targets the specific inconsistency identified in the assessment:

1. Comparative distance claims are explicit and prominent in public comparative docs.
2. Confidence intervals and perturbation-stability reporting are not surfaced alongside those claims.
3. A skeptic can frame current comparative outputs as over-deterministic and under-qualified.

---

## 2) SK-M2 Problem Statement

From `SK-M2`:

- Comparative distances and nearest-neighbor claims are explicit in `reports/phase8_comparative/PHASE_B_SYNTHESIS.md:8` through `reports/phase8_comparative/PHASE_B_SYNTHESIS.md:15`.
- Public comparative docs do not present confidence intervals or perturbation-stability sensitivity for those distance claims.

Related comparative artifacts currently emphasize point estimates:

- `reports/phase8_comparative/PROXIMITY_ANALYSIS.md`
- `results/phase7_human/phase_7c_results.json`
- `reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md`

Core skeptic attack:

- "Distance geometry appears deterministic in prose but uncertainty reporting is thin."

---

## 3) Scope and Non-Goals

## In Scope

- Comparative distance uncertainty policy and taxonomy.
- Confidence interval reporting for key distance claims.
- Perturbation-stability testing for ranking and nearest-neighbor outcomes.
- Artifact contracts for uncertainty outputs and claim-eligibility gates.
- Comparative narrative calibration in public reports.
- CI/release guardrails to prevent regression to point-estimate-only comparative claims.

## Out of Scope

- New decipherment or semantic-interpretation claims.
- Re-architecture of unrelated phase pipelines.
- Re-adjudication of SK-C1/SK-H1/SK-H2/SK-H3/SK-M1 findings except where SK-M2 cross-links are required.
- Full redesign of comparative ontology/artifact library selection criteria.

---

## 4) Success Criteria (Exit Conditions)

`SK-M2` is considered closed only if all criteria below are met:

1. Comparative distance outputs include uncertainty intervals and stability metrics, not only point values.
2. Nearest-neighbor and structural-isolation claims are accompanied by confidence/stability qualifiers.
3. Public comparative docs no longer present deterministic distance conclusions without uncertainty context.
4. A machine-readable SK-M2 policy defines required uncertainty fields and prohibited unqualified phrasing.
5. CI/release checks fail when comparative uncertainty artifacts or required markers are missing.
6. Audit trace links SK-M2 finding -> policy -> artifacts -> calibrated claims -> verification.

---

## 5) Workstreams

## WS-M2-A: Comparative Uncertainty Policy

**Goal:** Define admissible comparative claim classes and uncertainty requirements.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define SK-M2 taxonomy (`DISTANCE_POINT_ESTIMATE`, `DISTANCE_QUALIFIED`, `STABILITY_CONFIRMED`, `INCONCLUSIVE_UNCERTAINTY`). | `governance/COMPARATIVE_UNCERTAINTY_POLICY.md` (new) | Taxonomy and examples documented. |
| A2 | Define required uncertainty fields and banned narrative patterns. | `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json` (new) | Parseable machine policy exists and is versioned. |
| A3 | Define claim eligibility rules linking uncertainty status to allowed comparative claims. | same + docs | Public claim classes mapped to uncertainty evidence thresholds. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-M2-B: Distance Uncertainty Artifactization

**Goal:** Produce reproducible uncertainty artifacts for comparative distances.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add comparative uncertainty runner (bootstrap and/or resampling over lines/pages plus deterministic seed control). | `scripts/phase7_human/run_7c_comparative.py` and/or `scripts/phase8_comparative/run_proximity_uncertainty.py` (new) | Runner emits uncertainty artifact with reproducible provenance. |
| B2 | Emit comparative uncertainty artifact with CI fields and rank distribution. | `results/phase7_human/phase_7c_uncertainty.json` (new) | Artifact contains CI, rank stability, and nearest-neighbor confidence. |
| B3 | Include policy-linked summary status (`STABILITY_CONFIRMED`, `INCONCLUSIVE_UNCERTAINTY`, etc.). | same | Status block present and machine-checkable. |

### Verification

```bash
python3 scripts/phase7_human/run_7c_comparative.py
python3 - <<'PY'
import json
d=json.load(open('results/phase7_human/phase_7c_uncertainty.json'))
print(d.get('results', {}).get('status'))
PY
```

---

## WS-M2-C: Perturbation-Stability Stress Testing

**Goal:** Quantify sensitivity of comparative rankings to plausible perturbations.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define perturbation battery (feature weighting jitter, artifact-subset jackknife, token subsample, transliteration variant where applicable). | `src/phase7_human/phase8_comparative.py` and/or dedicated module | Perturbation set is explicit and deterministic. |
| C2 | Compute nearest-neighbor stability frequency and rank-order robustness. | `results/phase7_human/phase_7c_uncertainty.json` | Stability metrics and rank volatility fields populated. |
| C3 | Add failure class for unstable ranking despite favorable point estimates. | same | Unstable results are downgraded by policy. |

### Verification

```bash
python3 - <<'PY'
import json
d=json.load(open('results/phase7_human/phase_7c_uncertainty.json'))
r=d.get('results', {})
print(r.get('nearest_neighbor'), r.get('nearest_neighbor_stability'))
PY
```

---

## WS-M2-D: Comparative Narrative Calibration

**Goal:** Align public comparative prose with uncertainty-aware evidence classes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Update proximity report to include CI columns and stability notes. | `reports/phase8_comparative/PROXIMITY_ANALYSIS.md` | Table includes interval and stability fields. |
| D2 | Calibrate Phase B synthesis claims to uncertainty-qualified wording. | `reports/phase8_comparative/PHASE_B_SYNTHESIS.md` | Distance claims include uncertainty qualifiers and references. |
| D3 | Calibrate holistic summary language where deterministic framing persists. | `reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md` | Comparative conclusions reference uncertainty artifacts. |
| D4 | Ensure boundary statement references uncertainty-constrained interpretation scope. | `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md` | Boundary language remains consistent with SK-M2 constraints. |

### Verification

```bash
rg -n "confidence|interval|CI|stability|uncertainty|nearest neighbor" \
  reports/phase8_comparative/PROXIMITY_ANALYSIS.md \
  reports/phase8_comparative/PHASE_B_SYNTHESIS.md \
  reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md \
  reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md
```

---

## WS-M2-E: Automated SK-M2 Guardrails

**Goal:** Prevent regression to deterministic comparative claims without uncertainty disclosure.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Implement SK-M2 checker for required uncertainty markers/artifact fields and banned unqualified patterns. | `scripts/core_skeptic/check_comparative_uncertainty.py` (new) | Checker exits non-zero on SK-M2 violations. |
| E2 | Add SK-M2 checker tests (pass/fail/allowlist/artifact-schema). | `tests/core_skeptic/test_comparative_uncertainty_checker.py` (new) | Deterministic policy coverage exists. |
| E3 | Integrate SK-M2 checks into CI and pre-release paths. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh` | Guard runs automatically in ci/release modes. |

### Verification

```bash
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release
python3 -m pytest -q tests/core_skeptic/test_comparative_uncertainty_checker.py
```

---

## WS-M2-F: Governance and Audit Traceability

**Goal:** Make comparative uncertainty decisions durable and auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add SK-M2 section to reproducibility docs with artifact and checker commands. | `governance/governance/REPRODUCIBILITY.md` | Repro guide includes SK-M2 verification path. |
| F2 | Add SK-M2 comparative claim register with prior-risk phrase mapping. | `reports/core_skeptic/SK_M2_COMPARATIVE_REGISTER.md` (new) | Register links claims to uncertainty status. |
| F3 | Add execution status template for SK-M2 pass. | `reports/core_skeptic/SKEPTIC_M2_EXECUTION_STATUS.md` (during execution) | Traceable status file prepared for execution phase. |
| F4 | Add audit log entry linking SK-M2 finding to implemented controls/residuals. | `AUDIT_LOG.md` | End-to-end traceability present. |

### Verification

```bash
rg -n "SK-M2|comparative uncertainty|nearest_neighbor_stability|phase_7c_uncertainty" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M2-A (policy and taxonomy first)
2. WS-M2-B (uncertainty artifact generation)
3. WS-M2-C (perturbation stability stress battery)
4. WS-M2-D (report and narrative calibration)
5. WS-M2-E (guardrails and CI/release enforcement)
6. WS-M2-F (governance and audit traceability)

Rationale:

- Do not calibrate narrative claims before uncertainty artifacts and policy thresholds are defined.

---

## 7) Decision Matrix for SK-M2 Comparative Claim Status

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Distance CI present, nearest-neighbor stability high, perturbation rank robust | `STABILITY_CONFIRMED` | "Comparative proximity is uncertainty-qualified and robust under tested perturbations." |
| CI present but moderate rank volatility or borderline stability | `DISTANCE_QUALIFIED` | "Comparative proximity is directional with explicit uncertainty caveats." |
| Point estimates available but required CI/stability fields missing | `INCONCLUSIVE_UNCERTAINTY` | "Comparative claim remains provisional pending uncertainty-complete evidence." |
| Unqualified deterministic comparative language or policy violation present | `SUBJECTIVITY_RISK_BLOCKED` | "Comparative claim blocked until uncertainty policy compliance is restored." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M2-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M2 comparative uncertainty policy doc and machine-readable policy config. |
| WS-M2-B Uncertainty Artifacts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added uncertainty runner and generated canonical uncertainty artifact with status and allowed claim fields. |
| WS-M2-C Perturbation Stability | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added bootstrap + jackknife stability outputs and top-rank volatility diagnostics. |
| WS-M2-D Narrative Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Calibrated comparative reports to uncertainty-qualified wording and artifact references. |
| WS-M2-E Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M2 checker/tests and integrated ci/release enforcement paths. |
| WS-M2-F Governance/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated reproducibility docs, added SK-M2 claim register and execution status, and logged audit trace. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Uncertainty layer adds complexity without materially changing conclusions. | Medium | Medium | Require explicit claim-eligibility mapping and bounded caveat classes. |
| R2 | Bootstrap/resampling assumptions are mismatched to comparative data structure. | Medium | High | Pair CI with perturbation/jackknife stability and document assumptions. |
| R3 | Narrative updates lag artifact updates, creating temporary mismatch. | High | High | Sequence WS-M2-D after artifacts and enforce via checker markers. |
| R4 | Guardrails over-trigger on legitimate comparative phrasing. | Medium | Medium | Add scoped allowlist with tests and policy comments for approved edge cases. |
| R5 | Comparative artifact generation becomes expensive and slows iteration loops. | Medium | Medium | Add mode split (`quick` vs `release`) with deterministic thresholds and explicit evidence-class labels. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M2 comparative uncertainty policy and machine-readable config.
2. Comparative uncertainty artifact(s) with CI, perturbation stability, and claim status.
3. Calibrated comparative narrative docs with uncertainty-qualified claims.
4. SK-M2 checker and tests integrated into CI/release checks.
5. SK-M2 comparative claim register and execution status report under `reports/core_skeptic/`.
6. Audit log entry documenting SK-M2 decisions and residual risk.
