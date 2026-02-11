# Execution Plan: Skeptic Control-Comparability Terminal Closure (SK-H3.5)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`  
**Finding Target:** `SK-H3` (High, pass-5 residual)  
**Plan Date:** 2026-02-10  
**Attempt Context:** Fifth targeted remediation attempt for SK-H3  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Resolve SK-H3 as far as technically feasible while explicitly preventing another repeat cycle.

This pass focuses on two requirements:

1. close all fixable SK-H3 governance/consistency gaps,
2. classify non-fixable missing-folio constraints as terminal-qualified (not endlessly "pending fix").

---

## 2) Pass-5 SK-H3 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`:

- `SK-H3 (High): Full-data comparability remains blocked; subset path is governed but non-conclusive.`

Current canonical evidence:

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
  - `status=NON_COMPARABLE_BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - `evidence_scope=available_subset`
  - `full_data_closure_eligible=false`
  - `full_data_feasibility=irrecoverable`
  - `h3_4_closure_lane=H3_4_QUALIFIED`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
  - `status=DATA_AVAILABILITY_BLOCKED`
  - same feasibility/lane tuple and same missing-page basis

Residual skeptic leverage:

- "You still cannot claim full-data control comparability closure."

---

## 3) Fifth-Attempt Retrospective (Why SK-H3 Keeps Reappearing)

### 3.1 Governance is stronger, but closure framing still reopens

H3.4 added parity and lane semantics, but repeated assessments still treat the same irrecoverable-page fact pattern as an unresolved engineering defect.

### 3.2 Missing-folio constraints are external data limits, not code bugs

Approved-lost pages are not recoverable through additional computation or checker hardening. Re-running identical pipelines cannot remove that constraint.

### 3.3 Reopen criteria need to be operationally terminal

If conditions are unchanged (same approved-lost list, same classification, same parity), SK-H3 should remain terminal-qualified rather than "open pending fix."

### 3.4 Remaining work is mostly anti-drift and claim-boundary hardening

The fifth pass should target: stale artifact drift, report overreach risk, and explicit blocker taxonomy.

---

## 4) Missing-Folio Non-Fixable Boundary (Required)

This plan treats missing folio/pages as follows:

1. If approved irrecoverable-source classification is consistent and complete across canonical SK-H3 artifacts, missing pages are a **terminal external constraint**.
2. That state is **not** an open engineering blocker for SK-H3 process completion; it maps to terminal-qualified closure.
3. Reopening SK-H3 on missing-folio grounds requires one of:
   - new primary-source page availability,
   - policy classification change backed by new evidence,
   - parity inconsistency across canonical artifacts.

This is not a get-out-of-jail-free card:

- all fixable SK-H3 defects (parity, freshness, over-claiming, stale artifacts) must still be remediated.

---

## 5) Scope and Non-Goals

## In Scope

- SK-H3 closure semantics and anti-repeat terminal criteria,
- canonical artifact parity/freshness for comparability vs availability,
- report/checker/gate synchronization for lane-qualified claims,
- explicit blocker ledger (fixable vs non-fixable),
- playbook criteria updates for irrecoverable-source handling if needed.

## Out of Scope

- generating missing source pages,
- SK-C1 release sensitivity artifact production,
- non-SK-H3 remediation except direct dependency references.

---

## 6) Deterministic SK-H3.5 Closure Framework

SK-H3.5 defines explicit closure classes to stop repeated ambiguity.

## Lane A: `H3_5_ALIGNED`

All true:

- full-dataset comparability feasible,
- `missing_count=0`,
- full-data closure eligible and policy-valid,
- canonical artifacts and gate snapshots fully coherent.

## Lane B: `H3_5_TERMINAL_QUALIFIED`

All true:

- missing pages are approved irrecoverable,
- reason code remains `DATA_AVAILABILITY`,
- available-subset path is policy-valid and bounded,
- full-data closure ineligible state is explicit and consistent,
- reopen triggers are limited to new primary data or policy-evidence change.

## Lane C: `H3_5_BLOCKED`

Any true:

- artifact parity/freshness mismatch,
- missing required irrecoverability metadata,
- claim/report language exceeds bounded entitlement,
- checker/gate contract incoherence.

## Lane D: `H3_5_INCONCLUSIVE`

Evidence incomplete or insufficient to classify lane deterministically.

---

## 7) Success Criteria (Exit Conditions)

SK-H3.5 execution is complete only when all are true:

1. lane decision is deterministic (`H3_5_ALIGNED` or `H3_5_TERMINAL_QUALIFIED`) and machine-checkable,
2. fixable parity/freshness/claim-boundary defects are remediated,
3. missing-folio constraints are explicitly documented as non-fixable external blockers where applicable,
4. reopening requires objective triggers, not repeated restatement of unchanged missing pages,
5. governance artifacts explicitly separate fixable vs non-fixable blockers.

---

## 8) Workstreams

## WS-H3.5-A: Baseline Re-Freeze and Contradiction Scan

**Goal:** Freeze pass-5 SK-H3 state and prove whether any internal contradictions still exist.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-5 SK-H3 tuple from both canonical artifacts. | New `reports/core_skeptic/SK_H3_5_BASELINE_REGISTER.md` | Single source of truth with run-id/timestamp metadata. |
| A2 | Scan all SK-H3 fields for cross-artifact mismatch (status, reason, feasibility, lane, missing_count, policy version, source note path). | same | Contradiction set enumerated (empty or actionable). |
| A3 | Classify each contradiction as fixable implementation defect vs non-fixable data limit. | same | Blocker taxonomy is explicit. |

### Verification

```bash
python3 - <<'PY'
import json
for p in [
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json',
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json',
]:
    r=json.load(open(p)).get('results',{})
    print(p, r.get('status'), r.get('reason_code'), r.get('h3_4_closure_lane'), r.get('full_data_feasibility'), r.get('missing_count'))
PY
```

---

## WS-H3.5-B: Terminal-Qualified Decision Contract

**Goal:** Convert SK-H3 irrecoverability state into explicit terminal-qualified closure semantics.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add SK-H3.5 lane model (`H3_5_*`) with deterministic mapping from canonical H3.4 fields. | policy/checker/gate artifacts | Lane classification is reproducible and fail-closed. |
| B2 | Add explicit terminal-qualified residual reason and reopen-trigger contract. | core_status/checker outputs | Reopen loop cannot occur without objective trigger. |
| B3 | Preserve H3.4 backward compatibility while emitting H3.5 fields. | producer/checker surfaces | Existing integrations remain stable. |

### Verification

```bash
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

---

## WS-H3.5-C: Freshness and Staleness Immunization

**Goal:** Ensure stale artifacts cannot silently reintroduce SK-H3 ambiguity.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Tighten run-id/timestamp parity checks and max skew thresholds for SK-H3 pair. | checkers + gate scripts | Stale pairings fail with deterministic reason codes. |
| C2 | Add stale-artifact diagnosis markers to gate outputs and execution status docs. | gate-health + status reports | Teams can detect stale-state root cause immediately. |
| C3 | Add regression cases for stale/mismatched SK-H3 artifact states. | tests | Drift is caught before release checks. |

### Verification

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

---

## WS-H3.5-D: Claim-Boundary and Report Coherence

**Goal:** Prevent narrative overreach beyond terminal-qualified SK-H3 entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Build SK-H3.5 claim-boundary register (allowed/disallowed language by lane). | New `reports/core_skeptic/SK_H3_5_CLAIM_BOUNDARY_REGISTER.md` | Claim scope is explicit and auditable. |
| D2 | Synchronize governance/reports to lane-qualified language where SK-H3 appears. | docs + reports | No full-data comparability claims when lane is terminal-qualified. |
| D3 | Add marker checks for mandatory bounded-language fragments. | checker/policy/tests | Missing lane-bound wording fails closed. |

### Verification

```bash
rg -n "full-data|full dataset|available_subset|DATA_AVAILABILITY|terminal" docs reports status
```

---

## WS-H3.5-E: Missing-Folio Criterion Hardening in Playbook

**Goal:** Ensure adversarial review criteria no longer treat approved irrecoverable pages as endlessly fixable SK-H3 defects.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add SK-H3 terminal-qualified criterion to playbook irrecoverable section. | `planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md` | Playbook explicitly distinguishes non-fixable data blockers from fixable process defects. |
| E2 | Add explicit "do not reopen without new primary evidence/parity defect" rule. | same | Repeat-loop trigger is constrained. |
| E3 | Link criterion to required evidence fields (policy version, source note path, irrecoverability classification). | same | Reviewers can verify terminal criteria deterministically. |

### Verification

```bash
rg -n "irrecoverable|approved-lost|terminal|reopen|new primary" planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md
```

---

## WS-H3.5-F: Regression Locking and Governance Closeout

**Goal:** Prevent a sixth recurrence of identical SK-H3 residual framing.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add SK-H3.5 tests for lane mapping and terminal-qualified invariants. | core_skeptic/core_audit tests | H3.5 semantics are regression-locked. |
| F2 | Add SK-H3.5 decision record and blocker ledger (fixable vs non-fixable). | New `reports/core_skeptic/SK_H3_5_DECISION_RECORD.md` | Blockers are explicit and non-ambiguous. |
| F3 | Add SK-H3.5 execution status report with command evidence and outcomes. | New `reports/core_skeptic/SKEPTIC_H3_5_EXECUTION_STATUS.md` | Fifth-pass traceability is complete. |
| F4 | Link findings -> controls -> blockers -> reopen triggers in audit log. | `AUDIT_LOG.md` | Anti-repeat traceability is auditable. |

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

## 9) Execution Order

1. WS-H3.5-A Baseline + contradiction scan
2. WS-H3.5-B Terminal closure contract
3. WS-H3.5-C Freshness/staleness immunization
4. WS-H3.5-D Claim/report boundary sync
5. WS-H3.5-E Playbook criteria hardening
6. WS-H3.5-F Regression + governance closeout

Rationale:

- prove current reality and blocker types first,
- then formalize closure semantics,
- then lock drift channels and narrative boundaries,
- finally harden governance/test evidence.

---

## 10) Decision Matrix for SK-H3.5

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Full-data comparability feasible and policy-coherent. | `H3_5_ALIGNED` | "Control comparability is closed at full-dataset scope." |
| Full-data comparability infeasible due approved irrecoverable pages, subset path policy-valid and bounded. | `H3_5_TERMINAL_QUALIFIED` | "Full-data closure is terminally blocked by irrecoverable source gaps; subset evidence remains bounded." |
| Any parity/freshness/contract incoherence remains. | `H3_5_BLOCKED` | "SK-H3 remains process-blocked pending contract coherence." |
| Evidence incomplete. | `H3_5_INCONCLUSIVE` | "SK-H3.5 status provisional pending complete evidence." |

---

## 11) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H3.5-A Baseline + Contradiction Scan | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline register created; no canonical contradiction remained after parity refresh. |
| WS-H3.5-B Terminal Closure Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Producer/checkers/gate now emit and validate `H3_5_*` deterministic closure contract. |
| WS-H3.5-C Freshness Immunization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Freshness/parity checks extended to H3.5 fields across scripts and checkers. |
| WS-H3.5-D Claim/Report Boundary Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | SK-H3 docs updated with H3.5 bounded-language and lane semantics. |
| WS-H3.5-E Playbook Criteria Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Playbook now explicitly binds missing-page objections to `H3_5_TERMINAL_QUALIFIED` criteria. |
| WS-H3.5-F Regression + Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Tests passed; decision/execution/governance records produced. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 12) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Fifth-pass still treats irrecoverable pages as fixable engineering defects. | High | High | Terminal-qualified contract + explicit non-fixable blocker ledger. |
| R2 | Artifact freshness drift reintroduces false SK-H3 contradictions. | Medium | High | Run-id/timestamp parity enforcement + stale-state reason codes. |
| R3 | Report language overreaches beyond bounded subset entitlement. | Medium | High | Claim-boundary register + marker checks. |
| R4 | SK-C1 gate failure masks SK-H3 progress in operations. | Medium | Medium | Keep SK-H3 checker outputs independently inspectable and documented. |
| R5 | Missing-folio objections reopen without new evidence. | High | High | Playbook anti-repeat criteria requiring new primary evidence or parity defect. |

---

## 13) Deliverables

Required deliverables for SK-H3.5 implementation pass:

1. `reports/core_skeptic/SK_H3_5_BASELINE_REGISTER.md`
2. `reports/core_skeptic/SK_H3_5_CLAIM_BOUNDARY_REGISTER.md`
3. `reports/core_skeptic/SK_H3_5_DECISION_RECORD.md`
4. `reports/core_skeptic/SKEPTIC_H3_5_EXECUTION_STATUS.md`
5. updated SK-H3 checker/policy/gate/report surfaces with H3.5 terminal-closure semantics
6. `AUDIT_LOG.md` linkage of SK-H3 pass-5 finding -> blocker class -> closure lane -> reopen triggers

---

## 14) Closure Criteria

SK-H3 (pass-5 scope) is considered closed for this cycle only if one is true:

1. `H3_5_ALIGNED` (full-data closure), or
2. `H3_5_TERMINAL_QUALIFIED` (irrecoverable-source terminal-qualified closure with bounded claims).

If neither is satisfied, SK-H3 remains open (`H3_5_BLOCKED` or `H3_5_INCONCLUSIVE`).
