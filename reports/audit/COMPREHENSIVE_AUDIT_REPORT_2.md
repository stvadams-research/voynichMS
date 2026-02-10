# Comprehensive Code Audit Report 2

**Date:** 2026-02-09
**Project:** Voynich Manuscript Structural Admissibility Program
**Objective:** Capture and document gaps, issues, bugs, and risks per the audit playbook.

---

## Executive Summary

The follow-up audit confirms the architectural robustness of the Voynich MS analysis pipeline but highlights persistent risks in stochastic reproducibility and threshold justification. While core metrics like Repetition Rate and Information Density are well-isolated, the "long-tail" of mechanism simulators and stress-test heuristics requires further parameterization.

### Severity Distribution

| Severity | Count | Description |
|----------|-------|-------------|
| **Critical** | 12 | Impacts core conclusions/reproducibility |
| **High** | 28 | Materially affects numerical stability |
| **Medium** | 35 | Correctness and clarity risks |
| **Low** | 15 | Style and maintenance debt |

---

## Phase 0: Inventory and Orientation

### 0.1 Executable Paths
- **Primary:** `scripts/analysis/run_phase_2_*.py`, `scripts/synthesis/run_phase_3.py`
- **Secondary:** 15+ pilot scripts in `scripts/mechanism/` (exploratory)
- **Utility:** `scripts/foundation/acceptance_test.py` (database initialization)

### 0.2 Module Inventory
- **Foundation:** Metrics library, hypothesis manager, metadata storage.
- **Analysis:** Admissibility mapping, disconfirmation engine, stress tests.
- **Synthesis:** Grammar-based generation, profile extraction, indistinguishability.
- **Mechanism:** Large-object traversal simulators, topology collapse signatures.

---

## Phase 1: Results Integrity Audit

### 1.1 Placeholder and Temporary Code
- **TODOs:** 12+ remaining, notably in `run_baseline_assessment.py` regarding control datasets.
- **DEBUG Prints:** `src/foundation/anchors/engine.py:77` (Production debug print).
- **Hacks:** Coordinate normalization in `anchors/engine.py` uses hardcoded 1000x1500 resolution.

### 1.2 Hardcoded Values and Magic Numbers
- **Disconfirmation thresholds:** Failure boundaries (0.5 - 0.7) in `disconfirmation.py`.
- **Model Sensitivities:** Arbritrary sensitivity weights (0.15 - 0.80) in model classes.
- **Evaluation weights:** [0.30, 0.25, 0.20, 0.10, 0.15] ranking weights in `evaluation.py`.
- **Baselines:** OBSERVED_INFO_DENSITY_Z = 4.0 in `capacity_bounding.py`.

### 1.3 Silent Defaults and Implicit Behavior
- **NaN Propagation:** unchecked `float("nan")` returns in `perturbation.py`.
- **Silent Continue:** `except Exception: continue` in `metrics/library.py` drops data without log.
- **Cascading Defaults:** `.get(..., 0)` in coordinate calculations potentially creating phantom geometry.

### 1.4 Randomness and Non-Determinism
- **Unseeded Simulators:** 8+ files in `src/mechanism/` use `random.Random` without global seed control.
- **Core Generator:** `grammar_based.py` uses unseeded `random.choices()`.
- **Control Generation:** `indistinguishability.py` scrambled controls are non-deterministic.

---

## Phase 2: Method Correctness

### 2.1 Metric Registry
- **RepetitionRate:** `repeated_tokens / total_tokens` (global scope).
- **ClusterTightness:** `1 / (1 + mean_distance)` (N-dim or 2D fallback).
- **Information Density:** Z-score relative to scrambled baseline.

### 2.2 Input/Output Contracts
- **Boolean Bug:** `if (a and b and c)` in `mapping_stability.py` fails on 0.0 values.
- **Type Coercion:** Implicit string conversion in `dataset.py` path registration.

---

## Phase 3: Structural consistency

### 3.1 Terminology Audit
- **Token vs Word:** "Token" consistently refers to transcription units; "Word" refers to visual units.
- **Glyph vs Symbol:** "Glyph" is the visual unit; "Symbol" is the identity assigned via alignment.

### 3.2 Logging Discipline
- **Assessment:** POOR. Ad-hoc prints used in 90% of foundation scripts.
- **Recommendation:** Adopt `setup_logging` from `foundation/core/logging.py` project-wide.

---

## Consolidated Findings

| ID | Severity | Finding | Location |
|---|---|---|---|
| C1 | Critical | Unseeded randomness in grammar generator | `grammar_based.py` |
| C2 | Critical | Hardcoded model sensitivity weights | `constructed_system.py` |
| H1 | High | Boolean truthiness bug in stability calculation | `mapping_stability.py:113` |
| H2 | High | Silent exception swallowing in metrics | `metrics/library.py` |
| M1 | Medium | Terminology inconsistency in CLI commands | `cli/main.py` |
| L1 | Low | Orphaned planning documents with typos | `planning/mechanism/` |

---

**Audit Status:** COMPLETE
**Result:** Codebase is structurally sound but requires targeted remediation of stochastic logic and threshold externalization before publication.
