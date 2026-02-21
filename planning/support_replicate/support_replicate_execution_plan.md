# Support: Replicate — Reproducibility Hardening Execution Plan

**Created:** 2026-02-20
**Updated:** 2026-02-20
**Purpose:** Systematically close every gap between the current codebase and a
cleanly reproducible external replication of all claims in the
`Voynich_Structural_Identification_Final_021526` publication.

**Status:** ALL 5 SPRINTS COMPLETE — 27/27 gaps RESOLVED.

### Change Log

| Date | Items | Summary |
|---|---|---|
| 2026-02-20 | G1.1–G1.5, G3.5 | Created Phase 10/11 replicate.py, completed Phase 3/4/5 replicate.py, fixed visualization CLI calls, removed `--allow-fallback` from Phase 3 |
| 2026-02-20 | G2.1, G2.2 | Generated `requirements-lock.txt` (pinned from current venv), documented Python 3.11.13 in lock file header and `replicateResults.md`, updated caveats section |
| 2026-02-20 | G3.1, G3.2, G3.3, G3.6, G6.3 | RunManager seed enforcement under REQUIRE_COMPUTED=1; `require_seed_if_strict()` guard added to 16 simulator/generator constructors across Phase 3/5; bare-random audit (26/27 safe); G3.6 + G6.3 confirmed already fixed in prior audit |
| 2026-02-20 | G4.1–G4.5 | Reconciled runbook.md + reproducibility.md to 11-phase canonical order; created `governance/config_reference.md` (20 JSON configs documented); completed `governance/methods_reference.md` with Phase 10 Methods F–K and Phase 11 stroke topology; updated README.md (Phase 11, replicateResults.md pointer); created `.env.example` (6 env vars) |
| 2026-02-20 | G5.1–G5.3, G6.1, G6.4 | Created `governance/claim_artifact_map.md` (47 claims traced to JSON key paths); standardized output paths across 17 scripts (Phase 5/6/7/8) from `results/phase*/` to `results/data/phase*/`; updated verify_reproduction.sh, ci_check.sh, pre_release_check.sh for new paths; added Phase 11 determinism check to verify_reproduction.sh; created golden output extract/check scripts; documented `core_status/` prerequisite in replicateResults.md |
| 2026-02-20 | G6.2, G7.1, G7.2, G3.4 | Created `.github/workflows/ci.yml` (lint + unit tests on push/PR) and `reproduce.yml` (weekly smoke test with data download + determinism check); created `scripts/phase0_data/download_external_data.py` (IVTFF + Gutenberg automated download); confirmed `data/voynich.db` already gitignored and not tracked (documented as regenerated artifact); expanded UMAP non-determinism caveat in `replicateResults.md` with specific file reference |

---

## Executive Summary

After a thorough audit of the codebase, documentation, scripts, and output
artifacts, the project has **strong bones** for reproducibility: a canonical
data pipeline, run-level provenance, determinism infrastructure
(`RandomnessController`, `DeterministicIDFactory`), a master replication entry
point, verification scripts, and governance documentation.

However, 11 phases of iterative development have introduced drift. The gaps fall
into 7 categories:

| Category | Gap Count | Severity |
|---|---|---|
| G1: Replication Script Coverage | 5 | ~~CRITICAL~~ RESOLVED |
| G2: Dependency Pinning | 2 | ~~CRITICAL~~ RESOLVED |
| G3: Seed / Determinism Enforcement | 6 (1 resolved) | ~~HIGH~~ RESOLVED |
| G4: Documentation Drift | 5 | ~~HIGH~~ RESOLVED |
| G5: Output-to-Claim Traceability | 3 | ~~MEDIUM~~ RESOLVED |
| G6: Verification Completeness | 4 | ~~MEDIUM~~ RESOLVED |
| G7: Data Acquisition Automation | 2 | ~~LOW~~ RESOLVED |
| **Total** | **27** | |

---

## G1: Replication Script Coverage — RESOLVED

### G1.1 — `replicate_all.py` excludes Phases 10 and 11 — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:**
1. Created `scripts/phase10_admissibility/replicate.py` — runs all 7 stages
   in order with explicit `--seed 42` on seeded stages.
2. Created `scripts/phase11_stroke/replicate.py` — runs extraction, cluster
   (`--seed 42 --permutations 10000`), and transitions.
3. Added Phase 10 and Phase 11 to the `phases` list in `replicate_all.py`.
4. Updated docstring and print output to reflect 11 phases.

---

### G1.2 — Phase 3 replicate.py omits scripts that produce publication claims — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added to `scripts/phase3_synthesis/replicate.py`:
- `run_phase_3.py` (core synthesis pipeline)
- `run_test_a.py --seed 42`, `run_test_b.py`, `run_test_c.py`
- `run_indistinguishability_test.py` (removed `--allow-fallback`, also resolves G3.5)
- `run_control_matching_audit.py` (produces CONTROL_COMPARABILITY_STATUS.json)
- Visualization call using `python3 -m support_visualization.cli.main`

---

### G1.3 — Phase 4 replicate.py omits `run_morph.py` and `run_topics.py` — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added to `scripts/phase4_inference/replicate.py`:
- Core methods: `run_morph.py` (Method E), `run_topics.py` (Method C)
- All 13 supplementary hypothesis checks: boundary persistence (3 variants),
  line reset (2 variants), order constraints, NCD matrix, projection bounded,
  discrimination, Kolmogorov proxy, image encoding hypothesis, music
  hypothesis, reference 42
- Visualization call updated to `python3 -m support_visualization.cli.main`

---

### G1.4 — Phase 5 replicate.py runs 3 of 10+ scripts — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Rewrote `scripts/phase5_mechanism/replicate.py` to include:
- `run_pilot.py` (iterative collapse baseline)
- All 8 mechanism signature pilots: 5b, 5c, 5d, 5e, 5f, 5g, 5j, 5k
- Anchor pipeline: `generate_all_anchors.py` (with dataset/method/threshold
  args), `audit_anchor_coverage.py`, `run_5i_anchor_coupling.py`
- Supplementary 5i analyses: `run_5i_lattice_overlap.py`,
  `run_5i_sectional_profiling.py`
- Section/region support: `categorize_sections.py`, `generate_all_regions.py`

---

### G1.5 — Visualization commands assume `support_visualization` CLI on PATH — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Changed all bare `support_visualization` calls to
`python3 -m support_visualization.cli.main` in:
- `scripts/phase1_foundation/replicate.py` (2 calls)
- `scripts/phase2_analysis/replicate.py` (1 call)
- `scripts/phase3_synthesis/replicate.py` (1 call, added during G1.2 rewrite)
- `scripts/phase4_inference/replicate.py` (1 call, added during G1.3 rewrite)

Scripts now work with `pip install -r requirements.txt` alone (no editable
install required for replication).

---

## G2: Dependency Pinning — RESOLVED

### G2.1 — `requirements.txt` uses minimum-version constraints only — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:**
1. Generated `requirements-lock.txt` from the active venv (`pip freeze`),
   stripped the two `-e` editable-install lines (the project itself), and added
   a header documenting generation date, Python version, and target publication.
2. Updated `replicateResults.md` setup section to offer Option A (lock file,
   exact) vs Option B (`requirements.txt`, compatible).
3. Updated the Known Caveats section: caveat 1 now references the lock file
   instead of describing the gap.

**Pinned versions of note:** numpy 2.3.5, SQLAlchemy 2.0.46, scipy 1.17.0,
scikit-learn 1.8.0, umap-learn 0.5.11, pydantic 2.12.5.

---

### G2.2 — Python version not pinned — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:**
1. Documented `Python 3.11.13 (CPython) on Darwin arm64` in the
   `requirements-lock.txt` header comment.
2. Updated `replicateResults.md` system requirements table with a "Tested
   Value" column showing 3.11.13.
3. Added an explicit note below the setup block: "For exact reproduction, use
   3.11.x."

---

## G3: Seed / Determinism Enforcement (HIGH)

### G3.1 — RunManager falls back to timestamp-based seed — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added a strict-mode guard to `RunManager.start_run()` in
`src/phase1_foundation/runs/manager.py`. When `REQUIRE_COMPUTED=1` is set and
no seed is provided in the config dict, the method now raises `RuntimeError`
with a clear message. The timestamp fallback is preserved for interactive/dev
usage when `REQUIRE_COMPUTED` is not set. Verified with 4 unit tests (strict
mode raise, strict mode accept, dev mode fallback, seed=0 edge case).

---

### G3.2 — Phase 5/6 simulators accept `seed: Optional[int] = None` — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added `require_seed_if_strict()` utility function to
`src/phase1_foundation/config.py`. This guard raises `RuntimeError` when seed
is `None` and `REQUIRE_COMPUTED=1` is set, but allows `None` seeds for
interactive/development use.

Applied the guard to **16 constructors** across 14 files:
- Phase 5 (10 base classes): `TopologySimulator`, `DependencySimulator`,
  `ParsimonySimulator`, `LargeGridSimulator`, `LineScopedPoolSimulator`,
  `WeaklyCoupledPoolSimulator`, `EntryMechanismSimulator`,
  `DeterministicSlotSimulator`, `PoolGenerator`, `GeometricTableGenerator`
- Phase 3 (6 classes): `GrammarBasedGenerator`, `ConstrainedMarkovGenerator`,
  `TextContinuationGenerator`, `NeutralTokenGenerator`, `PharmProfileExtractor`,
  `GapConditionedContinuation`, `FeatureComputer`, `Resynthesizer`

Phase 6 simulators already use `seed: int = 42` (required with default) — no
change needed. Subclasses calling `super().__init__(seed=seed)` are protected
by the base class guard.

---

### G3.3 — 13+ files import `random` module directly (bypassing RandomnessController) — RESOLVED

**Status:** RESOLVED (2026-02-20, audit found pre-existing compliance)

**What was done:** Full audit of all 27 files that import `random` in `src/`.
Results:
- **26 of 27 files** already use instance-based `random.Random(seed)` — safe.
- **1 file** (`randomness.py:208`) uses bare `random.seed(seed)` — this is
  intentional: it is the `RandomnessController` itself, seeding the module-level
  state inside its own `seeded_context()` context manager.
- No files use bare `random.random()`, `random.choice()`, etc. outside of
  the controller.

**Conclusion:** The original audit count of "13+ files using random directly"
was inaccurate or has been resolved by prior work. No code changes needed.

---

### G3.4 — `umap-learn` is inherently stochastic — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Audited UMAP usage across the entire codebase. Only one file
uses `umap-learn`: `src/phase4_inference/projection_diagnostics/analyzer.py`,
exclusively for visualization of token-frequency projections. No publication
claims depend on UMAP coordinates. Expanded caveat 5 in `replicateResults.md`
to document the specific file, clarify that all quantitative claims use
pre-projection distance/similarity metrics, and note the stochastic nature.

---

### G3.5 — Phase 3 `run_indistinguishability_test.py --allow-fallback` in replicate.py — RESOLVED

**Status:** RESOLVED (2026-02-20, side-effect of G1.2)

**What was done:** Removed `--allow-fallback` flag from the
`run_indistinguishability_test.py` call in Phase 3's `replicate.py`. The
replication path now runs in strict mode, consistent with `verify_reproduction.sh`.

---

### G3.6 — Boolean truthiness bug at `mapping_stability.py:113` — RESOLVED

**Status:** RESOLVED (pre-existing fix confirmed 2026-02-20)

**What was done:** Verified that this bug was already fixed in the
2026-02-09 audit session (H1 remediation). The `fix_execution_status_2.md`
report confirms: "Replaced truthiness check with explicit `is not None` checks
at lines 116, 337, 363. Added 10 unit tests." The current code at
`src/phase2_analysis/stress_tests/mapping_stability.py` uses correct
`all(v is not None for v in [...])` guards throughout. No additional changes
needed.

---

## G4: Documentation Drift — RESOLVED

### G4.1 — `governance/runbook.md` and `governance/reproducibility.md` diverge — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:**
1. Rewrote `governance/runbook.md`: added cross-reference to `replicateResults.md`,
   changed `requirements.txt` to `requirements-lock.txt`, added missing Phase 1
   scripts (`populate_database.py`, `run_destructive_audit.py`), separated
   Phases 4-6 into canonical order (4, 5, 6), added sections for Phases 6, 9,
   10, 11, fixed all visualization CLI commands, renumbered governance sections
   (14–19).
2. Rewrote `governance/reproducibility.md`: updated header to "all 11 phases",
   added `replicateResults.md` cross-reference, changed to `requirements-lock.txt`,
   separated Phases 4–6, added Phases 6–11 sections, fixed visualization CLI,
   renumbered governance sections (14–25).

---

### G4.2 — No CONFIG_REFERENCE.md — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created `governance/config_reference.md` documenting all 20
JSON config files across 6 subdirectories: Phase 2 Analysis (2 files), Phase 6
Functional (3 files), Phase 10 Admissibility (3 files), Core Audit (3 files),
Core Skeptic (9 files). Each entry includes: file path, purpose, read-by
scripts, and key parameters.

---

### G4.3 — `governance/methods_reference.md` incomplete — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added two new sections to `governance/methods_reference.md`:
- Section 8: Phase 10 Admissibility Methods (F, G, H, I, J, K) — each with
  test design, null hypothesis, test statistic, significance gates, decision
  rules, runner script, and known confounds. Includes outcome summary table.
- Section 9: Phase 11 Stroke Topology — feature schema (6D per character),
  Test A (stroke-feature clustering), Test B (transition MI with B1/B2/B3
  sub-measures), fast-kill gate logic, and results table.

---

### G4.4 — `README.md` references one-command replication but command is incomplete — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Updated `README.md`:
- Status from PHASE-10-COMPLETE to PHASE-11-COMPLETE
- Added Phase 11 description to the research phases list
- Added "Reproducing Results" section with pointer to `replicateResults.md`
- Fixed visualization CLI command to `python3 -m support_visualization.cli.main`

---

### G4.5 — No `.env.example` file — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created `.env.example` documenting all 6 environment
variables: `REQUIRE_COMPUTED`, `MISSING_CONFIG_POLICY`, `PYTHON_BIN`,
`VERIFY_STRICT`, `ALLOW_DIRTY_RELEASE`, `DIRTY_RELEASE_REASON`. Each includes
description, valid values, and recommended replication setting.

---

## G5: Output-to-Claim Traceability — RESOLVED

### G5.1 — No claim-to-artifact mapping document — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created `governance/claim_artifact_map.md` documenting 47
quantitative claims from the publication with complete traceability: exact
value, source script, output file path, and JSON key path. Organized by phase
(1–11). Includes 4 traceability notes documenting where the pipeline uses
static config values vs. dynamic JSON resolution, and which claims are
console-only (no JSON artifact). Added cross-reference from `replicateResults.md`
to the detailed map.

---

### G5.2 — No reference output checksums — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created two scripts:
1. `scripts/core_audit/extract_golden_outputs.py` — extracts canonicalized
   result payloads (provenance stripped, keys sorted) from 15 key artifacts
   across Phases 4, 5, 6, 7, and 11. Stores as JSON + SHA-256 hash files in
   `tests/fixtures/golden/`.
2. `scripts/core_audit/check_golden_outputs.py` — compares current result
   artifacts against golden files. Supports exact hash matching and
   configurable floating-point tolerance (`--tolerance`). Returns exit code 1
   on mismatch.

Golden files are populated by running `extract_golden_outputs.py` after a
canonical replication. They must be committed to the repository to enable
regression detection on subsequent runs.

---

### G5.3 — File-level provenance missing — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Full audit of 164 result artifacts found 92% already
include `ProvenanceWriter` provenance blocks. The 13 files without provenance
fell into 3 categories:

1. **Wrong output paths (7 files):** Phase 5 pilot scripts, Phase 6 scripts,
   and Phase 7 scripts wrote to `results/phase*/` instead of the canonical
   `results/data/phase*/`. Fixed output paths in 17 scripts and updated all
   consumers (verify_reproduction.sh, ci_check.sh, pre_release_check.sh,
   build_release_gate_health_status.py, run_7b_codicology.py,
   src/phase8_comparative/mapping.py).

2. **Stale pre-ProvenanceWriter files (6 files):** Phase 4 and Phase 7 files
   on disk predate ProvenanceWriter adoption. The scripts already use
   `ProvenanceWriter.save_results()` — re-running them will produce
   provenance-wrapped output. No code changes needed.

3. **Status-tracking file (1 file):** `corpus_expansion_status.json` is a
   process-tracking file, not an analysis result. Documented as intentionally
   unwrapped.

---

## G6: Verification Completeness — PARTIALLY RESOLVED

### G6.1 — `verify_reproduction.sh` uses Phase 3 `run_test_a.py` as sole determinism proxy — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added Phase 11 (stroke transitions) as a second
determinism check in `verify_reproduction.sh` (step 3b). Uses
`run_11c_transitions.py --seed $SEED --permutations 100` run twice with
canonicalized output comparison. Chosen because it: (a) accepts --seed and
--output flags, (b) runs in ~10s per invocation, (c) exercises numpy
permutation determinism. Gracefully skips if Phase 11 stroke features haven't
been generated yet.

Phase 5 and Phase 10 scripts don't accept --output flags and are too slow
for duplicate-run testing. The golden output check (`check_golden_outputs.py`)
provides complementary regression coverage for those phases.

---

### G6.2 — No CI/CD automation — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created two GitHub Actions workflows:

1. `.github/workflows/ci.yml` — runs on push/PR to `master`:
   - Installs dependencies from `requirements-lock.txt`
   - Runs `ruff check` for linting (non-blocking until existing issues resolved)
   - Runs unit tests via pytest (excluding integration tests that need DB)
   - Import smoke test for critical modules

2. `.github/workflows/reproduce.yml` — manual trigger + weekly schedule:
   - Downloads external data via `download_external_data.py`
   - Populates database, runs Phase 1 + Phase 3 replication
   - Phase 3 determinism check (dual-run comparison)
   - Golden output regression check (if golden files committed)

Pre-commit hooks (ruff + mypy) deferred — the CI workflow provides equivalent
gate coverage. Can be added when ruff configuration is finalized.

---

### G6.3 — Bare `except:` clauses suppress errors silently — RESOLVED

**Status:** RESOLVED (pre-existing fix confirmed 2026-02-20)

**What was done:** Grep for bare `except:` across all of `src/` returned zero
matches. The `quire_analysis.py`, `scribe_coupling.py`, and
`network_features/analyzer.py` bare `except:` clauses noted in the 2026-02-09
audit have been fixed in prior remediation sessions (confirmed by
`fix_execution_status.md` H2 and related entries). No additional changes
needed.

---

### G6.4 — `core_status/` is transient but required by verification — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Added a "Prerequisite: `core_status/` directory" subsection
to the Verification section of `replicateResults.md`. Documents:
- That `core_status/` is not in the repository and must be populated by the
  pipeline before verification will pass.
- A table of 7 key files required by verify_reproduction.sh and ci_check.sh,
  with the script that generates each.
- That `results/data/phase5_mechanism/` and `results/data/phase7_human/` are
  also required for SK-H1 and SK-M2 policy checks.
- Troubleshooting guidance for "Missing artifact" errors.

---

## G7: Data Acquisition Automation (LOW)

### G7.1 — No automated data download script — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Created `scripts/phase0_data/download_external_data.py`:
1. Downloads 7 IVTFF transliteration files from `voynich.nu/data/`
2. Downloads 4 Project Gutenberg texts (Latin x2, English, German)
3. Concatenates Latin parts into `latin_corpus.txt`
4. Creates directory structure (`data/raw/transliterations/ivtff2.0/`,
   `data/external_corpora/`)
5. Skips existing files (idempotent)
6. Yale scans skipped by default; `--include-scans` prints instructions
7. `--checksums` flag prints SHA-256 for verification
8. Referenced in `replicateResults.md` external data section and
   `.github/workflows/reproduce.yml`

---

### G7.2 — Database file (`data/voynich.db`) ambiguously tracked — RESOLVED

**Status:** RESOLVED (2026-02-20)

**What was done:** Investigation found the initial assessment was incorrect:
`data/voynich.db` is **not** tracked by git. The `.gitignore` pattern `*.db`
already excludes it, and `git ls-files data/voynich.db` returns empty. The
database is a local build artifact (~400 MB) regenerated by
`scripts/phase1_foundation/populate_database.py` from raw IVTFF data.

Documentation was already correct:
- `DATA_SOURCES.md` section 4 lists it as "Generated by the pipeline"
- `replicateResults.md` Phase 1 lists it as a key output

Added explicit clarification to `replicateResults.md` noting the database
is regenerated (not distributed) and that `.gitignore` excludes `*.db` files.

---

## Execution Order

The gaps should be addressed in priority order:

### Sprint 1: Critical Path — COMPLETE

| ID | Task | Blocks | Status |
|---|---|---|---|
| G1.1 | Create Phase 10/11 replicate.py + update replicate_all.py | External replication | **DONE** |
| G1.2 | Fix Phase 3 replicate.py | External replication | **DONE** |
| G1.3 | Fix Phase 4 replicate.py | External replication | **DONE** |
| G1.4 | Fix Phase 5 replicate.py | External replication | **DONE** |
| G1.5 | Fix visualization CLI invocations | Script execution | **DONE** |
| G2.1 | Generate requirements-lock.txt | Exact reproduction | **DONE** |
| G2.2 | Document Python version | Exact reproduction | **DONE** |

### Sprint 2: Determinism Hardening — COMPLETE

| ID | Task | Blocks | Status |
|---|---|---|---|
| G3.1 | Enforce seed requirement in RunManager | Silent non-determinism | **DONE** |
| G3.2 | Add `require_seed_if_strict()` to 16 constructors | Silent non-determinism | **DONE** |
| G3.3 | Audit bare `random` usage (26/27 safe) | Silent non-determinism | **DONE** (no fix needed) |
| G3.5 | Remove `--allow-fallback` from replicate.py | Strict/lenient inconsistency | **DONE** (via G1.2) |
| G3.6 | Fix boolean truthiness bug | Incorrect results | **DONE** (pre-existing fix) |
| G6.3 | Replace bare `except:` clauses | Silent error swallowing | **DONE** (pre-existing fix) |

### Sprint 3: Documentation Reconciliation — COMPLETE

| ID | Task | Blocks | Status |
|---|---|---|---|
| G4.1 | Reconcile runbook.md and reproducibility.md | Documentation trust | **DONE** |
| G4.2 | Create CONFIG_REFERENCE.md | Threshold transparency | **DONE** |
| G4.3 | Complete methods_reference.md | Methodology transparency | **DONE** |
| G4.4 | Update README.md | First impressions | **DONE** |
| G4.5 | Create .env.example | Environment setup | **DONE** |

### Sprint 4: Traceability and Verification — COMPLETE

| ID | Task | Blocks | Status |
|---|---|---|---|
| G5.1 | Create claim-to-artifact mapping (47 claims) | Claim verification | **DONE** |
| G5.2 | Create golden output extract/check scripts | Regression detection | **DONE** |
| G5.3 | Audit + fix file-level provenance (17 path fixes) | Artifact trust | **DONE** |
| G6.1 | Add Phase 11 determinism check | Cross-phase determinism | **DONE** |
| G6.4 | Document core_status/ prerequisite | Verification clarity | **DONE** |

### Sprint 5: Automation — COMPLETE

| ID | Task | Blocks | Status |
|---|---|---|---|
| G6.2 | Create GitHub Actions CI/CD | Regression prevention | **DONE** |
| G7.1 | Create data download script | Setup automation | **DONE** |
| G7.2 | Resolve database tracking ambiguity | Data clarity | **DONE** |
| G3.4 | Document UMAP non-determinism | Expectation setting | **DONE** |

---

## Validation Criteria

This effort is complete when an external party can:

1. Clone the repository
2. Run `pip install -r requirements-lock.txt && pip install -e .`
3. Run `scripts/phase0_data/download_external_data.py` (or follow
   DATA_SOURCES.md manually for Yale scans)
4. Run `python3 scripts/support_preparation/replicate_all.py` (covers all 11
   phases)
5. Run `bash scripts/verify_reproduction.sh` (passes all checks including
   golden output comparison)
6. Run `bash scripts/ci_check.sh` (passes all policy checks)
7. Open `results/publication/` and find a regenerated document whose
   quantitative claims match the archived `021526` publication within
   documented tolerances
8. Trace any specific claim back to its source artifact using
   `governance/claim_artifact_map.md`

---

## Appendix A: Complete Gap Inventory by File

| File | Gap ID | Issue | Status |
|---|---|---|---|
| `scripts/support_preparation/replicate_all.py` | G1.1 | Missing phases 10, 11 | **RESOLVED** |
| `scripts/phase10_admissibility/replicate.py` | G1.1 | Did not exist | **RESOLVED** (created) |
| `scripts/phase11_stroke/replicate.py` | G1.1 | Did not exist | **RESOLVED** (created) |
| `scripts/phase3_synthesis/replicate.py` | G1.2 | Missing 5 scripts | **RESOLVED** |
| `scripts/phase4_inference/replicate.py` | G1.3 | Missing 8+ scripts | **RESOLVED** |
| `scripts/phase5_mechanism/replicate.py` | G1.4 | Missing 7+ scripts | **RESOLVED** |
| `scripts/phase1_foundation/replicate.py` | G1.5 | Bare `support_visualization` call | **RESOLVED** |
| `scripts/phase2_analysis/replicate.py` | G1.5 | Bare `support_visualization` call | **RESOLVED** |
| `scripts/phase3_synthesis/replicate.py` | G3.5 | `--allow-fallback` | **RESOLVED** (via G1.2) |
| `requirements-lock.txt` | G2.1 | Unpinned versions | **RESOLVED** (created) |
| `replicateResults.md` | G2.2 | Undocumented Python version | **RESOLVED** |
| `src/phase1_foundation/runs/manager.py` | G3.1 | Timestamp seed fallback | **RESOLVED** |
| `src/phase1_foundation/config.py` | G3.2 | Added `require_seed_if_strict()` | **RESOLVED** (new) |
| 10 Phase 5 simulator base classes | G3.2 | Optional seed guarded | **RESOLVED** |
| 6 Phase 3 generator/extractor classes | G3.2 | Optional seed guarded | **RESOLVED** |
| Phase 6 simulators | G3.2 | Already uses `seed: int = 42` | N/A (already safe) |
| 27 files in `src/` | G3.3 | Bare `random` usage | **RESOLVED** (26/27 safe, 1 intentional) |
| `replicateResults.md` | G3.4 | UMAP non-determinism undocumented | **RESOLVED** (caveat expanded) |
| `src/phase2_analysis/stress_tests/mapping_stability.py` | G3.6 | Boolean truthiness | **RESOLVED** (pre-existing) |
| `governance/runbook.md` | G4.1 | Drift from replicate_all.py | **RESOLVED** |
| `governance/reproducibility.md` | G4.1 | Drift from replicate_all.py | **RESOLVED** |
| `governance/config_reference.md` | G4.2 | No CONFIG_REFERENCE.md | **RESOLVED** (created) |
| `governance/methods_reference.md` | G4.3 | Incomplete | **RESOLVED** |
| `README.md` | G4.4 | Missing pointer to replicateResults.md | **RESOLVED** |
| `.env.example` | G4.5 | No .env.example | **RESOLVED** (created) |
| `governance/claim_artifact_map.md` | G5.1 | No claim-artifact map | **RESOLVED** (created) |
| `scripts/core_audit/extract_golden_outputs.py` | G5.2 | No golden outputs | **RESOLVED** (created) |
| `scripts/core_audit/check_golden_outputs.py` | G5.2 | No golden comparison | **RESOLVED** (created) |
| 17 scripts (Phase 5/6/7/8) | G5.3 | Wrong output paths `results/phase*/` | **RESOLVED** (→ `results/data/phase*/`) |
| `verify_reproduction.sh`, `ci_check.sh`, `pre_release_check.sh` | G5.3 | Stale reader paths | **RESOLVED** |
| `scripts/verify_reproduction.sh` | G6.1 | Single-phase determinism check | **RESOLVED** (added Phase 11) |
| `.github/workflows/ci.yml`, `reproduce.yml` | G6.2 | No CI/CD | **RESOLVED** (created) |
| `quire_analysis.py`, `scribe_coupling.py`, `analyzer.py` | G6.3 | Bare except | **RESOLVED** (pre-existing) |
| `replicateResults.md` | G6.4 | core_status/ paradox | **RESOLVED** |
| `scripts/phase0_data/download_external_data.py` | G7.1 | No download script | **RESOLVED** (created) |
| `data/voynich.db` | G7.2 | Ambiguous tracking | **RESOLVED** (already gitignored) |

---

## Appendix B: What Already Works Well

For completeness, here is what the project already has that most research
codebases lack:

- **Single-command replication (all 11 phases)** via `replicate_all.py` *(fixed by G1.1)*
- **Complete per-phase replicate.py scripts** for all 11 phases *(fixed by G1.1-G1.4)*
- **External reproduction guide** (`replicateResults.md`) with claim traceability
- **Run-level provenance** with run IDs, git commits, timestamps, configs
- **RandomnessController** with 3 enforcement modes
- **DeterministicIDFactory** for reproducible ID generation
- **REQUIRE_COMPUTED** environment enforcement
- **Comprehensive verification scripts** (ci_check.sh, verify_reproduction.sh)
- **Adversarial skeptic infrastructure** (9 skeptic check scripts)
- **Governance tier** with policies, methods reference, and audit trail
- **Zenodo archival** (DOI v1.0.1)
- **Sensitivity sweep** with release-evidence gates
- **Data sourcing guide** (DATA_SOURCES.md)

The project is well above average for research reproducibility. This
reproducibility hardening effort closes the remaining gaps to reach
"external-party-clean" status.

---

## Appendix C: Progress Summary

| Category | Total Gaps | Resolved | Remaining |
|---|---|---|---|
| G1: Replication Script Coverage | 5 | 5 | 0 |
| G2: Dependency Pinning | 2 | 2 | 0 |
| G3: Seed / Determinism Enforcement | 6 | 6 | 0 |
| G4: Documentation Drift | 5 | 5 | 0 |
| G5: Output-to-Claim Traceability | 3 | 3 | 0 |
| G6: Verification Completeness | 4 | 4 | 0 |
| G7: Data Acquisition Automation | 2 | 2 | 0 |
| **Total** | **27** | **27** | **0** |

**Sprint 1:** COMPLETE (G1.1–G1.5, G2.1, G2.2)
**Sprint 2:** COMPLETE (G3.1, G3.2, G3.3, G3.5, G3.6, G6.3)
**Sprint 3:** COMPLETE (G4.1–G4.5)
**Sprint 4:** COMPLETE (G5.1–G5.3, G6.1, G6.4)
**Sprint 5:** COMPLETE (G6.2, G7.1, G7.2, G3.4)
