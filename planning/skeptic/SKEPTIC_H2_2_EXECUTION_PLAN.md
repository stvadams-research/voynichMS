# Execution Plan: Skeptic Operational Claim-Entitlement Hardening (SK-H2.2 / SK-M1.2)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-H2 / SK-M1` (Medium residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and closeout artifacts updated.

---

## 1) Objective

Address the pass-2 `SK-H2 / SK-M1` residual by hardening closure and non-claim language so it remains defensible even when operational gates are degraded.

This plan targets the specific residual skeptic leverage from the assessment:

1. Boundary and non-claim language is materially improved.
2. Reopening criteria are explicit.
3. Closure language is still assertive enough that skeptics can challenge scope when operational gate health is failing.

Desired endpoint:

1. claim/closure text is operationally entitled (strength tracks gate status), and
2. public narrative cannot outrun release/CI evidence contract state.

---

## 2) SK-H2 / SK-M1 Problem Statement (Pass 2)

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Improvements already present:
  - Boundary and non-claim structure is explicit (`README.md`, `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md`).
  - Conditional reopening language is explicit (`reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`, `reports/comparative/PHASE_B_SYNTHESIS.md`, `docs/REOPENING_CRITERIA.md`).
- Residual:
  - Closure remains assertive enough for skeptic scope attack when operational gates fail.
- Context from same pass:
  - `pre_release_check.sh` failed.
  - `verify_reproduction.sh` failed.
  - `ci_check.sh` failed.

Core skeptic attack surface:

- "You improved wording, but claim strength still outpaces current operational evidence integrity."

---

## 3) Scope and Non-Goals

## In Scope

- SK-H2/SK-M1 residual hardening for pass-2.
- Operationally contingent claim-entitlement model (text strength tied to gate health).
- Cross-document closure/claim coherence for targeted public artifacts.
- Checker/test/CI enforcement preventing over-assertive language under failed gate state.
- Governance and audit traceability for H2.2/M1.2 decisions.

## Out of Scope

- Fixing underlying SK-C1/SK-C2 technical failures directly (this plan consumes their status as dependencies).
- New empirical experiments or reinterpretation of technical findings.
- Reworking SK-H1, SK-H3, SK-M2, SK-M3, SK-M4 beyond dependency references.

---

## 4) Success Criteria (Exit Conditions)

`SK-H2 / SK-M1` pass-2 residual is considered closed only if all criteria below are satisfied:

1. Claim and closure wording in tracked public docs is explicitly gated by operational evidence health.
2. No tracked document can emit high-confidence closure language when critical operational gates are failing.
3. Canonical gate-health artifact exists and is consumed by policy/checkers.
4. Claim-boundary and closure-conditionality policies include gate-dependent entitlement rules.
5. CI/release guardrails fail closed on entitlement mismatch (assertive language + failing gate state).
6. Audit trail links finding -> policy -> text constraints -> checker/test evidence.

---

## 5) Workstreams

## WS-H2M1.2-A: Residual Baseline and Assertion-Risk Register

**Goal:** Build an explicit map from current claim/closure statements to their operational preconditions.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Inventory all closure and non-claim assertions in tracked files and classify strength (qualified vs assertive). | New `reports/skeptic/SK_H2_M1_2_ASSERTION_REGISTER.md` | Register captures all tracked assertions and strength tags. |
| A2 | Map each assertion to required operational prerequisites (CI contract pass, release-check pass, reproduction-check pass). | same | Every assertion has explicit entitlement dependency mapping. |
| A3 | Mark residual over-assertion candidates where current text is stronger than current gate posture. | same | Remediation queue is explicit and prioritized. |

### Verification

```bash
rg -n "framework-bounded|conditionally|What This Does Not Claim|Criteria for Reopening|closed|closure" \
  README.md \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-H2M1.2-B: Gate-Dependent Entitlement Policy Extension

**Goal:** Extend SK-H2/SK-M1 policies so allowable language class is conditional on operational gate state.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add gate-dependent entitlement sections to claim-boundary policy (`allowed_claim_class_by_gate_state`). | `configs/skeptic/sk_h2_claim_language_policy.json`, `docs/CLAIM_BOUNDARY_POLICY.md` | SK-H2 policy can encode degraded entitlement under failed gates. |
| B2 | Add gate-dependent closure constraints (`allowed_closure_class_by_gate_state`). | `configs/skeptic/sk_m1_closure_policy.json`, `docs/CLOSURE_CONDITIONALITY_POLICY.md` | SK-M1 policy enforces conditional closure semantics tied to gate health. |
| B3 | Define shared reason-code taxonomy for entitlement downgrades (`GATE_CONTRACT_BLOCKED`, `RELEASE_EVIDENCE_UNQUALIFIED`, etc.). | same + new section in `docs/REOPENING_CRITERIA.md` | Residual states become machine-readable and narrative-stable. |

### Verification

```bash
python3 - <<'PY'
import json
h2=json.load(open('configs/skeptic/sk_h2_claim_language_policy.json'))
m1=json.load(open('configs/skeptic/sk_m1_closure_policy.json'))
print('h2_keys', sorted(h2.keys()))
print('m1_keys', sorted(m1.keys()))
PY
```

---

## WS-H2M1.2-C: Canonical Operational Gate-Health Artifact

**Goal:** Establish a single machine-readable source of truth for claim entitlement prerequisites.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define canonical gate-health artifact schema (`ci_check`, `pre_release_check`, `verify_reproduction`, reason codes, timestamp, mode). | New `status/audit/release_gate_health_status.json` contract | Gate health can be consumed deterministically by policy checkers. |
| C2 | Implement/define artifact builder from current gate outputs. | New `scripts/audit/build_release_gate_health_status.py` | Builder emits deterministic artifact and fail reasons. |
| C3 | Add by-run trace convention for gate-health snapshots. | `status/audit/by_run/*` | Entitlement decisions are reproducible per run context. |

### Verification

```bash
python3 scripts/audit/build_release_gate_health_status.py
python3 - <<'PY'
import json
p=json.load(open('status/audit/release_gate_health_status.json'))
print(p.get('results', {}).get('status'))
print(sorted((p.get('results', {}).get('gates') or {}).keys()))
PY
```

---

## WS-H2M1.2-D: Narrative Calibration for Gate-Contingent Claims

**Goal:** Ensure public-facing closure language automatically reflects current operational entitlement class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Add standardized "Operational Entitlement State" block to tracked closure/summary docs. | `README.md`, `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md`, `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`, `reports/comparative/PHASE_B_SYNTHESIS.md` | Each doc declares current entitlement class and source artifact. |
| D2 | Calibrate assertive wording into gate-contingent wording where required by policy state. | same | No document overclaims relative to gate-health artifact. |
| D3 | Align non-claim and reopening sections with operational dependency language. | same + `docs/REOPENING_CRITERIA.md` | Reopenability and operational prerequisites are coherently linked. |

### Verification

```bash
rg -n "Operational Entitlement State|release_gate_health_status.json|conditionally|reopen|What This Does Not Claim" \
  README.md \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-H2M1.2-E: Checker/Test Hardening for Entitlement Coherence

**Goal:** Enforce that claim and closure language class cannot exceed current gate-backed entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Extend SK-H2 checker with optional gate-state enforcement (mode-aware). | `scripts/skeptic/check_claim_boundaries.py`, `tests/skeptic/test_claim_boundary_checker.py` | Checker fails when claim class exceeds allowed level for gate state. |
| E2 | Extend SK-M1 checker with gate-state closure constraints. | `scripts/skeptic/check_closure_conditionality.py`, `tests/skeptic/test_closure_conditionality_checker.py` | Checker blocks contradictory assertive closure under failed gates. |
| E3 | Add cross-check for report coherence between gate-health artifact and public docs. | `scripts/skeptic/check_report_coherence.py`, `configs/skeptic/sk_m3_report_coherence_policy.json`, `tests/skeptic/test_report_coherence_checker.py` | Coherence checker catches gate-state/report-language divergence. |
| E4 | Integrate entitlement checks into CI/pre-release/reproduction paths. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, audit contract tests | Operational pipeline enforces H2.2/M1.2 contracts automatically. |

### Verification

```bash
python3 scripts/skeptic/check_claim_boundaries.py
python3 scripts/skeptic/check_closure_conditionality.py --mode release
python3 scripts/skeptic/check_report_coherence.py --mode release
python3 -m pytest -q \
  tests/skeptic/test_claim_boundary_checker.py \
  tests/skeptic/test_closure_conditionality_checker.py \
  tests/skeptic/test_report_coherence_checker.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py
```

---

## WS-H2M1.2-F: Governance and Traceability Closeout

**Goal:** Keep the residual-to-remediation chain auditable and reusable for future skeptic passes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend SK-H2 and SK-M1 registers with entitlement dependencies and current gate-state assumptions. | `reports/skeptic/SK_H2_CLAIM_REGISTER.md`, `reports/skeptic/SK_M1_CLOSURE_REGISTER.md` | Registers include explicit gate-state coupling. |
| F2 | Add combined H2.2/M1.2 execution status template. | New `reports/skeptic/SKEPTIC_H2_2_EXECUTION_STATUS.md` | Execution pass can be documented consistently. |
| F3 | Add audit log linkage requirement for residual closure decisions and downgrade rationale. | `AUDIT_LOG.md` | Finding -> controls -> outcome trace is complete. |

### Verification

```bash
rg -n "SK-H2.2|SK-M1.2|entitlement|gate health|release_gate_health_status" \
  reports/skeptic AUDIT_LOG.md docs
```

---

## 6) Execution Order

1. WS-H2M1.2-A (baseline and assertion-risk map)
2. WS-H2M1.2-B (policy extension)
3. WS-H2M1.2-C (gate-health artifact)
4. WS-H2M1.2-D (narrative calibration)
5. WS-H2M1.2-E (checker/test hardening)
6. WS-H2M1.2-F (governance closeout)

Rationale:

- Define entitlement semantics and status source before rewriting text or enforcing new checks.

---

## 7) Decision Matrix for SK-H2.2 / SK-M1.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Gate-health artifact is healthy and claim/closure language is fully entitlement-aligned. | `H2_2_M1_2_ALIGNED` | "Closure and non-claim framing is calibrated and operationally entitled." |
| Language is calibrated and explicitly downgraded under failing gate state; no overclaim remains. | `H2_2_M1_2_QUALIFIED` | "Closure framing is bounded and operationally contingent pending gate recovery." |
| Policy/checker/report state is internally inconsistent or allows over-assertive language under failed gates. | `H2_2_M1_2_BLOCKED` | "Residual closure/claim scope remains vulnerable to skeptic process attack." |
| Evidence is incomplete to determine entitlement alignment. | `H2_2_M1_2_INCONCLUSIVE` | "H2.2/M1.2 status provisional pending gate-entitlement evidence." |

Execution outcome: `H2_2_M1_2_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H2M1.2-A Baseline/Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `reports/skeptic/SK_H2_M1_2_ASSERTION_REGISTER.md` with assertion/dependency mapping. |
| WS-H2M1.2-B Policy Extension | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended H2/M1 policy JSON plus boundary/closure/reopening docs for gate-dependent entitlement. |
| WS-H2M1.2-C Gate-Health Artifact | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `scripts/audit/build_release_gate_health_status.py`; generated canonical + by-run artifacts. |
| WS-H2M1.2-D Narrative Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated README/comparative/final closure docs with operational entitlement blocks and downgraded phrasing. |
| WS-H2M1.2-E Checker/Test Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended claim/closure checks for gate-degraded rules; added/updated skeptic and audit tests. |
| WS-H2M1.2-F Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated registers, reproducibility docs, and added execution status/audit trace. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Claim/closure language remains partially static while gate posture changes, causing drift. | High | High | Add canonical gate-health artifact and require marker references in tracked docs. |
| R2 | New entitlement rules duplicate existing H2/M1/M3 checks and create policy conflicts. | Medium | High | Consolidate on shared rule keys and add contract tests for policy compatibility. |
| R3 | Over-correction weakens legitimate bounded conclusions. | Medium | Medium | Use tiered claim classes rather than blanket softening. |
| R4 | Dependency on SK-C1/SK-C2 status artifacts introduces brittle coupling. | Medium | Medium | Use explicit fallback states and reason codes when dependent artifacts are unavailable. |
| R5 | Manual report edits bypass entitlement model. | Medium | High | Enforce in CI/pre-release/reproduction paths and report coherence checks. |

---

## 10) Deliverables

Required deliverables for the execution pass:

1. SK-H2/SK-M1 assertion register with operational dependency mapping.
2. Updated SK-H2 and SK-M1 policy files with gate-dependent entitlement logic.
3. Canonical release gate-health artifact and generation path.
4. Calibrated gate-contingent language across targeted public/closure docs.
5. Extended checkers/tests enforcing entitlement coherence.
6. CI/pre-release/reproduction integration for new entitlement checks.
7. Combined execution status report under `reports/skeptic/`.
8. Audit-log trace linking pass-2 residual to implemented controls.

---

## 11) Closure Criteria

`SK-H2 / SK-M1` pass-2 residual is closed only when:

1. Public closure and non-claim language class is machine-enforced against current gate-health status.
2. Failing operational gates force downgraded claim/closure wording in all tracked docs.
3. Claim-boundary, closure-conditionality, and report-coherence checks pass together without contradiction.
4. Governance artifacts document why any residual qualification remains and what would upgrade entitlement class.
