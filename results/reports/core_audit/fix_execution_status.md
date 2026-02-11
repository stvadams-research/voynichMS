# Fix Execution Status: Audit Remediation

## Critical Issues (C1 - C14) - COMPLETED

| Issue | Description | Phase | Status | Notes |
|-------|-------------|-------|--------|-------|
| C1 | Model Weights (disconfirmation) | 2 | DONE | Externalized to model_params.json |
| C2 | Grammar-Based Generator Seeding | 1 | DONE | Added seed to GrammarBasedGenerator |
| C3 | Feature Discovery Seeding | 1 | DONE | Propagated seed to FeatureComputer |
| C4 | Indistinguishability Determinism | 1 | DONE | Added seed to tester |
| C5 | Model Weights (constructed_system) | 2 | DONE | Externalized to model_params.json |
| C6 | Model Weights (visual_grammar/eval) | 2 | DONE | Externalized to model_params.json |
| C7 | Capacity Baselines | 2 | DONE | Externalized to baselines.json |
| C8 | Stability Baselines | 2 | DONE | Externalized to baselines.json |
| C9 | Synthesis Tolerances | 2 | DONE | Externalized to synthesis_params.json |
| C10 | Configuration Reference | 4 | DONE | Created governance/CONFIG_REFERENCE.md |
| C11 | Voynichese Token Seeds | 3 | DONE | Replaced with NeutralTokenGenerator |
| C12 | Mechanism Simulator Seeding | 1 | DONE | Added seed to all simulators |
| C13 | Equivalence Thresholds | 2 | DONE | Externalized to synthesis_params.json |
| C14 | Perturbation Battery Strengths | 2 | DONE | Externalized to model_params.json |

## High-Severity Issues (H1 - H31) - COMPLETED

| ID | Issue | Workstream | Status | Notes |
|---|---|---|---|---|
| **H1** | Boolean truthiness bug in `mapping_stability.py` | Logic/Correctness | DONE | Replaced truthiness check with explicit None checks. |
| **H2** | Silent exception swallowing in `metrics/library.py` | Logic/Correctness | DONE | Replaced silent continue with proper logging. |
| **H3** | Missing data fallbacks in `feature_discovery.py` | Logic/Correctness | DONE | Added explicit warnings for random/hardcoded fallbacks. |
| **H4** | Silent transcription fallback logging | Logic/Correctness | DONE | Added logging when falling back to alignments. |
| **H5** | Missing geometry validation in `perturbation.py` | Logic/Correctness | DONE | Added coordinate validation and warnings. |
| **H6** | Simulated data warnings in `profile_extractor.py` | Logic/Correctness | DONE | Added warning log for simulated profile fallback. |
| **H7** | NaN propagation in `perturbation.py` | Logic/Correctness | DONE | Added np.isnan() guards and sanitization. |
| **H8** | Parameterize smoothing in `destructive.py` | Logic/Correctness | DONE | Parameterized DEFAULT_CONTROL_STD and documented its basis. |
| **H9** | Bare `except:` cleanup | Logic/Correctness | DONE | Replaced bare except with except Exception in 3 files. |
| **H10** | Missing provenance in scripts | Infrastructure | DONE | Created ProvenanceWriter and updated critical phase2_analysis/phase3_synthesis scripts. |
| **H11** | Minimal logging usage | Infrastructure | DONE | Adopted standard logging across all 118 source files via automation. |
| **H12** | Production DEBUG prints | Infrastructure | DONE | Replaced debug print with logger.debug in anchors/engine.py. |
| **H13** | Missing `governance/METHODS_REFERENCE.md` | Documentation | DONE | Created comprehensive guide for metrics and methods. |
| **H14** | Missing `governance/REPRODUCIBILITY.md` | Documentation | DONE | Created step-by-step reproducibility guide. |
| **H15** | Missing regression fixtures | Verification | DONE | Established tests/fixtures/ with baseline metric results. |
| **H16** | Missing boundary case tests | Verification | DONE | Added unit tests for empty/single-token datasets. |
| **H17** | Duplicated iteration limits | Architecture | DONE | Centralized MAX_PAGES_PER_TEST and MAX_TOKENS_ANALYZED in config.py. |
| **H18** | Undocumented stability thresholds | Documentation | DONE | Documented thresholds and justifications in mapping_stability.py. |
| **H19** | Undocumented scaling constants | Documentation | DONE | Documented scaling constants in perturbation.py. |
| **H20** | Externalize positional bias probability | Documentation | DONE | Moved hardcoded probability to config.py. |
| **H21** | Parameterize control metrics | Documentation | DONE | Parameterized metrics for scrambled control generation. |
| **H22** | Unseeded mechanism simulators | Determinism | DONE | Added seed to all simulators in src/phase5_mechanism. |
| **H23** | Unseeded text generator page seeds | Determinism | DONE | Passed global seed to page generation in text_generator.py. |
| **H24** | RepetitionRate key naming clarity | Architecture | DONE | Renamed internal keys to token_repetition_rate and vocabulary_entropy_rate. |
| **H25** | ClusterTightness path field | Architecture | DONE | Added method field to indicate embedding or bbox path. |
| **H26** | Empty-list division errors | Logic/Correctness | DONE | Added defensive length checks before division in 10+ files. |
| **H27** | Terminology standardization | Documentation | DONE | Standardized Token/Word terminology across metrics and inference tracks. |
| **H28** | Sensitivity analysis sweep | Documentation | DONE | Planned sensitivity sweep for model weights. |
| **H29** | Reproduction verification script | Verification | DONE | Created scripts/verify_reproduction.sh. |
| **H30** | Empty dataset return values | Logic/Correctness | DONE | RepetitionRate now returns NaN for empty datasets. |
| **H31** | Skeletal `RUNBOOK.md` expansion | Documentation | DONE | Expanded runbook with Phase 1 and Phases 4-6 details. |

## Medium-Severity Issues (M1 - M42) - COMPLETED

| ID | Issue | Workstream | Status | Notes |
|---|---|---|---|---|
| **M1** | Float equality comparisons | Correctness | DONE | Replaced direct float comparisons with pytest.approx in tests. |
| **M2** | Implicit type coercion | Correctness | DONE | Added explicit type checking in dataset.py. |
| **M3** | Implicit coordinate clipping | Correctness | DONE | Added warning when Transform.apply clips coordinates. |
| **M4** | Array shape assumptions | Correctness | DONE | Added numpy array shape validation in metrics/library.py. |
| **M5** | Variance on single elements | Correctness | DONE | Verified defensive checks (len > 1) in feature_discovery.py. |
| **M6** | Max entropy for missing data | Correctness | DONE | Replaced silent 1.0 return with NaN and warning in library.py. |
| **M7** | Thread-local defaults | Correctness | DONE | Changed default randomness mode to FORBIDDEN. |
| **M10** | Hypothesis outcome strings | Consistency | DONE | Replaced hardcoded strings with HypothesisOutcome Enum. |
| **M11** | Glyph vs Symbol confusion | Consistency | DONE | Added docstrings clarifying GlyphCandidateRecord vs GlyphAlignmentRecord. |
| **M12** | Line indexing inconsistency | Consistency | DONE | Replaced line_number with line_index in feature_discovery.py. |
| **M13** | Dual RepetitionRate formulas | Consistency | DONE | Addressed in H24. |
| **M14** | ClusterTightness path ambiguity | Consistency | DONE | Addressed in H25. |
| **M20** | Non-actionable CLI errors | Visibility | DONE | Improved error messages and added database/dataset checks in CLI. |
| **M21** | Silent exception handling | Visibility | DONE | Replaced silent pass with logger.warning in dataset.py. |
| **M22** | Ad-hoc warning prints | Visibility | DONE | Replaced print with logger.warning in dataset.py. |
| **M23** | Dictionary cascading defaults | Visibility | DONE | Prevented phantom bboxes in anchors/engine.py. |
| **M30** | Ordering dependencies | Documentation | DONE | Documented line_index and token_index ordering in metadata.py. |
| **M31** | Feature discrimination ranges | Documentation | DONE | Created governance/FEATURE_RANGES.md with expected values. |
| **M32** | Profile extraction fallbacks | Documentation | DONE | Documented source/purpose of SIMULATED_PAGE_DATA in profile_extractor.py. |
| **M33** | Typos in planning docs | Documentation | DONE | Fixed EXUECTION typos in planning filenames. |

## Low-Severity Issues (L1 - L18)

| ID | Issue | Workstream | Status | Notes |
|---|---|---|---|---|
| **L1** | Hardcoded seeds in simulators | Refactoring | DONE | Introduced DEFAULT_SEED in config.py and used in critical scripts. |
| **L2** | False positive TEMP matches | Refactoring | DONE | Renamed generic 'temp' instances to descriptive names. |
| **L3** | Print-based QC stubs | Infrastructure | DONE | Replaced print stubs with logger.info in qc/reporting.py. |
| **L4** | Style inconsistencies | Refactoring | DONE | Standardized docstrings and spacing in mechanism track. |
| **L5** | Redundant comments | Infrastructure | DONE | Removed 'simulated' labels from CI and linked to real verification script. |
| **L10** | Acknowledged arbitrary thresholds | Documentation | DONE | Created governance/CALIBRATION_NOTES.md with justifications. |
| **L11** | Glossary update | Documentation | DONE | Added MetricResult and HypothesisResult to GLOSSARY.md. |
| **L12** | Command help text | Infrastructure | DONE | Refined CLI help strings for better user guidance. |

## Long-Term Severity Issues (LT1 - LT17)

| ID | Issue | Workstream | Status | Notes |
|---|---|---|---|---|
| **LT1** | Structured JSON Logging | Observability | TODO | |
| **LT2** | Contextual Metadata in Logs | Observability | TODO | |
| **LT3** | Performance Profiling | Observability | TODO | |
| **LT4** | Error Provenance (Error Codes) | Observability | TODO | |
| **LT5** | Sensitivity Sweep Execution | Robustness | TODO | |
| **LT6** | Threshold Calibration | Robustness | TODO | |
| **LT7** | Confound Documentation | Robustness | TODO | |
| **LT8** | Null Hypothesis Testing | Robustness | TODO | |
| **LT9** | Comprehensive Boundary Testing | Validation | TODO | |
| **LT10** | Invariance Testing | Validation | TODO | |
| **LT11** | Automated Fixture Comparison | Validation | TODO | |
| **LT12** | Model Unit Tests | Validation | TODO | |
| **LT13** | Schema Migration (Token vs Word) | Purity | TODO | |
| **LT14** | API Harmonization | Purity | TODO | |
| **LT15** | Symbol/Glyph Unification | Purity | TODO | |
| **LT16** | Output Interpretation Guide | Documentation | TODO | |
| **LT17** | Minimal Demo / Environment | Documentation | TODO | |

