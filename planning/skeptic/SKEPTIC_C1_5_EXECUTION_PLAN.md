# Execution Plan: Skeptic Critical Sensitivity Release-Contract Closure (SK-C1.5)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`  
**Finding Target:** `SK-C1` (Critical, pass-5 residual)  
**Plan Date:** 2026-02-10  
**Attempt Context:** Fourth targeted remediation attempt for the same SK-C1 class  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Close the repeated SK-C1 release blocker by making release sensitivity evidence production deterministic, observable, and gate-coherent across all release paths.

This plan must eliminate the specific repeat pattern seen over prior attempts:

1. preflight passes,
2. release artifact/report are still missing,
3. release gate remains degraded for the same reason,
4. skeptic reassessment reopens SK-C1 with no new root-cause decomposition.

---

## 2) Pass-5 SK-C1 Problem Statement

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`:

- `SK-C1 (Critical): Release sensitivity release artifact/report remains missing; all release paths are blocked by design.`

Direct evidence chain:

- pre-release blocker:
  - `scripts/audit/pre_release_check.sh:60`
  - `scripts/audit/pre_release_check.sh:61`
  - `scripts/audit/pre_release_check.sh:64`
- release checker fail path:
  - `scripts/audit/check_sensitivity_artifact_contract.py:248`
  - `scripts/audit/check_sensitivity_artifact_contract.py:249`
  - `scripts/audit/check_sensitivity_artifact_contract.py:283`
- gate-health active blocker family:
  - `status/audit/release_gate_health_status.json:24`
  - `status/audit/release_gate_health_status.json:25`
  - `status/audit/release_gate_health_status.json:26`

Current nuance:

- release preflight now passes (`PREFLIGHT_OK`) but does not satisfy release evidence production:
  - `status/audit/sensitivity_release_preflight.json:15`
  - `status/audit/sensitivity_release_preflight.json:24`

---

## 3) Fourth-Attempt Retrospective (Why SK-C1 Still Reopened)

1. **Preflight became reliable, production did not.**  
   Preflight confirms prerequisites, but release run completion still does not guarantee artifact/report presence at canonical paths.

2. **Long-run operational reliability remains underspecified.**  
   Release sweep is expensive; interruption/restart behavior and progress semantics still allow repeated partial attempts.

3. **Gate/checker semantics are strict but recovery workflow is not fully standardized.**  
   The system fails correctly, but operator path to deterministic pass is still too brittle.

4. **SK-C1 is being conflated with unrelated bounded constraints in repeated reviews.**  
   Missing folio pages are a documented H3 bounded external constraint and should not be treated as SK-C1 release blocker.

---

## 4) External-Constraint Guardrail (Missing Folios)

SK-C1 closure must be evaluated independently from approved irrecoverable folio gaps.

Binding rule for this plan:

- Missing folio pages are **not** SK-C1 blockers when they are policy-pinned and lane-bounded under H3 artifacts.
- SK-C1 scope is strictly release sensitivity evidence production and release contract integrity.

Reference surfaces:

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- `planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md`

---

## 5) Scope and Non-Goals

## In Scope

- release-mode sensitivity artifact/report production and contract compliance,
- deterministic release run orchestration for expensive sweep workloads,
- contract/gate parity across:
  - `scripts/audit/pre_release_check.sh`
  - `scripts/verify_reproduction.sh`
  - `scripts/ci_check.sh`
  - `scripts/audit/check_sensitivity_artifact_contract.py`
  - `scripts/audit/build_release_gate_health_status.py`,
- regression tests that lock missing-artifact and release-path parity failure classes,
- explicit skeptic criteria separation between SK-C1 and approved-lost folio constraints.

## Out of Scope

- remediating SK-H1/H2/H3/M1/M2/M3/M4 substantive findings,
- changing H3 irrecoverability classification,
- scientific reinterpretation of sensitivity outcomes beyond contract/governance reliability,
- manual artifact fabrication/copying outside runner-emitted provenance paths.

---

## 6) Deterministic SK-C1.5 Closure Framework

## Lane A: `C1_5_ALIGNED`

All are true:

- `status/audit/sensitivity_sweep_release.json` exists and is runner-emitted,
- `reports/audit/SENSITIVITY_RESULTS_RELEASE.md` exists and contract-coherent,
- `check_sensitivity_artifact_contract.py --mode release` passes,
- pre-release/verify/CI SK-C1 checks pass with identical semantics,
- release gate health no longer includes sensitivity release blocker family.

## Lane B: `C1_5_QUALIFIED`

All are true:

- checker/gate semantics are coherent and deterministic,
- production path is stable and restart-safe,
- release artifact still fails on legitimate data/quality readiness criteria (not missing-file/process defect).

## Lane C: `C1_5_BLOCKED`

Any true:

- release artifact/report missing,
- producer/checker/gate reason drift,
- non-deterministic runner state or unrecoverable partial output behavior.

## Lane D: `C1_5_INCONCLUSIVE`

Used only when evidence is insufficient to classify due missing diagnostics or incomplete run-state traces.

---

## 7) Success Criteria (Exit Conditions)

SK-C1.5 is complete only if all are satisfied:

1. canonical release artifact/report pair are produced by release runner path,
2. release contract checker passes,
3. SK-C1 stage passes in pre-release, verify, and CI with coherent reasons,
4. gate-health sensitivity blocker reasons clear or transition to legitimate non-missing release outcome,
5. long-running release sweep has reliable progress/checkpoint semantics,
6. regression tests cover this pass-5 failure class and fail-closed behavior,
7. skeptic criteria explicitly prevent recurring misuse of missing-folio constraints as SK-C1 blockers.

---

## 8) Workstreams

## WS-C1.5-A: Baseline Freeze and Blocker Decomposition

**Goal:** Create a complete, line-referenced SK-C1 failure map for pass 5.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-5 SK-C1 tuple (commands, fail points, reason family). | New `reports/skeptic/SK_C1_5_CONTRACT_REGISTER.md` | Register captures producer->checker->gate->gate-health chain. |
| A2 | Decompose blocker vectors (`artifact_absent`, `run_completion_gap`, `reason_drift_risk`, `operator_retry_risk`). | same | Each vector has owner checks and tests. |
| A3 | Define canonical SK-C1 release paths and disallow alternates for gate entitlement. | same + policy references | No ambiguity in accepted release evidence paths. |

### Verification

```bash
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release
python3 scripts/audit/build_release_gate_health_status.py
```

---

## WS-C1.5-B: Release Production Determinism

**Goal:** Guarantee release artifact/report emission or fail with deterministic reason.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Enforce canonical release output path contract in runner (`status` + `report`). | `scripts/analysis/run_sensitivity_sweep.py` | Release mode cannot complete without both outputs. |
| B2 | Add terminal run-state artifact for release execution (`STARTED`, `RUNNING`, `COMPLETED`, `FAILED`) with reason codes. | New `status/audit/sensitivity_release_run_status.json` | Operator and gates can distinguish never-run vs incomplete vs failed. |
| B3 | Harden atomic write/rename semantics for release artifacts and run-state transitions. | runner output writer path | Partial writes cannot masquerade as valid evidence. |

### Verification

```bash
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release
```

---

## WS-C1.5-C: Testability for Expensive Release Sweep

**Goal:** Add explicit fast-validation modes that test contract logic without pretending release completion.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define release workflow profiles (`smoke`, `standard`, `release-depth`) and map entitlement rules. | runner args + `docs/SENSITIVITY_ANALYSIS.md` | Only `release-depth` may set release-evidence-ready true. |
| C2 | Add reduced-scope scenario execution mode for local contract-path testing with explicit non-release entitlement marker. | runner + summary fields | Fast runs are testable and never misclassified as release-ready. |
| C3 | Add deterministic preflight + smoke contract tests in CI for rapid feedback. | tests + CI contract config | Contract regressions caught without full sweep runtime. |

### Verification

```bash
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --max-scenarios 1
```

---

## WS-C1.5-D: Long-Run Observability and Resume Integrity

**Goal:** Eliminate repeated lockup ambiguity and restart churn.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Emit heartbeat updates with stage/scenario index/elapsed/ETA/last-write timestamp. | `status/audit/sensitivity_progress.json` | Progress is visible and monotonic. |
| D2 | Persist scenario-level checkpoint with checksum and resume pointer integrity checks. | `status/audit/sensitivity_checkpoint.json` | Resume is deterministic and idempotent. |
| D3 | Add stale-heartbeat detection reason code to run-status artifact. | run-status + checker diagnostics | Stalled vs slow is machine-distinguished. |

### Verification

```bash
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
cat status/audit/sensitivity_progress.json
cat status/audit/sensitivity_release_run_status.json
```

---

## WS-C1.5-E: Checker and Policy Semantic Parity

**Goal:** Keep producer/checker/policy release-readiness semantics perfectly aligned.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Expand release checker diagnostics for `preflight_ok_but_release_artifact_missing` as explicit reason class. | `scripts/audit/check_sensitivity_artifact_contract.py` | Failure messages are unambiguous and action-oriented. |
| E2 | Add freshness policy for preflight and release artifacts to avoid stale-state false confidence. | `configs/audit/sensitivity_artifact_contract.json` + checker | Stale preflight or stale release artifacts fail closed. |
| E3 | Enforce strict report-summary parity in release mode (decision/status/warnings/caveats). | checker + report generator | JSON/report drift cannot silently pass. |

### Verification

```bash
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode ci
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release
```

---

## WS-C1.5-F: Gate Path Consolidation and Coherence

**Goal:** Ensure pre-release, verify, and CI consume exactly the same SK-C1 semantics.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Introduce shared SK-C1 helper invocation used by all three gate scripts. | `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, `scripts/ci_check.sh` | Single-source SK-C1 gate logic prevents drift. |
| F2 | Align env var/path resolution order for all gate scripts. | same | Same workspace state yields same SK-C1 result. |
| F3 | Synchronize `build_release_gate_health_status.py` with checker reason set and run-state artifact. | `scripts/audit/build_release_gate_health_status.py` | Gate-health reasons are deterministic and current. |

### Verification

```bash
bash scripts/audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
python3 scripts/audit/build_release_gate_health_status.py
```

---

## WS-C1.5-G: Missing-Folio Non-Blocking Criteria and Playbook Alignment

**Goal:** Prevent false reopening loops where irrecoverable folio loss is misclassified as SK-C1 failure.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add explicit playbook criterion separating approved irrecoverable source gaps from open methodological blockers. | `planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md` | Skeptic criteria now enforce bounded external-constraint handling. |
| G2 | Add SK-C1 register section documenting that H3 approved-lost folios are non-blocking for release sensitivity contract. | `reports/skeptic/SK_C1_5_CONTRACT_REGISTER.md` | Future assessments cannot conflate SK-C1 with H3 irrecoverability. |
| G3 | Add checker/gate assertion that SK-C1 state depends only on sensitivity contract artifacts and release checker outputs. | checker/gate docs/tests | Cross-domain blocker leakage is prevented. |

### Verification

```bash
rg -n "Irrecoverable Source-Data Criteria|approved irrecoverable loss|not a new blocker" planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md
rg -n "SK-C1.*non-blocking|approved-lost" reports/skeptic/SK_C1_5_CONTRACT_REGISTER.md
```

---

## WS-C1.5-H: Regression Locking and Governance Closeout

**Goal:** Prevent a fifth recurrence of the same SK-C1 failure mode.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Add/extend contract tests for missing release artifact with preflight pass state. | `tests/audit/test_pre_release_contract.py`, `tests/audit/test_verify_reproduction_contract.py`, `tests/audit/test_ci_check_contract.py`, `tests/audit/test_sensitivity_artifact_contract.py` | Pass-5 failure class is test-locked. |
| H2 | Add runner tests for run-status/progress/checkpoint schema and stale heartbeat behavior. | `tests/analysis/test_sensitivity_sweep_end_to_end.py` | Long-run operational integrity is test-covered. |
| H3 | Define execution status report template and audit-log linkage requirements for SK-C1.5. | `reports/skeptic/SKEPTIC_C1_5_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | End-to-end traceability from finding to closure lane. |

### Verification

```bash
python3 -m pytest -q \
  tests/analysis/test_sensitivity_sweep_end_to_end.py \
  tests/audit/test_sensitivity_artifact_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_release_gate_health_status_builder.py
```

---

## 9) Execution Order

1. WS-C1.5-A Baseline Freeze
2. WS-C1.5-B Release Determinism
3. WS-C1.5-C Testability Profiles
4. WS-C1.5-D Observability/Resume Integrity
5. WS-C1.5-E Checker/Policy Parity
6. WS-C1.5-F Gate Consolidation
7. WS-C1.5-G Missing-Folio Non-Blocking Alignment
8. WS-C1.5-H Regression/Governance Closeout

Rationale:

- lock scope and blocker semantics first,
- harden producer behavior second,
- then enforce parity across checker/gates,
- and finish with regression locks plus governance proof.

---

## 10) Decision Matrix for SK-C1.5

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Release artifacts exist, release checker passes, and all gate paths are coherent. | `C1_5_ALIGNED` | "Release sensitivity evidence is produced and contract-valid for gate entitlement." |
| Contract/gate path is coherent but release evidence fails due legitimate quality/data readiness reasons. | `C1_5_QUALIFIED` | "SK-C1 process integrity is restored; release readiness remains policy-qualified." |
| Artifact/report missing or producer/checker/gate mismatch persists. | `C1_5_BLOCKED` | "SK-C1 remains blocked by release sensitivity contract failure." |
| Evidence is insufficient to classify reliably. | `C1_5_INCONCLUSIVE` | "SK-C1.5 remains provisional pending complete release diagnostics." |

---

## 11) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-C1.5-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Created `reports/skeptic/SK_C1_5_CONTRACT_REGISTER.md` with pass-5 failure tuple and dependency map. |
| WS-C1.5-B Release Determinism | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added deterministic release run-state lifecycle artifact and failure-state persistence in runner. |
| WS-C1.5-C Testability Profiles | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Codified `smoke`/`standard`/`release-depth` semantics in `docs/SENSITIVITY_ANALYSIS.md`. |
| WS-C1.5-D Observability/Resume Integrity | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added full-battery heartbeat events plus explicit `run_failed` progress/checkpoint/run-status transitions. |
| WS-C1.5-E Checker/Policy Parity | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added explicit preflight-ok/missing-artifact class and runtime freshness/run-status checks in checker + policy. |
| WS-C1.5-F Gate Consolidation | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Gate-health now consumes run-status path/state; SK-C1 semantics aligned through shared checker/runtime contract. |
| WS-C1.5-G Missing-Folio Alignment | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Registered SK-C1 scope boundary excluding approved irrecoverable H3 folio loss as blocker class. |
| WS-C1.5-H Regression/Governance | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended SK-C1 regression tests and added `SKEPTIC_C1_5_EXECUTION_STATUS.md` + audit-log linkage. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 12) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Release run remains operationally expensive and repeatedly interrupted, leaving artifacts absent. | High | High | Add run-status, heartbeat, checkpoint, and resume integrity checks. |
| R2 | Preflight success continues to be misread as release completion. | High | High | Add explicit checker reason class and gate messaging for preflight-only state. |
| R3 | Gate scripts drift in SK-C1 semantics and report inconsistent reasons. | Medium | High | Consolidate SK-C1 helper path and lock with parity tests. |
| R4 | Stale preflight/release artifacts produce false confidence. | Medium | Medium | Introduce freshness policy and fail-closed checks. |
| R5 | H3 missing-folio constraints are repeatedly misclassified as SK-C1 blockers. | Medium | Medium | Playbook criteria + SK-C1 register explicit non-blocking rule. |

---

## 13) Deliverables

Required deliverables for SK-C1.5 execution pass:

1. `reports/skeptic/SK_C1_5_CONTRACT_REGISTER.md`
2. deterministic release run-state artifact (`status/audit/sensitivity_release_run_status.json`)
3. hardened release sensitivity producer/checker/gate parity
4. explicit testability profile governance for expensive release sweep
5. expanded SK-C1 regression tests across analysis/audit surfaces
6. `reports/skeptic/SKEPTIC_C1_5_EXECUTION_STATUS.md`
7. `AUDIT_LOG.md` linkage from pass-5 finding to SK-C1.5 outcome

---

## 14) Closure Criteria

SK-C1 (pass-5 scope) can be considered closed only if one is true:

1. `C1_5_ALIGNED`: release evidence is produced and release gates are coherent/passing for SK-C1 contract checks, or
2. `C1_5_QUALIFIED`: contract integrity is fully restored and failures (if any) are legitimate non-missing policy outcomes with deterministic diagnostics.

If neither is satisfied, SK-C1 remains **OPEN**.
