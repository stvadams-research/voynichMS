# Execution Plan: Skeptic Control-Comparability Residual Closure (SK-H3.2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-H3` (High, pass-2 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and execution report reflect implementation outcomes.

---

## 1) Objective

Address the pass-2 `SK-H3` residual by resolving what is feasible under current source-data limits and hardening blocked-state governance where conclusive comparability is not currently attainable.

This plan targets the remaining core_skeptic attack:

- "You improved leakage controls, but comparability is still blocked rather than conclusively settled."

and focuses on producing a defensible, machine-checked outcome for either:

1. a policy-valid comparability determination on feasible evidence, or
2. an explicitly bounded and governance-complete `DATA_AVAILABILITY` block state.

---

## 2) SK-H3 Problem Statement (Pass 2)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Control-comparability artifact remains blocked:
  - `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `status=NON_COMPARABLE_BLOCKED`
  - `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` -> `reason_code=DATA_AVAILABILITY`
- Structural anti-leakage controls are present and reported:
  - `leakage_detected=false`
  - metric partition markers documented in policy/docs.

Current runtime evidence shows strict preflight block details in:

- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`
  - `status=BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - missing pages listed under `preflight.missing_pages`.

Observed issue:

- Governance and guardrails exist, but closure posture remains vulnerable if blocked-state semantics and feasible fallback evidence are not fully formalized.

---

## 3) Scope and Non-Goals

## In Scope

- SK-H3 residual closure under data-availability constraints.
- Canonical data-availability registry and eligibility policy for comparability runs.
- Feasible "available-data comparability" lane with explicit non-equivalence boundaries.
- Gate and checker semantics for blocked vs qualified outcomes.
- Documentation/report alignment for claim limits under SK-H3 block conditions.

## Out of Scope

- Re-implementing already shipped SK-H3 leakage/normalization foundations unless required by residual closure.
- SK-C1/SK-C2 remediations.
- New semantic decipherment claims.
- Acquiring unavailable source folios/pages.

---

## 4) Success Criteria (Exit Conditions)

`SK-H3` pass-2 residual is considered closed only if all criteria below are met:

1. Data-availability blocker is grounded in a canonical machine-readable registry (missing pages and rationale).
2. Comparability status semantics are deterministic and auditable across artifacts/checkers/gates.
3. If conclusive comparability remains impossible, blocked state is explicitly bounded with approved reason codes and allowed claims.
4. A feasible available-data comparability lane exists and is explicitly separated from full-data closure claims.
5. CI/release checks prevent over-claiming when status is blocked or qualified.
6. Public/report language is synchronized with status artifact semantics.

---

## 5) Workstreams

## WS-H3.2-A: Residual Baseline and Root-Cause Consolidation

**Goal:** Confirm exact unresolved SK-H3 residual and eliminate ambiguity between policy failure and data-availability constraint.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Record current SK-H3 artifact state (`CONTROL_COMPARABILITY_STATUS`, `TURING_TEST_RESULTS`). | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`, `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` | Baseline snapshot captured. |
| A2 | Trace strict preflight data-availability block details and affected page set. | `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` (`preflight.*`) | Missing page inventory canonicalized. |
| A3 | Create residual root-cause register for SK-H3.2. | `reports/core_skeptic/SK_H3_2_DATA_AVAILABILITY_REGISTER.md` (new) | Root-cause matrix completed with evidence links. |

### Verification

```bash
python3 - <<'PY'
import json
for p in ['core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json','core_status/phase3_synthesis/TURING_TEST_RESULTS.json']:
    d=json.load(open(p)); r=d.get('results',d)
    print(p, r.get('status'), r.get('reason_code'))
PY
```

---

## WS-H3.2-B: Data-Availability Contract and Eligibility Policy

**Goal:** Convert implicit missing-data caveat into explicit SK-H3 contract policy.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add machine-readable SK-H3 data-availability policy (approved reason codes, required evidence fields, lost-page handling). | `configs/core_skeptic/sk_h3_data_availability_policy.json` (new) | Policy is parseable and versioned. |
| B2 | Emit canonical data-availability status artifact for SK-H3 decisions. | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` (new) | Artifact contains expected/available/missing sets and policy pass flags. |
| B3 | Add checker for SK-H3 data-availability contract consistency. | `scripts/core_skeptic/check_control_data_availability.py` (new) | Checker fails on missing/contradictory blocker evidence. |

### Verification

```bash
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

---

## WS-H3.2-C: Feasible Available-Data Comparability Lane

**Goal:** Define and validate what comparability can be assessed on available source pages without over-claiming full-data closure.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Implement available-data comparability runner path with explicit lane labeling. | `scripts/phase3_synthesis/run_control_matching_audit.py` and/or new `scripts/phase3_synthesis/run_control_comparability_available.py` | Lane emits explicit `evidence_scope=available_subset`. |
| C2 | Add status field separating full-data closure from subset-qualified comparability. | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` | Status encodes scope and closure eligibility. |
| C3 | Add pass/fail thresholds for subset lane and map to allowed claim language. | SK-H3 policy + checker | Subset outputs cannot be interpreted as full-data conclusive closure. |

### Verification

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 - <<'PY'
import json
r=json.load(open('core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json'))['results']
print(r.get('status'), r.get('reason_code'), r.get('allowed_claim'), r.get('evidence_scope'))
PY
```

---

## WS-H3.2-D: Status/Gate Semantics Reconciliation

**Goal:** Ensure gate logic and status taxonomy are coherent for blocked and qualified paths.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Reconcile SK-H3 checker + release/repro gates with explicit handling for approved `DATA_AVAILABILITY` block states. | `scripts/core_skeptic/check_control_comparability.py`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Gates fail only on unapproved/incoherent states; approved blocked states remain bounded. |
| D2 | Add deterministic failure messages for invalid block evidence (missing pages not reported, inconsistent core_status/reason combinations). | same | Failure reasons are actionable and reproducible. |
| D3 | Add contract tests for approved blocked vs disallowed blocked states. | `tests/core_skeptic/test_control_comparability_checker.py`, `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py` | Regression matrix covers status semantic drift. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_control_comparability_checker.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-H3.2-E: Reporting and Claim-Boundary Synchronization

**Goal:** Prevent report-level overreach when comparability is blocked or subset-qualified.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Align phase8_comparative/control narrative docs with SK-H3 residual status semantics. | `governance/GENERATOR_MATCHING.md`, `governance/governance/METHODS_REFERENCE.md`, `governance/CONTROL_COMPARABILITY_POLICY.md` | Language reflects bounded claims for blocked/qualified states. |
| E2 | Update reproducibility/runbook with explicit SK-H3 residual verification flow. | `governance/governance/REPRODUCIBILITY.md`, `governance/RUNBOOK.md` | Operators can reproduce both block and subset-qualified checks. |
| E3 | Add report coherence checks for SK-H3 status-dependent claim wording. | SK-H3 checker and/or report checker | Reports cannot claim conclusive comparability under blocked state. |

### Verification

```bash
rg -n "NON_COMPARABLE_BLOCKED|DATA_AVAILABILITY|allowed_claim|evidence_scope|SK-H3" docs reports
```

---

## WS-H3.2-F: Audit Traceability and Governance Closeout

**Goal:** Maintain end-to-end trace from pass-2 finding to final SK-H3.2 state.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add SK-H3.2 execution status report template/artifact. | `reports/core_skeptic/SKEPTIC_H3_2_EXECUTION_STATUS.md` (during execution) | Implementation and verification evidence documented. |
| F2 | Add SK-H3.2 core_audit log entry linking blocker evidence, policy changes, and residual risks. | `AUDIT_LOG.md` | Trace entry complete and file-referenced. |
| F3 | Update plan status tracker and final decision matrix outcome. | `planning/core_skeptic/SKEPTIC_H3_2_EXECUTION_PLAN.md` | Workstream status and final outcome explicit. |

### Verification

```bash
rg -n "SK-H3.2|DATA_AVAILABILITY|evidence_scope|allowed_claim" AUDIT_LOG.md reports/core_skeptic planning/core_skeptic/SKEPTIC_H3_2_EXECUTION_PLAN.md
```

---

## 6) Execution Order

1. WS-H3.2-A (baseline/root-cause)
2. WS-H3.2-B (data-availability contract)
3. WS-H3.2-C (feasible available-data lane)
4. WS-H3.2-D (core_status/gate reconciliation)
5. WS-H3.2-E (report/claim synchronization)
6. WS-H3.2-F (core_audit closeout)

Rationale:

- Define blocker contract first, then add feasible evidence lane and only then reconcile gate/report semantics.

---

## 7) Decision Matrix for SK-H3.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Full comparability evidence is policy-complete and no approved blocker remains. | `H3_2_ALIGNED` | "Control comparability is conclusive under current policy." |
| Full closure remains blocked but data-availability governance is complete and subset lane is bounded/valid. | `H3_2_QUALIFIED` | "Comparability remains data-limited; bounded subset evidence is available with explicit non-closure limits." |
| Block state remains ambiguous/incoherent or gates/docs disagree with artifact semantics. | `H3_2_BLOCKED` | "SK-H3 remains unresolved due incoherent comparability/block governance." |
| Insufficient evidence to classify blocker legitimacy or subset-lane integrity. | `H3_2_INCONCLUSIVE` | "SK-H3.2 status provisional pending additional contract evidence." |

Execution outcome: `H3_2_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H3.2-A Baseline/Root Cause | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added residual root-cause register: `reports/core_skeptic/SK_H3_2_DATA_AVAILABILITY_REGISTER.md`. |
| WS-H3.2-B Data-Availability Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added policy/config/checker and canonical data-availability artifact. |
| WS-H3.2-C Available-Data Lane | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated core_audit runner with bounded available-subset semantics and explicit closure eligibility fields. |
| WS-H3.2-D Status/Gate Reconciliation | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Integrated SK-H3.2 checks into ci/pre-release/verify scripts and contract tests. |
| WS-H3.2-E Reporting/Claim Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated SK-H3 policy, methods, reproducibility, and runbook docs for blocked vs subset-qualified semantics. |
| WS-H3.2-F Audit Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added execution status report and core_audit log trace for SK-H3.2 closure path. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Missing-page constraints cannot be resolved with available source data. | High | High | Formalize approved blocked-state governance and bounded claims. |
| R2 | Subset-lane evidence is misread as full-data closure. | Medium | High | Add explicit `evidence_scope` and checker-enforced claim boundaries. |
| R3 | Gate scripts diverge on accepted blocked-state semantics. | Medium | High | Centralize in machine-readable policy and checker integration. |
| R4 | Status artifacts become stale across reruns. | Medium | Medium | Add generated timestamp/version and stale-artifact checks. |
| R5 | Narrative docs drift from machine-readable status semantics. | Medium | Medium | Add doc/report marker checks in SK-H3 policy checker path. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-H3.2 residual root-cause register (`SK_H3_2_DATA_AVAILABILITY_REGISTER.md`).
2. SK-H3 data-availability policy + checker.
3. Canonical SK-H3 data-availability status artifact.
4. Available-data comparability lane with bounded claim semantics.
5. Gate/test updates for blocked/qualified state consistency.
6. Documentation updates for SK-H3 residual semantics.
7. SK-H3.2 execution status report under `reports/core_skeptic/`.
8. Audit-log trace entry linking pass-2 finding to implemented controls.

---

## 11) Closure Criteria

`SK-H3` (pass-2 residual scope) is closed only when:

1. `DATA_AVAILABILITY` block evidence is complete, canonical, and checker-validated.
2. SK-H3 checker/gates/docs agree on blocked vs qualified vs conclusive semantics.
3. Available-data comparability outputs are policy-valid and explicitly non-conclusive unless full-data criteria are met.
4. CI/release contract tests pass for SK-H3 status governance without over-claim regressions.
