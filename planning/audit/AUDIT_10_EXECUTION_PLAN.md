# Execution Plan: Audit 10 Remediation

**Source Audit:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_10.md`  
**Requested Source:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_100.md` (not found in workspace)  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work and verification criteria; it does not execute changes.

---

## 1) Objective

Close all unresolved Audit 10 findings and move the project to a release-candidate state with explicit, auditable policy boundaries.

Primary objectives:

1. Resolve the remaining **High** blocker (`RI-13`) by producing conclusive release evidence or explicitly preserving fail-closed non-release posture.
2. Reduce unresolved **Medium** risk across strict execution policy, coverage confidence, provenance disposition, and release hygiene.
3. Preserve all previously resolved controls (`RI-10`, split-folio normalization, RI-11 documentation codification).

Success condition for Audit 11:

- `RI-13` closed.
- No open Medium finding without a documented disposition decision and objective evidence.
- Full release verification path behavior is deterministic and policy-consistent.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Severity | Planned Workstream |
|---|---|---|---|
| Sensitivity evidence non-ready/inconclusive | `RI-13` | High | WS-A |
| Strict/non-strict release-path posture | `RI-12` | Medium | WS-B |
| Data-availability boundary governance for strict preflight | `RI-11` | Medium | WS-C |
| Low-confidence module coverage | `MC-3` | Medium | WS-D |
| Historical orphaned-run provenance uncertainty | `MC-2R` | Medium | WS-E |
| Dirty release baseline / change-control hygiene | `INV-1` | Medium | WS-F |
| Integrated release verification and closure evidence | n/a | n/a | WS-G |

Monitor-only in this pass (already resolved; protect from regression):

- `RI-10` fail-closed gate semantics.
- Split-folio preflight normalization (`RI-14`/`ST-3`).
- RI-11 policy documentation codification (`DOC-5`).

---

## 3) Execution Status Tracker

Update during implementation; keep this table current in the execution pass.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Sensitivity Release Evidence Closure | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Canonical release sweep now produces `release_evidence_ready=true` with conclusive robustness (`PASS`). |
| WS-B Strict-Mode Release Enforcement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Indistinguishability runner now strict-by-default; exploratory fallback requires explicit `--allow-fallback`. |
| WS-C RI-11 Data-Availability Governance | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Playbook/provenance documentation codifies `DATA_AVAILABILITY` scope-constraint handling. |
| WS-D Coverage Confidence Uplift | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added targeted `feature_discovery` tests; module coverage increased to `40%` (from `12.85%`). |
| WS-E Orphaned-Run Provenance Disposition | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added manifest-backfill workflow; missing run manifests reduced to `0` in current workspace state. |
| WS-F Release Baseline Hygiene | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Dirty-release override now requires structured rationale (`:` + minimum length); clean-tree requirement remains enforced. |
| WS-G Final Verification + Audit Closure Evidence | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | `verify_reproduction.sh` and `ci_check.sh` pass; pre-release gate passes with compliant dirty override. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Sequencing and Dependencies

Recommended order:

1. WS-A
2. WS-B
3. WS-C
4. WS-D
5. WS-E
6. WS-F
7. WS-G

Dependency notes:

- WS-A is the release blocker and must be resolved before final release-readiness claims.
- WS-B should finish before WS-G so verifier behavior cannot silently rely on non-strict mode.
- WS-C should finalize before WS-G so RI-11 policy language in docs and artifacts is consistent.
- WS-E and WS-F must complete before final publication freeze and signoff.

---

## 5) Detailed Workstreams

## WS-A: Sensitivity Release Evidence Closure

**Addresses:** `RI-13`  
**Priority:** High  
**Goal:** Produce conclusive sensitivity evidence that satisfies release gates (`release_evidence_ready=true`, quality gate pass, conclusive robustness).

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Build root-cause matrix for `INCONCLUSIVE` result path (`valid_scenarios=0`, collapse behavior, warning flood). | `scripts/analysis/run_sensitivity_sweep.py`, `reports/audit/SENSITIVITY_RESULTS.md`, `status/audit/sensitivity_sweep.json` | Matrix identifies code/config/data causes with reproducible evidence. |
| A2 | Implement deterministic remediation for failure mode(s): scenario validity logic, warning handling, gating thresholds, or dataset assumptions (as applicable). | `scripts/analysis/run_sensitivity_sweep.py`, dependent modules in `src/analysis/*` | Canonical release sweep can produce non-empty valid scenario set under policy-compliant settings. |
| A3 | Regenerate canonical release artifact and align report output. | `status/audit/sensitivity_sweep.json`, `reports/audit/SENSITIVITY_RESULTS.md` | Artifact fields internally consistent and reflect remediated state. |
| A4 | Keep fail-closed protections intact and add/extend contract tests. | `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, `tests/audit/*` | Gates fail on non-ready state and pass only on truly compliant evidence. |
| A5 | Update sensitivity methodology documentation to match enforced behavior. | `docs/SENSITIVITY_ANALYSIS.md`, `docs/REPRODUCIBILITY.md` | Docs match script behavior with no ambiguity. |

### Planned Verification

```bash
python3 scripts/analysis/run_sensitivity_sweep.py --dataset-id voynich_real --mode release
bash scripts/audit/pre_release_check.sh
bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/audit/test_pre_release_contract.py tests/audit/test_verify_reproduction_contract.py
```

### Completion Evidence

- `status/audit/sensitivity_sweep.json` shows:
  - `release_evidence_ready=true`
  - `robustness_conclusive=true`
  - `quality_gate_passed=true`
- `scripts/audit/pre_release_check.sh` and `scripts/verify_reproduction.sh` both pass.

---

## WS-B: Strict-Mode Release Enforcement

**Addresses:** `RI-12`  
**Priority:** Medium  
**Goal:** Ensure release pathways cannot silently succeed on non-strict indistinguishability behavior.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Define definitive policy: strict required for release paths; non-strict allowed only for exploratory use. | `docs/REPRODUCIBILITY.md`, `docs/PROVENANCE.md` | Single, explicit policy statement present and cross-referenced. |
| B2 | Enforce policy in verifier and release checks (hard fail if strict evidence absent/mismatched). | `scripts/verify_reproduction.sh`, `scripts/audit/pre_release_check.sh` | Release verification cannot complete on non-strict artifacts. |
| B3 | Harden CLI/help signaling for strict requirement in release context. | `scripts/synthesis/run_indistinguishability_test.py` | Help text and errors clearly separate exploratory vs release mode. |
| B4 | Add regression tests around strict policy enforcement and artifact semantics. | `tests/audit/*`, `tests/synthesis/test_run_indistinguishability_runner.py` | Tests detect strict-policy regressions automatically. |

### Planned Verification

```bash
python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/audit/test_verify_reproduction_contract.py tests/synthesis/test_run_indistinguishability_runner.py
```

### Completion Evidence

- Strict-required release checks are enforced in scripts and tested.
- Non-strict execution is visibly marked non-release-evidentiary.

---

## WS-C: RI-11 Data-Availability Governance

**Addresses:** `RI-11`  
**Priority:** Medium  
**Goal:** Keep RI-11 criteria update operationally consistent across scripts, artifacts, and docs.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Confirm and document canonical policy wording for unavailable/lost source pages. | `docs/REPRODUCIBILITY.md`, `docs/PROVENANCE.md` | Policy text is consistent, non-contradictory, and release-facing. |
| C2 | Ensure strict blocked artifacts always emit required structure (`status=BLOCKED`, `reason_code=DATA_AVAILABILITY`, missing-page details). | `scripts/synthesis/run_indistinguishability_test.py` | Artifact contract is stable and machine-checkable. |
| C3 | Add/extend tests for blocked-state semantics under missing-page scenarios. | `tests/synthesis/test_run_indistinguishability_runner.py`, `tests/audit/*` | Missing-page conditions yield expected reason code and metadata. |
| C4 | Add checklist language so future audits classify this scenario consistently. | `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md` or audit template files | Severity/interpretation drift eliminated in future passes. |

### Planned Verification

```bash
REQUIRE_COMPUTED=1 python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
rg -n "DATA_AVAILABILITY|BLOCKED|lost|unavailable" docs planning/audit reports/audit
python3 -m pytest -q tests/synthesis/test_run_indistinguishability_runner.py
```

### Completion Evidence

- Strict blocked artifacts are structurally consistent.
- Documentation and audit criteria reflect the same governance rule.

---

## WS-D: Coverage Confidence Uplift

**Addresses:** `MC-3`  
**Priority:** Medium  
**Goal:** Raise confidence in under-tested critical synthesis logic, especially `src/synthesis/refinement/feature_discovery.py`.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Identify high-impact untested branches in `feature_discovery.py` and adjacent refinement modules. | `src/synthesis/refinement/feature_discovery.py`, `src/synthesis/refinement/*` | Prioritized branch list created with test targets. |
| D2 | Add focused unit tests for deterministic behavior, edge handling, and exception paths. | `tests/synthesis/refinement/*` | Module coverage materially improved and behavior assertions explicit. |
| D3 | Evaluate and set pragmatic minimum per-module threshold for critical refinement modules. | `scripts/ci_check.sh`, coverage contract tests | CI alerts on regression below agreed threshold. |
| D4 | Publish before/after coverage delta in execution status report. | `reports/audit/FIX_EXECUTION_STATUS_10.md` (future execution pass) | Delta is explicit and reproducible. |

### Planned Verification

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
python3 -m coverage report -m | rg "feature_discovery|TOTAL"
```

### Completion Evidence

- `feature_discovery.py` coverage is no longer below agreed confidence floor.
- Overall coverage remains above release threshold without regressions.

---

## WS-E: Orphaned-Run Provenance Disposition

**Addresses:** `MC-2R`  
**Priority:** Medium  
**Goal:** Convert orphaned-run ambiguity into a final, documented disposition policy with reproducible tooling behavior.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Decide final disposition strategy for historical `orphaned` rows (retain+annotate vs archival migration). | `docs/PROVENANCE.md`, `AUDIT_LOG.md` | Decision documented with rationale and scope. |
| E2 | Align reconciliation script/reporting with chosen strategy and idempotence guarantees. | `scripts/audit/repair_run_statuses.py`, `status/audit/run_status_repair_report.json` | Repeated runs produce stable, policy-compliant outputs. |
| E3 | Add regression tests for chosen disposition behavior. | `tests/audit/test_repair_run_statuses.py` | Future drift is caught by tests. |
| E4 | Update audit reporting template language for orphaned-state interpretation. | `reports/audit/COMPREHENSIVE_AUDIT_REPORT_*.md` templates/process docs | Future audits report orphaned state consistently. |

### Planned Verification

```bash
python3 scripts/audit/repair_run_statuses.py
python3 -m pytest -q tests/audit/test_repair_run_statuses.py
sqlite3 -header -column data/voynich.db "SELECT status, COUNT(*) FROM runs GROUP BY status;"
```

### Completion Evidence

- Orphaned-run policy is explicit and repeatable.
- Repair tooling and tests enforce that policy.

---

## WS-F: Release Baseline Hygiene

**Addresses:** `INV-1`  
**Priority:** Medium  
**Goal:** Ensure dirty-tree override usage is intentional, constrained, and documented for release-path integrity.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Define strict criteria for `ALLOW_DIRTY_RELEASE` usage (allowed contexts, required rationale format). | `docs/REPRODUCIBILITY.md`, `AUDIT_LOG.md` | Override policy is explicit and enforceable. |
| F2 | Improve script-level validation and operator guidance for dirty-release overrides. | `scripts/audit/pre_release_check.sh` | Invalid or missing rationale is hard-failed with actionable guidance. |
| F3 | Add contract tests for clean-tree, dirty-tree, and override behaviors. | `tests/audit/test_pre_release_contract.py` | Release-hygiene behavior is regression-protected. |
| F4 | Add signoff checklist item requiring explicit diff acknowledgment at release cut. | release checklist docs, `docs/REPRODUCIBILITY.md` | Final release checklist includes diff-state acknowledgment. |

### Planned Verification

```bash
bash scripts/audit/pre_release_check.sh
ALLOW_DIRTY_RELEASE=1 DIRTY_RELEASE_REASON='ticket: AUDIT-10 hygiene exception' bash scripts/audit/pre_release_check.sh
python3 -m pytest -q tests/audit/test_pre_release_contract.py
```

### Completion Evidence

- Dirty overrides are policy-bounded and test-covered.
- Release cut process has explicit change-state acknowledgment.

---

## WS-G: Final Verification and Audit Closure Evidence

**Addresses:** Integrated closure  
**Priority:** Required end-state  
**Goal:** Re-run full verification and publish an execution report demonstrating closure status of all open Audit 10 findings.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| G1 | Run full verification stack after WS-A..WS-F completion. | runtime outputs + `status/*` artifacts | All expected pass/fail states match policy. |
| G2 | Produce detailed implementation status report with per-finding closure evidence. | `reports/audit/FIX_EXECUTION_STATUS_10.md` | Every finding has status, evidence, and residual-risk note. |
| G3 | Re-run comprehensive audit (next pass) and compare deltas against Audit 10 baseline. | `reports/audit/COMPREHENSIVE_AUDIT_REPORT_11.md` (future) | Closure claims independently validated. |

### Planned Verification

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
bash scripts/audit/pre_release_check.sh
```

### Completion Evidence

- `FIX_EXECUTION_STATUS_10.md` contains full closure map and command evidence.
- Next audit pass confirms reduced finding count and severity.

---

## 6) Risk Register and Contingencies

| Risk | Impact | Mitigation |
|---|---|---|
| Sensitivity sweep remains structurally inconclusive after code fixes | High | Add explicit policy gate for non-release mode and document unresolved scope; do not claim release readiness. |
| Strict policy changes break exploratory workflows | Medium | Keep exploratory mode available, but non-evidentiary and clearly labeled. |
| Coverage gains require extensive fixture scaffolding | Medium | Prioritize highest-impact paths first; set staged thresholds with documented rationale. |
| Orphaned-run policy decision requires stakeholder input | Medium | Document interim policy and mark as required signoff gate before release freeze. |

---

## 7) Definition of Done (Audit 10 Execution)

Audit 10 remediation execution is complete when:

1. `RI-13` is closed with objective release-evidence fields set to ready/conclusive/pass.
2. `RI-12`, `RI-11`, `MC-3`, `MC-2R`, and `INV-1` are each closed or explicitly policy-accepted with documented evidence.
3. Full verification commands complete with expected outcomes and no ambiguous gate behavior.
4. `reports/audit/FIX_EXECUTION_STATUS_10.md` is published with traceable evidence links to scripts/artifacts/tests.

---

## 8) Planned Deliverables (Next Execution Pass)

1. `reports/audit/FIX_EXECUTION_STATUS_10.md` (full remediation log and evidence).
2. Updated scripts/tests/docs per workstream outcomes.
3. Fresh verification artifacts (`status/audit/sensitivity_sweep.json`, CI coverage output, strict preflight artifacts).
4. Follow-up assessment report (`reports/audit/COMPREHENSIVE_AUDIT_REPORT_11.md`).
