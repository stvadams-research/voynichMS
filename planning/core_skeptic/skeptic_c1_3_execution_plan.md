# Execution Plan: Skeptic Critical Sensitivity Release-Contract Closure (SK-C1.3)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`  
**Finding Target:** `SK-C1` (Critical)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Close the current pass-3 `SK-C1` release blocker by making sensitivity evidence contract-coherent across:

1. sensitivity artifact generation,
2. sensitivity markdown reporting,
3. release and reproduction gates,
4. gate-health entitlement logic.

Primary closure intent:

- remove the current mismatch where CI policy checks pass in `ci` mode while release paths fail on the same sensitivity artifact.

---

## 2) SK-C1 Problem Statement (Pass 3)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`:

- `pre_release_check.sh` fails on release-mode sensitivity contract.
- `verify_reproduction.sh` fails on release-mode sensitivity contract.
- `ci_check.sh` fails late because nested reproduction verification hits the same release-mode block.

Current canonical artifact state (pass-3 evidence):

- `execution_mode="iterative"`
- `release_evidence_ready=false`
- `dataset_policy_pass=false`
- `warning_policy_pass=false`
- `quality_gate_passed=false`
- `robustness_conclusive=false`
- `robustness_decision="INCONCLUSIVE"`
- `release_readiness_failures` non-empty
- `dataset_pages=18`
- `dataset_tokens=216`
- `total_warning_count=270`
- `warning_density_per_scenario=54.0`

Operational consequence:

- `core_status/core_audit/release_gate_health_status.json` remains:
  - `status=GATE_HEALTH_DEGRADED`
  - `reason_code=GATE_CONTRACT_BLOCKED`
  - `allowed_claim_class=QUALIFIED`
  - `allowed_closure_class=CONDITIONAL_CLOSURE_QUALIFIED`

Core skeptic leverage:

- "Release evidence remains non-release and inconclusive under your own enforced policy contract."

---

## 3) Scope and Non-Goals

## In Scope

- SK-C1 release-mode sensitivity contract failures only.
- Sensitivity artifact field semantics and generation path.
- Sensitivity report synchronization with canonical artifact state.
- Pre-release/verify/CI contract consistency for sensitivity release checks.
- Gate-health coupling accuracy relative to sensitivity contract outcomes.

## Out of Scope

- SK-C2, SK-H1, SK-H2, SK-H3, SK-M1, SK-M2, SK-M3, SK-M4 remediation.
- Broad sensitivity methodology redesign beyond contract closure needs.
- Any attempt in this plan to reclassify uncertain findings as conclusive without evidence.

---

## 4) Success Criteria (Exit Conditions)

`SK-C1` is considered closed for pass-3 scope only when all conditions below hold:

1. A release-mode sensitivity artifact is produced with contract-compliant values for all required release fields.
2. `release_evidence_ready=true` can only occur when all release prerequisites pass (`dataset_policy_pass`, `warning_policy_pass`, `quality_gate_passed`, `robustness_conclusive`, empty `release_readiness_failures`, full scenario execution, release execution mode).
3. `pre_release_check.sh` and `verify_reproduction.sh` both pass sensitivity checks against the same canonical artifact.
4. `ci_check.sh` completes without failing in nested reproduction due sensitivity contract regressions.
5. Sensitivity markdown report text and numeric summaries match the canonical JSON artifact and caveat burden.
6. Gate-health artifact reason codes/allowed claim class align deterministically with sensitivity contract outcomes.

---

## 5) Workstreams

## WS-C1.3-A: Canonical Baseline Freeze and Gap Register

**Goal:** Convert pass-3 SK-C1 evidence into an explicit machine-linked remediation baseline.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze current sensitivity summary and release-gate health snapshots used for SK-C1.3 remediation. | `core_status/core_audit/sensitivity_sweep.json`, `core_status/core_audit/release_gate_health_status.json` | Baseline snapshot IDs/timestamps captured. |
| A2 | Create structured SK-C1.3 gap register mapping each failing field to producer, consumer, and policy clause. | New `reports/core_skeptic/SK_C1_3_CONTRACT_REGISTER.md` | Every failing field has an owner and closure test. |
| A3 | Map direct and nested failure paths (`pre_release`, `verify`, `ci->verify`) with exact check order. | same + gate scripts | Failure topology documented and reproducible. |

### Verification

```bash
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
python3 - <<'PY'
import json
s=json.load(open('core_status/core_audit/sensitivity_sweep.json'))['results']['summary']
print({k:s.get(k) for k in [
  'execution_mode','release_evidence_ready','dataset_policy_pass',
  'warning_policy_pass','quality_gate_passed','robustness_conclusive',
  'robustness_decision','release_readiness_failures'
]})
PY
```

---

## WS-C1.3-B: Release-Mode Evidence Generation Integrity

**Goal:** Ensure release checks are evaluating intentionally generated release evidence, not iterative leftovers.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Audit release-mode invocation path and defaults in `run_sensitivity_sweep.py` and wrapper scripts. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Release execution path is explicit and deterministic. |
| B2 | Enforce artifact provenance markers that distinguish `release` vs `iterative` generation and block ambiguity. | `core_status/core_audit/sensitivity_sweep.json` | Artifact includes unambiguous generation mode provenance. |
| B3 | Add stale-artifact guard in release consumers to prevent old iterative artifacts being treated as release candidates. | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Release consumers reject stale/mode-mismatched artifacts with explicit reason. |

### Verification

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
```

---

## WS-C1.3-C: Dataset Policy and Robustness Conclusiveness Closure

**Goal:** Make release readiness impossible when dataset representativeness or robustness conclusiveness fails.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Review and harden dataset policy thresholds/IDs for release evidence to avoid permissive leakage. | `configs/core_audit/release_evidence_policy.json` | Policy is explicit, versioned, and test-backed. |
| C2 | Reconcile robustness decision logic so `INCONCLUSIVE` always blocks release readiness and closure language. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | `INCONCLUSIVE` cannot coexist with release-ready state. |
| C3 | Require complete scenario execution and policy pass as a strict conjunction for release readiness. | same | Partial/weak evidence cannot emit release-ready state. |

### Verification

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release
python3 - <<'PY'
import json
s=json.load(open('core_status/core_audit/sensitivity_sweep.json'))['results']['summary']
assert s['execution_mode']=='release'
assert s['scenario_count_expected']==s['scenario_count_executed']
print(s['dataset_policy_pass'], s['robustness_conclusive'], s['release_evidence_ready'])
PY
```

---

## WS-C1.3-D: Warning Burden and Caveat Coherence Hardening

**Goal:** Keep warning-heavy evidence from silently appearing caveat-light in machine or markdown outputs.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Validate warning-family classification coverage for current warning streams and fallback types. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Warning burden metrics are complete and stable. |
| D2 | Enforce warning policy pass criteria and bind it directly to release readiness. | policy + sweep runner | `warning_policy_pass=false` always blocks release-ready state. |
| D3 | Enforce caveat presence and report consistency when `total_warning_count>0` or warning policy fails. | `reports/core_audit/SENSITIVITY_RESULTS.md` renderer + checker | No warning-bearing artifact can emit caveat-empty narrative. |

### Verification

```bash
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
rg -n "warning|caveat|release_evidence_ready|warning_policy_pass" reports/core_audit/SENSITIVITY_RESULTS.md
```

---

## WS-C1.3-E: Gate Consistency and Nested-Failure Elimination

**Goal:** Remove pass-3 inconsistency where CI appears healthy until nested release verification fails.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Align CI sensitivity stage with nested release verification expectations (either explicit precondition or harmonized mode contract). | `scripts/ci_check.sh` | No hidden mode mismatch between CI stage and nested verify stage. |
| E2 | Ensure pre-release and verify scripts share one canonical sensitivity contract checker path and reason-code semantics. | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Same failing condition yields same reason and remediation message. |
| E3 | Validate gate-health builder consumes updated sensitivity outcomes and reason-code transitions deterministically. | `scripts/core_audit/build_release_gate_health_status.py` | Gate-health status changes only when sensitivity contract truly changes. |

### Verification

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
python3 scripts/core_audit/build_release_gate_health_status.py
```

---

## WS-C1.3-F: Test/Fixture/Contract Locking

**Goal:** Prevent SK-C1 regressions from reappearing in later passes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend sensitivity guardrail and e2e tests for pass-3 failure tuple (`iterative`, non-ready, policy false, inconclusive). | `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py`, `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py` | Pass-3 failure shape has explicit regression tests. |
| F2 | Extend audit contract tests to assert aligned sensitivity checks across pre-release/verify/CI stages. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, `tests/core_audit/test_ci_check_contract.py` | Nested verification mismatch is test-covered. |
| F3 | Add checker tests for reason-code parity between contract checker and gate-health builder. | `tests/core_audit/test_release_gate_health_status_builder.py` + new cases | Reason-code drift is blocked by tests. |

### Verification

```bash
python3 -m pytest -q \
  tests/phase2_analysis/test_sensitivity_sweep_guardrails.py \
  tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_release_gate_health_status_builder.py
```

---

## WS-C1.3-G: Documentation and Governance Closeout

**Goal:** Keep policy language synchronized with enforced contract behavior and release entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Update sensitivity and reproducibility docs to reflect exact release-readiness contract for pass-3 closure. | `governance/SENSITIVITY_ANALYSIS.md`, `governance/governance/REPRODUCIBILITY.md` | Docs match script/checker behavior exactly. |
| G2 | Produce SK-C1.3 execution status template/report for future execution pass. | `reports/core_skeptic/SKEPTIC_C1_3_EXECUTION_STATUS.md` (during execution) | Status path prepared before implementation. |
| G3 | Add audit-log trace requirement linking pass-3 SK-C1 diagnosis to implemented controls and final state. | `AUDIT_LOG.md` | End-to-end traceability ready for closeout. |

### Verification

```bash
rg -n "SK-C1.3|release_evidence_ready|dataset_policy_pass|warning_policy_pass|GATE_CONTRACT_BLOCKED" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-C1.3-A (baseline and gap register)
2. WS-C1.3-B (release-mode generation integrity)
3. WS-C1.3-C (dataset/robustness closure)
4. WS-C1.3-D (warning/caveat coherence)
5. WS-C1.3-E (gate consistency and nested-failure elimination)
6. WS-C1.3-F (tests/contracts)
7. WS-C1.3-G (governance/governance)

Rationale:

- stabilize producer semantics before tightening consumers and gates, then lock behavior with tests and docs.

---

## 7) Decision Matrix for SK-C1.3

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Release artifact/gates/checkers are coherent and sensitivity contract passes release mode end-to-end. | `C1_3_ALIGNED` | "Sensitivity release evidence is contract-consistent and release-valid." |
| Contract coherence is fixed but release evidence remains policy-failing due legitimate data/warning constraints. | `C1_3_QUALIFIED` | "SK-C1.3 contract integrity is restored; release evidence remains non-ready." |
| Any mismatch persists between artifact fields, gate expectations, or nested CI behavior. | `C1_3_BLOCKED` | "SK-C1 remains blocked by release-contract inconsistency." |
| Evidence is insufficient to classify closure safely. | `C1_3_INCONCLUSIVE` | "SK-C1.3 status is provisional pending full release-contract evidence." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-C1.3-A Baseline/Gap Register | NOT STARTED | Codex | TBD | TBD | Build SK-C1.3 contract register from pass-3 evidence. |
| WS-C1.3-B Release Generation Integrity | NOT STARTED | Codex | TBD | TBD | Ensure release-mode artifact provenance and stale-artifact guards. |
| WS-C1.3-C Dataset/Robustness Closure | NOT STARTED | Codex | TBD | TBD | Tighten dataset/robustness prerequisites for release-ready semantics. |
| WS-C1.3-D Warning/Caveat Coherence | NOT STARTED | Codex | TBD | TBD | Bind warning burden to caveats and release-readiness gating. |
| WS-C1.3-E Gate Consistency | NOT STARTED | Codex | TBD | TBD | Eliminate CI nested verify mismatch on sensitivity contract semantics. |
| WS-C1.3-F Tests/Contracts | NOT STARTED | Codex | TBD | TBD | Add regression coverage for pass-3 SK-C1 failure tuple. |
| WS-C1.3-G Docs/Governance | NOT STARTED | Codex | TBD | TBD | Update docs and audit traceability after implementation. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Release-mode sensitivity runs remain expensive and slow, impeding iteration speed. | High | Medium | Preserve fast contract-validation lanes and reserve full release runs for milestone validation. |
| R2 | Tightened release checks may expose additional latent failures outside SK-C1 scope. | Medium | Medium | Keep SK-C1.3 scope boundaries explicit and log out-of-scope findings without bundling. |
| R3 | CI/release mode semantics diverge again over time. | Medium | High | Centralize contract checker use and lock parity with script contract tests. |
| R4 | Warning thresholds may be overly strict or permissive for future datasets. | Medium | Medium | Keep thresholds policy-configurable and reason-code transparent. |
| R5 | Gate-health artifact may lag true contract state if build order is inconsistent. | Low | Medium | Enforce deterministic build sequence in pre-release/verify/CI scripts. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. `SK_C1_3_CONTRACT_REGISTER.md` with pass-3 failing tuple and closure mapping.
2. Updated release-mode sensitivity artifact contract behavior.
3. Harmonized gate scripts across pre-release/verify/CI for SK-C1 checks.
4. Updated/expanded tests locking pass-3 failure modes.
5. Updated docs for sensitivity release-readiness contract.
6. SK-C1.3 execution status report (`reports/core_skeptic/SKEPTIC_C1_3_EXECUTION_STATUS.md`).
7. Audit-log linkage from SK-C1 pass-3 diagnosis to implemented controls.

---

## 11) Closure Criteria

`SK-C1` (pass-3 scope) can be marked closed only when:

1. Release-mode sensitivity artifact passes release contract checker.
2. `pre_release_check.sh`, `verify_reproduction.sh`, and `ci_check.sh` no longer fail due SK-C1 sensitivity contract mismatch.
3. Gate-health status transitions out of `GATE_CONTRACT_BLOCKED` for sensitivity-related reasons.
4. Reported sensitivity caveats and machine-readable warning burden remain coherent.

Until then, `SK-C1` remains **OPEN**.
