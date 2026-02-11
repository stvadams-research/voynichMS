# Execution Plan: Skeptic Control-Comparability Residual Closure (SK-H3.3)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`  
**Finding Target:** `SK-H3` (High, pass-3 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and execution report reflect implemented outcomes.

---

## 1) Objective

Address pass-3 `SK-H3` residuals by attempting to close all feasible control-comparability gaps while preserving explicit bounded-state governance where full closure is impossible due source data constraints.

This plan targets the remaining core_skeptic leverage:

- "Comparability is policy-bounded, but still blocked rather than fully settled."

Desired endpoint:

1. a machine-checkable SK-H3 state that is internally coherent across status artifacts, gates, and reports, and  
2. a deterministic path to either full comparability closure or explicit qualified blocked closure.

---

## 2) SK-H3 Problem Statement (Pass 3)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`:

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` remains:
  - `status=NON_COMPARABLE_BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - `evidence_scope=available_subset`
  - `full_data_closure_eligible=false`
  - `missing_count=4`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` remains:
  - `status=DATA_AVAILABILITY_BLOCKED`
  - `reason_code=DATA_AVAILABILITY`
  - `missing_count=4`
- Leakage control remains positive (`leakage_detected=false`) but does not by itself close comparability.

Current operational interpretation:

- SK-H3 is governance-compliant but still non-conclusive at full-dataset level.

Core core_skeptic attack:

- "Your comparability policy is disciplined, but your closure claim remains blocked by missing source pages."

---

## 3) Scope and Non-Goals

## In Scope

- SK-H3 pass-3 residual closure strategy only.
- Data-availability blocker evidence quality and irrecoverability governance.
- Available-subset comparability strengthening and claim-boundary calibration.
- Artifact, gate, checker, and report coherence for SK-H3 status semantics.
- Regression tests and governance traceability for H3.3 state transitions.

## Out of Scope

- SK-C1, SK-C2, SK-H1, SK-H2, SK-M1, SK-M2, SK-M3, SK-M4 remediations.
- Acquisition of unavailable manuscript pages outside existing source corpus.
- Recasting blocked states as conclusive without new constraining evidence.

---

## 4) Success Criteria (Exit Conditions)

`SK-H3` pass-3 residual is considered closed only when all conditions below hold:

1. Data-availability evidence is canonical, current, and cross-artifact consistent.
2. Missing-page irrecoverability class is explicit (approved lost pages vs unexpected missing pages), machine-checked, and report-synchronized.
3. Available-subset comparability status has explicit quantitative/supporting diagnostics and bounded claim language.
4. SK-H3 checker/gates/repro path enforce identical status semantics for blocked, qualified, and conclusive states.
5. Report/docs cannot overstate comparability beyond artifact entitlement.
6. Audit and execution trace clearly link pass-3 SK-H3 diagnosis to implemented controls and residual risk state.

---

## 5) Workstreams

## WS-H3.3-A: Pass-3 Baseline Freeze and Delta Register

**Goal:** Freeze current pass-3 SK-H3 evidence and map residual deltas from H3.2 controls.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Snapshot current SK-H3 status and data-availability artifacts with generated timestamps and key fields. | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`, `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` | Baseline field set and timestamps captured. |
| A2 | Diff pass-3 findings vs H3.2 expected closure surface to isolate true residuals. | `reports/core_skeptic/SK_H3_2_DATA_AVAILABILITY_REGISTER.md` + new addendum | Residual list excludes already-closed controls. |
| A3 | Create H3.3 residual register mapping each residual to owner, control, and closure test. | New `reports/core_skeptic/SK_H3_3_RESIDUAL_REGISTER.md` | Every open residual has deterministic closure check. |

### Verification

```bash
python3 - <<'PY'
import json
for p in [
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json',
  'core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json'
]:
    r=json.load(open(p)).get('results', {})
    print(p, r.get('status'), r.get('reason_code'), r.get('missing_count'))
PY
```

---

## WS-H3.3-B: Irrecoverability Governance Hardening

**Goal:** Convert "data unavailable" into a rigorously bounded irrecoverability contract that cannot drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add explicit irrecoverability classification fields (`recoverable`, `approved_lost`, `unexpected_missing`) to SK-H3 data-availability artifact schema/policy. | `configs/core_skeptic/sk_h3_data_availability_policy.json`, `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` | Artifact carries explicit irrecoverability class and evidence source. |
| B2 | Add source-reference provenance for approved lost-page list (policy version + source note path). | same + governance/register | Lost-page approval is auditable and version-pinned. |
| B3 | Add checker rules to fail on missing/ambiguous irrecoverability metadata. | `scripts/core_skeptic/check_control_data_availability.py` | Checker blocks stale/under-specified block states. |

### Verification

```bash
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

---

## WS-H3.3-C: Available-Subset Evidence Strengthening

**Goal:** Improve technical quality of the available-subset lane so the qualified state is maximally defensible.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Extend available-subset artifact diagnostics (stability envelope, lane reproducibility markers, control-card coverage summary). | `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json` + cards | Qualified subset state includes richer reproducibility evidence. |
| C2 | Add explicit subset-lane confidence thresholds and reason-code transitions (`AVAILABLE_SUBSET_QUALIFIED`, `AVAILABLE_SUBSET_UNDERPOWERED`). | `configs/core_skeptic/sk_h3_control_comparability_policy.json`, checker | Subset state is policy-driven, not ad-hoc narrative. |
| C3 | Ensure subset diagnostics remain fully segregated from full-dataset closure eligibility. | status artifact + checker | No subset pass can imply `full_data_closure_eligible=true`. |

### Verification

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
```

---

## WS-H3.3-D: Status/Gate/Repro Semantic Unification

**Goal:** Ensure pre-release, verify, and CI consume and enforce identical SK-H3 semantics.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Add explicit SK-H3 semantic parity checks across pre-release and verify scripts (core_status/reason/evidence_scope/full_data_closure_eligible/missing_count). | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Scripts fail on semantic divergence across artifacts. |
| D2 | Ensure CI detects SK-H3 artifact staleness or mismatch before deep test stages where feasible. | `scripts/ci_check.sh` | Early SK-H3 mismatch detection reduces hidden drift. |
| D3 | Validate gate-health dependency snapshot remains coherent with SK-H3 state class semantics. | `scripts/core_audit/build_release_gate_health_status.py` (if needed) | Downstream entitlement interpretation remains consistent. |

### Verification

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

---

## WS-H3.3-E: Report and Policy Boundary Calibration

**Goal:** Keep phase7_human-facing interpretation exactly aligned with machine status entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Update SK-H3 policy docs with pass-3 residual wording and irrecoverability semantics. | `governance/CONTROL_COMPARABILITY_POLICY.md`, `governance/GENERATOR_MATCHING.md`, `governance/governance/METHODS_REFERENCE.md` | Docs encode bounded claims for `DATA_AVAILABILITY_BLOCKED` and subset-qualified states. |
| E2 | Update reproducibility/runbook SK-H3 section with canonical command path and expected outcomes. | `governance/governance/REPRODUCIBILITY.md`, `governance/RUNBOOK.md` | Operator flow reproduces blocked vs qualified states deterministically. |
| E3 | Add/refresh core_skeptic-facing SK-H3 register with explicit allowed/disallowed claim statements. | `reports/core_skeptic/SK_H3_3_RESIDUAL_REGISTER.md` | Narrative overreach becomes auditable against status artifact. |

### Verification

```bash
rg -n "SK-H3|DATA_AVAILABILITY|available_subset|full_data_closure_eligible|allowed_claim" docs reports
```

---

## WS-H3.3-F: Regression and Contract Test Expansion

**Goal:** Prevent recurrence of SK-H3 residual drift and semantics mismatch.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add tests for irrecoverability metadata completeness and approved-lost-page mismatch handling. | `tests/core_skeptic/test_control_data_availability_checker.py` | Checker regression captures ambiguous block states. |
| F2 | Add tests for subset-vs-full closure entitlement invariants. | `tests/core_skeptic/test_control_comparability_checker.py` | Subset pass cannot upgrade full closure eligibility. |
| F3 | Extend script contract tests for SK-H3 semantic parity markers. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, `tests/core_audit/test_ci_check_contract.py` | Contract tests detect script drift early. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_control_comparability_checker.py \
  tests/core_skeptic/test_control_data_availability_checker.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_ci_check_contract.py
```

---

## WS-H3.3-G: Governance Closeout and Traceability

**Goal:** Preserve end-to-end trace from pass-3 finding to final H3.3 state.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Create execution status report template/path for H3.3 implementation pass. | `reports/core_skeptic/SKEPTIC_H3_3_EXECUTION_STATUS.md` (during execution) | Implementation evidence can be captured consistently. |
| G2 | Add core_audit log linkage requirement for H3.3 residual resolution and remaining risk. | `AUDIT_LOG.md` | Finding -> control -> status transition trace is complete. |
| G3 | Update plan tracker and final decision classification at closeout. | `planning/core_skeptic/SKEPTIC_H3_3_EXECUTION_PLAN.md` | Plan reflects actual closure outcome and residual class. |

### Verification

```bash
rg -n "SK-H3.3|DATA_AVAILABILITY|available_subset|full_data_closure_eligible" AUDIT_LOG.md reports/core_skeptic planning/core_skeptic/SKEPTIC_H3_3_EXECUTION_PLAN.md
```

---

## 6) Execution Order

1. WS-H3.3-A (baseline and residual register)
2. WS-H3.3-B (irrecoverability governance)
3. WS-H3.3-C (available-subset evidence strengthening)
4. WS-H3.3-D (core_status/gate/repro semantic unification)
5. WS-H3.3-E (report/policy calibration)
6. WS-H3.3-F (test/contract expansion)
7. WS-H3.3-G (governance closeout)

Rationale:

- harden data-availability semantics first, then strengthen feasible evidence and enforce parity across automated gates.

---

## 7) Decision Matrix for SK-H3.3

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Full-dataset comparability becomes policy-complete with no active blocker and semantic parity across gates/artifacts. | `H3_3_ALIGNED` | "Control comparability is conclusive under current policy." |
| Full closure remains blocked, but irrecoverability and subset-qualified evidence are complete, coherent, and fail-closed. | `H3_3_QUALIFIED` | "Full-dataset comparability remains blocked; available-subset evidence is qualified and explicitly bounded." |
| Any cross-artifact inconsistency, ambiguous missing-page governance, or claim overreach persists. | `H3_3_BLOCKED` | "SK-H3 remains unresolved due comparability governance incoherence." |
| Evidence is insufficient to assign a coherent SK-H3 class. | `H3_3_INCONCLUSIVE` | "SK-H3.3 status remains provisional pending additional evidence." |

Execution outcome: `H3_3_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H3.3-A Baseline/Residual Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added baseline freeze and `reports/core_skeptic/SK_H3_3_RESIDUAL_REGISTER.md`. |
| WS-H3.3-B Irrecoverability Governance | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added irrecoverability schema/policy fields, source-note pinning, and checker enforcement. |
| WS-H3.3-C Available-Subset Strengthening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added subset diagnostics, confidence class, and `AVAILABLE_SUBSET_QUALIFIED` / `AVAILABLE_SUBSET_UNDERPOWERED` transitions. |
| WS-H3.3-D Status/Gate/Repro Unification | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-H3 semantic parity checks in pre-release/verify/CI and gate-health snapshot alignment. |
| WS-H3.3-E Report/Policy Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated SK-H3 policy, methods, reproducibility, and runbook documentation. |
| WS-H3.3-F Tests/Contracts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Expanded checker and gate contract coverage for irrecoverability and subset-transition invariants. |
| WS-H3.3-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added execution report and core_audit trace entry. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Source-page gaps remain permanently irrecoverable, limiting conclusive closure potential. | High | High | Encode irrecoverability explicitly and bind claims to qualified blocked state. |
| R2 | Subset-lane diagnostics may be misread as full-dataset closure evidence. | Medium | High | Enforce entitlement invariants in checker/tests and report language. |
| R3 | Script/gate semantics drift over time, reintroducing inconsistencies. | Medium | High | Expand script contract tests and centralize reason-code semantics. |
| R4 | Policy/docs become stale relative to status artifact schema changes. | Medium | Medium | Add required marker checks and doc update requirements in closeout checklist. |
| R5 | Additional strictness may surface unrelated failures outside SK-H3 scope during execution. | Medium | Medium | Keep scope boundaries explicit and log out-of-scope items separately. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. `reports/core_skeptic/SK_H3_3_RESIDUAL_REGISTER.md` with pass-3 residual mapping.
2. Updated SK-H3 data-availability and comparability policy semantics (if gaps are found).
3. Enhanced SK-H3 status artifacts with irrecoverability and subset-lane diagnostics.
4. Gate-script parity updates for SK-H3 semantics (if needed).
5. Expanded SK-H3 checker and contract tests.
6. Updated SK-H3 policy/repro documentation.
7. `reports/core_skeptic/SKEPTIC_H3_3_EXECUTION_STATUS.md` for implementation evidence.
8. `AUDIT_LOG.md` trace entry linking pass-3 SK-H3 findings to final state.

---

## 11) Closure Criteria

`SK-H3` (pass-3 scope) can be marked closed only when:

1. Data-availability blocker evidence is explicit, complete, and checker-validated.
2. Available-subset comparability status is policy-valid and explicitly non-conclusive for full-dataset closure.
3. Pre-release, verify, and CI gates agree on SK-H3 status semantics.
4. Report/docs language remains bounded to current artifact entitlement.

`SK-H3` pass-3 residual is now closed as `H3_3_QUALIFIED` (bounded blocked state with complete irrecoverability and subset-governance controls).
