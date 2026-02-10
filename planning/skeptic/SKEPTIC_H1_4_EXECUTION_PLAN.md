# Execution Plan: Skeptic Multimodal Robustness Closure (SK-H1.4)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
**Finding Target:** `SK-H1` (High, pass-4 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. See `reports/skeptic/SKEPTIC_H1_4_EXECUTION_STATUS.md` for command evidence and outcomes.

---

## 1) Objective

Resolve pass-4 `SK-H1` residual as fully as feasible by closing the remaining robustness gap:

- current canonical multimodal status is conclusive (`CONCLUSIVE_NO_COUPLING`), but
- cross-seed stability remains qualified, allowing continued skeptic leverage.

Primary objective:

1. define deterministic robustness closure criteria for SK-H1 beyond single canonical lane success,
2. enforce those criteria across artifacts/checkers/reports, and
3. produce governance outputs that prevent a fifth reopening of the same residual without new evidence.

---

## 2) Pass-4 SK-H1 Problem Statement

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`:

- Canonical artifact reports conclusive no-coupling:
  - `results/mechanism/anchor_coupling_confirmatory.json`
    - `status=CONCLUSIVE_NO_COUPLING`
    - `status_reason=adequacy_and_inference_support_no_coupling`
    - `adequacy.pass=true`
    - `inference.decision=NO_COUPLING`
- Residual remains high/narrowed because seed-lane fragility persists:
  - `reports/skeptic/SKEPTIC_H1_3_EXECUTION_STATUS.md`
  - `reports/skeptic/SK_H1_3_INFERENCE_REGISTER.md`

Skeptic leverage still valid:

- "Status semantics are improved, but robustness remains qualified across seed lanes."

---

## 3) Fourth-Attempt Retrospective (Why H1 -> H1.2 -> H1.3 Still Left Residual)

This plan explicitly addresses repeat-failure patterns from prior passes:

1. **Canonical lane was improved faster than robustness envelope formalization.**  
   A single publication lane can be conclusive while adjacent registered lanes remain ambiguous.

2. **Closure criteria for mixed-lane outcomes remained under-specified.**  
   Prior work separated adequacy vs inference semantics, but did not hard-lock when mixed seed outcomes are still closure-acceptable.

3. **Historical by-run artifacts include pre-hardening semantic patterns.**  
   Even if canonical output is coherent, skeptics can cite inconsistent legacy runs unless governance explicitly classifies them.

4. **Anti-repeat governance was not yet strict enough.**  
   Reassessment can keep reopening the same fragility claim without objective disconfirmability triggers.

---

## 4) Scope and Non-Goals

## In Scope

- SK-H1 pass-4 residual only (multimodal robustness under fixed policy lane).
- Seed/method/size robustness framing for coupling inference.
- Artifact/checker/report language synchronization to robustness class.
- Governance outputs required to classify residual as aligned/qualified/blocked.

## Out of Scope

- SK-C1 release sensitivity remediation.
- SK-H3/SK-H2/SK-M* fixes beyond direct SK-H1 dependencies.
- External data acquisition outside existing corpora and registered inputs.
- New decipherment claims.

---

## 5) Deterministic Closure Framework (H1.4 Lanes)

To prevent recurring ambiguity, H1.4 introduces explicit closure lanes:

## Lane A: Robust Conclusive Closure (`H1_4_ALIGNED`)

Allowed only when all are true:

- canonical lane remains conclusive,
- pre-registered robustness matrix meets stability thresholds,
- no policy-coherent lane emits inferential ambiguity beyond allowed tolerance,
- claim boundaries and checker/gate contracts all align.

## Lane B: Qualified Robustness Closure (`H1_4_QUALIFIED`)

Allowed only when all are true:

- canonical lane is policy-conclusive and coherent,
- at least one registered robustness lane remains inferentially ambiguous,
- ambiguity is bounded/documented with objective reopen triggers,
- public claims remain restricted to qualified language.

## Disallowed Ambiguous State

If neither lane is satisfied, classify as `H1_4_BLOCKED` (or `H1_4_INCONCLUSIVE` when evidence is incomplete).

---

## 6) Success Criteria (Exit Conditions)

SK-H1.4 is complete only when:

1. A closure lane (`H1_4_ALIGNED` or `H1_4_QUALIFIED`) is explicitly selected and machine-checkable.
2. Robustness matrix is pre-registered and reproducible (not post-hoc tuned).
3. Historical and canonical SK-H1 semantics are reconciled in governance artifacts.
4. SK-H1 checker/gate/report language cannot overstate lane entitlement.
5. Execution evidence + decision record define objective reopen conditions.

---

## 7) Workstreams

## WS-H1.4-A: Baseline Freeze and Residual Decomposition

**Goal:** Freeze pass-4 SK-H1 baseline and isolate every remaining fragility vector.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze canonical SK-H1 tuple from current confirmatory artifact. | New `reports/skeptic/SK_H1_4_ROBUSTNESS_REGISTER.md` | Baseline status/reason/adequacy/inference tuple captured with run_id. |
| A2 | Enumerate residual vectors: seed fragility, lane drift, legacy by-run semantics. | same | Each residual maps to a concrete control and verification command. |
| A3 | Define disconfirmability triggers for robustness claims. | same + decision section | Reopen conditions become objective instead of interpretive. |

### Verification

```bash
python3 - <<'PY'
import json
p='results/mechanism/anchor_coupling_confirmatory.json'
d=json.load(open(p))
r=d.get('results',{})
print(d.get('provenance',{}).get('run_id'))
print(r.get('status'), r.get('status_reason'))
print((r.get('adequacy') or {}).get('pass'), (r.get('inference') or {}).get('decision'))
PY
```

---

## WS-H1.4-B: Robustness Matrix Registration (Anti-Tuning)

**Goal:** Pre-register a bounded robustness matrix so stability is evaluated prospectively, not retrofitted.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define fixed matrix dimensions: seed band, cohort-size lanes, anchor method lanes, and allowed ranges. | `configs/skeptic/sk_h1_multimodal_policy.json` (or companion matrix config) | Matrix is explicit and versioned before reruns. |
| B2 | Define lane labeling and intent (`publication-default`, `stability-probe`, `adequacy-floor`, `method-variance`). | New `reports/skeptic/SK_H1_4_LANE_MATRIX.md` | Every lane has declared purpose and non-tuning constraint. |
| B3 | Add anti-selection rule: publication lane cannot be swapped post hoc based on preferred outcome. | same + policy note | Lane selection remains policy-bound. |

### Verification

```bash
python3 - <<'PY'
import json
p='configs/skeptic/sk_h1_multimodal_policy.json'
d=json.load(open(p))
print('anchor_method', d.get('anchor_method_name'))
print('seed', (d.get('sampling') or {}).get('seed'))
print('max_lines', (d.get('sampling') or {}).get('max_lines_per_cohort'))
PY
```

---

## WS-H1.4-C: Robustness Decision Contract

**Goal:** Convert seed-lane fragility from narrative into deterministic status logic.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add robustness summary fields (agreement ratio, ambiguity count, failing lanes list, robustness class). | confirmatory artifact schema + producer scripts | Robustness class is machine-readable and auditable. |
| C2 | Define allowed robustness classes (`ROBUST`, `MIXED`, `FRAGILE`) and status implications. | `configs/skeptic/sk_h1_multimodal_status_policy.json` | Status entitlement is deterministically tied to robustness class. |
| C3 | Add rule for mixed outcomes: canonical conclusive + mixed matrix -> must map to `H1_4_QUALIFIED`. | policy + checker | Mixed robustness can no longer be narrated as fully aligned. |

### Verification

```bash
python3 scripts/skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/skeptic/check_multimodal_coupling.py --mode release
```

---

## WS-H1.4-D: Producer and Artifact Coherence Hardening

**Goal:** Ensure produced artifacts preserve robustness context and historical coherence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Emit robustness-provenance block (lane id, seed/method/size, matrix id, run class). | `scripts/mechanism/run_5i_anchor_coupling.py` + artifact | Each run is traceable to a registered matrix lane. |
| D2 | Add by-run reconciliation index documenting pre-hardening runs vs current semantics. | New `reports/skeptic/SK_H1_4_LEGACY_RECONCILIATION.md` | Legacy runs cannot be misread as current policy regressions. |
| D3 | Add machine-checkable canonical-lane pinning metadata. | artifact + checker | Canonical publication lane is explicit and stable. |

### Verification

```bash
python3 scripts/mechanism/run_5i_anchor_coupling.py --seed 42 --max-lines-per-cohort 1600
python3 scripts/mechanism/run_5i_anchor_coupling.py --seed 2718 --max-lines-per-cohort 1600
```

---

## WS-H1.4-E: Gate and Health-Status Integration

**Goal:** Surface SK-H1 robustness lane directly in gate-health outputs.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add SK-H1 robustness summary fields to gate-health dependency snapshot. | `scripts/audit/build_release_gate_health_status.py` | Gate-health can report robustness class/lane without reading raw artifacts. |
| E2 | Ensure SK-H1 checker failures remain visible even when SK-C1 blocks release path. | gate scripts + health builder | H1 signals are inspectable under degraded gate state. |
| E3 | Add deterministic reason-code mapping for H1 robustness mismatches. | checker + gate-health builder | Root causes are actionable from status outputs alone. |

### Verification

```bash
python3 scripts/audit/build_release_gate_health_status.py
python3 - <<'PY'
import json
r=json.load(open('status/audit/release_gate_health_status.json'))['results']
print(r.get('status'), r.get('reason_code'))
print((r.get('dependency_snapshot') or {}).get('multimodal_status'))
PY
```

---

## WS-H1.4-F: Claim-Boundary and Report Synchronization

**Goal:** Keep narrative entitlement strictly bound to H1.4 lane class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Create H1.4 claim boundary register with lane-bound allowed/disallowed statements. | New `reports/skeptic/SK_H1_4_CLAIM_BOUNDARY_REGISTER.md` | Overreach is explicitly auditable. |
| F2 | Calibrate Phase 5/7 wording to robustness class semantics. | `results/reports/PHASE_5H_RESULTS.md`, `results/reports/PHASE_5I_RESULTS.md`, `results/reports/PHASE_5_FINAL_FINDINGS_SUMMARY.md`, `reports/human/PHASE_7_FINDINGS_SUMMARY.md`, `reports/human/PHASE_7B_RESULTS.md` | Language matches lane entitlement exactly. |
| F3 | Update multimodal policy docs for H1.4 robustness framework. | `docs/MULTIMODAL_COUPLING_POLICY.md`, `docs/REPRODUCIBILITY.md`, `docs/RUNBOOK.md` | Docs and artifact logic are coherent. |

### Verification

```bash
rg -n "INCONCLUSIVE_INFERENTIAL_AMBIGUITY|CONCLUSIVE_NO_COUPLING|status-gated|no conclusive claim is allowed|robustness" \
  docs/MULTIMODAL_COUPLING_POLICY.md \
  docs/REPRODUCIBILITY.md \
  docs/RUNBOOK.md \
  results/reports/PHASE_5H_RESULTS.md \
  results/reports/PHASE_5I_RESULTS.md \
  results/reports/PHASE_5_FINAL_FINDINGS_SUMMARY.md \
  reports/human/PHASE_7_FINDINGS_SUMMARY.md \
  reports/human/PHASE_7B_RESULTS.md
```

---

## WS-H1.4-G: Regression and Contract Locking

**Goal:** Prevent recurrence of SK-H1 robustness drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add tests for robustness-class/status coupling (including mixed-lane scenarios). | `tests/mechanism/test_anchor_coupling.py`, `tests/mechanism/test_anchor_coupling_contract.py` | Mixed outcomes cannot bypass qualified classification. |
| G2 | Extend SK-H1 checker tests for lane and robustness metadata contracts. | `tests/skeptic/test_multimodal_coupling_checker.py` | Missing/incoherent robustness fields fail deterministically. |
| G3 | Extend audit contract tests for SK-H1 gate-health/report markers. | `tests/audit/test_ci_check_contract.py`, `tests/audit/test_pre_release_contract.py`, `tests/audit/test_verify_reproduction_contract.py`, `tests/audit/test_release_gate_health_status_builder.py` | Gate/report drift is caught in CI. |

### Verification

```bash
python3 -m pytest -q \
  tests/mechanism/test_anchor_coupling.py \
  tests/mechanism/test_anchor_coupling_contract.py \
  tests/skeptic/test_multimodal_coupling_checker.py \
  tests/human/test_phase7_claim_guardrails.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py \
  tests/audit/test_release_gate_health_status_builder.py
```

---

## WS-H1.4-H: Governance Closeout and Anti-Repeat Controls

**Goal:** Prevent repeated reopening without new evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Add H1.4 decision record with lane choice and disconfirmability triggers. | New `reports/skeptic/SK_H1_4_DECISION_RECORD.md` | Final state is explicit and auditable. |
| H2 | Add execution status report template/path for implementation run. | `reports/skeptic/SKEPTIC_H1_4_EXECUTION_STATUS.md` (during execution) | Run evidence can be tracked systematically. |
| H3 | Link finding -> controls -> lane decision in audit log and plan tracker. | `AUDIT_LOG.md`, this plan | Future reassessment has traceable context and reopen criteria. |

### Verification

```bash
rg -n "SK-H1.4|H1_4_|seed|robustness|reopen" reports/skeptic AUDIT_LOG.md planning/skeptic/SKEPTIC_H1_4_EXECUTION_PLAN.md
```

---

## 8) Execution Order

1. WS-H1.4-A Baseline Freeze
2. WS-H1.4-B Robustness Matrix Registration
3. WS-H1.4-C Robustness Decision Contract
4. WS-H1.4-D Producer/Artifact Hardening
5. WS-H1.4-E Gate/Health Integration
6. WS-H1.4-F Claim-Boundary Synchronization
7. WS-H1.4-G Regression Locking
8. WS-H1.4-H Governance Closeout

Rationale:

- lock baseline and anti-tuning rules first,
- then enforce robustness semantics in code/checkers,
- then align reporting and governance, and only then close status.

---

## 9) Decision Matrix for SK-H1.4

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Canonical lane conclusive and robustness matrix meets pre-registered stability criteria. | `H1_4_ALIGNED` | "Multimodal no-coupling conclusion is robust across registered lanes." |
| Canonical lane conclusive but robustness matrix remains mixed/fragile; bounded claim controls are complete. | `H1_4_QUALIFIED` | "Canonical no-coupling signal is present, but robustness remains qualified across registered lanes." |
| Robustness semantics, artifacts, or report boundaries are inconsistent. | `H1_4_BLOCKED` | "SK-H1 remains unresolved due multimodal robustness governance inconsistency." |
| Evidence incomplete for lane assignment. | `H1_4_INCONCLUSIVE` | "SK-H1.4 status remains provisional pending complete robustness evidence." |

---

## 10) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H1.4-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline tuple and residual vectors frozen in `reports/skeptic/SK_H1_4_ROBUSTNESS_REGISTER.md`. |
| WS-H1.4-B Robustness Matrix Registration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Matrix lanes and anti-tuning constraints codified in policy + lane register. |
| WS-H1.4-C Robustness Decision Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Robustness class and H1.4 lane mapping are machine-enforced by producer/checker policy. |
| WS-H1.4-D Producer/Artifact Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Robustness provenance emitted; legacy reconciliation register added. |
| WS-H1.4-E Gate/Health Integration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Gate scripts and health snapshot now include deterministic H1.4 semantics. |
| WS-H1.4-F Claim Synchronization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Report/doc language aligned to lane-qualified robustness entitlement. |
| WS-H1.4-G Regression Locking | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Mechanism/checker/gate contract tests expanded and passing. |
| WS-H1.4-H Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Decision record, execution status, and audit log linkage completed. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 11) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Robustness remains mixed despite expanded matrix, preventing full aligned closure. | High | High | Support explicit `H1_4_QUALIFIED` lane with strict claim boundaries and reopen triggers. |
| R2 | Matrix expansion drifts into outcome-seeking tuning. | Medium | High | Pre-register matrix and enforce canonical-lane immutability rule. |
| R3 | Legacy by-run artifacts are interpreted as current regressions. | Medium | Medium | Add reconciliation register and explicit pre/post-hardening semantics. |
| R4 | Gate health noise from SK-C1 masks SK-H1 diagnostics. | Medium | Medium | Add independent SK-H1 robustness snapshot/reason paths in gate-health builder. |
| R5 | Report language overstates canonical run while matrix remains mixed. | Medium | High | Lane-bound claim register + checker marker enforcement + guardrail tests. |

---

## 12) Deliverables

Required deliverables for H1.4 execution pass:

1. `reports/skeptic/SK_H1_4_ROBUSTNESS_REGISTER.md`
2. `reports/skeptic/SK_H1_4_LANE_MATRIX.md`
3. `reports/skeptic/SK_H1_4_LEGACY_RECONCILIATION.md`
4. `reports/skeptic/SK_H1_4_CLAIM_BOUNDARY_REGISTER.md`
5. `reports/skeptic/SK_H1_4_DECISION_RECORD.md`
6. Updated SK-H1 policy/checker/docs/test artifacts per WS-H1.4-B through WS-H1.4-G
7. `reports/skeptic/SKEPTIC_H1_4_EXECUTION_STATUS.md`
8. `AUDIT_LOG.md` linkage from assessment -> controls -> closure lane

---

## 13) Closure Criteria

SK-H1 (pass-4 scope) can be marked closed for this cycle only when one is true:

1. `H1_4_ALIGNED`: robust conclusive status across the registered matrix, or
2. `H1_4_QUALIFIED`: canonical conclusive lane retained, robustness-mixed residual bounded with enforced governance and explicit reopen conditions.

If neither condition is met, SK-H1 remains **OPEN**.
