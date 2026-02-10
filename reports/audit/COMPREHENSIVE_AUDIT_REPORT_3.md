# Comprehensive Code Audit Report 3

**Date:** 2026-02-09
**Project:** Voynich Manuscript Structural Admissibility Program
**Methodology:** Per `planning/audit/CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md`

---

## Executive Summary

Third-pass audit confirms that prior remediations (Reports 1 and 2) addressed targeted issues but the long tail of findings remains substantial. The codebase is architecturally sound but has pervasive issues with unseeded randomness, hardcoded thresholds, silent fallbacks, and documentation lag.

### Severity Distribution

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 11 | Impacts core conclusions or reproducibility |
| **High** | 22 | Materially affects numerical stability or clarity |
| **Medium** | 38 | Correctness, clarity, or maintenance risks |
| **Low** | 16 | Style, test coverage gaps, minor docs |

---

## Phase 0: Inventory and Orientation

### 0.1 Executable Paths

| Category | Count | Location |
|----------|-------|----------|
| Primary analysis scripts | 4 | `scripts/analysis/run_phase_2_*.py` |
| Synthesis scripts | 5 | `scripts/synthesis/run_*.py` |
| Mechanism pilot scripts | 12 | `scripts/mechanism/run_5*_pilot.py` |
| Foundation scripts | 3 | `scripts/foundation/` |
| CLI entry point | 1 | `src/foundation/cli/main.py` |
| Shell scripts | 2 | `scripts/ci_check.sh`, `scripts/verify_reproduction.sh` |
| Audit scripts | 2 | `scripts/audit/` |
| Notebooks | 0 | None |

### 0.2 Module Inventory

| Module | Python Files | Submodules |
|--------|-------------|------------|
| `src/foundation/` | ~45 | alignment, analysis, anchors, cli, configs, controls, core, decisions, hypotheses, metrics, qc, regions, runs, segmentation, storage, transcription |
| `src/analysis/` | ~15 | admissibility, anomaly, models, stress_tests |
| `src/synthesis/` | ~12 | generators, refinement |
| `src/mechanism/` | ~30 | constraint_geometry, dependency_scope, deterministic_grammar, entry_selection, generators, large_object, matching, parsimony, tests, topology_collapse, workflow |
| `src/inference/` | ~10 | info_clustering, lang_id_transforms, morph_induction, network_features, topic_models |
| `src/functional/` | ~8 | adversarial, efficiency, formal_system |
| `src/human/` | ~5 | comparative, ergonomics, page_boundary, quire_analysis, scribe_coupling |
| `src/comparative/` | 1 | mapping |
| **Total** | **~126** | |

**Tests:** 7 test files covering <15% of source modules.

**Configuration files:** `configs/functional/model_params.json` (centralized model parameters).

---

## Phase 1: Results Integrity

### 1.1 Placeholder and Temporary Code

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| P1 | High | Hardcoded `positional_entropy=0.40` labeled `# Simulated` | `indistinguishability.py:120` |
| P2 | High | 7 `random.uniform()` fallback values in feature discovery | `refinement/feature_discovery.py:111,156,203,270,620,677,726` |
| P3 | High | Hardcoded default word length `return 5.2` | `profile_extractor.py:223` |
| P4 | High | Hardcoded default repetition rate `return 0.20` (2x) | `profile_extractor.py:236,248` |
| P5 | Medium | 6+ `return {}` stubs in inference analyzers | `human/comparative.py:26`, `inference/*/analyzer.py` |
| P6 | Medium | Simulated metric base values `3.0 + rng.uniform(...)` | `text_generator.py:325,330` |
| P7 | Medium | Debug `print()` in non-CLI code | `qc/anomalies.py:27`, `analysis/sensitivity.py:36` |
| P8 | Low | Commented-out database logic (6 lines) | `profile_extractor.py:276-281` |

### 1.2 Hardcoded Values and Magic Numbers

**Critical Thresholds (undocumented, affect conclusions):**

| ID | Severity | Value(s) | Location | Impact |
|----|----------|----------|----------|--------|
| H1 | Critical | `0.5, 0.6, 0.4, 0.7` | `mapping_stability.py:343-393` | Determine STABLE/FRAGILE/COLLAPSED outcomes |
| H2 | Critical | `2.0, 1.5, 1.0` | `locality.py:176-183` | Locality radius detection thresholds |
| H3 | Critical | `0.7, 0.5, 0.3` | `locality.py:315-322` | Compositional score classification |
| H4 | Critical | `0.15, 0.7, 0.6` | `locality.py:389-399` | Procedural signature detection |
| H5 | Critical | `0.6, 0.4` | `locality.py:655,657` | Stability outcome determination |
| H6 | Critical | `4.0, 3.0, 0.70, 1.2, 0.5, 8.0, 2.0` | `stability_analysis.py:40-48` | BASELINE_* anomaly constants |
| H7 | Critical | `0.05` | `mapping_stability.py:169` | Perturbation boundary shift |
| H8 | High | `0.7, 0.3` | `indistinguishability.py:79-80` | Separation success criteria |
| H9 | High | `0.05, 0.02` | `comparator.py:33-36` | Metric classification thresholds |
| H10 | High | `1.0, 0.5, 0.3` | `stability_analysis.py:228-247` | Representation sensitivity |
| H11 | High | `0.2, 0.3` | `constraint_formalization.py:51,58` | Feature importance thresholds |

**Hardcoded Parameters (operational, medium impact):**

| ID | Severity | Value(s) | Location | Description |
|----|----------|----------|----------|-------------|
| H12 | Medium | `100, 50` | `mapping_stability.py:41-42` | MAX_LINES/WORDS iteration limits |
| H13 | Medium | `500` | `adversarial/metrics.py:94` | Chunk size for decoy regularity |
| H14 | Medium | `0.8` | `adversarial/metrics.py:59` | Train/test split ratio |
| H15 | Medium | `(2, 4)` | `text_generator.py:61` | Locality window tuple |
| H16 | Medium | `50, 6, 7, 8` | `text_generator.py:70-76` | Vocabulary and bias counts |
| H17 | Medium | `0.05, 0.1, 0.5` | `self_citation.py:41-48` | Mutation/update probabilities |
| H18 | Medium | `0.05` | `pool_generator.py:30` | Pool replenishment probability |

### 1.3 Silent Defaults and Implicit Behavior

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| S1 | High | `ClusterTightness` returns `0.5` silently when no pages | `metrics/library.py:148` |
| S2 | High | Control test returns `0.3` when no control IDs | `mapping_stability.py:301` |
| S3 | High | `info_density` fallback to `4.0` | `indistinguishability.py:122` |
| S4 | Medium | `.get(..., 0)` in coordinate calculations | `perturbation.py:348` |
| S5 | Medium | `float("nan")` returned without caller awareness | `metrics/library.py` (multiple) |
| S6 | Medium | `except Exception: return 0` in folio parsing | `quire_analysis.py:31` |
| S7 | Medium | `except Exception: return "Unknown"` in hand detection | `scribe_coupling.py:34` |
| S8 | Medium | `except Exception: assortativity = 0.0` | `network_features/analyzer.py:53` |
| S9 | Medium | `except Exception:` with no logging in atomic write | `storage/filesystem.py:68` |
| S10 | Medium | Git failures silently return `"unknown"` | `runs/context.py:16,22` |

### 1.4 Randomness and Non-Determinism

**26 files import `random` module.** Audit of seed control:

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| R1 | Critical | `random.choice/randint/random` without seed | `mechanism/generators/pool_generator.py:27-31` |
| R2 | Critical | 7 `random.uniform()` in fallback paths, unseeded | `synthesis/refinement/feature_discovery.py` |
| R3 | Critical | `random.seed(seed)` then 8+ bare `random.*()` calls | `foundation/controls/self_citation.py:19-48` |
| R4 | Critical | `random.seed(seed)` then bare `random.*()` calls | `foundation/controls/synthetic.py:13` |
| R5 | High | `random.Random(seed)` used instead of RandomnessController | `synthesis/text_generator.py:308` |
| R6 | High | `random.randint()` without seed in table generator | `mechanism/generators/constraint_geometry/table_variants.py:47-48` |
| R7 | Medium | Multiple mechanism simulators use `random.Random(seed)` locally - correctly seeded but bypass RandomnessController | `mechanism/*/simulators.py` (8+ files) |
| R8 | Medium | `RandomBlobProposer` uses local `random.Random(self.seed)` | `regions/dummy.py:59` |
| R9 | Low | `uuid.uuid4()` in synthetic.py | `controls/synthetic.py:2` |

**RandomnessController adoption:** EXISTS at `foundation/core/randomness.py` but is NOT used by any file in `synthesis/`, `mechanism/`, or `foundation/controls/`.

### 1.5 Circularity and Data Leakage

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| CL1 | Critical | `BASELINE_INFO_DENSITY = 4.0` embeds observed Voynich measurement as constant | `stability_analysis.py:40` |
| CL2 | Critical | `BASELINE_LOCALITY = 3.0` embeds observed Voynich measurement | `stability_analysis.py:41` |
| CL3 | Critical | `BASELINE_ROBUSTNESS = 0.70` embeds observed Voynich measurement | `stability_analysis.py:42` |
| CL4 | High | Anomaly "confirmation" checks if baseline stable vs controls, but baseline IS Voynich | `stability_analysis.py:293` |
| CL5 | Medium | Feature discovery fallback values (0.7, 0.35, etc.) appear tuned to Voynich data | `refinement/feature_discovery.py` |

### 1.6 Control and Baseline Symmetry

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| CS1 | High | `SyntheticNullGenerator` uses `random.seed()` (global state) not local RNG | `controls/synthetic.py:13` |
| CS2 | High | `SyntheticNullGenerator.generate()` generates fake pages but NO tokens | `controls/synthetic.py:38-43` |
| CS3 | Medium | `SelfCitationGenerator` uses global `random.seed()` then global calls | `controls/self_citation.py:19` |
| CS4 | Medium | Controls don't pass through EVAParser (generated directly) | `controls/synthetic.py`, `controls/self_citation.py` |
| CS5 | Low | Scrambled controls do use `ScrambledControlGenerator` which accesses DB | `controls/scramblers.py` |

### 1.7 Output Provenance

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| OV1 | Medium | `StressTestResult` has no `run_id` or `timestamp` field | `stress_tests/interface.py:25-47` |
| OV2 | Medium | Stress test results are NOT stored in DB (returned as dataclass, not persisted) | `stress_tests/*.py` |
| OV3 | Medium | `MetricResultRecord` correctly stores `run_id` | `storage/metadata.py:254` |
| OV4 | Low | `ProvenanceWriter` exists but only used in mechanism scripts | `core/provenance.py` |
| OV5 | Low | RunContext captures git commit, timestamp, environment - comprehensive | `runs/context.py` |

---

## Phase 2: Method Correctness

### 2.1 Metric Registry

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| MR1 | High | RepetitionRate returns TWO formulas: `token_repetition_rate` (repeated/total) AND `vocabulary_entropy_rate` (1-unique/total) in same result | `metrics/library.py:88-103` |
| MR2 | Medium | ClusterTightness has dual computation paths (embeddings vs bboxes) producing different scales; `details["method"]` indicates which but main `value` is ambiguous | `metrics/library.py:156-289` |
| MR3 | Medium | No duplicate metrics found; metrics are well-isolated | - |

### 2.2 Input/Output Contracts

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| IO1 | Medium | `ProvenanceWriter.save_results(results: Any)` accepts `Any` without validation | `core/provenance.py:13` |
| IO2 | Medium | `guarded_shuffle()` mutates argument in-place without documentation | `core/randomness.py:130` |
| IO3 | Medium | 8+ public methods lack return type hints | `synthesis/text_generator.py`, `alignment/engine.py`, `refinement/feature_discovery.py` |
| IO4 | Low | Implicit int-to-float coercion in TTR calculation | `scribe_coupling.py:53` |

### 2.3 Canonical Preprocessing

**GOOD:** `EVAParser` is the single canonical tokenization path. No alternate tokenization of Voynichese text detected. Other string splits are for CLI arguments and metric name parsing only.

### 2.4 Unit Test Coverage

| Module | Test File | Status |
|--------|-----------|--------|
| `foundation/metrics/` | `test_boundary_cases.py` | Partial |
| `foundation/core/geometry` | `test_geometry.py` | Partial |
| `foundation/core/ids` | `test_ids.py` | Partial (1 failing) |
| `analysis/stress_tests/` | `test_mapping_stability.py` | Minimal (new) |
| `audit/` | `test_determinism.py` | Minimal |
| `integration/` | `test_enforcement.py` | Minimal |
| **synthesis/** | **None** | **NOT TESTED** |
| **mechanism/** | **None** | **NOT TESTED** |
| **inference/** | **None** | **NOT TESTED** |
| **functional/** | **None** | **NOT TESTED** |
| **human/** | **None** | **NOT TESTED** |
| **comparative/** | **None** | **NOT TESTED** |

**Coverage: ~15%.** 7 test files for 126+ source modules.

---

## Phase 3: Structural Consistency

### 3.1 Directory and File Structure

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| DS1 | High | 12+ mechanism pilot scripts duplicate `get_lines()` helper | `scripts/mechanism/run_5*_pilot.py` |
| DS2 | Medium | Script logic not importable from `src/` | `scripts/analysis/`, `scripts/synthesis/` |
| DS3 | Low | No orphaned files detected; all `src/` modules are imported | - |

### 3.2 Terminology Discipline

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| TD1 | High | "Word" overloaded: visual segment (WordRecord) AND transcribed token | `alignment/engine.py:46-73`, `metrics/library.py:112` |
| TD2 | Medium | "Page" vs "Folio" confused: PageRecord stores folio strings like "f1r" | `core/ids.py`, `human/quire_analysis.py:23`, `synthesis/interface.py:74` |
| TD3 | Medium | RepetitionRate dual naming: `token_repetition_rate` vs `vocabulary_entropy_rate` | `metrics/library.py:89,92` |
| TD4 | Low | "Score" / "Metric" / "Value" / "Result" used interchangeably | Various |

### 3.3 Logging Discipline

| ID | Severity | Finding | Location |
|----|----------|---------|----------|
| LG1 | High | 8+ silent `except Exception` handlers with no logging | `filesystem.py:68`, `context.py:16,22`, `quire_analysis.py:31`, `scribe_coupling.py:34` |
| LG2 | Medium | 2 `print()` statements in non-CLI code | `qc/anomalies.py:27`, `analysis/sensitivity.py:36` |
| LG3 | Medium | Inconsistent logging: some modules use `logger.*`, others use `print()`, some silently swallow | Various |

---

## Phase 4: Documentation

| Document | Status | Key Gaps |
|----------|--------|----------|
| `README.md` | Good | States "Phase 3 Completed"; actually through Phase 5K |
| `docs/METHODS_REFERENCE.md` | Good | Dual formula issue not documented; no confounds section |
| `docs/CONFIG_REFERENCE.md` | Good | No randomness control documented; rationale incomplete |
| `docs/REPRODUCIBILITY.md` | Moderate | Only covers Phase 2-3; Phase 4-5 missing entirely |
| `docs/CALIBRATION_NOTES.md` | Excellent | Comprehensive rationale for thresholds |
| `docs/SENSITIVITY_ANALYSIS.md` | Poor | Plan exists but NEVER EXECUTED; no results |
| `docs/GLOSSARY.md` | Good | Core terms defined |
| `docs/RUNBOOK.md` | Moderate | Phase 2 section incomplete; Phase 4-6 missing |
| `docs/FEATURE_RANGES.md` | Good | 16 features documented with ranges |

---

## Phase 5: External-Critique Assessment

### Skeptical Reader Checklist

| Question | Answer | Evidence |
|----------|--------|----------|
| Where are assumptions stated? | High-level: excellent. Quantitative: sparse. | README principles clear; parameter assumptions opaque |
| Which parameters matter most? | Not documented | SENSITIVITY_ANALYSIS.md planned but unexecuted |
| What happens if they change? | Unknown | No sensitivity sweep results exist |
| How do we know this isn't tuned? | Partially verifiable | REQUIRE_COMPUTED prevents simulation; but 150+ hardcoded thresholds lack justification |
| What negative evidence exists? | Documented for major findings | Language hypothesis falsified; minor null findings incomplete |

### Reproducibility Assessment

| Phase | Reproducible? | Reason |
|-------|--------------|--------|
| Phase 1 (Foundation) | Yes | Seeded, deterministic |
| Phase 2 (Analysis) | Yes | Documented in REPRODUCIBILITY.md |
| Phase 3 (Synthesis) | Partial | `grammar_based.py` now seeded; but `feature_discovery.py` has 7 unseeded random calls |
| Phase 4-5 (Mechanism) | No | Not documented in REPRODUCIBILITY.md; simulators use local seeds but no orchestration guide |

---

## Consolidated Findings Table

| ID | Severity | Category | Finding | Location |
|----|----------|----------|---------|----------|
| C1 | Critical | Randomness | Unseeded `random.*()` in pool_generator | `mechanism/generators/pool_generator.py:27-31` |
| C2 | Critical | Randomness | 7 unseeded `random.uniform()` in fallback paths | `synthesis/refinement/feature_discovery.py` |
| C3 | Critical | Randomness | Global `random.seed()` then bare calls | `foundation/controls/self_citation.py:19-48` |
| C4 | Critical | Randomness | Global `random.seed()` then bare calls | `foundation/controls/synthetic.py:13` |
| C5 | Critical | Circularity | `BASELINE_INFO_DENSITY=4.0` embeds observed Voynich value | `analysis/anomaly/stability_analysis.py:40` |
| C6 | Critical | Circularity | `BASELINE_LOCALITY=3.0` embeds observed Voynich value | `analysis/anomaly/stability_analysis.py:41` |
| C7 | Critical | Circularity | `BASELINE_ROBUSTNESS=0.70` embeds observed Voynich value | `analysis/anomaly/stability_analysis.py:42` |
| C8 | Critical | Thresholds | 4 undocumented thresholds determine STABLE/FRAGILE/COLLAPSED | `mapping_stability.py:343-393` |
| C9 | Critical | Thresholds | 3 undocumented locality radius thresholds | `locality.py:176-183` |
| C10 | Critical | Thresholds | Compositional score thresholds | `locality.py:315-322` |
| C11 | Critical | Placeholder | `positional_entropy=0.40` hardcoded as "Simulated" | `indistinguishability.py:120` |
| H1 | High | Metric | RepetitionRate returns TWO different formulas in same result | `metrics/library.py:88-103` |
| H2 | High | Default | ClusterTightness returns 0.5 silently when no data | `metrics/library.py:148` |
| H3 | High | Default | Control test returns 0.3 when no control IDs | `mapping_stability.py:301` |
| H4 | High | Default | `info_density` fallback to 4.0 | `indistinguishability.py:122` |
| H5 | High | Randomness | `random.Random(seed)` bypasses RandomnessController | `synthesis/text_generator.py:308` |
| H6 | High | Randomness | Unseeded `random.randint()` | `mechanism/generators/constraint_geometry/table_variants.py:47-48` |
| H7 | High | Control | SyntheticNullGenerator creates pages but NO tokens | `controls/synthetic.py:38-43` |
| H8 | High | Control | Controls don't pass through EVAParser | `controls/synthetic.py`, `controls/self_citation.py` |
| H9 | High | Placeholder | 7 hardcoded fallback values in feature_discovery | `refinement/feature_discovery.py` |
| H10 | High | Placeholder | Default word length 5.2 and repetition rate 0.20 | `profile_extractor.py:223,236,248` |
| H11 | High | Threshold | Separation success criteria 0.7/0.3 | `indistinguishability.py:79-80` |
| H12 | High | Threshold | Metric comparison thresholds 0.05/0.02 | `comparator.py:33-36` |
| H13 | High | Threshold | Representation sensitivity 1.0/0.5/0.3 | `stability_analysis.py:228-247` |
| H14 | High | Structure | 12+ pilot scripts duplicate `get_lines()` helper | `scripts/mechanism/run_5*_pilot.py` |
| H15 | High | Terminology | "Word" overloaded as visual segment AND transcript token | `alignment/engine.py`, `metrics/library.py` |
| H16 | High | Logging | 8+ silent exception handlers with no logging | Multiple files |
| H17 | High | Docs | SENSITIVITY_ANALYSIS.md plan never executed | `docs/SENSITIVITY_ANALYSIS.md` |
| H18 | High | Docs | REPRODUCIBILITY.md missing Phase 4-5 | `docs/REPRODUCIBILITY.md` |
| H19 | High | Thresholds | Procedural signature thresholds 0.15/0.7/0.6 | `locality.py:389-399` |
| H20 | High | Thresholds | Pattern type thresholds 4/8/0.5 | `locality.py:579-584` |
| H21 | High | Thresholds | Stability outcome thresholds 0.6/0.4 | `locality.py:655,657` |
| H22 | High | Thresholds | Feature formalization thresholds 0.2/0.3 | `constraint_formalization.py:51,58` |

*(38 Medium and 16 Low findings omitted for brevity; see detailed sections above.)*

---

## Comparison with Prior Audits

| Finding | Audit 1 | Audit 2 | Audit 3 (this) |
|---------|---------|---------|-----------------|
| Unseeded randomness | 13+ files | C1 fixed (grammar_based.py) | 4 critical + 2 high remaining |
| Hardcoded thresholds | 150+ | C2 externalized model weights | 30+ critical/high thresholds in stress tests and locality |
| Boolean truthiness bug | mapping_stability.py:113 | H1 fixed + tests added | Confirmed fixed |
| Silent exception handlers | metrics/library.py | H2 fixed in ClusterTightness | 8+ remaining across project |
| RepetitionRate dual formula | Noted | Not addressed | Still returns two formulas |
| ClusterTightness dual path | Noted | Not addressed | Still has undocumented fallback |
| CLI terminology | Noted | M1 standardized | Confirmed improved |
| Planning file typos | Noted | L1 renamed | Confirmed fixed |
| Config imports | Not found | C2a fixed (json/pathlib) | Confirmed fixed |
| evaluation.py weights | Not found | C2b externalized | Confirmed fixed |
| profile_extractor.py syntax | Not found | X1 fixed | Confirmed fixed |
| BASELINE_* circularity | Not specifically found | Not addressed | **NEW: 3 critical findings** |
| SyntheticNull generates no tokens | Not found | Not found | **NEW: High finding** |
| Sensitivity analysis unexecuted | Not found | Not found | **NEW: High finding** |
| Documentation lag (Phase 4-5) | Not found | Not found | **NEW: High finding** |

---

## Priority Remediation Recommendations

### Tier 1: Blocks Reproducibility (Critical)

1. **Seed all randomness in `feature_discovery.py`, `pool_generator.py`, `self_citation.py`, `synthetic.py`** - 4 files, ~20 `random.*()` calls
2. **Document or externalize BASELINE_* constants** in `stability_analysis.py` with provenance showing how values were derived
3. **Externalize stress test thresholds** in `mapping_stability.py` and `locality.py` to config

### Tier 2: Affects Conclusions (High)

4. **Resolve RepetitionRate dual formula** - choose one, remove the other from result details
5. **Fix SyntheticNullGenerator** - currently generates pages with no tokens (incomplete control)
6. **Execute sensitivity analysis** per SENSITIVITY_ANALYSIS.md or retract the document
7. **Update REPRODUCIBILITY.md** to cover Phase 4-5

### Tier 3: Clarity and Maintenance (Medium)

8. Replace silent exception handlers with logged warnings
9. Replace `print()` with `logger.*` in non-CLI code
10. Add `run_id` and `timestamp` to `StressTestResult`
11. Standardize "Word" vs "Token" terminology in alignment code
12. Extract pilot script helpers to importable modules

---

**Audit Status:** COMPLETE
**Result:** Prior remediations confirmed. Significant remaining work in randomness control (4 critical files), threshold externalization (30+ values), control completeness, sensitivity verification, and documentation currency.
