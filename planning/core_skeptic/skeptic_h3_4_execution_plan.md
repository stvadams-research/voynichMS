# Execution Plan: Skeptic Control-Comparability Closure Under Data-Availability Constraints (SK-H3.4)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
**Finding Target:** `SK-H3` (High, pass-4 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. See `reports/core_skeptic/SKEPTIC_H3_4_EXECUTION_STATUS.md` for command evidence and outcomes.

---

## 1) Objective

Resolve the recurring SK-H3 residual in a way that is complete, auditable, and non-cyclical.

This fourth-attempt plan is designed to prevent another loop where controls are improved but closure state remains ambiguous.

Primary objective:

1. establish a deterministic SK-H3 decision framework that cleanly distinguishes:
   - full-data conclusive closure, versus
   - qualified blocked closure due irrecoverable source gaps,
2. harden cross-artifact/gate/report semantics so SK-H3 state cannot drift, and
3. produce governance artifacts that explain why SK-H3 is (or is not) fully closable with current source data.

---

## 2) Pass-4 SK-H3 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`:

- SK-H3 remains high-risk because control comparability is still blocked at full-data scope.
- Canonical SK-H3 status remains bounded to available-subset evidence:
  - `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
    - `status=NON_COMPARABLE_BLOCKED`
    - `reason_code=DATA_AVAILABILITY`
    - `evidence_scope=available_subset`
    - `full_data_closure_eligible=false`
- Data-availability artifact remains blocked:
  - `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
    - `status=DATA_AVAILABILITY_BLOCKED`
    - `reason_code=DATA_AVAILABILITY`

Skeptic leverage that remains valid:

- "Comparability remains bounded to subset evidence and cannot support full-data closure."

---

## 3) Fourth-Attempt Retrospective (Why Prior Attempts Still Left Residual)

Based on H3 -> H3.2 -> H3.3 trajectory, prior attempts improved semantics and governance but did not eliminate repeat residual reporting because:

1. **Closure-class finalization remained underspecified.**
   Prior passes improved consistency, but did not lock a final, machine-enforced "terminal qualified" condition for irrecoverable-source scenarios.

2. **Feasibility boundary was documented but not formalized as a decision gate.**
   Missing pages were acknowledged, yet plan closure criteria still implied eventual full-data closure without a hard stop condition.

3. **Cross-layer language could still be interpreted as "pending fix" instead of "irrecoverable bounded state."**
   Even when artifacts were coherent, repeated reassessment keeps reopening the same unresolved high-level concern.

4. **Run-level freshness and semantic parity checks need stronger anti-staleness lock-in.**
   A correct status model is insufficient if stale or partially updated artifacts can reintroduce narrative inconsistency.

This H3.4 plan explicitly targets those four gaps.

---

## 4) Scope and Non-Goals

## In Scope

- SK-H3 closure semantics and comparability/data-availability artifact coherence.
- Explicit feasibility decisioning for missing-source-page scenarios.
- Available-subset evidence adequacy and bounded-claim enforcement.
- Gate/checker/report synchronization for SK-H3 status interpretation.
- Regression and governance hardening to prevent a fifth repetition of the same SK-H3 residual class.

## Out of Scope

- SK-C1 release sensitivity evidence production and release gate unblocking.
- SK-H1/SK-H2/SK-M1/SK-M2/SK-M3/SK-M4 remediation beyond direct SK-H3 dependencies.
- Acquiring external source pages not currently available in the approved corpus.

---

## 5) Deterministic Closure Framework (Dual-Lane)

To avoid repeated ambiguous outcomes, SK-H3.4 uses two explicit closure lanes:

## Lane A: Full-Data Conclusive Closure (`H3_4_ALIGNED`)

Allowed only when all are true:

- `missing_count == 0`
- `status != NON_COMPARABLE_BLOCKED`
- `evidence_scope == full_dataset`
- `full_data_closure_eligible == true`
- all SK-H3 semantic parity checks pass across checker/gates/reports

## Lane B: Irrecoverable Qualified Closure (`H3_4_QUALIFIED`)

Allowed only when all are true:

- missing pages are explicitly classified as approved irrecoverable source gaps,
- blocked reason remains exactly `DATA_AVAILABILITY`,
- available-subset status is policy-compliant and quality-scored,
- full-data closure is explicitly disallowed in artifacts and claims,
- governance artifacts contain a terminal rationale explaining why further engineering cannot produce full-data closure without new source data.

## Disallowed Ambiguous State

If neither lane is satisfied, outcome is `H3_4_BLOCKED` (or `H3_4_INCONCLUSIVE` if evidence is incomplete).

---

## 6) Success Criteria (Exit Conditions)

SK-H3.4 can be considered complete only when:

1. A closure lane (A or B) is explicitly selected and machine-checkable.
2. `CONTROL_COMPARABILITY_STATUS` and `CONTROL_COMPARABILITY_DATA_AVAILABILITY` are semantically synchronized across required keys.
3. Allowed/disallowed claim boundaries are synchronized with selected closure lane.
4. SK-H3 checker and gate scripts fail closed on stale, mismatched, or under-specified SK-H3 states.
5. A dedicated H3.4 governance package captures final rationale and prevents repeated reopening for the same unchanged evidence basis.

---

## 7) Workstreams

## WS-H3.4-A: Baseline Freeze and Issue Ledger

**Goal:** Freeze pass-4 SK-H3 evidence and map each residual to a closure gate.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-4 SK-H3 finding tuple from assessment and current canonical artifacts. | New `reports/core_skeptic/SK_H3_4_GAP_REGISTER.md` | Baseline values + evidence references captured. |
| A2 | Build issue->control->verification matrix for every SK-H3 residual. | same | No residual remains unassigned to a concrete control. |
| A3 | Define exact closure-lane decision predicates (A vs B) as checklist items. | same + plan section | Closure decision becomes deterministic and reproducible. |

### Verification

```bash
python3 - <<'PY'
import json
for p in [
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json',
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json'
]:
  r=json.load(open(p)).get('results',{})
  print(p, r.get('status'), r.get('reason_code'), r.get('evidence_scope'), r.get('full_data_closure_eligible'), r.get('missing_count'))
PY
```

---

## WS-H3.4-B: Irrecoverability and Feasibility Finalization

**Goal:** Convert irrecoverability from "context" into a terminal, enforced feasibility contract.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add explicit feasibility classification in SK-H3 policy (`full_data_feasibility`: `feasible`/`irrecoverable`). | `configs/core_skeptic/sk_h3_data_availability_policy.json` | Policy can machine-classify closure feasibility. |
| B2 | Add terminal rationale fields in data-availability artifact (why full-data closure is impossible with current source set). | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` producer/checker | Artifact carries explicit closure rationale and required metadata. |
| B3 | Enforce fail-closed checker rules for incomplete irrecoverability metadata. | `scripts/core_skeptic/check_control_data_availability.py` | Checker rejects ambiguous blocked states. |

### Verification

```bash
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

---

## WS-H3.4-C: Available-Subset Adequacy Hardening

**Goal:** Ensure subset lane is maximally defensible and quantitatively bounded.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Extend subset diagnostics to include minimum power/coverage indicators and confidence provenance. | `scripts/phase3_synthesis/run_control_matching_audit.py`, status artifact fields | Subset confidence class becomes quantitatively auditable. |
| C2 | Add explicit threshold-to-reason mapping for subset states (`QUALIFIED` vs `UNDERPOWERED` vs `BLOCKED`). | `configs/core_skeptic/sk_h3_control_comparability_policy.json`, checker | Every subset status is policy-derived, not interpretive. |
| C3 | Lock invariant: subset success cannot upgrade full-data closure eligibility. | checker + tests | Invariant is enforced and regression-tested. |

### Verification

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
```

---

## WS-H3.4-D: Artifact Freshness and Semantic Parity

**Goal:** Eliminate stale/mixed artifact narratives.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Add freshness checks (timestamps/run-id coherence) between comparability and data-availability artifacts. | checker scripts and/or core_audit utility | Stale pairings are detected fail-closed. |
| D2 | Add parity checks for required SK-H3 keys across both artifacts. | `scripts/core_skeptic/check_control_comparability.py`, `scripts/core_skeptic/check_control_data_availability.py` | No key-level semantic drift allowed. |
| D3 | Add explicit stale-artifact diagnostics in gate scripts. | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, `scripts/ci_check.sh` | Gate output pinpoints freshness/semantic mismatch root cause. |

### Verification

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

---

## WS-H3.4-E: Claim-Boundary Synchronization

**Goal:** Ensure reporting language mirrors lane-A/lane-B entitlement exactly.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add H3.4 claim taxonomy with lane-bound allowed/disallowed statements. | New `reports/core_skeptic/SK_H3_4_CLAIM_BOUNDARY_REGISTER.md` | Claims are explicitly bounded by closure lane. |
| E2 | Align governance/reports that mention control comparability to lane semantics. | `governance/CONTROL_COMPARABILITY_POLICY.md`, `governance/governance/REPRODUCIBILITY.md`, `governance/RUNBOOK.md`, key reports | No narrative overreach beyond artifact entitlement. |
| E3 | Add checker/policy marker for required language fragments where appropriate. | checker/tests/docs | Missing boundary language becomes test-detectable. |

### Verification

```bash
rg -n "full_data_closure_eligible|available_subset|DATA_AVAILABILITY|allowed_claim" docs reports
```

---

## WS-H3.4-F: Gate and Health-Status Coherence

**Goal:** Ensure release-health and SK-H3 policy narratives are identical across automation.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend release-gate-health dependency snapshot for H3.4 closure lane and feasibility class. | `scripts/core_audit/build_release_gate_health_status.py` | Gate-health surfaces exact H3.4 lane state. |
| F2 | Add reason-code mapping for H3.4-specific mismatches (stale, parity-fail, feasibility-unknown). | same + checker outputs | H3 failures become actionable from reason codes alone. |
| F3 | Ensure C1 blockers do not hide SK-H3 semantic failures in diagnostics output. | gate scripts + builder | SK-H3 health remains inspectable even when C1 fails. |

### Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 - <<'PY'
import json
r=json.load(open('core_status/core_audit/release_gate_health_status.json'))['results']
print(r.get('status'), r.get('reason_code'))
print(r.get('dependency_snapshot',{}).get('control_comparability_status'))
print(r.get('dependency_snapshot',{}).get('control_data_availability_status'))
PY
```

---

## WS-H3.4-G: Regression and Contract Locking

**Goal:** Prevent the same SK-H3 residual class from reappearing due implementation drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add unit tests for H3.4 feasibility classification and terminal qualified lane criteria. | `tests/core_skeptic/test_control_data_availability_checker.py` | Feasibility logic is regression-locked. |
| G2 | Add tests for freshness/parity mismatch detection and error specificity. | `tests/core_skeptic/test_control_comparability_checker.py` + core_audit tests | Stale/mismatch states fail with deterministic codes. |
| G3 | Extend gate script contract tests for new H3.4 markers/reason paths. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, `tests/core_audit/test_ci_check_contract.py`, `tests/core_audit/test_release_gate_health_status_builder.py` | Gate-path expectations remain stable over refactors. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_control_comparability_checker.py \
  tests/core_skeptic/test_control_data_availability_checker.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_release_gate_health_status_builder.py
```

---

## WS-H3.4-H: Governance and Anti-Repeat Closeout

**Goal:** Document final status in a way that prevents repeated reopening without new evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Produce H3.4 decision record with lane selection, rationale, and disconfirmability conditions. | New `reports/core_skeptic/SK_H3_4_DECISION_RECORD.md` | Final state is explicit and auditable. |
| H2 | Produce execution status report template/path for H3.4 implementation pass. | `reports/core_skeptic/SKEPTIC_H3_4_EXECUTION_STATUS.md` (during execution) | Execution evidence can be captured consistently. |
| H3 | Add core_audit-log linkage and reopen conditions (what new evidence would change status). | `AUDIT_LOG.md` | Reopening requires objective trigger, not restatement of known constraints. |

### Verification

```bash
rg -n "SK-H3.4|H3_4_|available_subset|DATA_AVAILABILITY|reopen" reports/core_skeptic AUDIT_LOG.md planning/core_skeptic/SKEPTIC_H3_4_EXECUTION_PLAN.md
```

---

## 8) Execution Order

1. WS-H3.4-A (baseline freeze)
2. WS-H3.4-B (feasibility finalization)
3. WS-H3.4-C (subset adequacy hardening)
4. WS-H3.4-D (freshness/parity enforcement)
5. WS-H3.4-E (claim synchronization)
6. WS-H3.4-F (gate-health coherence)
7. WS-H3.4-G (regression locking)
8. WS-H3.4-H (governance closeout)

Rationale:

- Resolve feasibility first, then enforce consistency, then lock behavior with tests, then finalize governance.

---

## 9) Decision Matrix for SK-H3.4

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Full-data comparability is feasible and passes all policy/gate parity checks. | `H3_4_ALIGNED` | "Control comparability is conclusive at full-dataset scope." |
| Full-data comparability is infeasible due approved irrecoverable source gaps; subset lane is policy-compliant and bounded. | `H3_4_QUALIFIED` | "Full-dataset closure remains blocked by irrecoverable source gaps; subset evidence is qualified and bounded." |
| Artifact semantics, freshness, or policy mapping remains inconsistent. | `H3_4_BLOCKED` | "SK-H3 remains unresolved due comparability governance inconsistency." |
| Evidence is insufficient to classify. | `H3_4_INCONCLUSIVE` | "SK-H3.4 status remains provisional pending complete evidence." |

---

## 10) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H3.4-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline tuple frozen in `reports/core_skeptic/SK_H3_4_GAP_REGISTER.md`. |
| WS-H3.4-B Feasibility Finalization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | H3.4 feasibility/lane fields added and checker-enforced. |
| WS-H3.4-C Subset Adequacy Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Subset confidence provenance and diagnostics strengthened. |
| WS-H3.4-D Freshness/Parity Enforcement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Cross-artifact run-id/timestamp parity enforced in checkers and gates. |
| WS-H3.4-E Claim Synchronization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | H3.4 lane-bound claim register and doc updates completed. |
| WS-H3.4-F Gate/Health Coherence | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Gate-health snapshot expanded with H3.4 lane and feasibility semantics. |
| WS-H3.4-G Regression Locking | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | SK-H3 checker and contract tests updated and passing. |
| WS-H3.4-H Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Decision record, execution status, and core_audit log linkage completed. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 11) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Full-data closure is structurally impossible without new source pages. | High | High | Use lane-B terminal qualified closure with explicit irrecoverability rationale. |
| R2 | Teams continue to reopen SK-H3 despite unchanged evidence basis. | High | High | Add decision record + explicit reopen triggers requiring new evidence. |
| R3 | Stale artifact pairing causes false narratives or contradictory states. | Medium | High | Add freshness checks and fail-closed parity invariants. |
| R4 | Subset evidence is overinterpreted as full-data closure. | Medium | High | Enforce strict claim boundaries and disallow closure upgrades from subset lane. |
| R5 | C1 blockers mask H3 diagnostics in release workflows. | Medium | Medium | Surface H3 state independently in gate-health dependency snapshots and reason codes. |

---

## 12) Deliverables

Required deliverables for the execution pass:

1. `reports/core_skeptic/SK_H3_4_GAP_REGISTER.md`
2. `reports/core_skeptic/SK_H3_4_CLAIM_BOUNDARY_REGISTER.md`
3. `reports/core_skeptic/SK_H3_4_DECISION_RECORD.md`
4. Updated SK-H3 policy/checker/gate/docs artifacts per workstreams B-F
5. Expanded SK-H3 regression/contract tests per WS-H3.4-G
6. `reports/core_skeptic/SKEPTIC_H3_4_EXECUTION_STATUS.md`
7. `AUDIT_LOG.md` trace linking assessment->controls->final lane decision

---

## 13) Closure Criteria

SK-H3 (pass-4 scope) can be marked closed for this cycle only when one of these is true:

1. `H3_4_ALIGNED`: full-data comparability is feasible and conclusive, or
2. `H3_4_QUALIFIED`: full-data closure is infeasible for approved irrecoverable data reasons, and all bounded-state invariants are enforced/tested/documented.

If neither condition is met, SK-H3 remains **OPEN**.
