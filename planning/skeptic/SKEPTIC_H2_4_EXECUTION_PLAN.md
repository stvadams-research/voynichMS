# Execution Plan: Skeptic Claim-Entitlement Closure (SK-H2.4)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
**Finding Target:** `SK-H2` (pass-4 residual; coupled with SK-M1 operationally)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. See `reports/skeptic/SKEPTIC_H2_4_EXECUTION_STATUS.md` for command evidence and outcomes.

---

## 1) Objective

Resolve the pass-4 `SK-H2` residual as fully as feasible by making claim entitlement deterministic, auditable, and resistant to repeated reopening.

Pass-4 residual summary:

- closure language is currently qualified and policy-consistent, but
- entitlement remains operationally contingent on degraded gate health.

Primary objective:

1. convert operational contingency from narrative convention into strict machine-enforced entitlement,
2. expand coverage so all public closure surfaces are guarded (not only a narrow subset), and
3. define anti-repeat closure criteria so SK-H2 is not reopened again without new gate evidence.

---

## 2) Pass-4 SK-H2 Problem Statement

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`:

- `SK-H2 / SK-M1 (Medium)` remains residual because closure wording is still contingent on gate health.
- Evidence references in pass-4 assessment:
  - `README.md:53`
  - `README.md:55`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:66`
  - `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md:68`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md:75`
  - `results/reports/FINAL_PHASE_3_3_REPORT.md:77`
  - `reports/comparative/PHASE_B_SYNTHESIS.md:38`
  - `reports/comparative/PHASE_B_SYNTHESIS.md:43`

Operational context in same assessment:

- release-path gate health is degraded due SK-C1 blocker (missing release sensitivity artifact).
- therefore claim class is qualified and reopenable by design.

Residual skeptic leverage:

- "Your language is better, but entitlement is still a dependent operational state, not a stable closure class."

---

## 3) Fourth-Attempt Retrospective (Why H2 -> H2.2 Still Left Residual)

This fourth-attempt plan is explicitly designed around the repeat pattern:

1. **Policy exists, but closure class remains dependency-driven.**  
   Prior passes calibrated wording, yet SK-H2 can still be repeatedly flagged whenever gate health is degraded.

2. **Coverage is strong but still partial in practice.**  
   Guardrails are centered on key files; repeated reassessment risk remains if new summary surfaces are added without equivalent controls.

3. **Entitlement state is visible but not yet a first-class SK-H2 closure artifact.**  
   H2 status is inferred from multiple checks instead of a dedicated deterministic H2 closure lane.

4. **Anti-repeat governance criteria were not explicit enough.**  
   Prior outputs improved policy, but did not hard-lock objective reopen triggers for SK-H2 itself.

---

## 4) Scope and Non-Goals

## In Scope

- SK-H2 claim-boundary and entitlement semantics for pass-4 residual.
- Operational coupling between claim language and gate-health artifact.
- Expanded checker/test/doc coverage for all high-visibility closure surfaces.
- Governance artifacts for deterministic SK-H2 closure decisioning.

## Out of Scope

- Direct remediation of SK-C1 release sensitivity artifact production.
- Re-running scientific experiments or changing empirical conclusions.
- Non-H2 skeptic findings except where required for consistency hooks.

---

## 5) Deterministic H2.4 Closure Framework

To prevent a fifth repetition, SK-H2.4 uses explicit closure lanes:

## Lane A: Entitlement-Aligned Closure (`H2_4_ALIGNED`)

Allowed only when all are true:

- gate health class is `GATE_HEALTH_OK`,
- all claim/closure checkers pass in CI and release modes,
- all tracked public docs are in allowed claim class for healthy-gate state,
- no entitlement drift or stale gate-health artifact detected.

## Lane B: Qualified Contingent Closure (`H2_4_QUALIFIED`)

Allowed only when all are true:

- gate health class is `GATE_HEALTH_DEGRADED`,
- all tracked public docs explicitly declare contingent/qualified closure posture,
- checkers enforce degraded-state markers and ban over-assertive language,
- dependency on SK-C1 blocker is explicit and auditable.

## Disallowed Ambiguous State

If neither lane is satisfied, classify as:

- `H2_4_BLOCKED` (policy/checker/report mismatch), or
- `H2_4_INCONCLUSIVE` (missing/incomplete entitlement evidence).

---

## 6) Success Criteria (Exit Conditions)

SK-H2.4 is complete only when:

1. H2.4 closure lane (`H2_4_ALIGNED` or `H2_4_QUALIFIED`) is machine-derived and explicit.
2. Claim-entitlement rules cover all public closure surfaces used by skeptic assessments.
3. Gate-health dependency is freshness-checked and not stale.
4. Degraded-state and healthy-state claim policies are both enforced in tests.
5. Decision record defines objective reopen triggers and anti-repeat constraints.

---

## 7) Workstreams

## WS-H2.4-A: Baseline Freeze and Residual Decomposition

**Goal:** Freeze pass-4 SK-H2 residual and map each remaining issue to deterministic controls.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze canonical SK-H2 residual evidence tuple from pass-4 assessment and current gate-health artifact. | New `reports/skeptic/SK_H2_4_ASSERTION_REGISTER.md` | Baseline includes claim sites, gate status, and residual rationale. |
| A2 | Classify residual vectors (`coverage_gap`, `state_dependency`, `staleness_risk`, `governance_gap`). | same | Every vector has mapped controls and verification commands. |
| A3 | Define objective disconfirmability triggers for SK-H2 residual reopening. | same + decision section | Reopen conditions are objective, not interpretive. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('status/audit/release_gate_health_status.json'))['results']
print(r.get('status'), r.get('reason_code'), r.get('allowed_claim_class'), r.get('allowed_closure_class'))
PY
```

---

## WS-H2.4-B: Assertion Surface Expansion and Dependency Matrix

**Goal:** Ensure SK-H2 guardrails cover all relevant public claim surfaces, not only legacy targets.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Expand claim inventory to include comparative synthesis and any additional public closure summaries referenced by skeptics. | New `reports/skeptic/SK_H2_4_GATE_DEPENDENCY_MATRIX.md` | Full inventory includes file ownership, claim class, dependency, risk. |
| B2 | Add explicit dependency graph from each claim surface to gate-health keys and reason codes. | same | Every claim maps to required entitlement predicates. |
| B3 | Identify uncovered files currently outside checker tracked scopes. | same | Coverage gaps are explicit and prioritized. |

### Verification

```bash
rg -n "Operational Entitlement State|GATE_HEALTH_DEGRADED|qualified|reopen" \
  README.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md
```

---

## WS-H2.4-C: Policy and Entitlement Schema Hardening

**Goal:** Upgrade policy from marker presence to deterministic state-policy contract.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add explicit H2.4 closure lane schema (`H2_4_*`) and lane derivation rules keyed to gate status and checker outputs. | `configs/skeptic/sk_h2_claim_language_policy.json` (or companion policy) | Lane derivation is machine-readable and versioned. |
| C2 | Add freshness policy for gate-health artifact (`max_age_seconds`, required provenance keys). | H2 policy + docs | Stale gate-state input cannot silently pass H2 checks. |
| C3 | Define healthy/degraded banned and required claim patterns as separate deterministic classes. | H2 policy | Claim class entitlement is mode- and state-aware. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/skeptic/sk_h2_claim_language_policy.json'))
print('version', p.get('version'))
print('gate policy keys', sorted((p.get('gate_health_policy') or {}).keys()))
PY
```

---

## WS-H2.4-D: Gate-Health Coupling and Freshness Guarantees

**Goal:** Ensure SK-H2 entitlement uses current, coherent operational status.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Extend gate-health builder output with fields needed for H2 lane derivation and freshness checks (if missing). | `scripts/audit/build_release_gate_health_status.py` | H2 dependencies can be derived without heuristic parsing. |
| D2 | Add deterministic stale-artifact diagnostics (`STALE_GATE_HEALTH_ARTIFACT`, timestamp skew checks). | builder + checkers | Stale gate evidence is detected and fail-closed. |
| D3 | Add by-run parity requirement between gate-health snapshot and H2 claim checks. | status artifact + checker rules | H2 checks are tied to current run context. |

### Verification

```bash
python3 scripts/audit/build_release_gate_health_status.py
python3 - <<'PY'
import json
r=json.load(open('status/audit/release_gate_health_status.json'))['results']
print(r.get('status'), r.get('reason_code'))
print('generated_at', r.get('generated_at'))
PY
```

---

## WS-H2.4-E: Checker and Pipeline Enforcement Upgrade

**Goal:** Prevent policy/report drift and enforce H2.4 lane semantics in CI/release paths.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Extend `check_claim_boundaries.py` to validate H2.4 lane derivation and freshness predicates. | `scripts/skeptic/check_claim_boundaries.py` | Checker fails on lane mismatch, stale gate health, or over-assertion. |
| E2 | Extend `check_closure_conditionality.py` for explicit H2-M1 consistency and cross-file parity. | `scripts/skeptic/check_closure_conditionality.py` | H2/M1 divergence cannot pass silently. |
| E3 | Add optional cross-check script for entitlement coherence across H2/M1/M3. | New `scripts/skeptic/check_claim_entitlement_coherence.py` (if needed) | Unified pass/fail signal for SK-H2 closure lane state. |
| E4 | Ensure CI/pre-release/verify scripts run H2.4 checks in the same order and mode semantics. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | No pipeline path bypasses H2.4 enforcement. |

### Verification

```bash
python3 scripts/skeptic/check_claim_boundaries.py --mode ci
python3 scripts/skeptic/check_claim_boundaries.py --mode release
python3 scripts/skeptic/check_closure_conditionality.py --mode ci
python3 scripts/skeptic/check_closure_conditionality.py --mode release
```

---

## WS-H2.4-F: Report and README Entitlement Synchronization

**Goal:** Normalize claim wording using one entitlement template to avoid manual drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Define a canonical entitlement statement template with strict required markers per lane. | `docs/CLAIM_BOUNDARY_POLICY.md`, `docs/CLOSURE_CONDITIONALITY_POLICY.md` | Single template used across tracked public docs. |
| F2 | Apply template to all tracked closure surfaces including comparative synthesis docs. | `README.md`, `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md`, `reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md`, `reports/comparative/PHASE_B_SYNTHESIS.md` | Marker and wording parity achieved across surfaces. |
| F3 | Enforce explicit dependency statement to SK-C1 when degraded lane is active. | same | Contingency source is explicit and consistent. |

### Verification

```bash
rg -n "Operational Entitlement State|status/audit/release_gate_health_status.json|operationally contingent|qualified/reopenable" \
  README.md \
  results/reports/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md \
  reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/comparative/PHASE_B_SYNTHESIS.md
```

---

## WS-H2.4-G: Regression and Contract Locking

**Goal:** Ensure H2.4 controls survive future reassessments.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add tests for lane derivation and stale gate-health fail-closed behavior. | `tests/skeptic/test_claim_boundary_checker.py`, `tests/skeptic/test_closure_conditionality_checker.py` | State-lane mismatch regressions are caught automatically. |
| G2 | Add contract tests for gate script invocation and mode parity. | `tests/audit/test_ci_check_contract.py`, `tests/audit/test_pre_release_contract.py`, `tests/audit/test_verify_reproduction_contract.py` | Pipeline bypass regressions are blocked. |
| G3 | Add gate-health builder tests for H2-required dependency fields. | `tests/audit/test_release_gate_health_status_builder.py` | H2 checker prerequisites remain stable. |

### Verification

```bash
python3 -m pytest -q \
  tests/skeptic/test_claim_boundary_checker.py \
  tests/skeptic/test_closure_conditionality_checker.py \
  tests/skeptic/test_report_coherence_checker.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py \
  tests/audit/test_release_gate_health_status_builder.py
```

---

## WS-H2.4-H: Governance Closeout and Anti-Repeat Controls

**Goal:** Make SK-H2 closure rationale and reopen conditions explicit.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Add H2.4 claim-boundary register with lane-bound allowed/disallowed statements. | New `reports/skeptic/SK_H2_4_CLAIM_BOUNDARY_REGISTER.md` | Claim entitlement boundaries are auditable. |
| H2 | Add H2.4 decision record with lane choice and objective reopen triggers. | New `reports/skeptic/SK_H2_4_DECISION_RECORD.md` | Reassessment can distinguish unchanged residual vs real regression. |
| H3 | Add execution status template/path for implementation pass and audit-log linkage requirements. | `reports/skeptic/SKEPTIC_H2_4_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | Full traceability from finding -> controls -> lane status. |

### Verification

```bash
rg -n "SK-H2.4|H2_4_|entitlement|gate health|reopen" \
  reports/skeptic \
  planning/skeptic/SKEPTIC_H2_4_EXECUTION_PLAN.md \
  AUDIT_LOG.md
```

---

## 8) Execution Order

1. WS-H2.4-A Baseline Freeze
2. WS-H2.4-B Assertion Surface Expansion
3. WS-H2.4-C Policy Hardening
4. WS-H2.4-D Gate-Health Coupling/Freshness
5. WS-H2.4-E Checker/Pipeline Enforcement
6. WS-H2.4-F Report Synchronization
7. WS-H2.4-G Regression Locking
8. WS-H2.4-H Governance Closeout

Rationale:

- freeze residual and scope first,
- then define deterministic policy/state,
- then enforce through checkers and tests,
- finally formalize anti-repeat governance artifacts.

---

## 9) Decision Matrix for SK-H2.4

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Gate health is healthy and all H2 checks pass with aligned claim surfaces. | `H2_4_ALIGNED` | "Closure language is framework-bounded and operationally entitled under healthy gate state." |
| Gate health is degraded but all claim surfaces are correctly qualified and checker-enforced. | `H2_4_QUALIFIED` | "Closure language remains framework-bounded and operationally contingent pending gate recovery." |
| Gate/claim/checker mismatch, stale gate artifact, or uncovered claim surface found. | `H2_4_BLOCKED` | "SK-H2 remains unresolved due entitlement coherence inconsistency." |
| Evidence is incomplete for lane assignment. | `H2_4_INCONCLUSIVE` | "SK-H2.4 status remains provisional pending complete entitlement evidence." |

---

## 10) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H2.4-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline tuple and residual vectors frozen in `reports/skeptic/SK_H2_4_ASSERTION_REGISTER.md`. |
| WS-H2.4-B Surface Expansion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Assertion inventory and dependency matrix expanded to comparative + summary closure surfaces. |
| WS-H2.4-C Policy Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | H2/M1 policies upgraded with H2.4 lane schema and freshness-aware gate checks. |
| WS-H2.4-D Gate Coupling/Freshness | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Gate-health artifact now emits H2.4 fields and freshness-compatible timestamps. |
| WS-H2.4-E Checker Enforcement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Claim, closure, and cross-policy coherence checkers enforce lane/state parity. |
| WS-H2.4-F Report Synchronization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Tracked closure docs now include explicit degraded-state SK-C1 dependency markers. |
| WS-H2.4-G Regression Locking | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Skeptic and audit contract tests expanded for freshness/lane/coherence checks. |
| WS-H2.4-H Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | H2.4 registers, decision record, execution status, and audit linkage completed. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 11) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | SK-H2 remains repeatedly reopened whenever SK-C1 is unresolved. | High | High | Formalize H2.4 lane model with objective dependency triggers and anti-repeat clause. |
| R2 | New public summary files bypass H2 policy coverage. | High | High | Expand assertion inventory and tracked file coverage; add coverage-gap checks. |
| R3 | Stale gate-health artifact yields false entitlement pass. | Medium | High | Add freshness policy and stale-artifact fail-closed checks. |
| R4 | Overly rigid wording rules create brittle false positives. | Medium | Medium | Keep lane-scoped allowlist and policy-versioned exceptions with tests. |
| R5 | Checker parity drifts across CI, pre-release, and verify scripts. | Medium | High | Add contract tests for invocation order and mode parity. |

---

## 12) Deliverables

Required deliverables for H2.4 execution pass:

1. `reports/skeptic/SK_H2_4_ASSERTION_REGISTER.md`
2. `reports/skeptic/SK_H2_4_GATE_DEPENDENCY_MATRIX.md`
3. `reports/skeptic/SK_H2_4_CLAIM_BOUNDARY_REGISTER.md`
4. `reports/skeptic/SK_H2_4_DECISION_RECORD.md`
5. Policy/checker/test updates across H2/M1/gate-health integration workstreams
6. `reports/skeptic/SKEPTIC_H2_4_EXECUTION_STATUS.md`
7. `AUDIT_LOG.md` linkage from pass-4 SK-H2 finding -> controls -> lane decision

---

## 13) Closure Criteria

SK-H2 (pass-4 scope) can be marked closed for this cycle only when one is true:

1. `H2_4_ALIGNED`: gate-healthy entitlement with fully aligned claim surfaces, or
2. `H2_4_QUALIFIED`: gate-degraded entitlement with fully enforced qualified/contingent claim boundaries and explicit dependency rationale.

If neither condition is met, SK-H2 remains **OPEN**.
