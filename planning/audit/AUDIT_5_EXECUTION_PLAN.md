# Execution Plan: Audit 5 Remediation

**Source Audit:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_5.md`  
**Plan Date:** 2026-02-10  
**Scope:** Planning only. This document defines remediation work but does not execute it.

---

## 1) Objective

Close all open findings from Audit 5, with priority on:

1. Sensitivity-analysis validity and claim integrity.
2. CI/test scope credibility and coverage risk.
3. Provenance/artifact contract consistency.
4. Release-baseline hygiene.

Success means a sixth audit pass can verify no remaining Critical findings and no unresolved High findings that block methodological release.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Sensitivity dataset validity and interpretation integrity | `RI-1`, `RI-2`, `RI-3`, `RI-4`, `DOC-1`, `DOC-2` | WS-A |
| Sensitivity runner artifact/provenance and config mutation safety | `RI-5`, `RI-6`, `ST-1` | WS-B |
| CI scope and coverage credibility | `MC-1`, `MC-2`, `MC-3` | WS-C |
| Remaining run-script provenance migration | `MC-4`, `ST-1` | WS-D |
| Fixture and presentation hygiene | `RI-7`, `RI-8` | WS-E |
| Release baseline and artifact lifecycle hygiene | `INV-1`, `INV-2`, `ST-2` | WS-F |

---

## 3) Execution Status Tracker

Update this table during implementation.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Sensitivity Validity and Claims | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Runner now enforces dataset validation, guardrails, and caveat-aware decision logic. |
| WS-B Sensitivity Artifact Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Removed in-place config mutation; moved status output to provenance writer contract in code path. |
| WS-C CI Scope and Coverage Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | CI now runs full test suite with staged coverage gate (Stage 1 default 40%); verified pass at 46.01%. |
| WS-D Provenance Migration Completion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added explicit display-only exemptions and audit test enforcing provenance contract for artifact runners. |
| WS-E Fixture and Output Hygiene | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Strict JSON fixture sanitization implemented (`NaN` -> `null`), and baseline display fallback clarified. |
| WS-F Release Baseline Hygiene | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | `status/` policy documented and ignored; reproducibility checklist updated for release freeze discipline. |
| Final Verification and Re-Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Full pytest, reproduction, and CI checks passed after remediation changes. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Execution Order and Dependencies

Recommended order:

1. WS-A (critical methodological validity)
2. WS-B (sensitivity execution safety and traceability)
3. WS-D (runner provenance completion, to avoid rework before CI hardening)
4. WS-C (CI scope and coverage enforcement after script contracts stabilize)
5. WS-E (fixture/output hygiene cleanup)
6. WS-F (repo/artifact hygiene freeze)
7. Final Verification and Re-Audit

Dependency notes:

- WS-C should follow WS-A/WS-B/WS-D to avoid repeatedly changing CI while target scripts are still evolving.
- WS-F should happen near the end to produce a clean, frozen baseline after functional fixes.

---

## 5) Workstream Details

## WS-A: Sensitivity Validity and Claims

**Addresses:** `RI-1`, `RI-2`, `RI-3`, `RI-4`, `DOC-1`, `DOC-2`  
**Priority:** Critical  
**Objective:** Ensure sensitivity conclusions are computed on the correct corpus and reported with defensible interpretation.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Replace hardcoded dataset `"real"` with canonical dataset selection (`voynich_real`) and make it explicit/configurable. | `scripts/analysis/run_sensitivity_sweep.py` | Sweep runs on existing canonical dataset and fails fast on unknown dataset IDs. |
| A2 | Add preflight dataset validation (existence + minimum data presence checks) before scenario loop. | `scripts/analysis/run_sensitivity_sweep.py` | Invalid/empty datasets abort early with actionable error. |
| A3 | Remove unconditional perturbation-warning suppression and replace with structured warning accounting. | `scripts/analysis/run_sensitivity_sweep.py` | Sweep output includes warning counts/types instead of hidden logs. |
| A4 | Add robustness-claim guardrails: if all models are falsified or no valid scenarios survive quality thresholds, mark conclusion as inconclusive/fail. | `scripts/analysis/run_sensitivity_sweep.py`, `reports/audit/SENSITIVITY_RESULTS.md` generation path | PASS cannot be emitted from uniformly collapsed scenarios. |
| A5 | Expand report schema with explicit data-quality caveats (invalid scenarios, fallback counts, insufficient-data rate). | `reports/audit/SENSITIVITY_RESULTS.md` writer in script | Report has dedicated caveats section and quality metrics table. |
| A6 | Align documentation language to scenario-level evidence (no overclaim). | `docs/SENSITIVITY_ANALYSIS.md` | Summary statements match measured outcomes and caveats exactly. |

### Verification Commands (during execution)

```bash
python3 scripts/analysis/run_sensitivity_sweep.py
python3 -c "import json; d=json.load(open('status/audit/sensitivity_sweep.json')); print(d['summary'])"
rg -n "Robustness decision|Caveat|Surviving|Falsified" reports/audit/SENSITIVITY_RESULTS.md docs/SENSITIVITY_ANALYSIS.md
```

---

## WS-B: Sensitivity Artifact Contract and Mutation Safety

**Addresses:** `RI-5`, `RI-6`, `ST-1`  
**Priority:** High  
**Objective:** Make sensitivity artifacts provenance-complete and remove in-place config mutation risk.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Move sensitivity status output to provenance-enabled artifact format (or equivalent canonical run envelope). | `scripts/analysis/run_sensitivity_sweep.py`, `src/foundation/core/provenance.py` | Sensitivity output includes run metadata and traceable configuration context. |
| B2 | Eliminate in-place writes to `configs/functional/model_params.json` by injecting scenario config in-memory or via temp copy. | `scripts/analysis/run_sensitivity_sweep.py`, model-loading utilities as needed | Original config file remains untouched even on interruption. |
| B3 | Standardize sensitivity output location with broader run artifact policy (`runs/` or approved status path with retention rules). | `scripts/analysis/run_sensitivity_sweep.py`, docs as needed | Artifact location and lifecycle are explicit and consistent with project conventions. |
| B4 | Add regression tests for non-mutation and provenance presence. | `tests/analysis/` and/or `tests/foundation/` | Tests fail if config file is modified or metadata envelope missing. |

### Verification Commands

```bash
git diff -- configs/functional/model_params.json
python3 scripts/analysis/run_sensitivity_sweep.py
python3 -c "import json; d=json.load(open('status/audit/sensitivity_sweep.json')); print('has_provenance', 'provenance' in d)"
python3 -m pytest -q tests/analysis tests/foundation
```

---

## WS-C: CI Scope and Coverage Hardening

**Addresses:** `MC-1`, `MC-2`, `MC-3`  
**Priority:** High  
**Objective:** Align CI gates with actual project risk surface and close critical coverage blind spots.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Expand CI test selection beyond `tests/foundation`, `tests/analysis`, `tests/audit` to include currently omitted suites (or document intentional exclusions with rationale). | `scripts/ci_check.sh` | CI scope policy is explicit and reflects release-critical test suites. |
| C2 | Align coverage measurement between local full-suite and CI gate to remove misleading delta. | `scripts/ci_check.sh`, pytest config if needed | CI coverage number is comparable to release coverage claims. |
| C3 | Add targeted tests for modules currently at/near 0% that are method-critical (`analysis.models.*`, `foundation.cli.main`, `foundation.qc.*`, and priority gaps). | `tests/analysis/`, `tests/foundation/`, possibly `tests/integration/` | Critical-module coverage no longer zero; regression risk materially reduced. |
| C4 | Establish phased coverage targets with explicit date/threshold policy. | `scripts/ci_check.sh`, docs | Coverage ratchets are enforced and documented. |

### Suggested Coverage Gates

| Stage | Minimum Coverage |
|---|---:|
| Stage 1 (immediate) | >= 40% |
| Stage 2 | >= 45% |
| Stage 3 | >= 50% |

### Verification Commands

```bash
bash scripts/ci_check.sh
python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
```

---

## WS-D: Provenance Migration Completion for Runner Scripts

**Addresses:** `MC-4`, `ST-1`  
**Priority:** High  
**Objective:** Complete provenance contract across remaining `run_*.py` scripts or explicitly classify exceptions.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Classify remaining non-provenance runners into: (a) artifact-producing runners that must adopt provenance, (b) display-only runners with documented exemption. | `scripts/analysis/run_phase_2_1.py`, `scripts/analysis/run_phase_2_3.py`, `scripts/analysis/run_phase_2_4.py`, `scripts/synthesis/run_phase_3.py`, `scripts/synthesis/run_phase_3_1.py`, `scripts/analysis/run_sensitivity_sweep.py` | Each script has explicit contract classification. |
| D2 | Implement provenance output for scripts in class (a). | Same files as applicable | Artifact-producing runners include provenance envelope consistently. |
| D3 | Add documentation for exempted class (b) scripts so reviewers understand why no artifact metadata exists. | `docs/PROVENANCE.md` and/or runner docstrings | No ambiguous script behavior remains. |
| D4 | Add audit test/check that reports missing provenance adoption for artifact-producing runners. | `tests/audit/` or script-based checker | Future drift is automatically detected. |

### Verification Commands

```bash
run_files=$(rg --files scripts | rg '/run_.*\.py$')
while IFS= read -r f; do rg -q "ProvenanceWriter" "$f" || echo "NO_PROVENANCE $f"; done <<< "$run_files"
python3 -m pytest -q tests/audit
```

---

## WS-E: Fixture and Output Hygiene

**Addresses:** `RI-7`, `RI-8`  
**Priority:** Medium  
**Objective:** Remove non-standard fixture data and eliminate ambiguous human-facing placeholders.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Replace JSON `NaN` fixture value with strict JSON-safe encoding (`null` plus explicit status metadata, or a numeric sentinel policy). | `tests/fixtures/cluster_tightness_baseline.json`, fixture generator if needed | Fixtures parse under strict JSON parsers. |
| E2 | Update fixture-generation and assertions to enforce strict JSON compatibility. | `scripts/audit/generate_fixtures.py`, relevant tests | New fixtures cannot introduce `NaN`/`Infinity`. |
| E3 | Replace `"NOT COMPUTED"` display fallback with explicit computed/error state language tied to prerequisites. | `scripts/synthesis/run_baseline_assessment.py` | Output clearly distinguishes unavailable metrics from computed metrics. |

### Verification Commands

```bash
python3 -m json.tool tests/fixtures/cluster_tightness_baseline.json >/dev/null
python3 scripts/audit/generate_fixtures.py
python3 scripts/synthesis/run_baseline_assessment.py
```

---

## WS-F: Release Baseline and Artifact Lifecycle Hygiene

**Addresses:** `INV-1`, `INV-2`, `ST-2`  
**Priority:** Medium  
**Objective:** Produce a clean release baseline and consistent artifact versioning policy.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Decide and document policy for `status/` artifacts (ignored transient outputs vs intentionally versioned reports). | `.gitignore`, docs | `status/` handling is intentional and documented. |
| F2 | Align ignore rules with policy and remove recurring noise from default workflow. | `.gitignore` | `git status` no longer shows unwanted recurring artifact noise. |
| F3 | Produce a clean-baseline checklist for release (expected changed files, generated artifacts, verification evidence). | `docs/REPRODUCIBILITY.md` and/or release checklist doc | Baseline freeze process is repeatable and auditable. |
| F4 | Ensure final remediation branch/worktree can be reduced to intentional deltas only. | repository process | Clean, reviewable change set for final signoff. |

### Verification Commands

```bash
git status --short
rg -n "^status/?$|^status/" .gitignore
```

---

## 6) Cross-Reference Matrix (Finding -> Closure Evidence)

| Finding ID | Closure Evidence Required |
|---|---|
| `RI-1` | Sensitivity script uses canonical dataset ID + preflight validation proof |
| `RI-2` | Robustness decision logic rejects degenerate all-falsified scenario sets |
| `RI-3` | Warning visibility restored via logs/summary counters |
| `RI-4`, `DOC-1` | Docs and report language updated to match scenario evidence |
| `RI-5` | Sensitivity outputs include provenance metadata |
| `RI-6` | No in-place config mutation during/after sweep |
| `RI-7` | Strict JSON fixture compatibility validated |
| `RI-8` | Baseline output no longer uses ambiguous placeholder messaging |
| `MC-1` | CI suite scope expanded or exclusions formally documented |
| `MC-2` | Critical zero-coverage modules receive targeted tests |
| `MC-3` | CI and full-suite coverage metrics aligned by policy |
| `MC-4` | Remaining runner provenance migration completed or exemptions documented |
| `ST-1` | Artifact contract consistency documented and enforced |
| `ST-2`, `INV-2` | Output lifecycle policy reflected in ignore rules and process |
| `INV-1` | Clean release-baseline workflow demonstrated |
| `DOC-2` | Sensitivity report includes explicit data-quality caveat section |

---

## 7) Final Verification Gate

Remediation is complete only if all checks pass:

1. `bash scripts/ci_check.sh` passes with updated scope/policy.
2. `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests` passes with improved coverage in identified critical gaps.
3. Sensitivity sweep rerun produces valid dataset targeting, non-degenerate interpretation, and explicit caveat reporting.
4. Provenance and artifact policy is consistent across runner outputs.
5. Worktree hygiene policy is enforced and documented.

Post-remediation deliverables:

- `reports/audit/FIX_EXECUTION_STATUS_5.md` (implementation log and evidence)
- `reports/audit/COMPREHENSIVE_AUDIT_REPORT_6.md` (next full assessment pass)

---

## 8) Change-Control Notes

- Apply WS-A first; do not tune CI thresholds before sensitivity validity is corrected.
- Keep each workstream in separately reviewable commits where practical.
- For every closed finding, include:
  - changed files list
  - verification command output summary
  - explicit reference to the finding ID(s) closed.
