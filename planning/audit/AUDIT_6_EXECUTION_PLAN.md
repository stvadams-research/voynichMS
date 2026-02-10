# Execution Plan: Audit 6 Remediation

**Source Audit:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_6.md`  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work but does not execute it.

---

## 1) Objective

Close all open findings from Audit 6 with priority on:

1. Removing hardcoded/estimated values from release-critical execution paths.
2. Replacing legacy-reconciled sensitivity artifacts with canonical runner output.
3. Correcting provenance/run-lifecycle status integrity.
4. Hardening reproducibility verification, CI confidence, and release hygiene.

Success condition for next pass:

- No open **Critical** findings.
- No unresolved **High** findings that block public methodological release.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Critical method integrity in indistinguishability runner | `RI-1`, `ST-2` | WS-A |
| Sensitivity canonicalization and claim alignment | `RI-2`, `RI-3`, `RI-4`, `DOC-1`, `ST-1` | WS-B |
| Provenance and run-lifecycle correctness | `MC-1`, `MC-2` | WS-C |
| Reproducibility harness depth and DB isolation | `RI-5`, `MC-5` | WS-D |
| Coverage credibility and test assurance | `MC-3`, `MC-4` | WS-E |
| Fallback policy and strict computed-mode enforcement | `RI-6` | WS-F |
| Audit/release hygiene and output contract completeness | `INV-1`, `INV-2`, `INV-3`, `DOC-2`, `RI-7` | WS-G |

---

## 3) Execution Status Tracker

Update this table during implementation.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Indistinguishability Method Integrity | NOT STARTED | TBD |  |  |  |
| WS-B Sensitivity Canonicalization and Claims | NOT STARTED | TBD |  |  |  |
| WS-C Provenance and Run Lifecycle Correctness | NOT STARTED | TBD |  |  |  |
| WS-D Reproducibility Harness Hardening | NOT STARTED | TBD |  |  |  |
| WS-E Coverage and Test Hardening | NOT STARTED | TBD |  |  |  |
| WS-F Fallback/Strict-Mode Policy | NOT STARTED | TBD |  |  |  |
| WS-G Hygiene and Audit Artifacts | NOT STARTED | TBD |  |  |  |
| Final Verification and Re-Audit | NOT STARTED | TBD |  |  |  |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Recommended Execution Order and Dependencies

Execute in this order:

1. WS-A (critical result validity)
2. WS-B (sensitivity evidence validity and documentation truth alignment)
3. WS-C (provenance/run-state integrity)
4. WS-D (verification harness quality and isolation)
5. WS-E (coverage/test confidence)
6. WS-F (strict computed policy finalization)
7. WS-G (hygiene and required audit artifacts)
8. Final Verification and Re-Audit

Dependency notes:

- WS-B should run after WS-A so no release narrative references a compromised core synthesis path.
- WS-D should follow WS-C so verification checks assert final, corrected run/provenance semantics.
- WS-E thresholds should be tightened only after WS-A/WS-B/WS-C stabilize to avoid churn.

---

## 5) Workstream Details

## WS-A: Indistinguishability Method Integrity

**Addresses:** `RI-1`, `ST-2`  
**Priority:** Critical  
**Objective:** Remove hardcoded/estimated metrics from `run_indistinguishability_test.py` and ensure reported conclusions are computed from live pipeline outputs.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Replace commented-out metric execution path with active computed path for information and locality tests. | `scripts/synthesis/run_indistinguishability_test.py` | No key decision metric is hardcoded/estimated. |
| A2 | Remove hardcoded constants (`real_z`, `syn_z`, `real_rad`, `syn_rad`) from pass/fail logic. | `scripts/synthesis/run_indistinguishability_test.py` | Decision derives entirely from measured outputs. |
| A3 | Enforce fail-fast behavior if required upstream artifacts/datasets are missing instead of silently substituting constants. | `scripts/synthesis/run_indistinguishability_test.py` | Script fails with actionable error when prerequisites are absent. |
| A4 | Correct stale human-facing script output text (page-count mismatch and similar drift). | `scripts/synthesis/run_indistinguishability_test.py` | Console/report text reflects actual runtime behavior. |
| A5 | Add regression test to prevent future reintroduction of hardcoded decision metrics in this runner. | `tests/synthesis/` or `tests/audit/` | Test fails if hardcoded path returns. |

### Verification Commands (during execution)

```bash
python3 scripts/synthesis/run_indistinguishability_test.py
rg -n "From final report|Estimated|real_z|syn_z|real_rad|syn_rad" scripts/synthesis/run_indistinguishability_test.py
python3 -m pytest -q tests/synthesis tests/audit
```

---

## WS-B: Sensitivity Canonicalization and Claims

**Addresses:** `RI-2`, `RI-3`, `RI-4`, `DOC-1`, `ST-1`  
**Priority:** Critical  
**Objective:** Replace legacy-reconciled sensitivity outputs with canonical runner-generated artifacts and align docs to actual evidence.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Run sensitivity from canonical runner path and retire legacy reconciliation as release evidence source. | `scripts/analysis/run_sensitivity_sweep.py`, `status/audit/sensitivity_sweep.json`, `reports/audit/SENSITIVITY_RESULTS.md` | Published sensitivity artifacts are generated by canonical runner execution. |
| B2 | Enforce canonical dataset profile in generated report (`dataset_id`, `pages`, `tokens`) and reject `unknown_legacy` for release output. | `scripts/analysis/run_sensitivity_sweep.py` | Release report cannot show legacy placeholder dataset metadata. |
| B3 | Ensure provenance command metadata reflects canonical command (not reconciliation shim). | `scripts/analysis/run_sensitivity_sweep.py`, `status/audit/sensitivity_sweep.json` | Provenance `command` aligns with actual runner path. |
| B4 | Align `docs/SENSITIVITY_ANALYSIS.md` statements to exact measured results and caveats from latest canonical run. | `docs/SENSITIVITY_ANALYSIS.md` | No mismatch between documentation claims and report/status artifacts. |
| B5 | Add end-to-end regression check validating sensitivity report/status coherence (dataset, scenario counts, decision consistency). | `tests/analysis/` or `tests/audit/` | Tests fail when report/status drift out of sync. |

### Verification Commands

```bash
python3 scripts/analysis/run_sensitivity_sweep.py
python3 -c "import json; d=json.load(open('status/audit/sensitivity_sweep.json')); print(d['results']['summary']['dataset_id'])"
rg -n "unknown_legacy|sensitivity_sweep_legacy_reconcile" status/audit/sensitivity_sweep.json reports/audit/SENSITIVITY_RESULTS.md docs/SENSITIVITY_ANALYSIS.md
python3 -m pytest -q tests/analysis tests/audit
```

---

## WS-C: Provenance and Run Lifecycle Correctness

**Addresses:** `MC-1`, `MC-2`  
**Priority:** High  
**Objective:** Ensure persisted artifacts and DB run records represent final run status and end time accurately.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Refactor run persistence flow so run records are written after run completion (or updated post-completion). | `src/foundation/runs/manager.py`, `src/foundation/storage/metadata.py`, runner scripts as needed | Completed runs are stored with `status=success/failed` and non-null `timestamp_end`. |
| C2 | Eliminate or redesign save-before-complete pattern in scripts using `store.save_run(run)` inside active context. | `scripts/**/run_*.py` | No stale `running` status persisted for completed runs. |
| C3 | Clarify provenance status semantics in output artifacts (capture-time vs final-state), then enforce chosen policy consistently. | `src/foundation/core/provenance.py`, `docs/PROVENANCE.md` | Artifact status semantics are explicit and internally consistent. |
| C4 | Add regression tests validating final-status persistence in DB and provenance output behavior. | `tests/foundation/`, `tests/audit/` | Tests catch stale run-state regressions. |
| C5 | Backfill or repair existing stale run metadata for local release baseline (scripted migration/cleanup step). | utility script under `scripts/audit/` or `scripts/foundation/` | Historical run rows no longer misleadingly show `running` for completed runs (or are clearly archived). |

### Verification Commands

```bash
python3 scripts/synthesis/run_test_a.py --seed 12345 --output status/verify_run_state.json
python3 - <<'PY'
import sqlite3
con=sqlite3.connect('data/voynich.db')
cur=con.cursor()
cur.execute("select id,status,timestamp_end from runs order by timestamp_start desc limit 5")
print(cur.fetchall())
con.close()
PY
python3 -c "import json; d=json.load(open('status/verify_run_state.json')); print(d.get('provenance',{}).get('status'))"
python3 -m pytest -q tests/foundation tests/audit
```

---

## WS-D: Reproducibility Harness Hardening

**Addresses:** `RI-5`, `MC-5`  
**Priority:** High  
**Objective:** Expand verification breadth and prevent baseline mutation side effects during reproducibility checks.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Update `verify_reproduction.sh` to run against isolated verification DB (temporary copy or dedicated DB URL), not primary baseline DB. | `scripts/verify_reproduction.sh` | Verification run does not mutate `data/voynich.db` baseline state. |
| D2 | Add cleanup logic for verification artifacts and DBs to keep local state stable. | `scripts/verify_reproduction.sh` | Script is repeatable without accumulating side effects. |
| D3 | Extend verification beyond Test A: include at least one analysis output and one sensitivity artifact integrity check. | `scripts/verify_reproduction.sh` | Verification gate covers representative multi-phase outputs. |
| D4 | Add explicit strict-mode branch (`REQUIRE_COMPUTED=1`) for release-grade verification path. | `scripts/verify_reproduction.sh`, `docs/REPRODUCIBILITY.md` | Release verification mode fails on fallback use. |
| D5 | Add tests for verifier behavior (canonical compare, isolated DB usage, failure semantics). | `tests/audit/` | Reproducibility harness behavior is regression-protected. |

### Verification Commands

```bash
bash scripts/verify_reproduction.sh
git status --short
python3 -m pytest -q tests/audit
```

---

## WS-E: Coverage and Test Hardening

**Addresses:** `MC-3`, `MC-4`  
**Priority:** High  
**Objective:** Raise trust in CI coverage gate and add missing end-to-end confidence for key risk areas.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Add targeted tests for currently untested critical modules (`foundation.cli.main`, `analysis.admissibility.manager`, `foundation.core.queries`, plus other 0% critical files). | `tests/foundation/`, `tests/analysis/` | Critical module coverage no longer near-zero. |
| E2 | Add end-to-end tests for canonical sensitivity artifact generation and report consistency. | `tests/analysis/`, `tests/audit/` | Tests assert canonical dataset metadata and non-legacy command provenance. |
| E3 | Tighten CI staged coverage thresholds after new tests land (stage policy update). | `scripts/ci_check.sh` | Coverage gate trajectory is stricter than current 40% baseline. |
| E4 | Add visibility for critical-module coverage deltas (report or threshold policy) so aggregate percentage cannot hide key blind spots. | `scripts/ci_check.sh` and/or test tooling | CI output includes actionable critical coverage status. |

### Suggested Coverage Gate Progression

| Stage | Coverage Minimum |
|---|---:|
| Stage 1 (current) | 40% |
| Stage 2 | 45% |
| Stage 3 | 50% |
| Stage 4 | 55% |

### Verification Commands

```bash
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
bash scripts/ci_check.sh
```

---

## WS-F: Fallback and Strict-Mode Policy

**Addresses:** `RI-6`  
**Priority:** Medium  
**Objective:** Define and enforce where simulated fallback is acceptable vs prohibited in release evidence workflows.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Enumerate fallback defaults in synthesis/profile extraction paths and classify each as allowed (exploratory) or forbidden (release path). | `src/synthesis/profile_extractor.py`, related docs | Fallback behavior is explicit and policy-backed. |
| F2 | Enforce strict-computed mode for release workflows and core verification pipelines. | `scripts/verify_reproduction.sh`, `docs/REPRODUCIBILITY.md`, run scripts as needed | Release commands fail when fallback paths are hit. |
| F3 | Add tests ensuring strict mode blocks fallback values in critical metrics. | `tests/integration/`, `tests/synthesis/` | Strict-mode policy is automatically enforced. |

### Verification Commands

```bash
REQUIRE_COMPUTED=1 bash scripts/verify_reproduction.sh
python3 -m pytest -q tests/integration tests/synthesis
```

---

## WS-G: Hygiene and Audit Artifacts

**Addresses:** `INV-1`, `INV-2`, `INV-3`, `DOC-2`, `RI-7`  
**Priority:** Medium  
**Objective:** Complete playbook-required audit artifacts and reduce release/noise ambiguity.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| G1 | Create and adopt `AUDIT_LOG.md` as the running decisions/issues ledger required by playbook. | `AUDIT_LOG.md` (repo root or documented canonical path) | Playbook-required output exists and is actively used. |
| G2 | Define `status/by_run` retention policy (keep local-only, archive path, or cleanup tooling) and document it. | `docs/PROVENANCE.md`, `docs/REPRODUCIBILITY.md`, optional cleanup script | Artifact lifecycle is clear and reproducible. |
| G3 | Add optional cleanup utility for transient status artifacts to keep review worktrees manageable. | `scripts/audit/` | Reviewers can produce clean baseline state reliably. |
| G4 | Remove residual debug/commented diagnostics from audited script paths. | `scripts/mechanism/run_5i_anchor_coupling.py` | Low-severity hygiene issue closed. |
| G5 | Publish release-baseline checklist requiring clean/intended diff before final audit signoff. | `docs/REPRODUCIBILITY.md` and/or release checklist | Baseline hygiene becomes an enforced release step. |

### Verification Commands

```bash
rg --files -g 'AUDIT_LOG.md'
git status --short
rg -n "DEBUG:|TODO|FIXME|HACK" scripts/mechanism/run_5i_anchor_coupling.py
```

---

## 6) Cross-Reference Matrix (Finding -> Planned Closure)

| Finding ID | Planned Closure Evidence |
|---|---|
| `RI-1` | Indistinguishability runner uses computed metrics only; no hardcoded decision constants. |
| `RI-2` | Sensitivity report/status regenerated from canonical run with non-legacy dataset metadata. |
| `RI-3` | Sensitivity provenance command reflects canonical runner execution. |
| `RI-4`, `DOC-1` | Sensitivity documentation text matches regenerated evidence exactly. |
| `RI-5`, `MC-5` | Reproduction verifier uses isolated DB and broader cross-phase checks. |
| `RI-6` | Strict-computed policy enforced for release verification path. |
| `RI-7` | Residual debug/commented diagnostics removed. |
| `MC-1`, `MC-2` | DB and artifact run status semantics corrected to final-state integrity. |
| `MC-3` | CI gate tightened with improved critical-module coverage evidence. |
| `MC-4` | End-to-end sensitivity artifact generation test coverage added. |
| `ST-1` | Artifact contract and location semantics aligned with canonical sensitivity outputs. |
| `ST-2` | Script runtime messaging aligned with actual generated outputs. |
| `INV-1` | Release baseline checklist and clean-worktree process enforced. |
| `INV-2`, `DOC-2` | `AUDIT_LOG.md` created and integrated into audit workflow. |
| `INV-3` | Status artifact retention/cleanup policy documented and operationalized. |

---

## 7) Final Verification Gate (Post-Execution)

Remediation is complete only if all checks pass:

1. `bash scripts/ci_check.sh` passes with updated coverage policy.
2. `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests` passes with improved critical-module coverage.
3. `bash scripts/verify_reproduction.sh` passes using isolated verification DB and expanded scope.
4. `scripts/synthesis/run_indistinguishability_test.py` runs with no hardcoded/estimated decision metrics.
5. `scripts/analysis/run_sensitivity_sweep.py` produces canonical, provenance-coherent artifacts and aligned docs.
6. Run metadata persistence shows final statuses in both DB and run artifacts.
7. `AUDIT_LOG.md` exists and captures remediation decisions.

Post-execution deliverables:

- `reports/audit/FIX_EXECUTION_STATUS_6.md`
- `reports/audit/COMPREHENSIVE_AUDIT_REPORT_7.md` (next assessment-only rerun)

---

## 8) Change-Control Notes

- Prioritize WS-A and WS-B first; do not advance release messaging before those are closed.
- Keep workstreams in discrete, reviewable commits where practical.
- For each closed finding, record:
  - changed files,
  - verification command results,
  - explicit finding ID closure statement.
