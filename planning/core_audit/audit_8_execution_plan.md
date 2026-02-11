# Execution Plan: Audit 8 Remediation

**Source Audit:** `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_8.md`  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work but does not execute it.

---

## 1) Objective

Close all open Audit 8 findings with emphasis on release-evidence integrity:

1. Prevent release-gate pass states when sensitivity robustness is `INCONCLUSIVE`.
2. Resolve strict indistinguishability release-path blockage (`REQUIRE_COMPUTED=1`).
3. Eliminate ambiguity in historical provenance/status artifacts.
4. Raise confidence in test/coverage depth and release baseline hygiene.
5. Align playbook output contract and repository documentation paths.

Success condition for next pass:

- No unresolved **High** findings.
- Medium findings either closed or explicitly policy-accepted with evidence.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Sensitivity release gate semantics vs robustness semantics | `RI-10` | WS-A |
| Strict indistinguishability data prerequisites + default strictness posture | `RI-11`, `RI-12` | WS-B |
| Coverage blind spots in zero-coverage modules | `MC-3` | WS-C |
| Historical orphaned run-state and legacy verify artifact semantics | `MC-2R`, `ST-1` | WS-D |
| Dirty release baseline / intentional-cut process | `INV-1` | WS-E |
| Playbook output filename/path contract mismatch | `DOC-4` | WS-F |

Out of scope (already improved/resolved in Audit 8, monitor for regression only):

- `MC-6` verifier false-pass condition
- CI sentinel integration improvements
- sensitivity full-sweep scenario count completion (`17/17`)

---

## 3) Execution Status Tracker

Update this during implementation.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Sensitivity Gate Semantics | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Release gates now require conclusive robustness + quality gate and fail closed on `INCONCLUSIVE`. |
| WS-B Indistinguishability Strict Path | BLOCKED | Codex | 2026-02-10 |  | Strict preflight + blocked artifact output implemented; strict computed run still fails on missing `voynich_real` pharma pages. |
| WS-C Coverage Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added targeted tests for prior 0%-coverage modules; coverage increased to 52.28%. |
| WS-D Provenance/Run-State Reconciliation | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Legacy verify artifact handling hardened (`legacy-report`, support_cleanup correctness, gate checks). |
| WS-E Release Baseline Hygiene | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Dirty release override now requires `DIRTY_RELEASE_REASON`; pre-release gate updated accordingly. |
| WS-F Documentation Contract Alignment | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added root-level doc aliases and updated policy docs for new gate semantics. |
| Final Verification + Audit 9 Prep | BLOCKED | Codex | 2026-02-10 |  | Final release gate remains blocked by inconclusive sensitivity evidence and strict data prerequisites. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Recommended Execution Order and Dependencies

Execute in this order:

1. WS-A (release-gate semantics; highest risk)
2. WS-B (strict indistinguishability evidentiary path)
3. WS-D (historical provenance clarity)
4. WS-C (coverage hardening after behavior stabilizes)
5. WS-E (release hygiene enforcement)
6. WS-F (docs contract support_cleanup)
7. Final verification + re-core_audit

Dependency notes:

- WS-A must complete before final release checks are trusted.
- WS-B can become `BLOCKED` if real-page prerequisites cannot be sourced; if blocked, policy documentation must be explicit before release.
- WS-D should complete before final report generation so stale-status findings do not recur.
- WS-F should be finalized after WS-A/WS-B semantics are stable to avoid documentation churn.

---

## 5) Workstream Details

## WS-A: Sensitivity Gate Semantics

**Addresses:** `RI-10`  
**Priority:** High  
**Objective:** Ensure automation cannot treat sensitivity artifacts as release-ready when robustness is `INCONCLUSIVE` or quality gates fail.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Define release-evidence policy contract: required robustness states (`PASS` only vs allow `FAIL` with caveats), and minimum quality-gate constraints. | `governance/SENSITIVITY_ANALYSIS.md`, `governance/governance/REPRODUCIBILITY.md` | Policy is explicit, testable, and reviewer-readable. |
| A2 | Implement gate checks that enforce the policy in release scripts. | `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Release checks fail when artifact summary violates policy (e.g., `robustness_decision=INCONCLUSIVE`). |
| A3 | Add machine-readable guard fields if needed to avoid parsing ambiguity. | `scripts/phase2_analysis/run_sensitivity_sweep.py`, `core_status/core_audit/sensitivity_sweep.json` schema | Gate scripts consume explicit fields instead of implicit interpretation. |
| A4 | Add/expand contract tests for gate behavior under `PASS`/`FAIL`/`INCONCLUSIVE` scenarios. | `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, sensitivity guardrail tests | Tests fail on false-pass regressions. |
| A5 | Update phase7_human report wording to mirror gate semantics exactly. | `reports/core_audit/SENSITIVITY_RESULTS.md` template logic | Human report and automation logic cannot drift semantically. |

### Verification Commands (post-implementation)

```bash
bash scripts/core_audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_guardrails.py
```

---

## WS-B: Indistinguishability Strict Release Path

**Addresses:** `RI-11`, `RI-12`  
**Priority:** High  
**Objective:** Make strict computed-only indistinguishability either executable and evidentiary, or explicitly blocked and policy-labeled.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Add explicit dataset prerequisite validator command/report for required pharma pages (presence + minimum content checks). | `scripts/phase3_synthesis/run_indistinguishability_test.py` or helper under `scripts/core_audit/` | Validator returns deterministic pass/fail with missing-page list. |
| B2 | Decide default mode policy: strict-by-default for release entrypoints, or mandatory strict flag in release scripts/docs. | `scripts/verify_reproduction.sh`, `governance/governance/REPRODUCIBILITY.md` | Release path cannot silently use fallback/simulated profile logic. |
| B3 | If prerequisite data can be populated: add/import missing real pages and re-run strict path; if not, codify blocked status with explicit release exclusion. | data loading scripts and/or docs | Clear closure: either strict run passes, or release policy explicitly forbids claiming this check as passed. |
| B4 | Add regression tests for strict preflight behavior and fallback prohibition. | `tests/phase3_synthesis/test_run_indistinguishability_runner.py` | Tests enforce fail-fast with actionable diagnostics. |
| B5 | Ensure final report artifact clearly records strict-mode execution outcome and provenance. | `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`, docs references | External readers can core_audit whether strict mode actually ran. |

### Verification Commands (post-implementation)

```bash
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 -m pytest -q tests/phase3_synthesis/test_run_indistinguishability_runner.py
```

---

## WS-C: Coverage Hardening

**Addresses:** `MC-3`  
**Priority:** Medium  
**Objective:** Reduce risk from untested core modules while preserving practical CI throughput.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Add targeted tests for 0%-coverage modules: `core/logging`, `core/models`, `qc/anomalies`, `qc/checks`, `storage/filesystem`, `storage/interface`. | `tests/phase1_foundation/core/`, `tests/phase1_foundation/qc/`, `tests/phase1_foundation/storage/` | Each prior 0%-coverage module reaches non-trivial coverage with behavior assertions. |
| C2 | Add minimum per-module coverage gates for critical low-level modules, or explicit justified exemptions. | `scripts/ci_check.sh`, core_audit tests | CI fails on regression below agreed thresholds. |
| C3 | Recompute baseline coverage target and stage policy after new tests. | `scripts/ci_check.sh`, `governance/governance/REPRODUCIBILITY.md` | Coverage thresholds reflect actual enforced target, not historical values. |

### Verification Commands (post-implementation)

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
```

---

## WS-D: Provenance and Run-State Reconciliation

**Addresses:** `MC-2R`, `ST-1`  
**Priority:** Medium  
**Objective:** Remove ambiguity around historical run state and legacy verify artifact status fields.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Define final policy for orphaned rows without manifests (retain vs archive_legacy vs purge, with rationale). | `governance/PROVENANCE.md`, `AUDIT_LOG.md` | Policy is explicit and reproducible. |
| D2 | Extend/validate repair tooling to enforce policy idempotently and report deltas. | `scripts/core_audit/repair_run_statuses.py`, `core_status/core_audit/run_status_repair_report.json` | Repeat runs produce stable results and clear reporting. |
| D3 | Resolve legacy `core_status/by_run/verify_*.json` `provenance.status` ambiguity (support_cleanup, archival move, or legacy tagging strategy). | `scripts/core_audit/cleanup_status_artifacts.sh`, `governance/PROVENANCE.md` | No ambiguous active artifacts remain in standard core_audit surface, or they are clearly marked legacy. |
| D4 | Add test coverage for reconciliation and artifact policy assumptions. | `tests/core_audit/test_repair_run_statuses.py`, provenance contract tests | Policy enforcement is protected from drift. |

### Verification Commands (post-implementation)

```bash
python3 scripts/core_audit/repair_run_statuses.py
python3 -m pytest -q tests/core_audit/test_repair_run_statuses.py tests/core_audit/test_provenance_contract.py
```

---

## WS-E: Release Baseline Hygiene

**Addresses:** `INV-1`  
**Priority:** Medium  
**Objective:** Ensure dirty-tree releases are explicit exceptions with traceable approval, not default behavior.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Define criteria for acceptable `ALLOW_DIRTY_RELEASE=1` usage and required evidence log. | `governance/governance/REPRODUCIBILITY.md`, `AUDIT_LOG.md` | Dirty release is controlled by policy, not ad hoc operator choice. |
| E2 | Optionally strengthen pre-release check output to require explicit reason text when override is used. | `scripts/core_audit/pre_release_check.sh` | Override path leaves an auditable rationale trail. |
| E3 | Add contract test for dirty-tree gate and override behavior. | `tests/core_audit/test_pre_release_contract.py` | Gate behavior is deterministic and test-backed. |

### Verification Commands (post-implementation)

```bash
bash scripts/core_audit/pre_release_check.sh
ALLOW_DIRTY_RELEASE=1 bash scripts/core_audit/pre_release_check.sh
python3 -m pytest -q tests/core_audit/test_pre_release_contract.py
```

---

## WS-F: Documentation Contract Alignment

**Addresses:** `DOC-4`  
**Priority:** Medium  
**Objective:** Align playbook expected-output paths and repo documentation so checklist interpretation is unambiguous.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Choose canonical output location convention (`governance/*` vs root-level aliases) and record it once. | `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md` and/or docs index | No path ambiguity remains for required outputs. |
| F2 | Add compatibility shim if needed (root-level pointers to docs, or updated playbook references). | root markdown stubs or playbook updates | Existing checklists and tooling continue to function. |
| F3 | Cross-link all required references in one index section to reduce reviewer search friction. | `README.md`, `governance/governance/REPRODUCIBILITY.md`, `AUDIT_LOG.md` | External reviewer can locate all core_audit artifacts from one entry point. |

### Verification Commands (post-implementation)

```bash
rg -n "METHODS_REFERENCE|CONFIG_REFERENCE|REPRODUCIBILITY" planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md README.md docs
```

---

## 6) Cross-Reference Matrix (Finding -> Planned Closure Evidence)

| Finding ID | Planned Closure Evidence |
|---|---|
| `RI-10` | Release gate scripts fail when sensitivity robustness is outside accepted policy state; contract tests pass. |
| `RI-11` | Strict computed indistinguishability path either passes with required data or is explicitly blocked and excluded by policy. |
| `RI-12` | Release invocation path enforces strict mode (default or mandatory flag) with tests. |
| `MC-3` | Prior 0%-coverage modules gain tests or documented exemptions; CI thresholds updated accordingly. |
| `MC-2R` | Orphaned run policy finalized and reconciliation tooling/tests show deterministic state. |
| `ST-1` | Legacy verify artifacts are cleaned/tagged per policy; no ambiguous active status artifacts in release core_audit path. |
| `INV-1` | Dirty-release override becomes policy-controlled with traceable rationale. |
| `DOC-4` | Playbook/document paths aligned or formally mapped via compatibility layer. |

---

## 7) Final Verification Gate (Post-Execution)

Remediation is complete only if all checks pass:

1. `bash scripts/core_audit/pre_release_check.sh` enforces updated sensitivity robustness policy.
2. `bash scripts/verify_reproduction.sh` enforces same policy consistently.
3. `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py` is either passing or formally blocked per documented release policy.
4. Coverage run shows improvement against current 0%-module baseline and meets updated gates.
5. Reconciliation scripts/tests confirm stable orphaned/legacy artifact handling.
6. Documentation links and output contracts are path-consistent for external reviewers.

Post-execution deliverables:

- `reports/core_audit/FIX_EXECUTION_STATUS_8.md`
- `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_9.md` (next assessment-only pass)

---

## 8) Change-Control Notes

- Keep WS-A and WS-B as separate review PRs; they affect release-evidence semantics and should be independently auditable.
- For each finding closure, capture:
  - modified files,
  - validation command output summary,
  - explicit mapping to finding IDs.
- If WS-B remains data-blocked, that state must be treated as a release blocker unless policy explicitly re-scopes release claims.
