# Comprehensive Code Audit Report

**Date:** 2026-02-09
**Project:** Voynich Manuscript Structural Admissibility Program
**Scope:** Full codebase audit per CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md
**Objective:** Capture and document gaps, issues, bugs, false assumptions, and risks. No fixes applied.

---

## Executive Summary

This audit examined the entire codebase across all five phases defined in the playbook. The codebase demonstrates strong architectural foundations (clean separation of concerns, comprehensive provenance infrastructure, symmetric preprocessing) but reveals significant issues in randomness control, hardcoded thresholds, silent defaults, documentation gaps, and logging discipline.

### Severity Distribution

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 14 | Could change conclusions |
| **High** | 31 | Could materially alter numbers |
| **Medium** | 42 | Correctness or clarity risk |
| **Low** | 18 | Style or maintainability |

### Top 5 Risks

1. **Unseeded randomness in core synthesis and mechanism simulators** (Critical) - 13+ files use `random` module without seed control
2. **150+ hardcoded thresholds without documented justification** (Critical) - Perturbation levels, failure boundaries, model weights
3. **Silent fallback to plausible-looking default values** (High) - NaN propagation, 0.0/0.5 returns masking missing data
4. **No CONFIG_REFERENCE.md, governance/METHODS_REFERENCE.md, or governance/REPRODUCIBILITY.md** (High) - External reader cannot modify, understand, or reproduce
5. **Boolean truthiness bug in mapping_stability.py** (High) - `min(a, b, c) if (a and b and c)` fails when any value is 0.0

---

## Phase 0: Inventory and Orientation (COMPLETE - Prior Run)

See `PHASE_0_INVENTORY.md` for full entry point and file inventory.

**Summary:** 40+ entry points identified across 7 script directories. Source organized in `src/` with clear submodules. No notebooks found (all logic importable).

---

## Phase 1: Results Integrity Audit

### 1.1 Placeholder and Temporary Code (COMPLETE - Prior Run)

349 matches for TODO/FIXME/HACK/TEMP/DEBUG. Key risks:
- **DEBUG print in production:** `src/phase1_foundation/anchors/engine.py:77` - `print(f"DEBUG: ...")` left in anchor computation
- **TODO in baseline assessment:** `scripts/phase3_synthesis/run_baseline_assessment.py` - "Info Density and Locality require control datasets"
- **Hypothesis manager:** `src/phase1_foundation/hypotheses/manager.py` - "Instantiate temporarily to get ID?"

Most "TEMP" matches are false positives (temporal, template, temperature).

### 1.2 Hardcoded Values and Magic Numbers

**150+ hardcoded values identified.** Organized by risk category:

#### Critical (52 values) - Could Change Conclusions

**Perturbation Battery (src/phase2_analysis/models/disconfirmation.py:40-59)**
| Perturbation Type | Strength Levels | Failure Threshold |
|---|---|---|
| Segmentation | [0.05, 0.10, 0.15] | 0.6 |
| Ordering | [0.10, 0.20, 0.30] | 0.6 |
| Omission | [0.05, 0.10, 0.20] | 0.7 |
| Anchor Disruption | [0.10, 0.25, 0.50] | 0.5 |

These define the entire perturbation testing matrix. Strength levels appear arbitrarily spaced (linear vs doubling). No documented justification for why these specific values.

**Hypothesis Falsification Thresholds (src/phase1_foundation/hypotheses/destructive.py)**
| Hypothesis | Falsified If | Weakly Supported If |
|---|---|---|
| FixedGlyphIdentity | collapse > 0.20 at 5% perturbation | collapse > 0.10 |
| WordBoundaryStability | agreement < 0.70 | agreement < 0.80 |
| DiagramTextAlignment | z-score < 1.0 | z-score < 2.0 |
| AnchorDisruption | survival < 0.50 at 10% perturbation | survival < 0.70 |

**Model Sensitivity Weights** - Each model class has different hardcoded sensitivity profiles:

| Model | Segmentation | Ordering | Omission | Anchor |
|---|---|---|---|---|
| Procedural Generation | 0.20 | 0.30 | 0.25 | 0.15 |
| Glyptic System | 0.35 | 0.40 | 0.35 | 0.20 |
| High-Info Density | 0.35 | 0.35 | 0.45 | 0.30 |
| Adjacency Grammar | 0.35 | 0.25 | 0.40 | 0.70 |
| Container Grammar | 0.30 | 0.20 | 0.45 | 0.60 |
| Diagram Annotation | 0.25 | 0.20 | 0.35 | 0.80 |

These weights critically affect perturbation outcomes. No empirical justification documented.

**Evaluation Weights (src/phase2_analysis/models/evaluation.py:113-118)**
- accuracy: 0.30, robustness: 0.25, scope: 0.20, parsimony: 0.10, falsifiability: 0.15
- Determine final model ranking. Tie-breaking threshold: 0.05.

**Capacity Bounding Constants (src/phase2_analysis/anomaly/capacity_bounding.py:38-42)**
- OBSERVED_INFO_DENSITY_Z = 4.0
- OBSERVED_LOCALITY_MIN = 2, MAX = 4
- OBSERVED_REPETITION_RATE = 0.20
- OBSERVED_VOCABULARY_SIZE = 8000

These form the basis for all capacity calculations.

**Stability Baselines (src/phase2_analysis/anomaly/stability_analysis.py:38-46)**
- BASELINE_INFO_DENSITY = 4.0, LOCALITY = 3.0, ROBUSTNESS = 0.70
- CONTROL_INFO_DENSITY_MEAN = 1.2, STD = 0.5
- CONTROL_LOCALITY_MEAN = 8.0, STD = 2.0

**Synthesis Constraints (src/phase3_synthesis/interface.py:158-167)**
- information_density_tolerance = 0.5
- positional_entropy_tolerance = 0.2
- repetition_rate_tolerance = 0.05
- locality_window = (2, 4)
- min_perturbation_robustness = 0.50
- max_novel_tokens = 0.10

#### High (64 values) - Could Alter Numbers

- **Iteration limits:** MAX_PAGES_PER_TEST=50, MAX_LINES_PER_PAGE=100, MAX_TOKENS_ANALYZED=10000 (duplicated across 3 stress test files)
- **Mapping stability thresholds:** 7 thresholds (0.3-0.7) for constructed_system, visual_grammar, hybrid_system model classification
- **Perturbation scaling:** Normalization divisors 0.5, 0.35, 0.40 and multiplier 2 in perturbation.py
- **Text generation:** 0.4 probability of positional bias; scrambled control metrics (locality=3.0, repetition=0.10, entropy=0.80)
- **Profile extraction defaults:** jar count 4, lines 24, words 72 as fallback values
- **Indistinguishability thresholds:** equivalence_threshold=0.30, improvement_threshold=0.10

#### Medium (28 values) and Low (8 values)

Feature discrimination ranges, fallback defaults, metric computations, and acknowledged arbitrary thresholds.

### 1.3 Silent Defaults and Implicit Behavior

**48 significant instances identified.**

#### Critical (2)
- **Bare `except:` clauses** in `src/phase7_human/quire_analysis.py:29`, `src/phase7_human/scribe_coupling.py:32`, `src/phase4_inference/network_features/analyzer.py:51` - catch all exceptions including SystemExit, silently return default values (0, "Unknown", 0.0)

#### High (10)
- **src/phase1_foundation/metrics/library.py:169,208** - `except Exception: continue` silently drops corrupted embeddings from ClusterTightness calculation
- **src/phase3_synthesis/refinement/feature_discovery.py:92-697** - 12+ functions return `random.uniform(...)` for scrambled pages or hardcoded defaults when data is None, with no indication to caller
- **src/phase1_foundation/metrics/library.py:64-65** - Silent fallback from TranscriptionTokenRecord to WordAlignmentRecord without warning
- **src/phase2_analysis/models/perturbation.py:119-135** - `.get()` with defaults (0, 1) creates phantom bounding boxes when coordinates missing
- **src/phase3_synthesis/profile_extractor.py:82-83** - `store is None` silently returns simulated profile
- **src/phase3_synthesis/refinement/feature_discovery.py:101** - Returns `float("nan")` which propagates silently through calculations (NaN comparisons always False)
- **src/phase1_foundation/hypotheses/destructive.py:440** - `std_control` defaults to 0.1 if variance is 0 (arbitrary smoothing factor)

#### Medium (10)
- Division-by-zero returns 0.0 (indistinguishable from actual zero result)
- Implicit coordinate clipping to [0,1] without warning
- Max entropy (1.0) returned for missing data (indistinguishable from truly random)
- Array shape compatibility assumed without validation
- Dictionary `.get()` cascading defaults in boundary calculations

### 1.4 Randomness and Non-Determinism

**27+ files use randomness. 13+ are UNSEEDED.**

#### Randomness Infrastructure

A `RandomnessController` exists at `src/phase1_foundation/core/randomness.py` with three modes (FORBIDDEN, SEEDED, UNRESTRICTED) and enforcement decorators. However, adoption is inconsistent - most modules don't use it.

#### Critical (Unseeded, impacts core results)

| File | Lines | Issue |
|---|---|---|
| `src/phase3_synthesis/refinement/feature_discovery.py` | 93-697 | 12+ `random.uniform()` calls for feature computation - UNSEEDED |
| `src/phase3_synthesis/generators/grammar_based.py` | 48 | Core text generation uses unseeded `random.choices()` |
| `src/phase3_synthesis/indistinguishability.py` | 132-140 | Scrambled control generation is non-deterministic |

#### High (Unseeded mechanism simulators)

| File | Unseeded Calls | Purpose |
|---|---|---|
| `src/phase5_mechanism/workflow/simulators.py` | 5 | Gaussian sampling, reservoir sampling, drift |
| `src/phase5_mechanism/large_object/simulators.py` | 2 | Grid start position |
| `src/phase5_mechanism/topology_collapse/simulators.py` | 6 | Grid, layered table, DAG, lattice start positions |
| `src/phase5_mechanism/entry_selection/simulators.py` | 5 | Entry point and coupling mechanisms |
| `src/phase5_mechanism/generators/pool_generator.py` | 3 | Pool reuse and drift |
| `src/phase5_mechanism/dependency_scope/simulators.py` | 3 | Dependency scope testing |
| `src/phase5_mechanism/parsimony/simulators.py` | 2 | Parsimony evaluation |

#### Properly Seeded (Good)

| Module | Method | Notes |
|---|---|---|
| Foundation controls (5 files) | `random.seed(seed)` or `random.Random(seed)` | Properly isolated |
| Functional simulators (3 files) | `random.Random(seed)` | Local RNG objects (seed hardcoded to 42) |
| Region embeddings | `np.random.RandomState(seed)` | NumPy best practice |
| Corpus builder | `random.seed(42)` | Fixed seed for shuffled control |

#### Summary

| Category | Seeded | Unseeded |
|---|---|---|
| Control Generators | 5 | 0 |
| Synthesis/Text Gen | 2 | 4 |
| Mechanism Simulators | 0 | 8+ |
| Functional Simulators | 3 | 0 |
| Analysis/Scripts | 2 | 1 |

### 1.5 Circularity and Data Leakage

#### Resolved Issues
- `_run_simulated()`, `_compute_simulated()`, `_calculate_simulated()` methods have been removed (documented in AUDIT.md remediation section 6.1-6.3)
- Hardcoded target values (z=5.68, rep=0.90) removed from baseline assessment script

#### Remaining Methodological Concern (By Design)
- **Generator Matching Circularity:** Phase 3-4 uses Phase 2 metrics as optimization targets. Passing indistinguishability proves generator is "as anomalous" as original, not that mechanism is identical. Documented as methodological observation, not code defect.

#### Residual Code-Level Risks
- **Voynichese token seeds:** `src/phase3_synthesis/profile_extractor.py:626-637` contains hardcoded Voynich-like tokens ("daiin", "chedy", "qokedy") used in fallback path when transcription database unavailable. Could seed biased synthesis.
- **Simulated page data:** Same file contains `SIMULATED_PAGE_DATA` for pharmaceutical section (f88r-f96v) as fallback. Used only when `store is None`.

#### Threshold Independence Assessment
Hypothesis thresholds appear domain-independent:
- 20% collapse at 5% shift is a general stability criterion
- 70-80% agreement thresholds are standard cross-validation practice
- z=2.0 is conventional statistical significance
- No evidence of Voynich-specific tuning found

### 1.6 Control and Baseline Symmetry

#### Symmetric (Good)
- **Data loading:** `DatasetManager.register_dataset()` treats all datasets identically
- **Tokenization:** `EVAParser` applies identical tokenization to all transcription sources
- **Database storage:** All records stored via identical `MetadataStore` methods
- **Analysis iteration limits:** MAX_PAGES_PER_TEST applied uniformly to all datasets
- **Stress tests:** Same code paths for real, control, and synthetic data

#### Minor Asymmetries
- **Empty dataset returns:** `RepetitionRate.calculate()` returns 0.0 for empty datasets - indistinguishable from actual zero repetition
- **Token fallback paths:** `_get_tokens_via_alignments()` may succeed for some datasets and fail for others depending on whether alignment records exist
- **Profile extraction:** Falls back to simulated profile for synthetic data when database empty; Voynich uses real computation
- **Scrambled control generation:** Implementation exists in `src/phase1_foundation/controls/scramblers.py` using `random.Random(seed)` (properly isolated), but mechanism could be better documented

#### Mapping Reference Point
- `src/phase8_comparative/mapping.py:15` hardcodes `target='Voynich'` as reference point for distance calculations - this is by design (comparisons need a reference)

### 1.7 Output Provenance Metadata

#### Run-Level Provenance: COMPREHENSIVE
`src/phase1_foundation/runs/context.py` captures:
- run_id, timestamp_start/end, git_commit, git_dirty, command_line, config, user
- Writes: run.json, config.json, inputs.json, outputs.json, manifest.json
- Environment: Python version, platform, package versions

#### Database-Level Provenance: COMPREHENSIVE
All `add_*` methods accept `run_id`. `MetricResultRecord`, `HypothesisRunRecord`, `ArtifactRecord` all link back to runs.

#### File-Level Provenance: MISSING
**20+ scripts** write JSON results without provenance metadata:
```python
# Common pattern (BAD):
with open("core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json", "w") as f:
    json.dump(findings, f, indent=2)
# Missing: run_id, timestamp, git_commit, config
```

Result files cannot be traced to their generation context without database lookup. This is the single largest provenance gap.

---

## Phase 2: Method Correctness and Internal Consistency

### 2.1 Metric Registry

**Two primary metrics found:**

| Metric | Location | Formula | Fallback |
|---|---|---|---|
| RepetitionRate | library.py:24-117 | `repeated_occurrences / total_tokens` | 0.0 on empty data |
| ClusterTightness | library.py:119-279 | `1.0 / (1.0 + mean_distance)` | 0.5 on error; bbox fallback path |

**Issues Found:**

1. **Dual RepetitionRate formulas (Medium):** Returns both `repetition_rate` (occurrences of multiply-occurring tokens / total) AND `vocabulary_repetition` (1 - unique/total) in the same result. These measure different things but naming doesn't distinguish them. Example: tokens [a,a,b,b,c] -> repetition_rate=0.8, vocabulary_repetition=0.4.

2. **ClusterTightness dual computation paths (Medium):** Computes from embeddings OR bounding boxes with no indication in MetricResult which path was taken. The formulas are semantically different (N-dimensional vs 2-dimensional distance).

3. **Hypothesis outcome string inconsistency (Medium):** Interface documents "NOT_SUPPORTED" but no hypothesis returns it. "INCONCLUSIVE" used but not documented. No enum prevents typos.

### 2.2 Input and Output Contracts

**Boolean Truthiness Bug (HIGH - mapping_stability.py:113):**
```python
overall_stability = min(avg_seg, avg_ord, avg_omit) if (avg_seg and avg_ord and avg_omit) else 0
```
When any stability score is legitimately 0.0, the condition evaluates to False and returns 0 instead of `min(0.5, 0.0, 0.7) = 0.0`. Should use `is not None` checks.

**NaN Propagation (Medium):** `perturbation.py:317` returns `float("nan")` for insufficient data. Consuming code doesn't guard against NaN: `min(1.0, degradation * factor)` propagates NaN silently.

**Missing input validation:** No metric or hypothesis validates that `dataset_id` exists before querying. Returns error details in result dict rather than raising exceptions.

**Inconsistent empty-list protection:** Some functions check `if items` before division, others don't. `destructive.py:306` could crash on empty `agreement_rates` list.

### 2.3 Canonical Preprocessing Pipeline

**Assessment: GOOD.** A single preprocessing path exists via `EVAParser` and `DatasetManager`. All analysis code queries from the same database tables. No duplicate tokenization implementations found.

**Minor issue:** `line_index` vs `line_number` naming inconsistency in query code suggests incomplete refactoring (`profile_extractor.py:592` has comment "Changed from line_number to line_index").

### 2.4 Unit-Level Validation

**Test infrastructure exists** at `/tests/` with proper directory structure matching `/src/`. An acceptance test exists at `scripts/phase1_foundation/acceptance_test.py`.

**Gaps:**
- No boundary case tests found (empty input, single token, degenerate cases)
- No invariance tests (renaming tokens should not change certain metrics)
- No documentation of what the acceptance test validates

### 2.5 End-to-End Sanity Checks

**No fixture-based regression testing found.** No locked expected outputs. No mechanism to detect accidental drift in results. The acceptance test exists but doesn't compare against known-good values.

---

## Phase 3: Structural and Naming Consistency

### 3.1 Directory and File Structure

**Assessment: GOOD.** Clear separation between:
- Analysis logic (`src/`)
- Execution scripts (`scripts/`)
- Data assets (`data/`)
- Documentation (`governance/`, `planning/`, `results/`)
- Tests (`tests/`)

No Jupyter notebooks found. All logic is importable from `src/` modules.

**Issues:**
- **Multiple pilot scripts:** 15 scripts in `scripts/phase5_mechanism/` with naming like `run_5b_pilot.py` through `run_5k_pilot.py`. These are sequential experiments, not duplicates, but naming convention is unclear to outsiders.
- **Orphaned planning docs:** Planning documents for Phases 5c and 5f have typo in filename ("EXUECTION" instead of "EXECUTION")

### 3.2 Terminology Discipline

**Token vs Word (HIGH inconsistency):**
- `phase1_foundation/cli/main.py:218` - `query_token(token: str)` for transcription units
- `phase1_foundation/cli/main.py:236` - `query_word(word_id: str)` for image units
- These are correctly distinct concepts but the distinction is not enforced or documented

**Glyph vs Symbol (MEDIUM):**
- `GlyphCandidateRecord` = image-level unit
- `GlyphAlignmentRecord.symbol` = transcription symbol stored as field of glyph record
- "Symbol" used in glyph context without clarification

**Line/Page/Section:** CONSISTENT. Well-defined hierarchy used uniformly.

**Generator/Artifact:** CONSISTENT. Clear class hierarchy.

**Reset:** Rare usage (4 occurrences, 2 files), consistent where used.

### 3.3 Logging and Error Clarity

**Assessment: POOR.**

**Only 2 files** in `src/` use the `logging` module properly (feature_discovery.py, perturbation.py). 118 Python files exist in `src/`.

**Ad hoc print statements:**
| File | Line | Content | Severity |
|---|---|---|---|
| `phase1_foundation/anchors/engine.py` | 77 | `print(f"DEBUG: ...")` | HIGH - Debug output in production |
| `phase1_foundation/qc/reporting.py` | 8,16 | `print(f"Generating...")` | LOW - Stubs |
| `phase1_foundation/qc/anomalies.py` | 25 | `print(f"WARNING: ...")` | MEDIUM |
| `phase1_foundation/core/dataset.py` | 66 | `print(f"Skipping...")` | MEDIUM |
| `phase1_foundation/phase2_analysis/sensitivity.py` | 34 | `print(f"Error...")` | MEDIUM |

**Bare except clauses:** 3 files (`quire_analysis.py:29`, `scribe_coupling.py:32`, `network_features/analyzer.py:51`)

**Silent exception handling:** `dataset.py:80` - `except Exception: pass` for image dimension loading

---

## Phase 4: Documentation for External Readers

### 4.1 README Assessment

| Criterion | Status |
|---|---|
| Project purpose | PRESENT |
| Scope and limitations | PRESENT |
| High-level pipeline overview | PARTIAL - lacks phase progression detail |
| How to run analysis | INCOMPLETE - RUNBOOK covers Phases 2-3 only |
| Expected outputs | INCOMPLETE - no output interpretation guide |
| Runtime expectations | MISSING |
| Dependencies and installation | PRESENT |

**Severity: MODERATE** - Users understand the "why" but struggle with the "how."

### 4.2 Methods Documentation

**No governance/METHODS_REFERENCE.md exists.**

`governance/METRICS.md` provides high-level metric definitions (4 metrics). Code has inline docstrings. But:
- No unified document explaining all methods
- No documentation of what metrics do NOT measure
- No confound documentation
- Fragmented across code files

**Severity: HIGH** - Reader can compute metrics but cannot confidently explain what they mean.

### 4.3 Configuration Documentation

**No CONFIG_REFERENCE.md exists.**

Parameters scattered across 5+ files. No unified inventory. No rationale for defaults. No sensitivity analysis documentation. Feature flags in `config.py` have 5 categories with no explanation.

**Severity: CRITICAL** - External user cannot modify configuration with confidence.

### 4.4 Reproducibility Instructions

**No governance/REPRODUCIBILITY.md exists.**

`governance/RUNBOOK.md` is skeletal (41 lines), covers Phases 2-3 only. No end-to-end reproduction script. No expected output specifications. No failure mode guide. No minimal reproducible example. No verification checklist.

**Severity: HIGH** - Infrastructure exists but is not documented cohesively.

---

## Phase 5: External-Critique Simulation

### 5.1 Skeptical Reader Checklist

**Q: Where are assumptions stated?**
A: `planning/phase1_foundation/PRINCIPLES_AND_NONGOALS.md` states core assumptions. However, 150+ hardcoded thresholds are not documented as assumptions. A skeptical reader would question every threshold in Phase 1.2 above.

**Q: Which parameters matter most?**
A: The perturbation battery (disconfirmation.py:40-59) and model sensitivity weights (constructed_system.py, visual_grammar.py) are the most consequential. Changing failure thresholds from 0.6 to 0.4 could flip model pass/fail verdicts. No sensitivity analysis exists to quantify this.

**Q: What happens if they change?**
A: Unknown. No sensitivity sweep has been performed or documented. The `phase1_foundation/phase2_analysis/sensitivity.py` module exists but has a print-based error handler, suggesting it may not be production-ready.

**Q: How do we know this is not tuned?**
A: The prior audit (AUDIT.md) addressed the most egregious cases: simulated logic removal, hardcoded target removal. Hypothesis thresholds use conventional statistical boundaries (z=2.0, 70-80% agreement). However, model sensitivity weights (0.15-0.80) have no documented justification and appear hand-selected. The evaluation dimension weights (0.30, 0.25, 0.20, 0.10, 0.15) are particularly vulnerable to this criticism.

**Q: What evidence is negative or null?**
A: The framework reports "FALSIFIED" and "WEAKLY_SUPPORTED" outcomes alongside "SUPPORTED." The disconfirmation framework explicitly tests for model failure. However, negative results are not prominently documented in any summary report - a reader must trace through individual hypothesis results.

### 5.2 Clean-Room Re-Execution Assessment

**Cannot currently be performed because:**
1. No governance/REPRODUCIBILITY.md exists
2. RUNBOOK.md is incomplete (Phases 2-3 only)
3. No expected output values are locked for comparison
4. 13+ files have unseeded randomness, so results would not be deterministic
5. No minimal demo exists that could verify the environment in <5 minutes

**Blocking issues for clean-room execution:**
- Database population via `populate_database.py` is not documented in RUNBOOK
- Phase 4+ scripts are not documented anywhere
- No verification checklist exists to confirm successful execution

---

## Consolidated Findings by Severity

### Critical (14 findings)

| ID | Phase | Finding | Location |
|---|---|---|---|
| C1 | 1.2 | 52 hardcoded values in perturbation/hypothesis/model thresholds | disconfirmation.py, destructive.py, evaluation.py |
| C2 | 1.4 | Grammar-based generator uses unseeded random.choices() | phase3_synthesis/generators/grammar_based.py:48 |
| C3 | 1.4 | Feature discovery uses 12+ unseeded random.uniform() calls | phase3_synthesis/refinement/feature_discovery.py |
| C4 | 1.4 | Indistinguishability test controls are non-deterministic | phase3_synthesis/indistinguishability.py:132-140 |
| C5 | 1.2 | Model sensitivity weights have no empirical justification | constructed_system.py, visual_grammar.py |
| C6 | 1.2 | Evaluation dimension weights (0.30, 0.25, etc.) determine rankings | evaluation.py:113-118 |
| C7 | 1.2 | Capacity bounding constants are hardcoded observations | capacity_bounding.py:38-42 |
| C8 | 1.2 | Stability baselines are hardcoded control statistics | stability_analysis.py:38-46 |
| C9 | 1.2 | Synthesis constraint tolerances are hardcoded | interface.py:158-167 |
| C10 | 4.3 | No CONFIG_REFERENCE.md - parameters undocumented | N/A |
| C11 | 1.5 | Voynichese token seeds in fallback path | profile_extractor.py:626-637 |
| C12 | 1.4 | 8+ mechanism simulators completely unseeded | phase5_mechanism/*/simulators.py |
| C13 | 1.2 | Equivalence/improvement thresholds (0.30/0.10) | refinement/interface.py:155-156 |
| C14 | 1.2 | Perturbation battery strength levels arbitrarily spaced | disconfirmation.py:40-59 |

### High (31 findings)

| ID | Phase | Finding | Location |
|---|---|---|---|
| H1 | 2.2 | Boolean truthiness bug: `if (a and b and c)` fails at 0.0 | mapping_stability.py:113 |
| H2 | 1.3 | Silent exception swallowing drops embeddings | metrics/library.py:169,208 |
| H3 | 1.3 | 12+ feature functions return random/hardcoded on missing data | feature_discovery.py:92-697 |
| H4 | 1.3 | Silent fallback from tokens to alignments | metrics/library.py:64-65 |
| H5 | 1.3 | Phantom bounding boxes from `.get()` defaults | perturbation.py:119-135 |
| H6 | 1.3 | Profile extractor silently returns simulated data | profile_extractor.py:82-83 |
| H7 | 1.3 | NaN propagation through calculations unchecked | perturbation.py:317 |
| H8 | 1.3 | std_control defaults to 0.1 (arbitrary smoothing) | destructive.py:440 |
| H9 | 1.3 | Bare except clauses catch SystemExit | 3 files |
| H10 | 1.7 | 20+ scripts write results without provenance metadata | scripts/*.py |
| H11 | 3.3 | Only 2/118 src files use logging module | src/ |
| H12 | 3.3 | DEBUG print statement in production code | anchors/engine.py:77 |
| H13 | 4.2 | No governance/METHODS_REFERENCE.md | N/A |
| H14 | 4.4 | No governance/REPRODUCIBILITY.md | N/A |
| H15 | 2.5 | No fixture-based regression testing | N/A |
| H16 | 2.4 | No boundary case or invariance tests | N/A |
| H17 | 1.2 | Iteration limits (50 pages, 10000 tokens) duplicated across 3 files | stress_tests/*.py |
| H18 | 1.2 | 7 mapping stability thresholds undocumented | mapping_stability.py:325-406 |
| H19 | 1.2 | Perturbation scaling constants (0.5, 0.35, 2) | perturbation.py:144-292 |
| H20 | 1.2 | Text generation positional bias probability (0.4) | text_generator.py:122 |
| H21 | 1.2 | Scrambled control hardcoded metrics | indistinguishability.py:118-140 |
| H22 | 1.4 | Pool generator, workflow simulators unseeded | phase5_mechanism/generators/, phase5_mechanism/workflow/ |
| H23 | 1.4 | Text generator page seed generation unseeded | text_generator.py:360 |
| H24 | 2.1 | Dual RepetitionRate formulas in same result | metrics/library.py:84-98 |
| H25 | 2.1 | ClusterTightness dual computation paths (embedding vs bbox) | metrics/library.py:159-162 |
| H26 | 2.2 | Inconsistent empty-list protection before division | Multiple files |
| H27 | 3.2 | Token vs Word terminology inconsistency | cli/main.py, throughout |
| H28 | 5.1 | No sensitivity analysis performed or documented | N/A |
| H29 | 5.2 | Clean-room re-execution not possible | N/A |
| H30 | 1.6 | Empty dataset returns 0.0 instead of NaN | metrics/library.py |
| H31 | 4.4 | RUNBOOK.md is skeletal (41 lines, Phases 2-3 only) | governance/RUNBOOK.md |

### Medium (42 findings) - Summary

- Implicit type coercion in token extraction
- Hypothesis outcome string inconsistency (no enum)
- Float equality comparisons
- Ordering dependency not documented (line_index vs implicit)
- Feature discrimination ranges undocumented
- Profile extraction fallback defaults
- Implicit coordinate clipping
- Max entropy returned for missing data
- Array shape compatibility assumed
- Glyph vs Symbol terminology confusion
- Silent exception handling in dataset.py, qc/anomalies.py
- Non-actionable error messages in CLI
- Variance calculation defaulting on single element
- Implicit thread-local state defaults to UNRESTRICTED
- Planning document typos (EXUECTION)

### Low (18 findings) - Summary

- False positive TEMP matches (temporal, template)
- Hardcoded seed=42 in functional simulators
- Acknowledged arbitrary thresholds with inline comments
- Style inconsistencies
- QC reporting stubs using print()

---

## Known High-Risk Areas (from Playbook) - Assessment

| Area | Status | Key Finding |
|---|---|---|
| Tokenization and segmentation | GOOD | Single canonical path via EVAParser |
| Reset definitions | GOOD | Sparse, consistent usage |
| History window logic | NOT ASSESSED | No explicit history window found in core analysis |
| Generator parameterization | CRITICAL | 150+ hardcoded values, unseeded randomness |
| Distance normalization | MEDIUM | 1/(1+distance) formula used consistently but implicitly |
| Visualization smoothing or binning | NOT ASSESSED | No visualization code examined in this audit |

---

## Appendix: Files Requiring Attention (Priority Order)

### Immediate (Blocks Publication)
1. `src/phase3_synthesis/generators/grammar_based.py` - Add seed propagation
2. `src/phase3_synthesis/refinement/feature_discovery.py` - Seed all random calls
3. `src/phase3_synthesis/indistinguishability.py` - Seed scrambled control generation
4. `src/phase2_analysis/stress_tests/mapping_stability.py:113` - Fix boolean truthiness bug
5. All mechanism simulators (8+ files) - Add seed parameters

### Before External Review
6. Create `governance/CONFIG_REFERENCE.md`
7. Create `governance/governance/METHODS_REFERENCE.md`
8. Create `governance/governance/REPRODUCIBILITY.md`
9. Remove DEBUG print from `src/phase1_foundation/anchors/engine.py:77`
10. Replace bare `except:` clauses in 3 files
11. Add provenance metadata to script output files
12. Document all Critical-severity hardcoded values

### Longer Term
13. Implement structured logging across all src/ modules
14. Add boundary case tests
15. Create fixture-based regression tests with locked expected values
16. Perform and document sensitivity analysis on key parameters
17. Standardize Token/Word/Glyph/Symbol terminology

---

**Audit Status: COMPLETE**
**Remediation Status: NOT STARTED (audit-only pass)**
