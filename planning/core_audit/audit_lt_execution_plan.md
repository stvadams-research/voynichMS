# Execution Plan: Long-Term Audit Remediation (LT1 - LT17)

This plan outlines the long-term strategic actions required to move the Voynich MS Structural Admissibility Program from "reproduction-ready" to "production-hardened." These tasks focus on deep architectural consistency, advanced observability, and comprehensive methodological validation.

---

## Track 1: Advanced Observability and Logging (LT1 - LT4)
**Goal:** Transition from basic logging to structured, contextual observability that supports automated phase2_analysis of execution paths.

| ID | Task | Action |
|---|---|---|
| **LT1** | Structured JSON Logging | Implement a JSON-format logger in `logging.py` to facilitate machine-parsing of execution traces. |
| **LT2** | Contextual Metadata | Update loggers to automatically include `run_id`, `dataset_id`, and `thread_id` in every log record. |
| **LT3** | Performance Profiling | Integrate timing decorators into the `StressTest` and `Metric` base classes to track bottlenecks. |
| **LT4** | Error Provenance | Add unique error codes to all `ValueError` and `RuntimeError` instances for easier troubleshooting in the field. |

---

## Track 2: Methodological Robustness & Sensitivity (LT5 - LT8)
**Goal:** Execute the planned sensitivity sweeps to quantify the stability of the program's conclusions.

| ID | Task | Action |
|---|---|---|
| **LT5** | Sensitivity Sweep Execution | Implement `scripts/phase2_analysis/run_sensitivity_sweep.py` to automate the testing of 100+ parameter permutations. |
| **LT6** | Threshold Calibration | Analyze results from LT5 to derive "statistically optimal" thresholds for falsification criteria. |
| **LT7** | Confound Documentation | Create `governance/METHODOLOGICAL_CONFOUNDS.md` documenting known limits of the metrics (e.g., impact of transcription noise). |
| **LT8** | Null Hypothesis Testing | Establish a battery of "known random" datasets to verify that metrics correctly return null results. |

---

## Track 3: Total Validation & Regression (LT9 - LT12)
**Goal:** Expand the test suite to cover all edge cases and prevent accidental drift in findings.

| ID | Task | Action |
|---|---|---|
| **LT9** | Comprehensive Boundary Testing | Add unit tests for every module in `src/` specifically targeting empty sets, NaN inputs, and infinite values. |
| **LT10** | Invariance Testing | Implement tests to verify that certain metrics (e.g., RepetitionRate) remain constant under token renaming. |
| **LT11** | Automated Fixture Comparison | Integrate `scripts/core_audit/generate_fixtures.py` into the CI/CD pipeline to block PRs that change baseline numbers. |
| **LT12** | Model Unit Tests | Create dedicated tests for each `ExplicitModel` to verify their `apply_perturbation` logic independently. |

---

## Track 4: Terminological and Schema Purity (LT13 - LT15)
**Goal:** Resolve the fundamental Word/Token/Glyph/Symbol ambiguity at the persistence layer.

| ID | Task | Action |
|---|---|---|
| **LT13** | Schema Migration | Rename database columns (e.g., in `word_alignments`) to strictly enforce the "Token" (transcription) vs "Word" (image) distinction. |
| **LT14** | API Harmonization | Update all `MetadataStore` method signatures to use standardized terminology. |
| **LT15** | Symbol/Glyph Unification | Refactor the `GlyphCandidate` and `GlyphAlignment` relationship to clarify the "Visual Unit" vs "Identity Symbol" distinction. |

---

## Track 5: Documentation & Public Review Readiness (LT16 - LT17)
**Goal:** Prepare the project for external core_audit and academic publication.

| ID | Task | Action |
|---|---|---|
| **LT16** | Output Interpretation Guide | Create `governance/INTERPRETATION_GUIDE.md` explaining how to read the JSON results from Phase 2 and 3. |
| **LT17** | Minimal Demo (Demo Environment) | Create a Docker-based or automated script that sets up the environment and runs a full Phase 1-3 sequence in <10 minutes. |

---

## Execution Phasing

1.  **Quarterly Maintenance:** Tracks 1 and 3 (Observability & Validation).
2.  **Pre-Publication Pass:** Track 2 (Sensitivity Analysis).
3.  **Architectural Sprint:** Track 4 (Schema Migration).
4.  **Release/Review Prep:** Track 5 (Interpretation & Demo).
