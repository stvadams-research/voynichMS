# Execution Plan: Skeptic Closure-Conditionality Hardening (SK-M1)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-M1` (listed as Medium in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and execution report reflect implementation outcomes.

---

## 1) Objective

Address `SK-M1` by removing closure-language contradictions that enable the "stopped too early" skeptic attack.

This plan targets the specific inconsistency identified in the assessment:

1. Some documents use terminal closure language ("formally closed", "no further amount ... will help").
2. Other documents correctly specify reopening criteria.
3. Skeptic can frame this as internal inconsistency and overreach.

---

## 2) SK-M1 Problem Statement

From `SK-M1`:

- Comparative boundary statement asserts no further text-internal comparison will help in `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md:15`.
- Reopening criteria are explicitly defined in `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:34` through `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:38`.

Core skeptic attack:

- "You assert exhaustion and also admit reopening criteria; closure should be conditional, not terminal."

---

## 3) Scope and Non-Goals

## In Scope

- Closure-language policy for conditional vs terminal wording.
- Cross-document closure consistency across comparative and final summary artifacts.
- Canonical reopening criteria references for all closure statements.
- Automated checks to prevent future terminal-overreach regressions.
- Governance/audit traceability for closure decisions and residual uncertainty.

## Out of Scope

- New empirical model work not needed for wording/consistency closure.
- Re-adjudication of SK-H1/SK-H2/SK-H3 technical findings except where wording dependencies exist.
- Historical/authorial interpretation claims beyond closure-condition framing.

---

## 4) Success Criteria (Exit Conditions)

`SK-M1` is considered closed only if all criteria below are met:

1. Closure statements in targeted docs are explicitly conditional and framework-bounded.
2. Reopening criteria are consistently referenced where closure language appears.
3. No targeted public document retains terminal wording that conflicts with reopening criteria.
4. A canonical closure-conditionality policy and decision taxonomy exist.
5. CI/release guardrails fail on contradictory closure patterns in tracked files.
6. Audit trail links SK-M1 finding -> policy -> edits -> verification results.

---

## 5) Workstreams

## WS-M1-A: Closure Conditionality Policy

**Goal:** Define allowed closure-language classes and prohibited terminal patterns.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define closure taxonomy (for example `FRAMEWORK_CONDITIONAL_CLOSURE`, `DEFERRED_REOPENABLE`, `INCONCLUSIVE`). | `docs/CLOSURE_CONDITIONALITY_POLICY.md` (new) | Taxonomy and examples documented. |
| A2 | Define prohibited contradiction patterns and required closure markers. | `configs/skeptic/sk_m1_closure_policy.json` (new) | Machine-readable policy versioned. |
| A3 | Define canonical reopening criteria reference block for closure docs. | same + docs | Reopening block template documented. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/skeptic/sk_m1_closure_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-M1-B: Closure Claim Inventory and Contradiction Register

**Goal:** Enumerate all closure assertions and mark contradiction risk.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Inventory closure claims and classify as conditional vs terminal. | `reports/skeptic/SK_M1_CLOSURE_REGISTER.md` (new) | All targeted closure claims listed with status. |
| B2 | Map each claim to reopening criteria reference or identify missing linkage. | same | Every closure claim has criteria linkage or remediation flag. |
| B3 | Mark high-risk contradictory phrases for rewrite. | same | Clear remediation queue created. |

### Verification

```bash
rg -n "formally closed|No further amount|remains closed|terminal|exhaust" \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-M1-C: Comparative and Closure Document Calibration

**Goal:** Rewrite contradictory closure phrasing into conditional, criteria-bound wording.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Reframe Phase B boundary statement from absolute "no further amount..." to framework-bounded conditional closure. | `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md` | Boundary section no longer reads terminal against reopening logic. |
| C2 | Rephrase any "formally closed" comparative language to criteria-bound closure language. | `reports/comparative/PHASE_B_SYNTHESIS.md` | Comparative closure aligns with reopening conditions. |
| C3 | Ensure Phase 4.5 closure summary language remains explicitly conditional and references reopening criteria consistently. | `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md` | No internal contradiction between closure and reopening sections. |
| C4 | Align other top-level closure docs where wording can reintroduce SK-M1 attack surface. | `results/reports/FINAL_PHASE_3_3_REPORT.md`, related summaries | Closure language harmonized across public docs. |

### Verification

```bash
rg -n "No further amount|formally closed|PROJECT CLOSED|remains closed|Criteria for Reopening|framework-bounded" \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-M1-D: Canonical Reopening Criteria Linkage

**Goal:** Centralize and standardize reopening-criteria references.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Create canonical reopening criteria reference document. | `docs/REOPENING_CRITERIA.md` (new) | Single source of truth exists. |
| D2 | Link all closure-bearing docs to canonical criteria source. | comparative/final closure docs | Every closure doc references canonical criteria. |
| D3 | Add explicit "what could reopen this conclusion" block where missing. | targeted docs | Reopenability is explicit and standardized. |

### Verification

```bash
rg -n "Reopening|Gatekeeper|REOPENING_CRITERIA|what could reopen" docs reports
```

---

## WS-M1-E: Automated Closure Guardrails

**Goal:** Prevent regression to contradictory terminal closure wording.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Implement SK-M1 checker for contradictory closure patterns and missing criteria markers. | `scripts/skeptic/check_closure_conditionality.py` (new) | Checker exits non-zero on SK-M1 violations. |
| E2 | Add tests for pass/fail/allowlist behavior. | `tests/skeptic/test_closure_conditionality_checker.py` (new) | Deterministic policy coverage. |
| E3 | Integrate SK-M1 checker into CI/release paths. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh` | Guard runs automatically. |

### Verification

```bash
python3 scripts/skeptic/check_closure_conditionality.py
python3 -m pytest -q tests/skeptic/test_closure_conditionality_checker.py
```

---

## WS-M1-F: Governance and Audit Traceability

**Goal:** Make closure conditionality decisions auditable and durable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add SK-M1 section to reproducibility/governance docs. | `docs/REPRODUCIBILITY.md`, related governance docs | Contributor workflow includes SK-M1 policy checks. |
| F2 | Add execution status report template for SK-M1 pass. | `reports/skeptic/SKEPTIC_M1_EXECUTION_STATUS.md` (during execution) | File records all changes/tests/residuals. |
| F3 | Add audit log entry mapping finding -> fixes -> residual risk. | `AUDIT_LOG.md` | End-to-end traceability present. |

### Verification

```bash
rg -n "SK-M1|closure conditionality|reopening criteria" docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M1-A (policy/taxonomy first)
2. WS-M1-B (inventory and contradiction mapping)
3. WS-M1-C (document calibration)
4. WS-M1-D (canonical reopening criteria linkage)
5. WS-M1-E (automated guardrails)
6. WS-M1-F (governance/audit trace)

Rationale:

- Do not rewrite closure language before policy and contradiction mapping are defined.

---

## 7) Decision Matrix for SK-M1 Closure Status

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Conditional closure wording aligned + reopening criteria linked across all tracked docs | `CONDITIONAL_CLOSURE_ALIGNED` | "Closure is framework-bounded and explicitly reopenable under defined criteria." |
| Most docs aligned but one or more non-critical phrasing caveats remain | `CONDITIONAL_CLOSURE_QUALIFIED` | "Closure framing is largely aligned with minor residual wording caveats." |
| Any tracked doc retains terminal wording that contradicts reopening criteria | `CONTRADICTORY_CLOSURE_BLOCKED` | "Closure claim blocked until contradiction is removed." |
| Evidence base insufficient to classify closure conditionally | `INCONCLUSIVE_CLOSURE_SCOPE` | "Closure scope remains provisional pending policy-complete alignment." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M1-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M1 closure-conditionality policy doc and machine-readable policy config. |
| WS-M1-B Inventory/Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M1 closure register mapping contradictory phrases to calibrated closure markers. |
| WS-M1-C Document Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Calibrated closure language in comparative and final reports to framework-bounded reopenable wording. |
| WS-M1-D Reopening Linkage | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added canonical reopening criteria doc and cross-referenced all tracked closure-bearing docs. |
| WS-M1-E Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M1 checker/tests and integrated enforcement into CI and pre-release scripts. |
| WS-M1-F Governance/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated reproducibility guidance, added execution status report, and logged SK-M1 audit decisions. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Over-softening language dilutes valid structural conclusions. | Medium | Medium | Use taxonomy-driven edits with explicit evidence references, not blanket weakening. |
| R2 | Inconsistent updates across comparative/final docs create new contradictions. | High | High | Maintain closure register and canonical reopening reference document. |
| R3 | Guardrails trigger false positives for legitimate technical closure phrasing. | Medium | Medium | Add scoped allowlist and tests for approved phrases. |
| R4 | Future edits reintroduce terminal wording without criteria linkage. | Medium | High | Integrate checker into CI and pre-release path. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M1 closure-conditionality policy and machine-readable config.
2. Closure contradiction register with remediation mapping.
3. Calibrated comparative/final closure language aligned with reopening criteria.
4. Canonical reopening criteria document and cross-references.
5. Automated SK-M1 checker and tests integrated into CI/release checks.
6. SK-M1 execution status report under `reports/skeptic/`.
7. Audit log entry documenting SK-M1 decisions and residual risk.
