# Execution Plan: Audit 9 Remediation

**Source Audit:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_9.md`  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work but does not execute it.

---

## 1) Objective

Close all open Audit 9 findings with emphasis on release-evidence readiness and policy clarity.

Primary objectives:

1. Resolve the remaining **High** blocker (`RI-13`) preventing release verification.
2. Implement and document the RI-11 criteria update as an explicit release-policy decision.
3. Correct indistinguishability preflight page-ID matching logic (`RI-14` / `ST-3`).
4. Improve enforcement posture for strict vs non-strict execution (`RI-12`).
5. Reduce residual confidence risks in coverage, historical provenance, and release hygiene (`MC-3`, `MC-2R`, `INV-1`, `DOC-5`).

Success condition for next pass:

- No unresolved **High** findings.
- All **Medium** findings either closed or explicitly policy-accepted with verifiable evidence.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Sensitivity release-evidence non-readiness | `RI-13` | WS-A |
| Indistinguishability preflight ID normalization and naming consistency | `RI-14`, `ST-3` | WS-B |
| RI-11 criteria reclassification and release-policy codification | `RI-11`, `DOC-5` | WS-C |
| Strict-mode enforcement posture (default/fail-safe behavior) | `RI-12` | WS-D |
| Coverage depth risk in low-covered modules | `MC-3` | WS-E |
| Historical orphaned-run provenance uncertainty | `MC-2R` | WS-F |
| Dirty release baseline policy/hygiene | `INV-1` | WS-G |

Out of scope (monitor-only, currently resolved/improved):

- `RI-10` gate false-pass semantics
- Legacy `status/by_run` verify artifact drift (currently clean in workspace)

---

## 3) Execution Status Tracker

Update this during implementation.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Sensitivity Release Evidence Closure | BLOCKED | Codex | 2026-02-10 |  | Canonical `voynich_real` release sweep attempts did not complete in this environment; active artifact remains non-ready (`release_evidence_ready=false`). |
| WS-B Indistinguishability Page-ID Normalization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Split folio normalization implemented (`f89r1` -> `f89r`), reducing strict missing-page count from `10` to `4`. |
| WS-C RI-11 Policy Codification | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added explicit `DATA_AVAILABILITY` reason-code handling and release-policy documentation for lost/unavailable source pages. |
| WS-D Strict-Mode Enforcement Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Verifier now always enforces strict preflight policy and validates strict artifact semantics. |
| WS-E Coverage Risk Reduction | IN PROGRESS | Codex | 2026-02-10 |  | Coverage increased to `56.08%`; only one module remains `<20%` (`feature_discovery`). |
| WS-F Orphaned-Run Provenance Resolution | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added idempotence reconciliation test; repair script confirms stable run-state (`scanned=0 updated=0`). |
| WS-G Release Baseline Hygiene | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Pre-release contract tests updated; strict preflight artifact policy is now part of baseline checks. |
| Final Verification + Audit 10 Prep | BLOCKED | Codex | 2026-02-10 |  | Blocked by WS-A unresolved sensitivity release-evidence state. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Recommended Execution Order and Dependencies

Execute in this order:

1. WS-A (release blocker)
2. WS-B (correctness of strict preflight accounting)
3. WS-C (policy alignment for RI-11 criteria update)
4. WS-D (strict/non-strict enforcement consistency)
5. WS-F (historical provenance policy closure)
6. WS-E (coverage confidence hardening)
7. WS-G (release hygiene and change-control enforcement)
8. Final verification and re-audit

Dependency notes:

- WS-A must complete before final release checks can pass.
- WS-B should complete before WS-C/WS-D are finalized, so policy and behavior reference the same page-ID semantics.
- WS-C documentation updates should reflect outputs of WS-B and WS-D.
- WS-F policy decisions should be finalized before publication-freeze claims.

---

## 5) Workstream Details

## WS-A: Sensitivity Release Evidence Closure

**Addresses:** `RI-13`  
**Priority:** High  
**Objective:** Produce conclusive, release-ready sensitivity evidence or enforce an explicit non-release gate state.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Diagnose why all release scenarios remain invalid/insufficient and classify root causes (data sufficiency vs threshold policy vs implementation behavior). | `scripts/analysis/run_sensitivity_sweep.py`, `reports/audit/SENSITIVITY_RESULTS.md`, `status/audit/sensitivity_sweep.json` | Root-cause matrix documented with at least one reproducible evidence run. |
| A2 | Implement remediation for root causes that are code/config issues (not policy constraints). | `scripts/analysis/run_sensitivity_sweep.py` and dependent analysis modules | `valid_scenarios > 0` and non-collapse conditions become attainable under defined conditions. |
| A3 | Regenerate canonical release-mode sensitivity artifacts. | `status/audit/sensitivity_sweep.json`, `reports/audit/SENSITIVITY_RESULTS.md` | Artifact summary shows internally consistent fields and updated provenance. |
| A4 | Preserve strict fail-closed gate semantics and add regression tests around release-evidence criteria. | `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, `tests/audit/` | Gates fail on inconclusive/non-ready states and pass only on policy-conformant evidence. |
| A5 | Update docs to match exact enforced criteria. | `docs/REPRODUCIBILITY.md`, `docs/SENSITIVITY_ANALYSIS.md` | Human guidance and script behavior are semantically identical. |

### Verification Commands (post-implementation)

```bash
python3 scripts/analysis/run_sensitivity_sweep.py
bash scripts/audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py
```

---

## WS-B: Indistinguishability Page-ID Normalization

**Addresses:** `RI-14`, `ST-3`  
**Priority:** High  
**Objective:** Ensure strict preflight missing-page accounting is accurate when corpus pages use split folio identifiers.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Define canonical page-ID normalization policy (e.g., `f89r1`/`f89r2` -> base `f89r`) for preflight matching. | `scripts/synthesis/run_indistinguishability_test.py`, `src/synthesis/profile_extractor.py` | Policy is explicit and deterministic. |
| B2 | Implement normalization in preflight availability checks and emitted diagnostics. | `scripts/synthesis/run_indistinguishability_test.py` | Missing-page list no longer over-counts split-folio cases. |
| B3 | Add tests covering canonical, split, and genuinely missing folio scenarios. | `tests/synthesis/test_run_indistinguishability_runner.py` | Tests fail on regression to exact-string-only matching. |
| B4 | Validate by-run artifact payload correctness for missing page counts and lists. | `status/synthesis/TURING_TEST_RESULTS.json` (runtime output) | Preflight payload reflects true missing set under normalization rules. |

### Verification Commands (post-implementation)

```bash
python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
python3 -m pytest -q tests/synthesis/test_run_indistinguishability_runner.py
```

---

## WS-C: RI-11 Policy Codification (Criteria Update)

**Addresses:** `RI-11`, `DOC-5`  
**Priority:** Medium  
**Objective:** Encode the agreed interpretation that lost/unavailable source pages are a scope constraint, not a coding defect.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Add explicit policy language for source-data unavailability in release docs and audit framework docs. | `docs/REPRODUCIBILITY.md`, `docs/PROVENANCE.md`, optional `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md` appendix | Policy appears once as canonical text and is cross-referenced. |
| C2 | Define release-claim boundary for strict indistinguishability when prerequisite pages are unavailable. | `docs/REPRODUCIBILITY.md`, `reports/audit/` templates | Release claims cannot imply strict completion when data prerequisites are unmet. |
| C3 | Add machine-readable status annotation if strict path is blocked by approved data-scope constraints. | `status/synthesis/TURING_TEST_RESULTS.json` schema handling and/or reporting scripts | Blocked state includes reason category (`DATA_AVAILABILITY`) and is distinguishable from code failure. |
| C4 | Update audit report template/checklist language to prevent recurring severity reclassification drift. | `planning/audit/*` templates or checklist docs | Future audits classify similar cases consistently. |

### Verification Commands (post-implementation)

```bash
rg -n "data availability|lost|unavailable source|strict" docs planning/audit reports/audit
python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
```

---

## WS-D: Strict-Mode Enforcement Hardening

**Addresses:** `RI-12`  
**Priority:** Medium  
**Objective:** Prevent accidental non-strict execution in release-evidence paths.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Decide release-policy default: strict-by-default or mandatory strict flag for release scripts. | `scripts/verify_reproduction.sh`, `scripts/audit/pre_release_check.sh`, docs | One enforceable policy is selected and documented. |
| D2 | Implement policy enforcement in release entrypoints and verifier flow. | `scripts/verify_reproduction.sh`, `scripts/ci_check.sh` (if needed) | Release verification cannot complete using non-strict indistinguishability path silently. |
| D3 | Add contract tests for mode-selection behavior and failure messaging. | `tests/audit/`, `tests/synthesis/` | Mode drift is automatically detected. |
| D4 | Ensure command help and docs clearly separate exploratory vs release-evidentiary invocation. | `scripts/synthesis/run_indistinguishability_test.py` help text, `docs/REPRODUCIBILITY.md` | External users can execute correct mode without ambiguity. |

### Verification Commands (post-implementation)

```bash
bash scripts/verify_reproduction.sh
VERIFY_STRICT=1 bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/audit tests/synthesis
```

---

## WS-E: Coverage Risk Reduction

**Addresses:** `MC-3`  
**Priority:** Medium  
**Objective:** Increase confidence in under-tested synthesis/anomaly modules (currently <20%).

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Prioritize low-covered modules by release impact and add focused behavior tests. | `tests/analysis/`, `tests/synthesis/` | Targeted modules move above agreed minimum (or are explicitly exempted with rationale). |
| E2 | Add/adjust module-level coverage thresholds for critical paths where practical. | `scripts/ci_check.sh`, coverage contract tests | CI prevents regression in selected critical modules. |
| E3 | Re-run coverage baseline and publish delta in fix status report. | `status/ci_coverage.json`, `reports/audit/FIX_EXECUTION_STATUS_9.md` | Coverage improvements are measurable and traceable. |

### Verification Commands (post-implementation)

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
```

---

## WS-F: Orphaned-Run Provenance Resolution

**Addresses:** `MC-2R`  
**Priority:** Medium  
**Objective:** Resolve or explicitly accept historical orphaned runs with durable policy and reproducible tooling.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Decide final treatment of `orphaned` rows lacking manifests (retain + annotate, archive, or migrate state). | `docs/PROVENANCE.md`, `AUDIT_LOG.md` | Final policy accepted and documented. |
| F2 | Update reconciliation tooling to enforce policy idempotently and emit machine-readable report. | `scripts/audit/repair_run_statuses.py`, `status/audit/run_status_repair_report.json` | Repeat runs produce stable counts and clear deltas. |
| F3 | Add tests around reconciliation behavior and policy invariants. | `tests/audit/test_repair_run_statuses.py` | Tooling behavior is regression-protected. |
| F4 | Ensure audit reporting includes orphaned-state interpretation to avoid recurring ambiguity. | `reports/audit/` report templates | Future audit reports reference same policy language. |

### Verification Commands (post-implementation)

```bash
python3 scripts/audit/repair_run_statuses.py
python3 -m pytest -q tests/audit/test_repair_run_statuses.py
```

---

## WS-G: Release Baseline Hygiene

**Addresses:** `INV-1`  
**Priority:** Medium  
**Objective:** Ensure dirty-tree release conditions are intentional, traceable, and policy-governed.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| G1 | Define acceptable dirty-release scenarios and mandatory rationale metadata. | `docs/REPRODUCIBILITY.md`, `AUDIT_LOG.md` | Override usage is policy-bounded. |
| G2 | Enforce rationale capture and optional ticket linkage in pre-release script output. | `scripts/audit/pre_release_check.sh` | Dirty override cannot run without structured reason string. |
| G3 | Add tests for clean-tree and dirty-override gate behaviors. | `tests/audit/test_pre_release_contract.py` | Gate behavior is deterministic and tested. |
| G4 | Add release checklist step to summarize active diff scope before signoff. | `docs/REPRODUCIBILITY.md`, release checklist docs | Final signoff includes explicit diff acknowledgment. |

### Verification Commands (post-implementation)

```bash
bash scripts/audit/pre_release_check.sh
ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='planned release exception' bash scripts/audit/pre_release_check.sh
python3 -m pytest -q tests/audit/test_pre_release_contract.py
```

---

## 6) Cross-Reference Matrix (Finding -> Planned Closure Evidence)

| Finding ID | Planned Closure Evidence |
|---|---|
| `RI-13` | Sensitivity artifact reaches release-ready conclusive state (or explicit release-block policy) and verifier/pre-release checks pass accordingly. |
| `RI-14` | Preflight missing-page diagnostics normalize split folios and report accurate missing counts. |
| `RI-11` | Data-availability constraint policy explicitly documented and reflected in release-claim boundaries. |
| `RI-12` | Release workflows enforce strict-mode requirements with contract tests. |
| `MC-3` | Low-covered high-impact modules gain coverage or documented exemptions; CI reflects intended thresholds. |
| `MC-2R` | Orphaned-run treatment policy finalized with reproducible reconciliation outputs/tests. |
| `INV-1` | Dirty-release override remains controlled, justified, and test-validated. |
| `DOC-5` | RI-11 criteria update is codified in canonical docs and reused by audit/report templates. |
| `ST-3` | Page-ID naming normalization implemented for preflight consistency. |

---

## 7) Final Verification Gate (Post-Execution)

Remediation is complete only if all checks pass:

1. `bash scripts/audit/pre_release_check.sh`
2. `bash scripts/verify_reproduction.sh`
3. `bash scripts/ci_check.sh`
4. `REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only`
5. `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
6. Any new/updated audit contract tests for gate semantics, strict mode, and provenance reconciliation

Post-execution deliverables:

- `reports/audit/FIX_EXECUTION_STATUS_9.md`
- `reports/audit/COMPREHENSIVE_AUDIT_REPORT_10.md` (next assessment-only pass)

---

## 8) Change-Control Notes

- Keep WS-A and WS-B in separate review units; both alter release evidence interpretation.
- Treat WS-C as a policy-control change that must be approved by stakeholders before release narrative updates.
- For each finding closure, record:
  - changed files,
  - verification command outputs,
  - explicit finding-ID closure statement.
- Any remaining blocked items must be explicitly listed in `FIX_EXECUTION_STATUS_9.md` with reason category (`CODE`, `DATA_AVAILABILITY`, or `POLICY_PENDING`).
