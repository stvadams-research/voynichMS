# Execution Plan: Skeptic Comparative Confidence Closure (SK-M2.2)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-M2` (pass-2 residual, Medium)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and closeout artifacts updated.

---

## 1) Objective

Address the pass-2 `SK-M2` residual by attempting to resolve nearest-neighbor confidence as far as feasible while preserving fail-closed uncertainty governance.

This plan targets the residual skeptic challenge:

- Comparative uncertainty is now explicit, but nearest-neighbor confidence remains non-conclusive.

Desired endpoint:

1. confidence-strengthened comparative outcome (`STABILITY_CONFIRMED` or durable `DISTANCE_QUALIFIED`) if stability criteria are met, or
2. governance-complete bounded non-conclusive outcome (`INCONCLUSIVE_UNCERTAINTY`) with explicit confidence limits and anti-overreach safeguards.

---

## 2) SK-M2 Problem Statement (Pass 2)

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Comparative uncertainty is bounded but unresolved:
  - `results/human/phase_7c_uncertainty.json` -> `status=INCONCLUSIVE_UNCERTAINTY`
  - `results/human/phase_7c_uncertainty.json` -> provisional allowed claim
- Comparative reports are uncertainty-qualified:
  - `reports/comparative/PROXIMITY_ANALYSIS.md`
  - `reports/comparative/PHASE_B_SYNTHESIS.md`

Current residual condition:

- Claims are better calibrated, but confidence in nearest-neighbor ranking remains unstable under perturbation.

---

## 3) Scope and Non-Goals

## In Scope

- SK-M2 residual closure strategy for nearest-neighbor confidence and rank stability.
- Uncertainty artifact completeness and stability diagnostics hardening.
- Pre-registered perturbation matrix and confidence-recovery attempt path.
- Decision policy refinement for `STABILITY_CONFIRMED` vs `DISTANCE_QUALIFIED` vs `INCONCLUSIVE_UNCERTAINTY`.
- Comparative report/status coherence and claim-boundary hardening.
- CI/release contract updates that prevent deterministic comparative over-claim regressions.

## Out of Scope

- New semantic/decipherment claims.
- Reworking SK-C*, SK-H*, SK-M1, SK-M3, SK-M4 beyond explicit dependency integration.
- Expansion of external comparative corpus beyond currently available sources unless already policy-approved.

---

## 4) Success Criteria (Exit Conditions)

`SK-M2` pass-2 residual is considered closed only when all criteria below are satisfied:

1. Residual uncertainty is decomposed into measurable components (sampling variance, perturbation sensitivity, rank-gap fragility).
2. Comparative uncertainty artifact has complete required fields (no structural nulls for required stability metrics).
3. A pre-registered confidence-recovery matrix has been defined (and is ready for execution in a later pass).
4. Final comparative status mapping is deterministic and auditable:
   - strengthened confidence class (if criteria met), or
   - explicitly bounded non-conclusive class (if criteria unmet).
5. Comparative narrative cannot exceed status entitlement in public reports.
6. CI/release guardrails fail closed on missing/invalid uncertainty semantics.

---

## 5) Workstreams

## WS-M2.2-A: Residual Baseline and Confidence-Gap Decomposition

**Goal:** Convert the broad "non-conclusive" label into explicit confidence gaps.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Capture current SK-M2 status, reason code, and stability metrics from uncertainty artifact. | `results/human/phase_7c_uncertainty.json` | Baseline values are frozen for this remediation cycle. |
| A2 | Quantify threshold gap against policy targets (bootstrap and jackknife stability, top-2 gap robustness). | New `reports/skeptic/SK_M2_2_CONFIDENCE_REGISTER.md` | Gap table identifies exactly which criteria fail and by how much. |
| A3 | Classify missing or weak metrics (for example `rank_stability` absent/null) as schema vs signal problems. | same | Each gap has a remediation lever and owner. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('results/human/phase_7c_uncertainty.json')).get('results',{})
print(r.get('status'), r.get('reason_code'))
print('nearest_neighbor_stability', r.get('nearest_neighbor_stability'))
print('jackknife', r.get('jackknife_nearest_neighbor_stability'))
print('rank_stability', r.get('rank_stability'))
PY
```

---

## WS-M2.2-B: Uncertainty Artifact Completeness Hardening

**Goal:** Ensure the canonical uncertainty artifact is structurally complete and policy-ready.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define/confirm required uncertainty fields for SK-M2.2 (including rank stability fields and explicit sample metadata). | `configs/skeptic/sk_m2_comparative_uncertainty_policy.json` | Policy contains full field contract for comparative confidence. |
| B2 | Add/adjust artifact emission logic so required confidence fields are always populated or explicitly typed fallback values are emitted with reason codes. | `scripts/comparative/run_proximity_uncertainty.py`, `src/comparative/mapping.py` | Required fields are non-missing and semantically valid in output. |
| B3 | Add explicit data-quality/metric-validity block in artifact (`metric_validity`, `field_completeness`, `status_inputs`). | `results/human/phase_7c_uncertainty.json` schema | Downstream checker can distinguish missing-data from statistical instability. |

### Verification

```bash
python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 - <<'PY'
import json
r=json.load(open('results/human/phase_7c_uncertainty.json')).get('results',{})
required=['status','reason_code','allowed_claim','nearest_neighbor','nearest_neighbor_stability',
          'jackknife_nearest_neighbor_stability','distance_summary','ranking_point_estimate',
          'top2_gap','parameters']
print('missing', [k for k in required if k not in r])
PY
```

---

## WS-M2.2-C: Registered Confidence-Recovery Matrix

**Goal:** Create a pre-registered execution matrix to attempt confidence recovery without outcome tuning.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define perturbation matrix axes (iterations, seeds, jackknife variants, optional corpus-subset checks). | New matrix section in `configs/skeptic/sk_m2_comparative_uncertainty_policy.json` and/or dedicated matrix config | Confidence-recovery search is explicit and reproducible before reruns. |
| C2 | Define anti-tuning selection rule (choose lane by stability diagnostics and data quality, not desired nearest neighbor). | New `reports/skeptic/SK_M2_2_METHOD_SELECTION.md` | Selection protocol is auditable and deterministic. |
| C3 | Define by-run artifact logging requirements for comparative uncertainty trials. | `results/human/by_run/*` conventions + register template | Every candidate lane can be traced and compared post-run. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/skeptic/sk_m2_comparative_uncertainty_policy.json'))
print('has_thresholds', 'thresholds' in p)
print('has_artifact_policy', 'artifact_policy' in p)
PY
```

---

## WS-M2.2-D: Decision Policy Refinement for Residual Confidence

**Goal:** Make SK-M2 decision transitions explicit and robust to partial improvements.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Refine criteria separating `DISTANCE_QUALIFIED` from `INCONCLUSIVE_UNCERTAINTY` when nearest-neighbor point estimate is stable directionally but rank confidence is below full threshold. | `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`, `docs/COMPARATIVE_UNCERTAINTY_POLICY.md` | Boundary rules are precise and machine-enforceable. |
| D2 | Add explicit reason-code taxonomy for residual cases (`RANK_UNSTABLE_UNDER_PERTURBATION`, `TOP2_GAP_FRAGILE`, `FIELD_INCOMPLETE`, etc.). | uncertainty artifact + policy docs | Non-conclusive outcomes are diagnostically specific. |
| D3 | Require deterministic allowed-claim strings keyed to status + reason code. | artifact emitter + policy | Reports can only consume permitted claim class. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('results/human/phase_7c_uncertainty.json')).get('results',{})
print(r.get('status'), r.get('reason_code'), r.get('allowed_claim'))
PY
```

---

## WS-M2.2-E: Comparative Narrative and Boundary Coherence

**Goal:** Keep comparative reporting aligned to uncertainty status class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Re-verify proximity table/report language against current status and allowed claim. | `reports/comparative/PROXIMITY_ANALYSIS.md` | No wording exceeds current uncertainty class. |
| E2 | Re-verify synthesis and boundary docs for uncertainty-qualified nearest-neighbor framing. | `reports/comparative/PHASE_B_SYNTHESIS.md`, `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md` | Narrative stays directional/caveated when status is non-conclusive. |
| E3 | Extend final findings summary coherence markers for SK-M2.2 status-driven language. | `reports/comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md` | Final comparative statements remain status-gated. |

### Verification

```bash
rg -n "uncertainty|nearest-neighbor|stability|INCONCLUSIVE_UNCERTAINTY|phase_7c_uncertainty.json" \
  reports/comparative/PROXIMITY_ANALYSIS.md \
  reports/comparative/PHASE_B_SYNTHESIS.md \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md
```

---

## WS-M2.2-F: Gate/Test Hardening for Comparative Confidence

**Goal:** Prevent regressions where comparative claims outrun uncertainty evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend SK-M2 checker to enforce any new required fields/reason-code constraints from WS-M2.2-B/D. | `scripts/skeptic/check_comparative_uncertainty.py` | Checker fails closed on incomplete or incoherent uncertainty artifacts. |
| F2 | Extend checker tests for new residual scenarios and edge cases (null fields, threshold boundary, reason-code mismatch). | `tests/skeptic/test_comparative_uncertainty_checker.py` | Regression coverage exists for SK-M2.2 residual classes. |
| F3 | Confirm CI/release/reproduction contracts include SK-M2 checks and required marker semantics. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, audit contract tests | Pipeline catches comparative overreach automatically. |

### Verification

```bash
python3 scripts/skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/skeptic/check_comparative_uncertainty.py --mode release
python3 -m pytest -q tests/skeptic/test_comparative_uncertainty_checker.py
```

---

## WS-M2.2-G: Governance Traceability and Closeout

**Goal:** Preserve an auditable chain from pass-2 SK-M2 residual to final SK-M2.2 decision.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-M2.2 confidence register and method-selection register templates. | `reports/skeptic/SK_M2_2_CONFIDENCE_REGISTER.md`, `reports/skeptic/SK_M2_2_METHOD_SELECTION.md` | Residual decomposition and lane-selection logic are documented. |
| G2 | Add SK-M2.2 execution status report template for implementation pass. | `reports/skeptic/SKEPTIC_M2_2_EXECUTION_STATUS.md` | End-state and residual risks can be recorded deterministically. |
| G3 | Add audit-log linkage requirement for implementation pass. | `AUDIT_LOG.md` (future execution entry) | Trace from finding -> controls -> final status is complete. |

### Verification

```bash
rg -n "SK-M2.2|INCONCLUSIVE_UNCERTAINTY|RANK_UNSTABLE_UNDER_PERTURBATION|phase_7c_uncertainty" \
  planning/skeptic reports/skeptic AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M2.2-A (baseline decomposition)
2. WS-M2.2-B (artifact completeness)
3. WS-M2.2-C (registered recovery matrix)
4. WS-M2.2-D (decision policy refinement)
5. WS-M2.2-E (report coherence)
6. WS-M2.2-F (gate/test hardening)
7. WS-M2.2-G (governance closeout)

Rationale:

- Resolve measurement/schema ambiguity first; then attempt confidence strengthening; finally calibrate claims and lock regression checks.

---

## 7) Decision Matrix for SK-M2.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Nearest-neighbor and perturbation stability pass policy thresholds; uncertainty artifact complete and coherent. | `M2_2_ALIGNED` | "Comparative nearest-neighbor signal is uncertainty-qualified and stability-supported under tested conditions." |
| Artifact complete and directional nearest-neighbor signal present, but confidence remains below full-confirmation thresholds. | `M2_2_QUALIFIED` | "Comparative nearest-neighbor signal is directional but remains confidence-qualified and non-conclusive." |
| Artifact schema, reason-code logic, or report/gate semantics are incoherent. | `M2_2_BLOCKED` | "SK-M2.2 remains unresolved due comparative uncertainty contract incoherence." |
| Evidence insufficient to determine whether confidence limits are remediable. | `M2_2_INCONCLUSIVE` | "SK-M2.2 provisional pending deeper comparative confidence diagnostics." |

Execution outcome: `M2_2_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M2.2-A Baseline/Gap Decomposition | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added confidence-gap decomposition with threshold deltas in `reports/skeptic/SK_M2_2_CONFIDENCE_REGISTER.md`. |
| WS-M2.2-B Artifact Completeness | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended uncertainty artifact schema/metrics and metric-validity block in `src/comparative/mapping.py`. |
| WS-M2.2-C Recovery Matrix | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Executed registered 9-lane confidence matrix and documented outcomes in `reports/skeptic/SK_M2_2_METHOD_SELECTION.md`. |
| WS-M2.2-D Decision Policy Refinement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added threshold and reason-code semantics in `configs/skeptic/sk_m2_comparative_uncertainty_policy.json`. |
| WS-M2.2-E Report/Boundary Coherence | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated proximity/synthesis/boundary comparative language to align with current status/reason code. |
| WS-M2.2-F Gate/Test Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended SK-M2 checker/tests and added verify-path SK-M2 contract checks. |
| WS-M2.2-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M2.2 confidence/method/status reports and audit trace linkage. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Nearest-neighbor instability is structurally irreducible with current comparative library/metrics. | Medium | High | Prefer bounded qualified closure over forced conclusive claims. |
| R2 | Confidence-recovery sweeps drift into outcome tuning. | Medium | High | Pre-register matrix and anti-tuning selection rules before reruns. |
| R3 | Null/partial metrics (for example missing rank stability) hide schema issues as statistical issues. | Medium | Medium | Enforce explicit completeness checks and reason-code separation. |
| R4 | Report language drifts from status class after reruns. | Medium | High | Add checker markers and contract tests for SK-M2.2 language coherence. |
| R5 | Recovery matrix increases compute cost and slows release cadence. | Medium | Medium | Stage runs by low-cost diagnostics first; run full matrix only for promising lanes. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M2.2 confidence-gap decomposition register.
2. Updated SK-M2 uncertainty policy/schema for residual confidence fields.
3. Registered confidence-recovery matrix and anti-tuning method-selection protocol.
4. Updated uncertainty artifact semantics and reason-code taxonomy.
5. Comparative report coherence updates aligned to status class.
6. SK-M2 checker/test/gate hardening for new residual rules.
7. SK-M2.2 execution status report under `reports/skeptic/`.
8. Audit-log trace entry linking pass-2 SK-M2 finding to controls and final status.

---

## 11) Closure Criteria

`SK-M2` pass-2 residual is closed only when:

1. Confidence gaps are explicitly measured and policy-linked.
2. Uncertainty artifact fields are complete and checker-valid.
3. Comparative claim language is no stronger than emitted status.
4. CI/release checks enforce SK-M2.2 constraints against over-claim regression.
5. Final state is either confidence-strengthened with supporting evidence or explicitly bounded as non-conclusive with full governance traceability.
