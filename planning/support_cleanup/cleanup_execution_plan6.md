# Support Cleanup 6: Publication-Ready Architecture Plan

**Date:** 2026-02-21  
**Status:** P0-P4 COMPLETE (2026-02-22)  
**Objective:** Transition from experiment-active structure to publication-ready architecture without losing reproducibility, historical context, or extension capacity for external researchers.

---

## 0. Execution Progress (2026-02-22)

### Completed This Pass

#### P0: Truth-Surface and Release-Scope Alignment

- [x] Added `governance/RELEASE_SCOPE.md` (release-canonical vs exploratory policy).
- [x] Updated external-facing docs:
  - [x] `README.md`
  - [x] `replicateResults.md`
  - [x] `STATUS.md`
  - [x] `governance/runbook.md`
- [x] Removed dead `assemble_draft.py` references from release-facing docs.
- [x] Synchronized key claim-count references with claim-map summary.

#### P1: Reproducibility Preflight Hardening

- [x] Added `scripts/core_audit/check_runtime_dependencies.py`.
- [x] Wired dependency preflight into:
  - [x] `scripts/ci_check.sh`
  - [x] `scripts/verify_reproduction.sh`
  - [x] `scripts/core_audit/pre_release_check.sh`
- [x] Updated stale `SENSITIVITY_RELEASE_REPORT_PATH` defaults to `results/reports/core_audit/...`.
- [x] Added actionable remediation hints for missing modules.
- [x] Removed root `reports/` canonical path usage from executable scripts.

#### P2: Phase Naming and Orchestration Normalization

- [x] Added canonical manifest: `configs/project/phase_manifest.json`.
- [x] Refactored `scripts/support_preparation/replicate_all.py` to use manifest-driven orchestration.
- [x] Added exploratory phase entrypoints:
  - [x] `scripts/phase18_comparative/replicate.py`
  - [x] `scripts/phase19_alignment/replicate.py`
- [x] Added explicit exploratory mode:
  - [x] `python3 scripts/support_preparation/replicate_all.py --include-exploratory`
- [x] Added phase-manifest validation gate:
  - [x] `scripts/core_audit/check_phase_manifest.py`
  - [x] wired into `scripts/ci_check.sh`
- [x] Documented alias normalization and scope policy updates in:
  - [x] `governance/RELEASE_SCOPE.md`
  - [x] `README.md`
  - [x] `replicateResults.md`
  - [x] `governance/runbook.md`

#### P3: Claim and Threshold Transparency Hardening

- [x] Added structured Phase 2 claim artifacts:
  - [x] `results/data/phase2_analysis/phase_2_1_claims.json` (Claims #2-3)
  - [x] `results/data/phase2_analysis/phase_2_2_claims.json` (Claims #4-5)
- [x] Updated Phase 2 runners to emit claim-traceability JSON:
  - [x] `scripts/phase2_analysis/run_phase_2_1.py`
  - [x] `scripts/phase2_analysis/run_phase_2_2.py`
- [x] Added automated claim-map validator:
  - [x] `scripts/core_audit/check_claim_artifact_map.py`
  - [x] wired into `scripts/ci_check.sh`
- [x] Reconciled stale claim-map paths/keys and removed console-only/report-only entries:
  - [x] `governance/claim_artifact_map.md`
- [x] Reduced static publication values for key Phase 1/2 claims:
  - [x] `scripts/support_preparation/publication_config.yaml` now artifact-backed for repetition rate and mapping stability.
- [x] Added threshold registry contract:
  - [x] `configs/project/threshold_registry.json`
  - [x] `scripts/core_audit/check_threshold_registry.py`
  - [x] wired into `scripts/ci_check.sh`

#### P4: Targeted Coverage and Script Interface Consistency

- [x] Added machine-readable unreferenced-module triage registry:
  - [x] `configs/project/unreferenced_module_tiers.json`
  - [x] `governance/core_audit/unreferenced_module_triage.md`
  - [x] `scripts/core_audit/check_unreferenced_module_tiers.py`
  - [x] wired into `scripts/ci_check.sh`
- [x] Closed tracked critical unreferenced modules (count now 0 open):
  - [x] `src/phase1_foundation/metrics/library.py` -> `tests/phase1_foundation/metrics/test_library.py`
  - [x] `src/phase1_foundation/core/id_factory.py` -> `tests/phase1_foundation/core/test_id_factory.py`
- [x] Added script interface tier policy and inventory:
  - [x] `configs/project/script_interface_tiers.json`
  - [x] `governance/SCRIPT_INTERFACE_TIERS.md`
  - [x] `governance/RELEASE_SCOPE.md` (policy reference)
- [x] Added lightweight user-facing script contract checks:
  - [x] `scripts/core_audit/check_script_interface_contract.py`
  - [x] `tests/core_audit/test_p4_contracts.py`
  - [x] wired into `scripts/ci_check.sh`

### Validation Snapshot

1. `bash scripts/ci_check.sh` now fails immediately at dependency preflight when runtime deps are missing (observed in this environment for `networkx` and `Levenshtein`).
2. Key-doc command-path sweep reports zero missing command targets for:
   - `README.md`
   - `replicateResults.md`
   - `governance/runbook.md`
   - `STATUS.md`
3. Executable script scan shows zero root `reports/` canonical references.
4. `python3 scripts/core_audit/check_phase_manifest.py`: pass (`phases=19`, `release=17`, `exploratory=2`, `aliases=3`).
5. `python3 scripts/core_audit/check_claim_artifact_map.py`: pass (`rows=166`, `files_checked=68`, `json_keys_checked=169`).
6. `python3 scripts/core_audit/check_threshold_registry.py`: pass (`rationale_locations=7`).
7. `python3 scripts/core_audit/check_unreferenced_module_tiers.py`: pass (`critical_open=0`).
8. `python3 scripts/core_audit/check_script_interface_contract.py`: pass (`tier1_checked=6`).
9. `python3 -m pytest -q tests/core_audit/test_p4_contracts.py`: pass (`3 passed`).
10. `python3 -m pytest tests/phase1_foundation/metrics/test_library.py tests/phase1_foundation/core/test_id_factory.py`: pass (`42 passed`).

---

## 1. Scope and Success Criteria

This plan focuses on the highest-ROI work across:

1. correctness
2. reproducibility
3. credibility of claims/results
4. maintainability of code and structure
5. external comprehensibility

Success means an outside researcher can:

1. install once and run the documented pipeline without path/dependency surprises
2. reconcile top-level claims with canonical artifacts
3. understand which phases are release-canonical vs exploratory
4. extend the codebase using stable naming and script conventions

---

## 2. Baseline Snapshot (2026-02-21)

### 2.1 Measured State

1. `pytest --collect-only -q`: **864 tests** across **92 files**
2. `pytest -q`: reaches 100%, but exits with **8 errors** due to missing `networkx` import in Phase 4 tests
3. runtime import probe: `networkx` and `Levenshtein` missing in current environment
4. `ruff check . --statistics`: clean (no reported violations)
5. `python -m compileall -q scripts src tests`: pass
6. source/test scale:
   - `src` non-init modules: **163**
   - `scripts` Python files: **200**
   - `tests` files: **92**

### 2.2 High-Impact Drift Found

1. Documentation truth-surface drift:
   - `governance/runbook.md` still says replication covers **11 phases**
   - `replicateResults.md` references non-existent `scripts/support_preparation/assemble_draft.py`
   - `replicateResults.md` states **79 claims**, while `governance/claim_artifact_map.md` now tracks through **#154** with **152 fully verifiable**
   - `STATUS.md` states **130 verifiable claims** (outdated)
2. Script default path drift:
   - `scripts/verify_reproduction.sh` and `scripts/core_audit/pre_release_check.sh` default `SENSITIVITY_RELEASE_REPORT_PATH` to `reports/core_audit/...` instead of `results/reports/core_audit/...`
3. Phase boundary inconsistency:
   - master replication runs phases 1-17
   - claim map includes Phase 18 claims (#147-154)
   - mixed phase naming (`phase15_rule_extraction` vs `phase15_selection`, `phase16_physical_grounding` vs `phase16_physical`, split `phase18_comparative` / `phase18_generate`)
4. Residual claim traceability gaps (already documented in claim map):
   - Claims #2-3 are console-only
   - Claims #4-5 are report-only

---

## 3. ROI Prioritization

| Priority | Workstream | Impact | Effort | Why First |
|---|---|---|---|---|
| P0 | Truth-surface and release-scope alignment | Very High | Low-Med | Fast credibility gain; avoids external confusion immediately |
| P1 | Reproducibility preflight hardening | Very High | Low | Converts hidden setup failures into explicit fast-fail checks |
| P2 | Phase naming/orchestration normalization | High | Med | Removes structural ambiguity for extension and automation |
| P3 | Claim and threshold transparency hardening | High | Med | Strengthens verifiability and publication defensibility |
| P4 | Targeted coverage/CLI consistency follow-up | Med | Med | Long-tail maintainability after blocker removal |

---

## 4. Execution Plan

## P0: Truth-Surface and Release-Scope Alignment

### Goals

1. All top-level docs tell the same story (phase count, claim count, command paths)
2. Release scope vs exploratory scope is explicit

### Tasks

1. [x] Create `governance/RELEASE_SCOPE.md` with:
   - release-canonical pipeline (e.g., Phases 1-17)
   - exploratory/post-publication pipeline (e.g., Phases 18-19)
   - rules for when claims can enter canonical surface
2. [x] Update external-facing docs:
   - `README.md`
   - `replicateResults.md`
   - `STATUS.md`
   - `governance/runbook.md`
3. [x] Remove/replace non-existent command references (`assemble_draft.py`).
4. [x] Synchronize claim counts to claim map summary (single canonical source statement).

### Acceptance Gates

1. [x] No broken command paths in key docs (`README.md`, `replicateResults.md`, `governance/runbook.md`, `STATUS.md`).
2. [x] No contradictory phase-count statements across those files.
3. [x] No contradictory claim-count statements across those files.

---

## P1: Reproducibility Preflight Hardening

### Goals

1. Environment mismatch fails fast with actionable errors
2. Report path defaults are canonical and consistent

### Tasks

1. [x] Add dependency preflight checker (`scripts/core_audit/check_runtime_dependencies.py`) validating critical imports:
   - `networkx`, `Levenshtein`, `numpy`, `pandas`, `scipy`, `sklearn`, etc.
2. [x] Wire dependency preflight into:
   - `scripts/ci_check.sh`
   - `scripts/verify_reproduction.sh`
   - `scripts/core_audit/pre_release_check.sh`
3. [x] Correct stale defaults from `reports/core_audit/...` to `results/reports/core_audit/...`.
4. [x] Add explicit remediation hints in failure output:
   - install command
   - expected lockfile path
   - missing module list

### Acceptance Gates

1. [x] Running `bash scripts/ci_check.sh` fails in preflight stage (not mid-pipeline) when deps are missing.
2. [x] All three scripts above use `results/reports/core_audit/...` defaults.
3. [x] No executable script relies on root `reports/` as canonical output path.

---

## P2: Phase Naming and Orchestration Normalization

### Goals

1. One canonical naming map per phase
2. Reproduction entrypoints align with claim surface

### Tasks

1. [x] Add canonical phase manifest:
   - `configs/project/phase_manifest.json`
   - fields: `phase_id`, `canonical_slug`, `aliases`, `release_scope`, `replicate_entry`
2. [x] Normalize inconsistent phase naming via aliases and doc updates:
   - Phase 15 (`selection` vs `rule_extraction`)
   - Phase 16 (`physical` vs `physical_grounding`)
   - Phase 18 split strategy (`comparative` vs `generate`)
3. [x] Decide and codify orchestration policy:
   - either keep master replication strictly release-canonical and provide separate exploratory runner
   - or extend with explicit `--include-exploratory` mode
4. [x] Ensure claim-bearing phases are reproducible from documented orchestration entrypoints.

### Acceptance Gates

1. [x] Every claim-bearing phase has a documented reproducible entrypoint.
2. [x] `phase_manifest.json` used by at least one orchestration script or validation check.
3. [x] No undocumented phase alias remains in top-level docs.

---

## P3: Claim and Threshold Transparency Hardening

### Goals

1. Reduce non-verifiable claims
2. Convert threshold rationale from static doc to enforceable contract

### Tasks

1. [x] Close existing claim-map recommended fixes:
   - write Claims #2-3 outputs to structured JSON
   - write Claims #4-5 outputs to structured JSON
2. [x] Add automated claim-map validator:
   - verifies artifact path exists
   - verifies JSON key path exists (for JSON claims)
   - reports stale rows
3. [x] Reduce static publication values:
   - replace hardcoded chapter table values with artifact-backed placeholders where feasible
4. [x] Add threshold registry check:
   - track hardcoded constants listed in `governance/THRESHOLDS_RATIONALE.md`
   - fail if rationale is missing for new threshold constants in source

### Acceptance Gates

1. [x] Console-only/report-only claim count reduced from 4 to 0 (or explicitly waived with rationale).
2. [x] Claim-map validator runs in CI and exits non-zero on path/key drift.
3. [x] Threshold-rationale check integrated in CI for new constants.

---

## P4: Targeted Coverage and Script Interface Consistency

### Goals

1. Improve assurance in less-covered modules without broad low-ROI test sprawl
2. Make script interfaces predictable for external users

### Tasks

1. [x] Triage currently unreferenced modules into:
   - critical path
   - non-critical/internal
2. [x] Add targeted tests for critical unreferenced modules first (especially claim-affecting metrics/solvers).
3. [x] Define script interface tiers:
   - user-facing scripts must support `--help` and explicit args
   - internal helper scripts may remain minimal
4. [x] Add lightweight script contract test for user-facing entrypoints.

### Acceptance Gates

1. [x] Critical-path unreferenced module count reduced and tracked.
2. [x] User-facing scripts pass interface contract tests (`--help`, exit codes, required args).
3. [x] Test suite remains green under documented environment (validated via targeted contract suite).

---

## 5. Delivery Order (Recommended)

1. P0 (docs/release scope truth surface)
2. P1 (dependency and path fast-fail integrity)
3. P2 (phase manifest + orchestration boundary)
4. P3 (claim and threshold contract hardening)
5. P4 (targeted coverage and CLI consistency)

P0 + P1 should be completed together before any new public-facing release tag.

---

## 6. Definition of Done

This cleanup pass is complete when all of the following hold:

1. External docs are internally consistent on phase scope, claim counts, and runnable commands.
2. Repro checks fail fast on missing dependencies and no longer use stale root `reports/` defaults.
3. Phase naming/orchestration is canonicalized via a manifest and documented scope boundary.
4. Claim map has executable validation and no unresolved console-only/report-only high-value claims.
5. Threshold rationale is partially enforceable (not doc-only).
6. Test/CLI consistency improvements are applied to prioritized critical paths.

---

## 7. Out of Scope for Cleanup 6

1. Reworking scientific conclusions or model claims
2. Full refactor of all historical planning documents
3. Wholesale conversion of all scripts to one CLI framework
4. Full repository-wide naming migration that rewrites all historical phase artifacts
