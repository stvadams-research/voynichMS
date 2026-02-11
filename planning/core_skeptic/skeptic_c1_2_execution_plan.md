# Execution Plan: Skeptic Critical Sensitivity-Contract Remediation (SK-C1.2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-C1` (Critical)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Address the updated `SK-C1` finding by eliminating the sensitivity-evidence contract mismatch where:

1. Sensitivity artifacts claim strong release readiness.
2. Release/repro gates fail due missing or invalid policy fields.
3. Public summary language remains under-caveated for warning-heavy runs.

This plan is focused on restoring coherence between:

- `core_status/core_audit/sensitivity_sweep.json`
- `reports/core_audit/SENSITIVITY_RESULTS.md`
- `scripts/core_audit/pre_release_check.sh`
- `scripts/verify_reproduction.sh`

---

## 2) SK-C1 Problem Statement (Pass 2)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Sensitivity artifact currently reports:
  - `release_evidence_ready=true`
  - `robustness_decision=PASS`
  - `dataset_pages=18`, `dataset_tokens=216`
  - `total_warning_count=918`
  - empty caveat list / "none"-equivalent caveating
- The same artifact fails current gate policy expectations for:
  - `dataset_policy_pass=true`
  - `warning_policy_pass=true`
  - `warning_density_per_scenario` presence

Observed impact:

- `pre_release_check.sh` fails
- `verify_reproduction.sh` fails

Core core_skeptic attack:

- "Your release artifact says PASS while your own gates reject it."

---

## 3) Scope and Non-Goals

## In Scope

- Sensitivity artifact field contract and generation path.
- Sensitivity report synchronization with machine-readable artifact.
- Release/repro gate contract alignment for sensitivity policy fields.
- Tests and docs that guarantee this contract.

## Out of Scope

- SK-C2 provenance-runner contract remediation.
- SK-H1/H2/H3, SK-M1/M2/M3/M4 remediation.
- Major redesign of sensitivity methodology beyond contract integrity and evidence gating.

---

## 4) Success Criteria (Exit Conditions)

`SK-C1` (pass-2 scope) is closed only if all criteria below are met:

1. `core_status/core_audit/sensitivity_sweep.json` always includes required policy fields:
   - `dataset_policy_pass`
   - `warning_policy_pass`
   - `warning_density_per_scenario`
   - `total_warning_count`
   - `caveats`
2. `release_evidence_ready=true` is impossible unless all release policy checks pass.
3. Warning-bearing runs cannot emit "no caveats" outputs in either JSON summary or markdown report.
4. `reports/core_audit/SENSITIVITY_RESULTS.md` is generated from the current canonical JSON artifact and reflects the same values.
5. `scripts/core_audit/pre_release_check.sh` and `scripts/verify_reproduction.sh` have contract-consistent expectations and deterministic failure messages.
6. Targeted phase2_analysis/core_audit tests prevent regression of the above.

---

## 5) Workstreams

## WS-C1.2-A: Contract Baseline and Root-Cause Isolation

**Goal:** Determine whether failures are due to stale artifact generation, schema drift, or report-render drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Inventory current required sensitivity summary fields used by release/repro gates. | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Canonical required-field list documented. |
| A2 | Trace producer path for each required field in sweep runner/report pipeline. | `scripts/phase2_analysis/run_sensitivity_sweep.py`, report-render path | Each field has single source assignment point. |
| A3 | Classify current mismatch as stale artifact vs generation regression vs report regression. | `reports/core_skeptic/SK_C1_2_CONTRACT_REGISTER.md` (new) | Root cause table completed and evidence-linked. |

### Verification

```bash
rg -n "dataset_policy_pass|warning_policy_pass|warning_density_per_scenario|total_warning_count|caveats" \
  scripts/phase2_analysis/run_sensitivity_sweep.py \
  scripts/core_audit/pre_release_check.sh \
  scripts/verify_reproduction.sh
```

---

## WS-C1.2-B: Sensitivity Artifact Schema Hardening

**Goal:** Make artifact schema explicit and non-optional for release-critical fields.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add explicit schema metadata (`schema_version`, `policy_version`, `generated_utc`, `generated_by`). | `core_status/core_audit/sensitivity_sweep.json` contract | Artifact carries versioned contract metadata. |
| B2 | Add machine-checkable schema/contract definition. | `configs/core_audit/sensitivity_artifact_contract.json` (new) | Contract file parseable and test-consumed. |
| B3 | Add contract checker for sensitivity artifact fields and value invariants. | `scripts/core_audit/check_sensitivity_artifact_contract.py` (new) | Checker fails on missing/invalid required fields. |

### Verification

```bash
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode ci
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
```

---

## WS-C1.2-C: Release-Readiness Logic Reconciliation

**Goal:** Ensure `release_evidence_ready` semantics are strictly coupled to policy-pass semantics.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Enforce fail-closed expression for `release_evidence_ready` from complete policy prerequisites only. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | No path yields `true` with missing/failed policy fields. |
| C2 | Add explicit `release_readiness_failures` reason list in summary. | same | Failed prereqs are machine-readable and non-ambiguous. |
| C3 | Ensure warning-heavy scenarios generate caveats and policy-failure states consistently. | same | Empty caveat list disallowed when warnings are present. |

### Verification

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode iterative
python3 - <<'PY'
import json
s=json.load(open('core_status/core_audit/sensitivity_sweep.json'))['results']['summary']
print(s.get('release_evidence_ready'), s.get('dataset_policy_pass'), s.get('warning_policy_pass'), s.get('caveats'))
PY
```

---

## WS-C1.2-D: Report/Artifact Synchronization

**Goal:** Prevent stale or contradictory markdown summaries relative to canonical JSON artifact.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Centralize markdown rendering from canonical JSON summary values only. | `reports/core_audit/SENSITIVITY_RESULTS.md` render path | Report fields mirror artifact values exactly. |
| D2 | Add report coherence markers for policy-pass fields and caveat burden. | report + contract config | Report includes required policy/caveat markers. |
| D3 | Add checker rule blocking "Caveat: none" with warning-bearing runs. | checker/config/tests | Contradiction is machine-blocked. |

### Verification

```bash
rg -n "dataset_policy_pass|warning_policy_pass|warning_density_per_scenario|Total warnings observed|Caveat" \
  reports/core_audit/SENSITIVITY_RESULTS.md core_status/core_audit/sensitivity_sweep.json
```

---

## WS-C1.2-E: Gate and Test Contract Locking

**Goal:** Ensure gates and tests enforce the same SK-C1.2 contract.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Wire sensitivity contract checker into CI and/or pre-release sequence. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh` | Contract checker runs automatically. |
| E2 | Extend core_audit contract tests to assert new checker integration and field expectations. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, `tests/core_audit/test_ci_check_contract.py` | Contract tests fail on missing integration. |
| E3 | Extend sensitivity guardrail/E2E tests for missing-field, empty-caveat, and stale-schema cases. | `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py`, `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py` | Regression matrix covers SK-C1.2 failure modes. |

### Verification

```bash
python3 -m pytest -q \
  tests/phase2_analysis/test_sensitivity_sweep_guardrails.py \
  tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_ci_check_contract.py
```

---

## WS-C1.2-F: Documentation and Audit Traceability

**Goal:** Keep SK-C1.2 evidence semantics explicit and auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Update sensitivity docs with exact release-field contract and caveat rules. | `governance/SENSITIVITY_ANALYSIS.md` | Field-level policy semantics documented. |
| F2 | Update reproducibility doc with SK-C1.2 contract check command path. | `governance/governance/REPRODUCIBILITY.md` | Repro flow includes contract checker and expected fields. |
| F3 | Add SK-C1.2 execution status and core_audit log trace templates. | `reports/core_skeptic/SKEPTIC_C1_2_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | End-to-end traceability path prepared. |

### Verification

```bash
rg -n "dataset_policy_pass|warning_policy_pass|warning_density_per_scenario|caveats|SK-C1.2" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-C1.2-A (root-cause isolation)
2. WS-C1.2-B (schema hardening)
3. WS-C1.2-C (readiness logic reconciliation)
4. WS-C1.2-D (report/artifact synchronization)
5. WS-C1.2-E (gate/test locking)
6. WS-C1.2-F (governance/core_audit traceability)

Rationale:

- Resolve producer/consumer contract definition before changing gate logic or report rendering.

---

## 7) Decision Matrix for SK-C1.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Artifact fields, report values, and gate checks are coherent and release contract passes. | `C1_2_ALIGNED` | "Sensitivity release evidence is contract-consistent and policy-valid." |
| Contract is coherent but evidence remains policy-failing (for example representativeness/warning burden). | `C1_2_QUALIFIED` | "Contract integrity restored; release evidence still non-compliant pending evidence improvements." |
| Any required field mismatch, stale report contradiction, or gate/artifact inconsistency remains. | `C1_2_BLOCKED` | "SK-C1 remains blocked by evidence-contract inconsistency." |
| Insufficient data to assign contract coherence confidently. | `C1_2_INCONCLUSIVE` | "SK-C1.2 status is provisional pending full contract validation." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-C1.2-A Baseline/Root Cause | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added root-cause register: `reports/core_skeptic/SK_C1_2_CONTRACT_REGISTER.md`. |
| WS-C1.2-B Schema Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added contract config/checker and schema metadata fields. |
| WS-C1.2-C Readiness Logic | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `release_readiness_failures` fail-closed readiness semantics. |
| WS-C1.2-D Report Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Regenerated canonical sensitivity artifact/report via quick iterative run. |
| WS-C1.2-E Gates/Tests | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Wired checker into CI/pre-release/verify and expanded regression tests. |
| WS-C1.2-F Docs/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated docs, core_audit log, and execution status artifacts. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Existing release artifact is stale and appears valid in prose despite failing policy fields. | High | High | Add contract checker + schema metadata + report synchronization checks. |
| R2 | Tightened field requirements could break legacy fixtures and tests. | High | Medium | Update fixtures and contract tests in same execution batch. |
| R3 | Heavy release sensitivity runs delay remediation verification cycles. | Medium | Medium | Preserve iterative mode for contract checks; reserve release mode for final evidentiary validation. |
| R4 | Multiple gate scripts diverge in required-field semantics over time. | Medium | High | Centralize field contract in one machine-readable config and checker. |
| R5 | Caveat policy may over-trigger noisy, low-impact warnings. | Medium | Medium | Add warning-family thresholds and explicit policy reason codes. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-C1.2 sensitivity artifact contract config and checker.
2. Reconciled sensitivity runner output contract with required policy fields.
3. Synchronized markdown summary generation (no stale contradiction path).
4. Gate integration for contract checks in CI/release verification.
5. Expanded tests locking SK-C1.2 failure modes.
6. Updated docs reflecting field-level release evidence contract.
7. SK-C1.2 execution status report under `reports/core_skeptic/`.
8. Audit-log entry mapping SK-C1 pass-2 findings to implemented controls.

---

## 11) Closure Criteria

`SK-C1` (pass-2 scope) is closed only when:

1. A newly generated sensitivity artifact satisfies the full field/value contract.
2. `pre_release_check.sh` and `verify_reproduction.sh` both pass sensitivity policy checks against that artifact.
3. CI passes contract tests without sensitivity-field or provenance-contract regressions.
4. Reported caveat burden is consistent with warning burden in machine-readable summary.
