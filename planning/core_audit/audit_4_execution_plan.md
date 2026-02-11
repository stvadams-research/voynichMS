# Execution Plan: Audit 4 Remediation

**Source Audit:** `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_4.md`  
**Plan Date:** 2026-02-10  
**Scope:** Remediation planning only. No implementation is performed in this document.

---

## 1) Goal

Resolve all release-blocking findings from Audit 4, then run a clean verification pass with deterministic outputs, stable provenance, improved methodological completeness, and documentation/CI alignment.

---

## 2) Findings Coverage Map

| Finding Group | IDs | Planned Workstream |
|---|---|---|
| Reproducibility and determinism blockers | `RI-2`, `RI-3`, `RI-4`, `RI-6`, `ST-1`, `DOC-3` | WS-A |
| Runtime/import integrity | `RI-1`, `MC-4` | WS-B |
| Provenance/run identity and artifact immutability | `RI-5`, `MC-1`, `MC-2` | WS-C |
| Placeholder/incomplete computation and data ingestion defects | `RI-7`, `RI-8`, `RI-9`, `RI-11`, `RI-12`, `RI-13`, `RI-14`, `MC-5` | WS-D |
| Methodological circularity and sensitivity completeness | `RI-10`, `DOC-1` | WS-E |
| Structural consistency and duplicated script logic | `MC-6`, `ST-2`, `ST-3`, `ST-4` | WS-F |
| Coverage and regression protection | `MC-3`, `MC-7` | WS-G |
| Documentation truth alignment | `DOC-2`, `DOC-3` | WS-H |
| Inventory hygiene | `INV-1` | WS-I |

---

## 3) Execution Status Tracker

Update this table during execution.

| Workstream | Status | Owner | Start Date | End Date | Notes |
|---|---|---|---|---|---|
| WS-A Reproducibility and Determinism | NOT STARTED | TBD |  |  |  |
| WS-B Runtime and Import Integrity | NOT STARTED | TBD |  |  |  |
| WS-C Provenance and Run Identity | NOT STARTED | TBD |  |  |  |
| WS-D Incomplete Logic and Data Integrity | NOT STARTED | TBD |  |  |  |
| WS-E Methodology and Sensitivity | NOT STARTED | TBD |  |  |  |
| WS-F Structural Consistency | NOT STARTED | TBD |  |  |  |
| WS-G Test and Coverage Hardening | NOT STARTED | TBD |  |  |  |
| WS-H Documentation Alignment | NOT STARTED | TBD |  |  |  |
| WS-I Hygiene Cleanup | NOT STARTED | TBD |  |  |  |
| Final Verification and Re-Audit | NOT STARTED | TBD |  |  |  |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 4) Dependency Order

Execute in this order to minimize rework:

1. WS-B Runtime and Import Integrity  
2. WS-A Reproducibility and Determinism  
3. WS-C Provenance and Run Identity  
4. WS-D Incomplete Logic and Data Integrity  
5. WS-E Methodology and Sensitivity  
6. WS-F Structural Consistency  
7. WS-G Test and Coverage Hardening  
8. WS-H Documentation Alignment  
9. WS-I Hygiene Cleanup  
10. Final Verification and Re-Audit

---

## 5) Workstream Details

## WS-A: Reproducibility and Determinism

**Addresses:** `RI-2`, `RI-3`, `RI-4`, `RI-6`, `ST-1`, `DOC-3`  
**Priority:** Critical  
**Objective:** Ensure repeated runs with same seed produce identical, verification-safe outputs.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| A1 | Seed Test A grammar generator explicitly and thread seed through all random generation paths. | `scripts/phase3_synthesis/run_test_a.py`, `src/phase3_synthesis/generators/grammar_based.py` | Repeated Test A runs with same seed produce identical metric payloads. |
| A2 | Remove unstable use of Python `hash()` for RNG seed derivation; replace with stable deterministic hash (for example SHA256-derived int). | `src/phase3_synthesis/text_generator.py`, `src/phase3_synthesis/refinement/feature_discovery.py` | Seed-derived behavior is stable across interpreter restarts. |
| A3 | Repair `verify_reproduction.sh`: pass seed explicitly, compare canonicalized result payloads (exclude volatile fields like timestamps), preserve strict failure semantics. | `scripts/verify_reproduction.sh` | Script passes in clean environment when determinism is valid; fails only on true nondeterminism. |
| A4 | Update CI determinism step to use repaired verifier and clear environment preconditions. | `scripts/ci_check.sh` | CI check no longer fails due to environment mismatch alone. |
| A5 | Add deterministic regression test for Test A output consistency. | `tests/core_audit/` | Automated test catches future nondeterminism regressions. |

### Verification Commands (to run during execution)

```bash
python scripts/phase3_synthesis/run_test_a.py
cp core_status/phase3_synthesis/TEST_A_RESULTS.json /tmp/test_a_1.json
python scripts/phase3_synthesis/run_test_a.py
cp core_status/phase3_synthesis/TEST_A_RESULTS.json /tmp/test_a_2.json
diff /tmp/test_a_1.json /tmp/test_a_2.json
bash scripts/verify_reproduction.sh
bash scripts/ci_check.sh
```

---

## WS-B: Runtime and Import Integrity

**Addresses:** `RI-1`, `MC-4`  
**Priority:** Critical  
**Objective:** Remove immediate runtime failures and invalid default initialization paths.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| B1 | Fix missing `Tuple` import in config loader return annotation. | `src/phase1_foundation/configs/loader.py` | Module imports successfully in isolation. |
| B2 | Ensure `RunContext` default construction path is valid or explicitly prohibited with clear error contract. | `src/phase1_foundation/runs/context.py`, `src/phase1_foundation/core/ids.py`, `src/phase1_foundation/runs/manager.py` | `RunContext` usage is consistent and no hidden constructor trap remains. |
| B3 | Add targeted unit tests for loader import and run context lifecycle behavior. | `tests/phase1_foundation/` | Regressions caught automatically. |

### Verification Commands

```bash
python -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader"
python -c "import sys; sys.path.insert(0,'src'); from foundation.runs.context import RunContext; print('ok')"
python -m pytest -q tests/phase1_foundation
```

---

## WS-C: Provenance and Run Identity

**Addresses:** `RI-5`, `MC-1`, `MC-2`  
**Priority:** Critical  
**Objective:** Guarantee unique run identity per execution and immutable result artifacts with provenance.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| C1 | Redesign run identity model to avoid seed-only run ID collisions. Keep deterministic experiment linkage separately from unique run instance ID. | `src/phase1_foundation/runs/manager.py`, `src/phase1_foundation/core/ids.py`, `src/phase1_foundation/storage/metadata.py` | Repeated same-seed runs generate distinct run records without overwrite. |
| C2 | Update result-writing conventions so outputs are run-scoped or append-only, not static overwrite paths. | `scripts/*/run_*.py`, `src/phase1_foundation/core/provenance.py` | Running same script twice preserves both outputs. |
| C3 | Migrate scripts that currently use raw `json.dump` to standardized provenance writer pattern. | all affected `scripts/*/run_*.py` identified in audit | All runner outputs include provenance block and run linkage. |
| C4 | Add compatibility strategy for existing consumers expecting old static filenames (index file or latest symlink/pointer). | `scripts/`, `governance/` | Backward compatibility maintained with explicit policy. |

### Verification Commands

```bash
python scripts/phase3_synthesis/run_test_a.py
python scripts/phase3_synthesis/run_test_a.py
ls -la runs
find results -type f | sort
```

---

## WS-D: Incomplete Logic and Data Integrity

**Addresses:** `RI-7`, `RI-8`, `RI-9`, `RI-11`, `RI-12`, `RI-13`, `RI-14`, `MC-5`  
**Priority:** High  
**Objective:** Eliminate placeholder behavior from production paths and close ingestion/runtime integrity gaps.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| D1 | Complete baseline synthesis assessment metrics currently marked `NOT COMPUTED` (or enforce explicit fail-fast if prerequisites missing). | `scripts/phase3_synthesis/run_baseline_assessment.py` | No silent placeholder outputs in baseline report path. |
| D2 | Make language-ID transform randomization seed-controlled and deterministic per run configuration. | `scripts/phase4_inference/run_lang_id.py` | Same seed yields same transform set and scores. |
| D3 | Fix token ingestion remainder loss by ingesting final partial page/chunk. | `scripts/phase4_inference/build_corpora.py` | Token count in DB matches intended source count exactly. |
| D4 | Ensure transcription source IDs are registered consistently before use (`corpus_gen` path). | `scripts/phase4_inference/build_corpora.py` | No unregistered source ID usage. |
| D5 | Replace bare `except:` with explicit exception handling and logging. | `scripts/phase5_mechanism/categorize_sections.py` | No bare exception remains in this module. |
| D6 | Replace silent empty-config fallback behavior with explicit warning/error policy. | `src/phase1_foundation/config.py` | Missing config files cannot silently alter behavior unnoticed. |
| D7 | Implement or explicitly decommission placeholder/stub analysis methods in phase7_human/QC modules. | `src/phase7_human/ergonomics.py`, `src/phase7_human/page_boundary.py`, `src/phase1_foundation/qc/reporting.py` | Placeholders no longer appear in release path. |

### Verification Commands

```bash
rg -n "TODO|NOT COMPUTED|return \\{\\}|except:\\s*$" src scripts
python scripts/phase4_inference/build_corpora.py
python scripts/phase3_synthesis/run_baseline_assessment.py
```

---

## WS-E: Methodology and Sensitivity Completeness

**Addresses:** `RI-10`, `DOC-1`  
**Priority:** High  
**Objective:** Remove unresolved methodological ambiguity around circularity and sensitivity claims.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| E1 | Externalize observed anomaly constants and annotate provenance lineage clearly (inputs vs conclusions). | `src/phase2_analysis/anomaly/stability_analysis.py`, `src/phase2_analysis/anomaly/capacity_bounding.py`, `src/phase2_analysis/anomaly/constraint_analysis.py`, config files | No hidden hardcoded observed-value dependence in core anomaly logic. |
| E2 | Implement sensitivity sweep runner and execute documented sweep plan. | `scripts/phase2_analysis/run_sensitivity_sweep.py`, `governance/SENSITIVITY_ANALYSIS.md` | Sweep executed; results artifact generated. |
| E3 | Publish sensitivity outcomes and decision impact summary. | `reports/core_audit/SENSITIVITY_RESULTS.md` | Explicit statement of robustness/fragility across parameter ranges. |

### Verification Commands

```bash
python scripts/phase2_analysis/run_sensitivity_sweep.py
test -f reports/core_audit/SENSITIVITY_RESULTS.md
```

---

## WS-F: Structural Consistency and Duplication Removal

**Addresses:** `MC-6`, `ST-2`, `ST-3`, `ST-4`  
**Priority:** Medium  
**Objective:** Reduce duplicated runner logic and normalize logging/error style.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| F1 | Replace duplicated runner data-extraction helper with shared query utility usage. | `scripts/phase7_human/run_7c_comparative.py`, `src/phase1_foundation/core/queries.py` | Single canonical helper path is used. |
| F2 | Normalize exception handling style: no silent swallows in audited script paths. | selected `scripts/` and `src/phase1_foundation/*` | Exceptions are explicit and logged. |
| F3 | Standardize script logging conventions (CLI display vs internal logger boundaries). | `scripts/`, `src/phase1_foundation/cli/main.py` | Consistent operational behavior and cleaner logs. |

### Verification Commands

```bash
rg -n "except:\\s*$|except Exception:\\s*pass" src scripts
rg -n "def get_lines\\(" scripts
```

---

## WS-G: Test Coverage and Regression Protection

**Addresses:** `MC-3`, `MC-7`  
**Priority:** High  
**Objective:** Raise confidence by expanding tests over high-risk modules and removing known warning debt.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| G1 | Add tests for reproducibility pipeline, run identity behavior, provenance writing, and baseline assessment correctness. | `tests/core_audit/`, `tests/phase1_foundation/`, `tests/phase3_synthesis/` | New high-risk paths covered. |
| G2 | Add focused tests for anomaly modules currently at 0% coverage. | `tests/phase2_analysis/` | Non-zero meaningful coverage in anomaly package. |
| G3 | Address Pydantic config deprecation to remove warning debt. | `src/phase1_foundation/runs/context.py` | `pytest` warning removed. |
| G4 | Set and enforce minimum coverage threshold gate for CI (phased target). | `scripts/ci_check.sh`, pytest config | CI blocks coverage regressions. |

### Suggested Coverage Targets

| Stage | Total Coverage Target |
|---|---:|
| Stage 1 | >= 45% |
| Stage 2 | >= 55% |
| Stage 3 | >= 65% |

### Verification Commands

```bash
python -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests
```

---

## WS-H: Documentation Truth Alignment

**Addresses:** `DOC-2`, `DOC-3`  
**Priority:** High  
**Objective:** Ensure docs reflect actual behavior, constraints, and known limitations.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| H1 | Update README determinism claims to match enforced behavior and verification strategy. | `README.md` | No mismatch between claims and current pipeline behavior. |
| H2 | Update reproducibility guide with real environment prerequisites and repaired verification flow. | `governance/governance/REPRODUCIBILITY.md` | Following doc commands succeeds in clean setup. |
| H3 | Add explicit provenance/run-output policy docs. | `governance/RUNBOOK.md` or new `governance/PROVENANCE.md` | External readers can trace output lifecycle and identity semantics. |

---

## WS-I: Hygiene Cleanup

**Addresses:** `INV-1`  
**Priority:** Low  
**Objective:** Remove repository artifacts that should not be versioned.

### Tasks

| Task ID | Action | Target Files | Exit Criteria |
|---|---|---|---|
| I1 | Remove `.DS_Store` from config tree and add ignore protection if needed. | `configs/.DS_Store`, `.gitignore` | Artifact removed and prevented from reappearing. |

---

## 6) Final Verification and Exit Criteria

The remediation campaign is complete only when all criteria are met:

1. Determinism checks pass reliably:
   - `bash scripts/verify_reproduction.sh` passes.
   - repeated same-seed runs produce identical canonical result payloads.
2. CI gate passes end-to-end:
   - `bash scripts/ci_check.sh` passes from documented setup.
3. No critical findings from Audit 4 remain open.
4. Sensitivity analysis is executed and reported.
5. Provenance is present for all runner outputs and repeated runs do not overwrite history.
6. Coverage target for current stage is met with no new warning debt.
7. A fresh comprehensive audit is generated after remediation:
   - output target: `reports/core_audit/COMPREHENSIVE_AUDIT_REPORT_5.md`.

---

## 7) Suggested Milestones

| Milestone | Scope | Completion Gate |
|---|---|---|
| M1 | WS-B + WS-A | Runtime/import defects fixed; determinism verifier repaired |
| M2 | WS-C + WS-D | Provenance/run identity hardened; placeholders and ingestion defects addressed |
| M3 | WS-E + WS-F | Methodology and structural consistency stabilized |
| M4 | WS-G + WS-H + WS-I | Test, docs, and hygiene complete |
| M5 | Final Verification | All exit criteria met; re-audit produced |

---

## 8) Change Control Notes

- Prioritize smallest safe changes in critical paths first (`WS-B`, `WS-A`).
- For run identity/provenance redesign (`WS-C`), define backward compatibility strategy before merging.
- Require PR-level evidence for each workstream:
  - changed files
  - verification command output
  - updated status row in Section 3.

