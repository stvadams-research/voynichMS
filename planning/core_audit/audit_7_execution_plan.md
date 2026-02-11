# Execution Plan: Audit 7 Remediation

**Source Audit:** `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_7.md`  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work but does not execute it.

---

## 1) Objective

Close all open findings from Audit 7 with immediate emphasis on:

1. Restoring trust in release verification gates (no false-positive pass states).
2. Producing release-grade sensitivity evidence from canonical full-sweep execution.
3. Hardening the indistinguishability release path to computed-only behavior.
4. Resolving historical run-state ambiguity and tightening release hygiene.

Success condition for next pass:

- No open **Critical** findings.
- No unresolved **High** findings that undermine reproducibility claims.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Verification gate false-positive pass behavior | `MC-6`, `DOC-3` | WS-A |
| Sensitivity evidence completeness (canonical but bounded/inconclusive release posture) | `RI-9` | WS-B |
| Indistinguishability release-path fallback dependence and runtime reliability | `RI-8`, `RI-6` | WS-C |
| Historical run metadata ambiguity and mixed status artifact semantics | `MC-2`, `ST-1` | WS-D |
| Coverage confidence and verification depth hardening | `MC-3`, `MC-5` | WS-E |
| Release-baseline cleanliness and transient artifact lifecycle | `INV-1`, `INV-3` | WS-F |

Resolved/improved findings (track only for non-regression):

- `RI-1`, `RI-2`, `RI-3`, `INV-2`, `DOC-2`, `ST-2`, partial `MC-1`

---

## 3) Execution Status Tracker

Update this table during implementation.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Verification Gate Integrity | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Verifier/CI false-pass condition closed; sentinel + exit semantics enforced. |
| WS-B Sensitivity Release Evidence Completion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Full release-mode sweep executed (17/17) with release metadata in artifacts. |
| WS-C Indistinguishability Release Path Hardening | BLOCKED | Codex | 2026-02-10 |  | Code-level strict preflight/fallback guard shipped; strict run blocked by missing real pharmaceutical page records. |
| WS-D Run Metadata and Provenance Reconciliation | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Historical stale runs classified as `orphaned`; reconciliation report emitted. |
| WS-E Coverage and Verification Depth Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | CI default coverage floor raised to 50%; critical-module enforcement non-optional; new contract tests added. |
| WS-F Baseline Hygiene and Artifact Lifecycle | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Pre-release check script and support_cleanup dry-run summary implemented/documented. |
| Final Verification and Re-Audit | IN PROGRESS | Codex | 2026-02-10 |  | All gates pass except strict indistinguishability execution, which is data-blocked. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Recommended Execution Order and Dependencies

Execute in this order:

1. WS-A (critical trust gate)
2. WS-B (release evidence integrity)
3. WS-C (release-path computational validity)
4. WS-D (historical metadata/provenance consistency)
5. WS-E (coverage and verifier depth confidence)
6. WS-F (release baseline and artifact hygiene)
7. Final Verification and Re-Audit

Dependency notes:

- WS-A must complete first; all downstream pass/fail evidence is suspect until verifier exit semantics are fixed.
- WS-B and WS-C should complete before final documentation lock to avoid narrative drift.
- WS-D should finalize before the next core_audit snapshot so stale historical statuses are not re-reported.
- WS-E threshold tightening should occur after WS-A through WS-C stabilize to avoid noisy breakages.

---

## 5) Workstream Details

## WS-A: Verification Gate Integrity

**Addresses:** `MC-6`, `DOC-3`  
**Priority:** Critical  
**Objective:** Ensure verification scripts fail with non-zero exit codes when any required check fails, and ensure CI cannot report success on verifier abort.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Remove unbound variable failure mode for `VIRTUAL_ENV` under `set -u` (safe default expansion). | `scripts/verify_reproduction.sh` | Default invocation behaves deterministically with/without active venv and does not abort at environment check. |
| A2 | Add explicit verifier failure trap and final pass sentinel check to guarantee non-zero exit on any failed prerequisite/step. | `scripts/verify_reproduction.sh` | Script exits non-zero whenever a required check fails; success path always includes explicit completion marker. |
| A3 | Harden `ci_check.sh` to treat verifier completion marker as mandatory (not just subprocess return code). | `scripts/ci_check.sh` | CI cannot print `PASSED` unless verifier reached full completion marker. |
| A4 | Add regression tests for verifier and CI failure semantics (including environment-variable edge cases). | `tests/core_audit/test_verify_reproduction_contract.py`, optional new CI contract tests | Tests fail if false-positive pass behavior reappears. |
| A5 | Update reproducibility docs to specify expected verifier exit semantics and error behavior. | `governance/governance/REPRODUCIBILITY.md` | Documentation matches actual gate behavior with concrete pass/fail expectations. |

### Verification Commands

```bash
env -u VIRTUAL_ENV bash scripts/verify_reproduction.sh
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
python3 -m pytest -q tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-B: Sensitivity Release Evidence Completion

**Addresses:** `RI-9`  
**Priority:** High  
**Objective:** Produce release-grade sensitivity evidence via full canonical sweep execution and align reports/docs to that run.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Define explicit sweep modes (`smoke` vs `release`) or equivalent guardrail so bounded runs cannot be mistaken for release evidence. | `scripts/phase2_analysis/run_sensitivity_sweep.py` | Release evidence path requires full scenario execution; bounded mode is clearly labeled non-release. |
| B2 | Run canonical full sweep for release dataset profile and regenerate machine/phase7_human artifacts. | `core_status/core_audit/sensitivity_sweep.json`, `reports/core_audit/SENSITIVITY_RESULTS.md` | Artifacts reflect full-sweep execution metadata (scenario count and dataset profile consistent with release mode). |
| B3 | Encode release-evidence metadata in output summary (mode, scenario_count_expected vs executed). | `scripts/phase2_analysis/run_sensitivity_sweep.py`, artifacts | Consumers can detect whether artifact is release-grade without manual phase4_inference. |
| B4 | Update sensitivity documentation to reference latest full-sweep evidence and caveats verbatim. | `governance/SENSITIVITY_ANALYSIS.md` | Documentation and artifacts remain claim-consistent. |
| B5 | Add end-to-end contract test that fails when release report/status are generated from bounded runs. | `tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py`, `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py` | Regression test enforces release evidence completeness policy. |

### Verification Commands

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py
python3 - <<'PY'
import json
p=json.load(open('core_status/core_audit/sensitivity_sweep.json'))
s=p['results']['summary']
print(s['dataset_id'], s['total_scenarios'], s['robustness_decision'])
PY
rg -n "unknown_legacy|sensitivity_sweep_legacy_reconcile|max-scenarios 1" core_status/core_audit/sensitivity_sweep.json reports/core_audit/SENSITIVITY_RESULTS.md governance/SENSITIVITY_ANALYSIS.md
python3 -m pytest -q tests/phase2_analysis/test_sensitivity_sweep_end_to_end.py tests/phase2_analysis/test_sensitivity_sweep_guardrails.py
```

---

## WS-C: Indistinguishability Release Path Hardening

**Addresses:** `RI-8`, `RI-6`  
**Priority:** High  
**Objective:** Ensure `run_indistinguishability_test.py` is release-safe: computed metrics only, fallback-aware policy, and operationally reliable runtime completion.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Add explicit release-mode switch (or enforce `REQUIRE_COMPUTED=1`) for indistinguishability execution path. | `scripts/phase3_synthesis/run_indistinguishability_test.py`, `src/phase3_synthesis/profile_extractor.py` | Release mode fails on simulated/fallback profile use. |
| C2 | Add preflight dataset completeness checks for required pharmaceutical pages and required transcription/glyph prerequisites. | `scripts/phase3_synthesis/run_indistinguishability_test.py`, optionally helper in `src/phase3_synthesis/profile_extractor.py` | Script fails early with actionable missing-data diagnostics instead of deep fallback. |
| C3 | Instrument runtime phases and add explicit timeout/error messaging guidance for long-running segments. | `scripts/phase3_synthesis/run_indistinguishability_test.py`, docs | Runtime status is observable; hangs can be diagnosed quickly. |
| C4 | Add regression tests for strict computed mode and missing-data fail-fast behavior. | `tests/phase3_synthesis/test_run_indistinguishability_runner.py`, optional new tests | Test suite catches fallback leakage in release path. |
| C5 | Update reproducibility docs to classify this runner as release-evidentiary only under strict computed mode. | `governance/governance/REPRODUCIBILITY.md`, optional `governance/SENSITIVITY_ANALYSIS.md` references | External readers can distinguish exploratory vs release invocation paths. |

### Verification Commands

```bash
REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 -m pytest -q tests/phase3_synthesis/test_run_indistinguishability_runner.py
rg -n "fallback to simulated|Using fallback value" /tmp/indistinguishability*.log
```

---

## WS-D: Run Metadata and Provenance Reconciliation

**Addresses:** `MC-2`, `ST-1`  
**Priority:** High  
**Objective:** Resolve stale historical `runs` records lacking manifests and align provenance interpretation policy across old/new artifacts.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Define policy for stale `runs` rows with missing manifests (e.g., `orphaned`, archived, or purged with core_audit trail). | `governance/PROVENANCE.md`, `AUDIT_LOG.md` | Clear, documented policy exists for irreparable historical rows. |
| D2 | Extend repair utility to handle missing-manifest rows according to policy and produce a reconciliation report artifact. | `scripts/core_audit/repair_run_statuses.py` | Utility reports scanned/repaired/orphaned counts deterministically. |
| D3 | Add DB-level tests for missing-manifest handling and idempotent re-run behavior. | `tests/core_audit/test_repair_run_statuses.py` | Tests enforce no silent partial remediation. |
| D4 | Optionally add one-time migration/archival command for historical stale `core_status/by_run` verify artifacts or annotate them as legacy. | `scripts/core_audit/cleanup_status_artifacts.sh`, `governance/PROVENANCE.md` | Legacy artifact handling is explicit and reproducible. |
| D5 | Ensure recent run persistence remains correct for active scripts (`status` final, `timestamp_end` non-null). | `tests/phase1_foundation/storage/test_metadata_run_persistence.py`, scripts using `store.save_run(run)` | No new stale rows are generated in normal execution. |

### Verification Commands

```bash
python3 scripts/core_audit/repair_run_statuses.py
python3 - <<'PY'
import sqlite3
con=sqlite3.connect('data/voynich.db')
cur=con.cursor()
cur.execute("select count(*) from runs where status='running' and timestamp_end is null")
print(cur.fetchone()[0])
con.close()
PY
python3 -m pytest -q tests/core_audit/test_repair_run_statuses.py tests/phase1_foundation/storage/test_metadata_run_persistence.py
```

---

## WS-E: Coverage and Verification Depth Hardening

**Addresses:** `MC-3`, `MC-5`  
**Priority:** Medium  
**Objective:** Reduce residual blind spots and improve reliability of quality gates beyond aggregate coverage.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Add targeted tests for currently 0% modules or explicitly reclassify non-critical modules outside release gate scope. | `tests/phase1_foundation/`, `tests/phase2_analysis/`, possible coverage config | 0% module list is reduced or intentionally excluded with documented rationale. |
| E2 | Tighten default CI stage to reflect current achieved baseline (>=50%) after tests land. | `scripts/ci_check.sh` | Default coverage stage aligns with current realistic minimum and fails below target. |
| E3 | Make critical-module coverage enforcement non-optional for release/CI mode. | `scripts/ci_check.sh` | CI fails when critical-module coverage floor is violated. |
| E4 | Expand verifier checks to include at least one additional representative phase output equality/integrity check beyond current spot checks. | `scripts/verify_reproduction.sh`, related tests | Verifier covers phase3_synthesis + phase2_analysis + sensitivity with explicit integrity assertions. |
| E5 | Add regression tests covering CI threshold and enforcement behavior. | `tests/core_audit/` | Gate policy drift is caught automatically. |

### Verification Commands

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
python3 -m pytest -q tests/core_audit
```

---

## WS-F: Baseline Hygiene and Artifact Lifecycle

**Addresses:** `INV-1`, `INV-3`  
**Priority:** Medium  
**Objective:** Enforce release-baseline cleanliness and clarify lifecycle boundaries for transient artifacts.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Add pre-release checklist gate/script that verifies intentional diff scope before signoff. | `governance/governance/REPRODUCIBILITY.md`, optional new `scripts/core_audit/pre_release_check.sh` | Release process includes explicit clean/intended diff confirmation step. |
| F2 | Define retention window and support_cleanup procedure for `core_status/by_run` transient verification outputs. | `governance/PROVENANCE.md`, `governance/governance/REPRODUCIBILITY.md`, support_cleanup script | Teams can consistently clean/retain artifacts with policy traceability. |
| F3 | Ensure support_cleanup utility supports dry-run reporting + deterministic support_cleanup summary for core_audit logs. | `scripts/core_audit/cleanup_status_artifacts.sh` | Cleanup operations are reviewable and repeatable. |
| F4 | Record closure decisions and artifact policy updates in `AUDIT_LOG.md`. | `AUDIT_LOG.md` | Audit trail includes rationale and closure evidence references. |

### Verification Commands

```bash
git status --short
bash scripts/core_audit/cleanup_status_artifacts.sh list
bash scripts/core_audit/cleanup_status_artifacts.sh clean
rg --files -g 'AUDIT_LOG.md'
```

---

## 6) Cross-Reference Matrix (Finding -> Planned Closure)

| Finding ID | Planned Closure Evidence |
|---|---|
| `MC-6` | Verifier/CI scripts fail non-zero on failed checks; no false-positive pass logs. |
| `DOC-3` | Reproducibility docs updated to reflect reliable gate semantics and expected failures. |
| `RI-9` | Full canonical sensitivity sweep artifacts produced and tagged as release-grade evidence. |
| `RI-8` | Indistinguishability release path enforces computed-only/strict behavior and reliable completion diagnostics. |
| `RI-6` | Fallback policy clearly separated by mode with strict release enforcement. |
| `MC-2` | Historical stale run rows reconciled or policy-classified (including missing-manifest cases). |
| `ST-1` | Legacy/current artifact semantics documented and operationally managed. |
| `MC-3` | Coverage policy tightened with reduced high-risk blind spots. |
| `MC-5` | Reproduction verification breadth expanded and contract-tested. |
| `INV-1` | Release checklist includes intentional-diff requirement. |
| `INV-3` | Transient status artifact lifecycle and support_cleanup policy enforced. |

---

## 7) Final Verification Gate (Post-Execution)

Remediation is complete only if all checks pass:

1. `env -u VIRTUAL_ENV bash scripts/verify_reproduction.sh` completes successfully.
2. `bash scripts/verify_reproduction.sh` fails non-zero on injected failure conditions and succeeds on healthy path.
3. `bash scripts/ci_check.sh` cannot report `PASSED` if verifier aborts.
4. `python3 scripts/phase2_analysis/run_sensitivity_sweep.py` generates full release-mode canonical artifacts.
5. `REQUIRE_COMPUTED=1 python3 scripts/phase3_synthesis/run_indistinguishability_test.py` completes without simulated/fallback metrics.
6. Historical run-state reconciliation script leaves no ambiguous unresolved rows without policy classification.
7. `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests` and targeted core_audit tests pass under tightened gate settings.

Post-execution deliverables:

- `reports/core_audit/FIX_EXECUTION_STATUS_7.md`
- `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_8.md` (next assessment-only rerun)

---

## 8) Change-Control Notes

- Prioritize WS-A first; no release claims should rely on current verifier semantics.
- Keep sensitivity and indistinguishability remediations separate for review clarity.
- For each closed finding, capture:
  - changed files,
  - verification command outputs,
  - explicit finding-ID closure statements.
- Treat unresolved high findings as release blockers until evidenced closed in `FIX_EXECUTION_STATUS_7.md`.
