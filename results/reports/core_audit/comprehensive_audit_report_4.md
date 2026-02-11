# Comprehensive Code Audit Report 4

**Date:** 2026-02-10  
**Project:** Voynich Manuscript Structural Admissibility Program  
**Method:** `planning/core_audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`  
**Run Type:** Assessment-only (no fixes applied)

---

## Executive Summary

This fourth-pass audit was rerun from the playbook and validated with fresh code inspection plus command execution evidence. The codebase remains functionally rich, but there are still release-blocking issues in reproducibility, provenance integrity, and method completeness.

### Severity Distribution

| Severity | Count | Interpretation |
|---|---:|---|
| Critical | 5 | Can invalidate reproducibility or execution integrity |
| High | 11 | Materially affects trustworthiness of outputs |
| Medium | 14 | Correctness/clarity risks that accumulate reviewer skepticism |
| Low | 6 | Maintainability and hygiene issues |

---

## Audit Scope and Evidence

This pass included:

- Full playbook phase coverage (0 through 5)
- Inventory refresh across `src/`, `scripts/`, `tests/`, `configs/`, docs
- Runtime verification commands:
  - `python -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests`
  - `bash scripts/verify_reproduction.sh`
  - `bash scripts/ci_check.sh`
  - two independent runs of `python scripts/phase3_synthesis/run_test_a.py` with result diff
  - import validation for `foundation.configs.loader`

No code modifications were made during this audit.

---

## Phase 0: Inventory and Orientation

### 0.1 Executable and Module Inventory (refreshed)

| Item | Count | Evidence |
|---|---:|---|
| `src` Python files | 129 | `find src -name '*.py'` |
| `scripts` Python files | 47 | `find scripts -name '*.py'` |
| `tests` Python files | 21 | `find tests -name '*.py'` |
| test files (`test_*.py`) | 12 | `find tests -name 'test_*.py'` |
| notebooks | 0 | `find . -name '*.ipynb'` |
| shell scripts | 2 | `scripts/ci_check.sh`, `scripts/verify_reproduction.sh` |

Top-level source module distribution:

- `src/phase1_foundation`: 55 files
- `src/phase2_analysis`: 22 files
- `src/phase5_mechanism`: 21 files
- `src/phase3_synthesis`: 13 files
- `src/phase4_inference`: 6 files
- `src/phase6_functional`: 6 files
- `src/phase7_human`: 5 files
- `src/phase8_comparative`: 1 file

### 0.2 Inventory Findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| INV-1 | Low | Finder artifact committed in config tree (`.DS_Store`) | `configs/.DS_Store` |

---

## Phase 1: Results Integrity Audit

### 1.1 Critical and High Findings

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| RI-1 | **Critical** | Import-time crash in config loader due missing `Tuple` import in return annotation. | `src/phase1_foundation/configs/loader.py:16` (uses `Tuple[...]`); import fails with `NameError`. |
| RI-2 | **Critical** | Determinism failure in Test A because grammar generator is instantiated without seed. | `scripts/phase3_synthesis/run_test_a.py:55` (`GrammarBasedGenerator(GRAMMAR_PATH)`), while run config sets `seed`. |
| RI-3 | **Critical** | Empirical nondeterminism confirmed: two Test A runs produced different metric outputs for same declared seed path. | `core_status/phase3_synthesis/TEST_A_RESULTS.json` differs across two immediate runs (`pool 20/30` changed). |
| RI-4 | **Critical** | Reproduction checker is structurally invalid as determinism oracle. | `scripts/verify_reproduction.sh:23` sets `SEED` but never passes it; `:29` and `:33` run script without CLI seed; `:36` raw `diff` compares JSON containing timestamps. |
| RI-5 | **Critical** | Run IDs are deterministic from seed only, causing run-identity collisions and overwrite behavior for repeated seed values. | `src/phase1_foundation/runs/manager.py:93-103`, `src/phase1_foundation/core/ids.py:55-64`, `src/phase1_foundation/storage/metadata.py:478-492` (`session.merge`). |
| RI-6 | **Critical** | Hash-based seed derivation introduces cross-process nondeterminism due Python hash randomization. | `src/phase3_synthesis/text_generator.py:138`, `src/phase3_synthesis/refinement/feature_discovery.py:131`; repeated interpreter calls show different `hash('spatial_jar_variance')`. |
| RI-7 | High | Baseline synthesis assessment still leaves key metrics uncomputed (`NOT COMPUTED`) under TODO. | `scripts/phase3_synthesis/run_baseline_assessment.py:172-178`, output rows at `:196-197`. |
| RI-8 | High | Language-ID transform generation includes unseeded random mappings. | `scripts/phase4_inference/run_lang_id.py:74` (`random.choice(...)` in transform loop). |
| RI-9 | High | Corpus ingestion drops remainder tokens due floor division page count. | `scripts/phase4_inference/build_corpora.py:88` (`len(tokens) // tokens_per_page`), loop `:92-99`. |
| RI-10 | High | Circularity risk persists: anomaly/capacity modules rely on fixed observed constants. | `src/phase2_analysis/anomaly/stability_analysis.py:52-54`; `src/phase2_analysis/anomaly/capacity_bounding.py:46-50`; `src/phase2_analysis/anomaly/constraint_analysis.py:145,151,189,198,214`. |

### 1.2 Medium/Low Integrity Findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| RI-11 | Medium | Bare `except:` swallows all errors in section categorization helper. | `scripts/phase5_mechanism/categorize_sections.py:31` |
| RI-12 | Medium | Silent empty-config fallback (`return {}`) can mask missing config files. | `src/phase1_foundation/config.py:331`, `src/phase1_foundation/config.py:344` |
| RI-13 | Medium | Partially implemented placeholder logic remains in human analysis modules. | `src/phase7_human/ergonomics.py:61-66`, `src/phase7_human/ergonomics.py:92`, `src/phase7_human/page_boundary.py:47` |
| RI-14 | Medium | `_ingest_tokens` uses source id `corpus_gen` without corresponding source registration in this script path. | `scripts/phase4_inference/build_corpora.py:101` |

---

## Phase 2: Method Correctness and Internal Consistency

| ID | Severity | Finding | Evidence |
|---|---|---|---|
| MC-1 | High | Output provenance is inconsistent: 23 `run_*.py` scripts write JSON directly without `ProvenanceWriter`. | audit scan across `scripts/run_*.py`; e.g., `scripts/phase4_inference/run_lang_id.py:116-117`, `scripts/phase7_human/run_7c_comparative.py:125-126`, `scripts/phase5_mechanism/run_5k_pilot.py:115-116`. |
| MC-2 | High | Result files are static names, so repeated runs overwrite artifacts rather than append immutable run snapshots. | Same script set as MC-1 (fixed filenames under `results/*`). |
| MC-3 | High | Test coverage remains low for release-grade confidence (33% total; many critical modules at 0%). | `pytest --cov` output (phase2_analysis/anomaly, phase2_analysis/models, many foundation modules). |
| MC-4 | Medium | `RunContext` default constructor path is invalid because `RunID` requires explicit value or seed. | `src/phase1_foundation/runs/context.py:31`, `src/phase1_foundation/core/ids.py:64`; `RunContext()` raises `ValueError`. |
| MC-5 | Medium | Stubs in QC/reporting remain non-functional (`pass`). | `src/phase1_foundation/qc/reporting.py:11`, `src/phase1_foundation/qc/reporting.py:19` |
| MC-6 | Medium | Duplicated data-access helper in human runner bypasses shared query utility. | `scripts/phase7_human/run_7c_comparative.py:27-54` vs shared `src/phase1_foundation/core/queries.py:21-51`. |
| MC-7 | Low | Pydantic v2 deprecation still present for class-based config. | `src/phase1_foundation/runs/context.py:91-92` (warning observed in pytest). |

---

## Phase 3: Structural and Naming Consistency

| ID | Severity | Finding | Location |
|---|---|---|---|
| ST-1 | High | CI flow is coupled to reproduction script that fails early outside activated venv; CI check currently fails at determinism stage. | `scripts/ci_check.sh:21`; `scripts/verify_reproduction.sh:8-10` |
| ST-2 | Medium | Exception-handling discipline remains inconsistent (bare exceptions and silent fallbacks). | `scripts/phase5_mechanism/categorize_sections.py:31`; `src/phase1_foundation/runs/context.py:16-25` |
| ST-3 | Medium | Significant helper and script logic duplication persists in runner layer. | `scripts/phase7_human/run_7c_comparative.py:27-54`; similar duplicated patterns in multiple runners writing near-identical output paths. |
| ST-4 | Low | Mixed script logging style (`print`, `console.print`, logger) adds operational inconsistency. | representative examples across `scripts/*` and `src/phase1_foundation/cli/main.py`. |

---

## Phase 4: Documentation for External Readers

| ID | Severity | Finding | Location |
|---|---|---|---|
| DOC-1 | High | Sensitivity analysis remains documented as planned-only and unexecuted; required sweep script is still absent. | `governance/SENSITIVITY_ANALYSIS.md:5-9`, planned script at `:39`; no `scripts/phase2_analysis/run_sensitivity_sweep.py` present. |
| DOC-2 | Medium | README principle says determinism is mandatory, but reproducibility checks currently demonstrate nondeterministic outputs in Test A path. | `README.md:39`; empirical test output diff for `run_test_a.py`. |
| DOC-3 | Medium | Reproducibility guide points users to verification script that currently fails in default shell state without venv. | `governance/governance/REPRODUCIBILITY.md:92-93`; `scripts/verify_reproduction.sh:8-10`. |

---

## Phase 5: External-Critique Simulation and Clean-Room Re-Execution

### 5.1 Skeptical Reader Checklist

| Question | Current Answer |
|---|---|
| Where are assumptions stated? | Partially documented in methods/config docs, but several high-impact defaults and constants remain embedded in code paths. |
| Which parameters matter most? | Threshold sets and anomaly constants are identifiable, but sensitivity sweep is not executed. |
| What happens if they change? | No complete empirical sensitivity report currently exists (`governance/SENSITIVITY_ANALYSIS.md` is plan-only). |
| How do we know this is not tuned? | Circularity disclosures exist, but hardcoded observed values remain in anomaly modules. |
| What evidence is negative/null? | Some null/placeholder states are explicit (`NOT COMPUTED`), but this is still a maturity gap for publication-level claims. |

### 5.2 Clean-Room/Verification Outcomes (command-backed)

| Check | Result | Notes |
|---|---|---|
| `python -m pytest --cov=src --cov-report=term-missing:skip-covered -q tests` | Pass | Tests pass; coverage = 33%; warning from Pydantic deprecated config style. |
| `bash scripts/verify_reproduction.sh` | **Fail** | Stops at environment check: `ERROR: Virtual environment not active.` |
| `bash scripts/ci_check.sh` | **Fail** | Reaches determinism stage then fails via `verify_reproduction.sh`. |
| `python scripts/phase3_synthesis/run_test_a.py` twice + diff output | **Fail (non-deterministic)** | Result metrics differ between run 1 and run 2. |
| `python -c "import foundation.configs.loader"` | **Fail** | Import raises `NameError: Tuple is not defined`. |

---

## Consolidated Findings Register (Prioritized)

1. **RI-2/RI-3/RI-4/RI-6:** determinism and reproducibility controls are not yet trustworthy.
2. **RI-1:** import-time loader failure is a hard runtime defect.
3. **RI-5 + MC-2:** provenance and run identity are collision-prone/overwrite-prone for fixed-seed runs.
4. **MC-1:** artifact metadata coverage is incomplete across most runner outputs.
5. **MC-3 + DOC-1:** low coverage plus unexecuted sensitivity sweep leaves major confidence gaps.

---

## Release Readiness Verdict

**Assessment Complete:** Yes (fourth pass executed per playbook).  
**Code Changes Applied:** No (documentation-only, as requested).  
**Ready for public methodological release:** **No**.

Primary blockers are deterministic reproducibility integrity, provenance consistency, and unresolved high-impact completeness gaps.

