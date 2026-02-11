# Execution Plan: Skeptic Critical Remediation (SK-C1)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-C1` (Critical) only  
**Plan Date:** 2026-02-10  
**Execution Policy:** Planning document only. Do not execute changes in this step.

---

## 1) Objective

Address the `SK-C1` skeptic finding by hardening sensitivity evidence so `release_evidence_ready=true` is only possible when evidence is:

1. Sufficiently representative of release claims.
2. Transparent about warning/fallback behavior.
3. Protected by fail-closed quality gates across scripts and docs.

This plan aims to eliminate the skeptic argument that conclusive robustness is being inferred from narrow, warning-heavy evidence without explicit caveat burden.

---

## 2) SK-C1 Problem Statement

From `SK-C1`:

- Sensitivity evidence is marked conclusive/release-ready.
- Current artifact profile is narrow for release-level claims (small pages/tokens in observed run).
- Warning volume is high.
- Caveat reporting can still appear as `none` despite warning-heavy runs.

Core risk:

- Methodological overconfidence, not CI instability.

---

## 3) Scope and Non-Goals

## In Scope

- Sensitivity sweep evidence policy (`scripts/phase2_analysis/run_sensitivity_sweep.py`).
- Sensitivity output contract (`core_status/core_audit/sensitivity_sweep.json`, `reports/core_audit/SENSITIVITY_RESULTS.md`).
- Release gate consumers (`scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`).
- Tests and docs for the above behavior.

## Out of Scope

- SK-H/SK-M findings (images, comparative uncertainty, closure language, provenance orphan policy).
- Mechanism/model refactoring unrelated to sensitivity evidence gating.
- Any fix execution in this planning pass.

---

## 4) Success Criteria (Exit Conditions)

`SK-C1` can be closed when all conditions below are satisfied:

1. `release_evidence_ready` requires explicit dataset representativeness pass (policy-backed, machine-checkable).
2. Warning classification captures sparse/fallback warning families (not only legacy insufficient-data tokens).
3. High warning burden cannot silently produce "no caveats"; caveat text is required when warning burden crosses policy thresholds.
4. `pre_release_check.sh` and `verify_reproduction.sh` enforce new sensitivity evidence fields fail-closed.
5. Test suite includes regression coverage for:
   - dataset representativeness failures,
   - warning taxonomy and threshold gating,
   - caveat reporting behavior,
   - release-gate enforcement behavior.
6. Documentation reflects the tightened evidence interpretation contract.

---

## 5) Workstreams

## WS-C1-A: Baseline and Diagnostic Instrumentation

**Goal:** Quantify current warning burden, fallback sources, and dataset profile limitations.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Add diagnostic summary fields for warning-family counts and warning density. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | JSON contains per-family counts and density metrics. |
| A2 | Capture scenario-level fallback indicators in `quality_flags`. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Scenario rows indicate fallback-heavy cases. |
| A3 | Add optional machine-readable diagnostics sidecar for audits. | `core_status/core_audit/sensitivity_quality_diagnostics.json` (new) | Sidecar present and linked from report. |

### Verification

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release
python3 - <<'PY'
import json; d=json.load(open('core_status/core_audit/sensitivity_sweep.json'))
print(d['results']['summary'].keys())
PY
```

---

## WS-C1-B: Dataset Representativeness Policy for Release Evidence

**Goal:** Prevent release-ready labeling when sensitivity runs are not representative enough for release-level conclusions.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define release dataset policy (allowed dataset IDs and/or minimum profile thresholds). | `configs/core_audit/release_evidence_policy.json` (new) | Policy file exists and is consumed by sweep runner. |
| B2 | Enforce policy in summary generation and `release_evidence_ready` calculation. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | `release_evidence_ready=false` when policy check fails. |
| B3 | Emit explicit policy evaluation fields in summary. | `core_status/core_audit/sensitivity_sweep.json` | Fields like `dataset_policy_pass` and reasons exist. |
| B4 | Add smoke-mode allowance behavior (clearly non-release-evidentiary). | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Smoke output cannot satisfy release-ready state. |

### Verification

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release
python3 - <<'PY'
import json; s=json.load(open('core_status/core_audit/sensitivity_sweep.json'))['results']['summary']
print(s.get('dataset_policy_pass'), s.get('release_evidence_ready'))
PY
```

---

## WS-C1-C: Warning Taxonomy and Quality-Gate Tightening

**Goal:** Ensure warnings and fallback behavior are materially reflected in validity, caveats, and release readiness.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Expand warning parser beyond `"Insufficient data for"` to include sparse-data/fallback families. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | `insufficient_data_warnings` and new families reflect actual logs. |
| C2 | Add warning-burden thresholds (absolute + per-scenario rate) to quality gate policy. | `scripts/phase2_analysis/run_sensitivity_sweep.py`, `configs/core_audit/release_evidence_policy.json` | Quality gate fails when warning burden exceeds thresholds. |
| C3 | Require caveats when warning burden > 0 (or above threshold); prohibit "Caveat: none" in such runs. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Report caveat section always consistent with warning metrics. |
| C4 | Mark scenario invalid when fallback burden exceeds per-scenario threshold. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Scenario `valid` reflects fallback severity policy. |

### Verification

```bash
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_guardrails.py
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py
```

---

## WS-C1-D: Gate Consumer Hardening (Fail-Closed)

**Goal:** Ensure release checks require the new SK-C1 evidence fields and reject under-specified artifacts.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Extend `pre_release_check.sh` to validate dataset policy + warning/caveat policy fields. | `scripts/core_audit/pre_release_check.sh` | Script fails if new required fields are absent or failing. |
| D2 | Extend `verify_reproduction.sh` sensitivity integrity checks with same conditions. | `scripts/verify_reproduction.sh` | Verifier fails on non-compliant sensitivity artifacts. |
| D3 | Keep backward-compatibility failure explicit (error messages direct operator action). | both scripts | Fail messages identify exact missing/failed policy condition. |

### Verification

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
```

---

## WS-C1-E: Tests and Contract Coverage

**Goal:** Lock SK-C1 behavior through deterministic tests.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add/extend guardrail tests for dataset representativeness policy and warning threshold gating. | `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py` | Unit tests cover pass/fail branches. |
| E2 | Extend end-to-end test to assert new summary keys and report caveat behavior. | `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py` | E2E test validates contract fields and caveat text. |
| E3 | Extend script contract tests for new pre-release and verifier checks. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py` | Contract tests enforce field/guard presence. |
| E4 | Add negative test fixtures for malformed sensitivity artifacts. | `tests/core_audit/*` | Gate scripts correctly fail malformed artifacts. |

### Verification

```bash
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_guardrails.py \
  tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-C1-F: Documentation and Audit Traceability

**Goal:** Align written policy with executable behavior so skeptic attack surface is reduced.

### Tasks

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Update sensitivity methodology to document representativeness and warning burden criteria for release evidence. | `governance/SENSITIVITY_ANALYSIS.md` | Doc includes exact release-ready prerequisites. |
| F2 | Update reproducibility guide to reflect new sensitivity policy fields checked by release scripts. | `governance/governance/REPRODUCIBILITY.md` | Guide matches script behavior and field names. |
| F3 | Add audit-log entry documenting SK-C1 remediation boundaries and non-claims. | `AUDIT_LOG.md` | Traceable entry ties implementation to skeptic finding. |

### Verification

```bash
rg -n "dataset_policy|warning|caveat|release_evidence_ready" docs scripts tests
```

---

## 6) Execution Order

1. WS-C1-A (instrumentation)
2. WS-C1-B (dataset representativeness gating)
3. WS-C1-C (warning/caveat policy)
4. WS-C1-D (release/verifier enforcement)
5. WS-C1-E (tests)
6. WS-C1-F (docs + audit traceability)

Rationale:

- Compute and expose metrics first, then enforce policy, then lock with tests and docs.

---

## 7) Detailed Status Tracker (For Future Execution Pass)

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-C1-A Baseline/Diagnostics | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added warning-family metrics and diagnostics sidecar output. |
| WS-C1-B Dataset Policy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added dataset representativeness policy config and enforcement fields. |
| WS-C1-C Warning/Caveat Gates | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added warning threshold gates and enforced caveats for warning-bearing runs. |
| WS-C1-D Gate Consumer Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated pre-release and verifier checks for new policy fields. |
| WS-C1-E Tests/Contracts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended sensitivity and audit contract tests; targeted suites pass. |
| WS-C1-F Docs/Traceability | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated sensitivity/repro docs and added audit-log SK-C1 entry. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 8) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Stricter gates make current artifact non-release-ready | High | Medium | Stage policy behind explicit fields first; validate with smoke/release test matrix before enforcing. |
| R2 | Warning taxonomy over-matches benign logs | Medium | Medium | Introduce deterministic pattern allowlist and test fixtures for true/false positives. |
| R3 | Representativeness thresholds too rigid for constrained environments | Medium | Medium | Keep smoke mode non-release and make release thresholds policy-configurable. |
| R4 | Existing tests assume permissive release-ready logic | High | Low | Update tests concurrently with script changes in same PR/workstream. |

---

## 9) Deliverables

Required deliverables in execution pass:

1. Updated sensitivity runner with representativeness and warning-quality gates.
2. Updated sensitivity artifact/report contract fields.
3. Updated pre-release/verifier checks consuming new fields fail-closed.
4. Expanded tests in `tests/phase2_analysis` and `tests/core_audit`.
5. Updated docs in `governance/SENSITIVITY_ANALYSIS.md` and `governance/governance/REPRODUCIBILITY.md`.
6. Execution summary report under `reports/core_skeptic/` (name TBD during execution).

---

## 10) Closure Criteria for SK-C1

`SK-C1` can be marked **CLOSED** only when:

1. A release-mode sensitivity run on release-representative data passes the new policy.
2. Warning and fallback burden are explicitly quantified and policy-compliant.
3. Caveat reporting cannot silently understate warning-heavy runs.
4. `pre_release_check.sh` and `verify_reproduction.sh` enforce these guarantees.
5. Regression tests pass and protect these semantics.

Until then, `SK-C1` remains **OPEN**.
