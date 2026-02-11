# Comprehensive Code Audit Report 6

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no fixes applied)

---

## Executive Summary

Sixth-pass assessment was rerun against the current repository state with fresh static and runtime evidence.

Compared with Audit 5:

- Runtime checks still pass (`pytest`, reproduction verifier, CI check).
- A **new critical integrity issue** remains in a published execution path: `run_indistinguishability_test.py` still uses commented-out computed logic plus hardcoded/estimated values for key metrics.
- Sensitivity artifacts remain legacy-reconciled (`unknown_legacy`) rather than regenerated from canonical runner execution.
- Provenance/run lifecycle metadata remains internally inconsistent (`running` status in persisted result artifacts and DB run records).

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 1 | Can materially invalidate a headline conclusion |
| High | 5 | Major reproducibility/auditability weaknesses |
| Medium | 6 | Important correctness or release-readiness risk |
| Low | 2 | Hygiene/maintainability gaps |

---

## Audit Scope and Evidence

Playbook Phases 0-5 were rerun with direct command evidence and source inspection.

### Runtime commands executed

- `python3 -c "import sys; sys.path.insert(0,'src'); import foundation.configs.loader; print('loader_import_ok')"`
- `python3 scripts/phase3_synthesis/run_test_a.py --seed 4242 --output /tmp/audit6_test_a_1.json` (run twice; canonical payload compare)
- `python3 -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
- `bash scripts/verify_reproduction.sh`
- `bash scripts/ci_check.sh`
- inventory/static scans with `find`, `rg`, `git status --short`, and targeted file/database inspection

### Runtime outcomes

| Check | Result | Notes |
|---|---|---|
| Config loader import | Pass | `loader_import_ok` |
| Deterministic replay (`run_test_a.py`) | Pass | `results_equal True` for same seed |
| Full pytest + coverage | Pass | Total coverage `46%` |
| Reproduction verifier | Pass | Still only checks Test A canonicalization + fixture generation |
| CI check | Pass | Stage-1 gate still `40%`; observed `46.01%` |

No remediation code changes were made in this audit run.

---

## Phase 0: Inventory and Orientation

### 0.1 Inventory snapshot

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 48 | `find scripts -name '*.py'` |
| `tests` Python files | 31 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 22 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 2 | `find scripts -name '*.sh'` |

Top-level source distribution:

- `src/phase1_foundation`: 55
- `src/phase2_analysis`: 22
- `src/phase5_mechanism`: 21
- `src/phase3_synthesis`: 13
- `src/phase4_inference`: 6
- `src/phase6_functional`: 6
- `src/phase7_human`: 5
- `src/phase8_comparative`: 1

### 0.2 Inventory findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Medium | Worktree is not release-clean (`68` modified/untracked paths), which complicates freeze/baseline claims. | `git status --short` |
| INV-2 | Medium | Playbook-required `AUDIT_LOG.md` artifact is still missing. | Expectation: `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md:43`; not found via `rg --files -g 'AUDIT_LOG.md'` |
| INV-3 | Low | Repository keeps accumulating transient verification artifacts under `core_status/by_run/`, increasing local audit noise even though `core_status/` is ignored. | `core_status/by_run/*`; `.gitignore:39` |

---

## Phase 1: Results Integrity Audit

### 1.1 Critical/High findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-1 | **Critical** | `run_indistinguishability_test.py` still uses commented-out computed logic and hardcoded/estimated values (`real_z`, `syn_z`, `real_rad`, `syn_rad`) that feed the pass/fail conclusion. | Commented-out metric runs: `scripts/phase3_synthesis/run_indistinguishability_test.py:97`; hardcoded/estimated values: `scripts/phase3_synthesis/run_indistinguishability_test.py:102`; conclusion logic: `scripts/phase3_synthesis/run_indistinguishability_test.py:129`; script is in reproducibility path: `governance/governance/REPRODUCIBILITY.md:44` |
| RI-2 | **High** | Sensitivity artifacts remain legacy-reconciled and not evidence of a fresh canonical sweep (`dataset_id=unknown_legacy`, `pages=0`, `tokens=0`). | `reports/core_audit/SENSITIVITY_RESULTS.md:4`; `reports/core_audit/SENSITIVITY_RESULTS.md:5`; `core_status/core_audit/sensitivity_sweep.json:31`; `core_status/core_audit/sensitivity_sweep.json:33` |
| RI-3 | **High** | Sensitivity artifact provenance shows non-canonical execution command (`sensitivity_sweep_legacy_reconcile`) rather than `run_sensitivity_sweep`, so current published sensitivity evidence is not directly runner-derived. | `core_status/core_audit/sensitivity_sweep.json:10`; canonical runner config command is `scripts/phase2_analysis/run_sensitivity_sweep.py:427`; unresolved rerun noted in `reports/core_audit/FIX_EXECUTION_STATUS_5.md:161` |
| RI-4 | **High** | Reproducibility docs mark sensitivity status as executed with quality gates, but current published sensitivity outputs still reflect legacy/zero-data profile, causing documentation-evidence mismatch. | Claimed executed: `governance/SENSITIVITY_ANALYSIS.md:5`; legacy/zero-data output: `reports/core_audit/SENSITIVITY_RESULTS.md:4`; `reports/core_audit/SENSITIVITY_RESULTS.md:6` |

### 1.2 Medium/Low findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| RI-5 | Medium | Verification workflow mutates primary `data/voynich.db` (not an isolated test DB), allowing verification runs to alter baseline state. | `scripts/verify_reproduction.sh:16`; `scripts/verify_reproduction.sh:32`; `scripts/phase3_synthesis/run_test_a.py:38`; `scripts/phase3_synthesis/run_test_a.py:63` |
| RI-6 | Medium | Strict no-fallback mode (`REQUIRE_COMPUTED=1`) remains optional in reproducibility guidance while fallback defaults are present in core synthesis profile extraction. | Optional strict mode: `governance/governance/REPRODUCIBILITY.md:93`; fallback defaults and simulated page data: `src/phase3_synthesis/profile_extractor.py:71`; `src/phase3_synthesis/profile_extractor.py:102` |
| RI-7 | Low | Residual debug/commented diagnostic code remains in execution path script. | `scripts/phase5_mechanism/run_5i_anchor_coupling.py:58` |

---

## Phase 2: Method Correctness and Internal Consistency

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| MC-1 | **High** | Provenance snapshots frequently persist `status: running` because metadata is captured before run completion. | Status sourced from active run: `src/phase1_foundation/core/provenance.py:27`; save-before-complete pattern: `scripts/phase3_synthesis/run_test_a.py:121` then `scripts/phase3_synthesis/run_test_a.py:123`; artifact example `running`: `core_status/by_run/verify_1.1291aeff-2f29-02e2-551d-1aa8b0ea6912.json:6`; corresponding run manifest `success`: `runs/1291aeff-2f29-02e2-551d-1aa8b0ea6912/run.json:3` |
| MC-2 | **High** | Run records in metadata DB are systematically stale (`status=running`, `timestamp_end=NULL`) for completed runs, weakening run-history trustworthiness. | `MetadataStore.save_run` records current run status: `src/phase1_foundation/storage/metadata.py:489`; run completion occurs later in context manager: `src/phase1_foundation/runs/manager.py:178`; DB query evidence shows widespread `running` statuses |
| MC-3 | **High** | Coverage gate passes at 40% despite important modules remaining effectively untested (including 0% coverage in key components). | Gate config `scripts/ci_check.sh:20`; full-suite output still includes 0% files (e.g., `src/phase1_foundation/cli/main.py`, `src/phase2_analysis/admissibility/manager.py`, `src/phase1_foundation/core/queries.py`) |
| MC-4 | Medium | Sensitivity guardrail tests validate helper logic but do not provide end-to-end proof that published sensitivity artifacts are generated by canonical runner execution. | `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py:14`; `tests/phase2_analysis/test_sensitivity_sweep_guardrails.py:43` |
| MC-5 | Medium | Reproduction verifier scope is narrow (Test A determinism + fixture generation only), so major phase outputs are not locked by automated equality/regression checks. | `scripts/verify_reproduction.sh:30`; `scripts/verify_reproduction.sh:67` |

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-1 | Medium | Output contracts are still mixed in practice: provenance-managed JSON exists, but audit-significant sensitivity artifacts currently reflect legacy reconciliation path and transient `core_status/` location. | `core_status/core_audit/sensitivity_sweep.json:10`; `governance/PROVENANCE.md:67`; `reports/core_audit/SENSITIVITY_RESULTS.md:4` |
| ST-2 | Low | Human-facing message drift in `run_indistinguishability_test.py` (declares “18 pages” while generating count=2) indicates stale script narration. | Generation count: `scripts/phase3_synthesis/run_indistinguishability_test.py:60`; message: `scripts/phase3_synthesis/run_indistinguishability_test.py:86` |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | **High** | Documentation and current sensitivity evidence are misaligned: docs present executed quality-gated process while extant outputs remain legacy/zero-data reconciled. | `governance/SENSITIVITY_ANALYSIS.md:5`; `reports/core_audit/SENSITIVITY_RESULTS.md:4`; `reports/core_audit/FIX_EXECUTION_STATUS_5.md:162` |
| DOC-2 | Medium | Playbook output contract is only partially met; `METHODS_REFERENCE`/`CONFIG_REFERENCE`/`REPRODUCIBILITY` exist, but required `AUDIT_LOG.md` is absent. | Expected output list: `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md:43`; existing files: `governance/governance/METHODS_REFERENCE.md`, `governance/CONFIG_REFERENCE.md`, `governance/governance/REPRODUCIBILITY.md` |

---

## Phase 5: External-Critique Simulation

### Skeptical reader checklist (current answers)

| Question | Current answer |
|---|---|
| Where are assumptions stated? | Broadly documented, but a key execution script still embeds hardcoded/estimated metric values (`run_indistinguishability_test.py`). |
| Which parameters matter most? | Perturbation thresholds, sensitivity scales, and model-evaluation weights remain primary. |
| What happens if they change? | Sensitivity framework is designed for this, but currently published sensitivity outputs are legacy-reconciled and not fresh canonical-run evidence. |
| How do we know this is not tuned? | Determinism checks pass, but hardcoded values in a published script and stale run-status metadata weaken that argument. |
| What evidence is negative/null? | Scenario tables show all-model falsification and `INCONCLUSIVE` robustness framing, but those artifacts are still based on reconciled legacy data. |

---

## Consolidated Findings Register (Prioritized)

1. **RI-1 (Critical):** `run_indistinguishability_test.py` still uses hardcoded/estimated key metrics with commented-out computed paths.
2. **RI-2/RI-3/RI-4/DOC-1 (High):** sensitivity evidence remains legacy-reconciled and not regenerated from canonical sweep execution, despite “executed” documentation framing.
3. **MC-1/MC-2 (High):** provenance/run lifecycle status is systematically stale (`running`) across persisted results and DB run records.
4. **MC-3 (High):** coverage gate passes at a low threshold while critical modules remain untested.
5. **MC-5 + RI-5 (Medium):** reproducibility verification remains narrow and mutates the primary DB rather than isolated verification storage.
6. **INV-1 + INV-2 (Medium):** release baseline hygiene and expected-output completeness remain incomplete.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (sixth pass rerun per playbook).  
**Code Changes Applied:** No (assessment/documentation only).  
**Ready for public methodological release:** **Not yet**.

### Blocking items before release confidence

- Remove hardcoded/estimated metric path in `run_indistinguishability_test.py` and restore computed metric path end-to-end.
- Produce fresh sensitivity sweep artifacts from canonical runner execution (`run_sensitivity_sweep`) and align docs to those outputs.
- Fix run-status lifecycle persistence so artifact and DB run records reflect completed status.
- Raise effective test assurance for currently untested critical modules and broaden reproduction verification coverage.
- Establish a clean release baseline and satisfy playbook output contract (`AUDIT_LOG.md` or explicit equivalent policy accepted and documented).
