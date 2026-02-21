# Support Cleanup 5: Holistic Critical Assessment and ROI Execution Plan

**Date:** 2026-02-21  
**Objective:** Identify the highest-ROI work to improve correctness, reproducibility, credibility, and maintainability across code, tests, results, claims, and project structure.

## Executive Summary

The project has strong conceptual architecture and extensive artifact production, but the current operational state is **not publication-grade** due to three high-impact failures:

1. **Replication path is broken at syntax level** in multiple runner scripts.
2. **Verification surfaces disagree** (tests, docs, claim map, and orchestration are out of sync).
3. **Traceability claims are overstated** relative to actual artifact/key integrity.

High-ROI work exists and is concentrated in a small number of fixes that unlock trust quickly.

## Assessment Scorecard

| Area | Grade | Why |
|---|---|---|
| Code execution reliability | D | Multiple replication scripts fail to parse; master runner fails immediately. |
| Test health & coverage fidelity | C- | Coverage exists (64.28%) but test collection/import failures and dependency drift distort confidence. |
| Results/claims traceability | D | Claim map contains missing files and invalid key paths while asserting broad verifiability. |
| Documentation coherence | D | Contradictory phase counts and stale numeric claims (e.g., 914 vs 202 slips). |
| Packaging/dependency integrity | C- | Runtime deps and package discovery do not match actual code usage. |
| Architectural direction | B | Overall phase decomposition and governance scaffolding remain strong. |

## Evidence Snapshot (Verified)

1. **Master replication fails immediately:** `scripts/support_preparation/replicate_all.py` fails when calling `scripts/phase0_data/verify_external_assets.py` (syntax error), then reports a misleading "missing assets" message.
2. **Syntax errors in orchestration scripts:** compile sweep reports unterminated strings in:
`scripts/phase0_data/verify_external_assets.py`, `scripts/phase6_functional/replicate.py`, `scripts/phase7_human/replicate.py`, `scripts/phase8_comparative/replicate.py`, `scripts/phase9_conjecture/replicate.py`, `scripts/phase12_mechanical/replicate.py`, `scripts/phase13_demonstration/replicate.py`, `scripts/phase17_finality/replicate.py`.
3. **Test failures by default environment:** `pytest -q` produced 12 errors (missing `networkx`, `Levenshtein`).
4. **Full test collection fails:** `pytest tests -q --tb=no` interrupted with 4 collection errors from `from src...` imports in phase 12/14 tests.
5. **Coverage currently measured:** 64.28% (7,835/12,188 covered lines), but with failing tests and known collection issues.
6. **Static quality debt is high:** `ruff check src tests scripts --statistics` reported 4,343 issues (including 299 syntax errors).
7. **Claim map integrity drift:** declared JSON paths include missing files (`stage5b_k_adjudication.json`, `cross_section_analysis.json`, `window_reordering.json`, `phase3_synthesis/test_a_results.json`) plus multiple key mismatches.
8. **Numeric contradiction in public-facing docs:** multiple documents still state **914** slips while current artifact reports **202**.

## Critical Findings by Domain

### 1. Code & Runner Logic

- `scripts/support_preparation/replicate_all.py` has lifecycle and messaging flaws:
  - Header says "14 phases" but phase list includes phase 17 and omits phases 9, 15, 16.
  - Calls missing script `scripts/support_preparation/assemble_draft.py`.
  - Does not check final publication command return codes.
  - Misclassifies any Phase 0 verifier failure as missing assets.

### 2. Test Coverage and Verification Surfaces

- `pyproject.toml` `testpaths` excludes phase12/14/15/16/17 tests from default `pytest` runs.
- Phase12/14 test modules import `from src...` instead of package imports, causing collection failures under `pytest tests`.
- CI strategy is inconsistent:
  - `.github/workflows/ci.yml` runs `pytest tests/` (will catch those import failures).
  - `scripts/ci_check.sh` disables lint execution in practice.

### 3. Results, Claims, and Entitlement Risk

- `governance/claim_artifact_map.md` contains path/key drift while asserting broad verifiability.
- Key fields in referenced JSONs changed (e.g., `observed_partial_rho`, `B1_boundary_mi`, nested structures), but map not updated.
- Traceability note already admits static/hardcoded publication values for some claims, which weakens "fully computed" messaging.

### 4. Structure, Packaging, and Dependencies

- `requirements.txt` and `pyproject.toml` dependencies miss libraries used by code (`networkx`, `scikit-learn`, `scipy`, `pandas`, `python-Levenshtein`).
- `requirements-lock.txt` does include many of them, creating split behavior between "compatible" and "exact" installs.
- `pyproject.toml` package discovery omits newer packages (`phase12_mechanical`, `phase14_machine`).
- Version coherence gap: package version is `0.1.0` while docs reference archived release `v1.0.1`.

### 5. Documentation Coherence

- README conflicts internally on project phase completion and replication scope.
- `replicateResults.md` still frames lifecycle as 11 phases.
- Several reports continue to state obsolete 914-slip claims, conflicting with current canonical outputs and claim map notes.

## ROI-Prioritized Execution Plan

## P0: Restore Core Reproducibility Surface (Highest ROI)

### P0.1 Fix syntax-breaking scripts and add parse gate
- **Impact:** Unblocks replication immediately.
- **Effort:** Low.
- **Actions:** Repair broken string literals in the 8 files above; add `python -m compileall -q scripts src tests` to CI/ci_check hard gate.
- **Acceptance:** `python3 scripts/support_preparation/replicate_all.py` reaches phase dispatch; compileall returns clean.

### P0.2 Fix master replication orchestration logic
- **Impact:** Prevents false confidence and broken "success" messaging.
- **Effort:** Low-Medium.
- **Actions:**
  - Align declared phase count and actual executed phases.
  - Add phases 15/16 integration or explicitly scope them out with rationale.
  - Remove/replace missing `assemble_draft.py` call.
  - `check=True` (or explicit return code checks) for final generation calls.
  - Correct Phase 0 failure messaging (distinguish syntax/runtime vs missing data).
- **Acceptance:** runner messaging and executed phase list are consistent and truthful.

### P0.3 Repair test collection integrity
- **Impact:** Converts test suite from partially informative to reliable gate.
- **Effort:** Low.
- **Actions:**
  - Fix `from src...` imports in phase12/14 tests.
  - Include phase12/14/15/16/17 in default `testpaths` or document explicit exclusions.
- **Acceptance:** `pytest tests -q --tb=short` collects without import errors.

## P1: Repair Claim/Artifact Truth Surface

### P1.1 Reconcile claim map with actual artifacts and keys
- **Impact:** High credibility gain; prevents citation-level errors.
- **Effort:** Medium.
- **Actions:**
  - Correct missing file paths and changed JSON key paths.
  - Add machine-check script: verify each claim row’s path exists and key resolves.
  - Make this check a CI gate.
- **Acceptance:** automated check reports 0 missing paths and 0 unresolved keys.

### P1.2 Normalize canonical slip count across all high-visibility reports
- **Impact:** Removes a major contradiction (914 vs 202).
- **Effort:** Low.
- **Actions:** update stale reports/summaries or clearly mark them historical.
- **Acceptance:** no unqualified "914" slip claims in current-state docs.

## P2: Dependency and Packaging Coherence

### P2.1 Align runtime dependencies
- **Impact:** Reduces environment-specific failures and support burden.
- **Effort:** Low.
- **Actions:** ensure runtime manifests include actually imported libraries; define policy for optional extras vs required runtime.
- **Acceptance:** fresh install from declared "compatible" path runs baseline tests without ModuleNotFoundError.

### P2.2 Align package discovery with source tree
- **Impact:** Improves installation and CLI/script portability.
- **Effort:** Low.
- **Actions:** include `phase12_mechanical*` and `phase14_machine*` (and others as intended) in setuptools package discovery.
- **Acceptance:** editable install exposes intended modules without ad-hoc path hacks.

## P3: Quality Gate Hardening (Post-Stability)

### P3.1 Make lint meaningful
- **Impact:** Medium-long-term maintainability.
- **Effort:** Medium.
- **Actions:**
  - Remove `|| true` in CI lint once syntax errors are gone.
  - Stage rollout: fail on syntax/import errors first, then ratchet style debt.
- **Acceptance:** lint enforces at least parser/import correctness on every PR.

### P3.2 Target coverage where risk is highest
- **Impact:** Medium.
- **Effort:** Medium.
- **Actions:** prioritize tests for low-coverage, high-size modules (`stage2_pipeline.py`, `stage3_pipeline.py`, `feature_discovery.py`, etc.) and 0%-covered visualization modules if production-critical.
- **Acceptance:** agreed risk modules exceed minimum coverage threshold.

## Not High ROI Right Now (Defer)

- Large-scale stylistic reformatting across the full codebase before replication/test integrity is restored.
- Broad refactors of stable phase internals without evidence of active defects.
- Expanding new phase features before claim-map and runner trust surfaces are fixed.

## Suggested Execution Order (Fastest Trust Recovery)

1. P0.1 (syntax + compile gate)
2. P0.2 (replication orchestration truth)
3. P0.3 (test collection integrity)
4. P1.1 (claim map path/key validator)
5. P1.2 (914 vs 202 doc normalization)
6. P2.1/P2.2 (dependency + packaging coherence)
7. P3 rollout (lint/coverage ratchet)

## Definition of Done for Cleanup 5

- Master replication entrypoint is executable and truthful about what it runs.
- Test suite collection is clean for all intended phase test directories.
- Claim map is machine-validated against current artifacts.
- No unresolved contradictory headline metrics across core docs.
- Dependency/package manifests reflect real runtime import surface.

## Appendix: Key References

- `scripts/support_preparation/replicate_all.py`
- `scripts/phase0_data/verify_external_assets.py`
- `scripts/phase6_functional/replicate.py`
- `scripts/phase7_human/replicate.py`
- `scripts/phase8_comparative/replicate.py`
- `scripts/phase9_conjecture/replicate.py`
- `scripts/phase12_mechanical/replicate.py`
- `scripts/phase13_demonstration/replicate.py`
- `scripts/phase17_finality/replicate.py`
- `pyproject.toml`
- `requirements.txt`
- `requirements-lock.txt`
- `README.md`
- `replicateResults.md`
- `governance/claim_artifact_map.md`
- `governance/PROJECT_CLOSURE_SUMMARY.md`
- `results/reports/phase12_mechanical/MECHANICAL_ARCHITECTURE.md`
- `results/reports/phase14_machine/FINAL_FIDELITY_CALIBRATION.md`
