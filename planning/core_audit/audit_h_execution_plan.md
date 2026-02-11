# Execution Plan: High-Severity Audit Remediation (H1 - H31)

This plan outlines the specific actions required to resolve the 31 high-severity issues identified in the `COMPREHENSIVE_AUDIT_REPORT.md`. These issues primarily impact results integrity, provenance, and reproducibility.

---

## Workstream 1: Logic and Correctness (Correctness, Bugs, Silent Failures)

Targeting issues where code logic is flawed or fails silently without alerting the user.

| ID | Issue | Remediation Action |
|---|---|---|
| **H1** | Boolean truthiness bug in `mapping_stability.py:113` | Replace `if (a and b and c)` with explicit `is not None` checks to allow 0.0 values. |
| **H2** | Silent exception swallowing in `metrics/library.py` | Replace `except Exception: continue` with proper logging of corrupted embeddings. |
| **H3** | Missing data fallbacks in `feature_discovery.py` | Add explicit warnings or raise errors when functions return random/hardcoded values due to missing data. |
| **H4** | Silent fallback from tokens to alignments | Log a `WARNING` in `metrics/library.py` when transcription fallback occurs. |
| **H5** | Phantom bounding boxes in `perturbation.py` | Validate coordinate presence before `.get()` defaults; log warnings for missing geometry. |
| **H6** | Silent simulated data in `profile_extractor.py` | Log a `WARNING` when `store is None` and simulated profiles are returned. |
| **H7** | NaN propagation in `perturbation.py` | Add `np.isnan()` guards and explicit sanitization for insufficient data returns. |
| **H8** | Arbitrary smoothing in `destructive.py` | Parameterize the `std_control` default (0.1) and document its statistical basis. |
| **H9** | Bare `except:` clauses | Replace with `except Exception:` or specific error types in `quire_analysis.py`, `scribe_coupling.py`, and `network_features/analyzer.py`. |
| **H26** | Empty-list division errors | Implement defensive checks (`if len(list) > 0`) before all division operations across identified files. |
| **H30** | Empty dataset return values | Update `RepetitionRate.calculate()` to return `float("nan")` instead of `0.0` for empty datasets. |

---

## Workstream 2: Determinism and Randomness Control

Ensuring all stochastic processes can be reproduced exactly.

| ID | Issue | Remediation Action |
|---|---|---|
| **H22** | Unseeded mechanism simulators | Update all simulators in `src/phase5_mechanism/` to accept and utilize a `seed` parameter. |
| **H23** | Unseeded text generator page seeds | Pass the global run seed into the page-level seed generation in `text_generator.py`. |

---

## Workstream 3: Infrastructure (Logging, Provenance, Metadata)

Enhancing the traceability and observability of the system.

| ID | Issue | Remediation Action |
|---|---|---|
| **H10** | Missing provenance in scripts | Update all scripts in `scripts/*.py` to use a centralized result writer that includes `run_id`, `git_commit`, and `timestamp`. |
| **H11** | Minimal logging usage | Implement a standard `logging` configuration in `src/phase1_foundation/core/logging.py` and adopt it across all 118 source files. |
| **H12** | Production DEBUG prints | Remove or convert `print(f"DEBUG: ...")` at `src/phase1_foundation/anchors/engine.py:77` to standard logging. |

---

## Workstream 4: Documentation and Methodological Clarity

Providing the necessary context for external readers and reviewers.

| ID | Issue | Remediation Action |
|---|---|---|
| **H13** | Missing `governance/METHODS_REFERENCE.md` | Create a comprehensive guide explaining every metric, its formula, and its interpretation. |
| **H14** | Missing `governance/REPRODUCIBILITY.md` | Create a step-by-step guide for clean-room execution and result verification. |
| **H18** | Undocumented stability thresholds | Document the 7 thresholds (0.3-0.7) in `mapping_stability.py` with their justification. |
| **H19** | Undocumented scaling constants | Document perturbation scaling constants (0.5, 0.35, 2) in `perturbation.py`. |
| **H20** | Positional bias probability | Move the hardcoded `0.4` probability in `text_generator.py` to `config.py`. |
| **H21** | Hardcoded control metrics | Parameterize the metrics used for scrambled control generation in `indistinguishability.py`. |
| **H27** | Terminology inconsistency | Perform a global audit and update to standardize "Token" vs "Word" vs "Glyph". |
| **H28** | No sensitivity analysis | Plan and execute a sensitivity sweep for key model weights and document the stability of conclusions. |
| **H31** | Skeletal `RUNBOOK.md` | Expand to include database population (Phase 1) and generator matching (Phases 4-6). |

---

## Workstream 5: Verification and Validation (Tests and Quality)

Building confidence in the correctness and stability of the results.

| ID | Issue | Remediation Action |
|---|---|---|
| **H15** | Missing regression fixtures | Establish `tests/fixtures/` with locked JSON outputs for known inputs to detect drift. |
| **H16** | Missing boundary case tests | Add unit tests for empty inputs, single-token datasets, and degenerate geometries. |
| **H29** | Clean-room execution failure | Create a `scripts/verify_reproduction.sh` that checks environment, data, and deterministic outputs. |

---

## Workstream 6: Architectural Cleanup

Resolving technical debt and ambiguity.

| ID | Issue | Remediation Action |
|---|---|---|
| **H17** | Duplicated iteration limits | Centralize `MAX_PAGES_PER_TEST` and `MAX_TOKENS_ANALYZED` into `src/phase1_foundation/core/config.py`. |
| **H24** | Dual RepetitionRate naming | Rename internal keys to `token_repetition_rate` and `vocabulary_entropy_rate` for clarity. |
| **H25** | ClusterTightness path ambiguity | Add a `method` field to the `MetricResultRecord` to indicate if embedding or bbox path was used. |

---

## Execution Phasing

1.  **Phase A (Logic & Determinism):** Address H1, H2, H7, H9, H22, H23, H30. (Critical for results)
2.  **Phase B (Infrastructure):** Address H10, H11, H12. (Critical for provenance)
3.  **Phase C (Documentation):** Address H13, H14, H18-H21, H27, H31. (Critical for review)
4.  **Phase D (Verification):** Address H15, H16, H28, H29. (Final validation)
