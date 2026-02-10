# Execution Plan: Skeptic Critical Provenance-Runner Contract Remediation (SK-C2.2)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-C2` (Critical)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Address the updated `SK-C2` finding by eliminating provenance-runner contract gaps where:

1. CI fails provenance contract enforcement for runner scripts.
2. `run_*.py` entrypoints and provenance policy become inconsistent or ambiguous.
3. Skeptics can claim process-integrity failure despite policy documentation.

This plan targets explicit and machine-verifiable alignment across:

- `scripts/comparative/run_proximity_uncertainty.py`
- `tests/audit/test_provenance_contract.py`
- `docs/PROVENANCE.md`
- CI/release verification entrypoints that depend on provenance contract integrity.

---

## 2) SK-C2 Problem Statement (Pass 2)

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- CI failed provenance contract checks in:
  - `tests/audit/test_provenance_contract.py:13` through `tests/audit/test_provenance_contract.py:22`
- Failing runner:
  - `scripts/comparative/run_proximity_uncertainty.py`
- Assessment claim:
  - Script currently outputs JSON but does not show explicit `ProvenanceWriter` usage.

Observed impact:

- `bash scripts/ci_check.sh` fails contract stage.
- Skeptic attack remains active:
  - "Your provenance policy says one thing; your runner contract currently violates it."

---

## 3) Scope and Non-Goals

## In Scope

- Provenance contract semantics for `run_*.py` scripts (especially comparative runner entrypoints).
- Explicit conformance pattern for direct provenance writing vs approved delegated writing.
- CI test and checker hardening for provenance-runner contract.
- Documentation alignment for provenance contract rules and exemptions.

## Out of Scope

- SK-C1 sensitivity evidence contract remediation.
- SK-H1/H2/H3 and SK-M1/M2/M3/M4 claim-scope or methodological remediations.
- Historical orphaned-run reduction itself (this is SK-M4 domain, except where contract references must remain coherent).

---

## 4) Success Criteria (Exit Conditions)

`SK-C2` (pass-2 scope) is closed only if all criteria below are met:

1. Every non-exempt `run_*.py` script satisfies provenance contract via one explicit mode:
   - direct `ProvenanceWriter` integration in the runner, or
   - declared delegated provenance path that is machine-verified.
2. `scripts/comparative/run_proximity_uncertainty.py` is contract-compliant and no longer fails provenance checks.
3. CI provenance contract checks fail closed with deterministic, script-specific error messages.
4. Provenance contract policy, checker behavior, and tests are centralized and consistent (single source of truth).
5. Documentation clearly states runner categories (`artifact-producing`, `display-only`, delegated provenance) and enforcement expectations.
6. `scripts/ci_check.sh` passes provenance contract stage under the updated rules.

---

## 5) Workstreams

## WS-C2.2-A: Contract Baseline and Root-Cause Isolation

**Goal:** Determine whether SK-C2 failure is true contract violation, checker false-negative, or policy ambiguity.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Inventory all `run_*.py` scripts and classify as direct provenance, delegated provenance, or display-only. | `scripts/**/run_*.py`, `docs/PROVENANCE.md` | Classification table completed. |
| A2 | Trace provenance writer path for comparative uncertainty flow (`run_proximity_uncertainty.py` -> downstream writer). | `scripts/comparative/run_proximity_uncertainty.py`, `src/comparative/mapping.py` | Producer path documented with file-level evidence. |
| A3 | Record root cause for SK-C2 (contract gap vs checker-model gap). | `reports/skeptic/SK_C2_2_PROVENANCE_REGISTER.md` (new) | Root-cause matrix with evidence and remediation choice. |

### Verification

```bash
rg -n "ProvenanceWriter|run_" scripts/comparative/run_proximity_uncertainty.py src/comparative/mapping.py tests/audit/test_provenance_contract.py docs/PROVENANCE.md
python3 - <<'PY'
from pathlib import Path
runs = sorted(Path('scripts').rglob('run_*.py'))
print('\n'.join(p.as_posix() for p in runs))
PY
```

---

## WS-C2.2-B: Runner-Level Provenance Contract Remediation

**Goal:** Make comparative uncertainty runner provenance compliance explicit, unambiguous, and testable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Implement explicit provenance conformance in `run_proximity_uncertainty.py` (direct writer or explicit delegated contract marker). | `scripts/comparative/run_proximity_uncertainty.py` | Runner no longer fails provenance contract checks. |
| B2 | Ensure no duplicate/contradictory output writes for uncertainty artifact path. | `scripts/comparative/run_proximity_uncertainty.py`, `src/comparative/mapping.py` | Single canonical write path per run and deterministic output behavior. |
| B3 | Ensure runner emits clear provenance-related execution metadata/logging for contract traceability. | comparative runner output and status artifacts | Runtime output names provenance path and status outcome. |

### Verification

```bash
python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 - <<'PY'
import json
p='results/human/phase_7c_uncertainty.json'
obj=json.load(open(p))
print('has_provenance', isinstance(obj.get('provenance'), dict), 'has_results', isinstance(obj.get('results'), dict))
PY
```

---

## WS-C2.2-C: Provenance Contract Policy and Checker Hardening

**Goal:** Replace fragile string-only assumptions with explicit policy-driven runner provenance validation.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Introduce policy file enumerating runner provenance modes and approved exemptions/delegations. | `configs/audit/provenance_runner_contract.json` (new) | Single machine-readable contract source added. |
| C2 | Add contract checker for runner provenance conformance and delegation validation. | `scripts/audit/check_provenance_runner_contract.py` (new) | Checker fails on undeclared/non-conformant runners. |
| C3 | Keep `test_provenance_contract.py` aligned to checker/policy rather than brittle ad-hoc assumptions. | `tests/audit/test_provenance_contract.py` | Contract test behavior reflects policy file semantics. |

### Verification

```bash
python3 scripts/audit/check_provenance_runner_contract.py --mode ci
python3 scripts/audit/check_provenance_runner_contract.py --mode release
```

---

## WS-C2.2-D: Gate and Test Contract Locking

**Goal:** Ensure CI and release checks enforce SK-C2.2 consistently.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Integrate provenance runner contract checker into CI path. | `scripts/ci_check.sh` | CI always executes provenance runner contract check. |
| D2 | Integrate checker into release/repro verification where applicable. | `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Release/repro checks surface provenance runner contract drift early. |
| D3 | Add targeted tests for checker integration and failure messaging. | `tests/audit/test_ci_check_contract.py`, `tests/audit/test_pre_release_contract.py`, `tests/audit/test_verify_reproduction_contract.py`, `tests/audit/test_provenance_runner_contract_checker.py` (new) | Tests fail on missing checker wiring or policy drift. |

### Verification

```bash
python3 -m pytest -q \
  tests/audit/test_provenance_contract.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py \
  tests/audit/test_provenance_runner_contract_checker.py
```

---

## WS-C2.2-E: Documentation and Audit Traceability

**Goal:** Make SK-C2.2 provenance contract behavior explicit and auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Update provenance docs with direct/delegated runner contract semantics and exemption governance. | `docs/PROVENANCE.md` | Documentation reflects actual enforced contract model. |
| E2 | Update reproducibility guide with provenance-runner contract check commands. | `docs/REPRODUCIBILITY.md` | Repro flow includes provenance runner checker usage. |
| E3 | Add SK-C2.2 execution status template and audit-log trace entry requirements. | `reports/skeptic/SKEPTIC_C2_2_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | End-to-end traceability path prepared. |

### Verification

```bash
rg -n "SK-C2.2|provenance runner contract|check_provenance_runner_contract" docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-C2.2-A (baseline/root-cause)
2. WS-C2.2-B (runner-level remediation)
3. WS-C2.2-C (policy/checker hardening)
4. WS-C2.2-D (gate/test locking)
5. WS-C2.2-E (docs/audit traceability)

Rationale:

- Confirm root cause and remediation mode first (direct vs delegated provenance), then lock it in policy/checkers/tests.

---

## 7) Decision Matrix for SK-C2.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Runner provenance contract is explicit, policy-checked, and all gates/tests pass. | `C2_2_ALIGNED` | "Runner-level provenance contract is coherent and enforced." |
| Contract framework is implemented but one or more runner integrations remain incomplete. | `C2_2_QUALIFIED` | "Contract enforcement framework exists; runner conformance remains partially open." |
| Any non-exempt runner remains untracked/non-conformant or CI provenance contract still fails. | `C2_2_BLOCKED` | "SK-C2 remains blocked by provenance-runner contract inconsistency." |
| Evidence is insufficient to distinguish true violation from checker ambiguity. | `C2_2_INCONCLUSIVE` | "SK-C2.2 status is provisional pending deeper contract trace." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-C2.2-A Baseline/Root Cause | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added root-cause register: `reports/skeptic/SK_C2_2_PROVENANCE_REGISTER.md`. |
| WS-C2.2-B Runner Remediation | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated comparative runner with explicit delegated provenance contract and envelope assertion. |
| WS-C2.2-C Policy/Checker Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `configs/audit/provenance_runner_contract.json` and `scripts/audit/check_provenance_runner_contract.py`; updated provenance contract tests. |
| WS-C2.2-D Gates/Tests | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Integrated checker into CI/pre-release/verify scripts and expanded audit contract coverage. |
| WS-C2.2-E Docs/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated provenance/repro docs and added SK-C2.2 execution status and audit log trace. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Contract checker remains too string-fragile and causes false positives. | High | High | Move to policy-based checker with explicit delegation semantics. |
| R2 | Delegation model can hide real provenance omissions if policy is too permissive. | Medium | High | Require delegation to point to writer-verified module paths with tests. |
| R3 | Runner remediation can introduce duplicate or conflicting artifact writes. | Medium | Medium | Define one canonical output writer path and test for envelope shape. |
| R4 | Heavy comparative runs slow validation loops. | Medium | Medium | Use CI-safe parameterized checks for contract, reserve full run for release evidence. |
| R5 | Legacy exemption list drifts from actual runner behavior over time. | Medium | Medium | Keep exemptions in contract policy and test for stale/unused entries. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-C2.2 provenance runner contract register documenting root cause and remediation mode.
2. Contract-compliant comparative runner (`run_proximity_uncertainty.py`) behavior.
3. Central provenance runner contract policy + checker.
4. Gate integration in CI (and release/repro paths if required by policy).
5. Expanded audit tests locking SK-C2.2 failure modes.
6. Updated provenance/repro docs.
7. SK-C2.2 execution status report under `reports/skeptic/`.
8. Audit-log entry mapping SK-C2 pass-2 finding to implemented controls.

---

## 11) Closure Criteria

`SK-C2` (pass-2 scope) is closed only when:

1. CI no longer fails `tests/audit/test_provenance_contract.py` for `run_proximity_uncertainty.py`.
2. All non-exempt `run_*.py` scripts are provenance-contract conformant under policy/checker.
3. Provenance runner contract checker passes in CI mode and gate integration is tested.
4. Runner-to-artifact provenance envelope is consistent with project provenance policy and docs.
