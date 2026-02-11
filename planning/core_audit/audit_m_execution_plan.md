# Execution Plan: Medium-Severity Audit Remediation (M1 - M42)

This plan outlines the actions required to resolve the 42 medium-severity issues identified in the `COMPREHENSIVE_AUDIT_REPORT.md`. These issues primarily concern code correctness, clarity, and consistency.

---

## Workstream 1: Correctness and Robustness

| ID | Issue | Remediation Action |
|---|---|---|
| **M1** | Float equality comparisons | Replace direct `==` comparisons for floats with `math.isclose()` or delta checks. |
| **M2** | Implicit type coercion | Add explicit type casting or validation in token extraction modules. |
| **M3** | Implicit coordinate clipping | Add warnings or explicit boundary checks when clipping coordinates to [0,1]. |
| **M4** | Array shape assumptions | Implement `numpy` shape validation before matrix operations in metrics. |
| **M5** | Variance on single elements | Add defensive checks to return 0.0 or NaN when calculating variance on a single item. |
| **M6** | Max entropy for missing data | Replace silent 1.0 returns with NaN or logged warnings to distinguish from random data. |
| **M7** | Thread-local defaults | Update `RandomnessController` to default to `SEEDED` or `FORBIDDEN` instead of `UNRESTRICTED`. |

## Workstream 2: Consistency and Naming

| ID | Issue | Remediation Action |
|---|---|---|
| **M10** | Hypothesis outcome strings | Replace hardcoded strings ("SUPPORTED", "FALSIFIED") with a formal `Enum`. |
| **M11** | Glyph vs Symbol confusion | Clarify naming in `GlyphCandidateRecord` vs `GlyphAlignmentRecord` via documentation or refactoring. |
| **M12** | Line indexing inconsistency | Resolve `line_index` vs `line_number` across the query layer. |
| **M13** | Dual RepetitionRate formulas | Split or rename result keys to explicitly distinguish `token_repetition` from `vocabulary_entropy`. |
| **M14** | ClusterTightness path ambiguity | Add a `computation_path` metadata field to `MetricResult` (embeddings vs bboxes). |

## Workstream 3: Visibility and Errors

| ID | Issue | Remediation Action |
|---|---|---|
| **M20** | Non-actionable CLI errors | Update `phase1_foundation/cli/main.py` to provide specific recovery steps for common failures. |
| **M21** | Silent exception handling | Replace `except Exception: pass` in `dataset.py` and `qc/anomalies.py` with scoped logging. |
| **M22** | Ad-hoc warning prints | Convert `print("WARNING: ...")` statements to standard `logger.warning()` calls. |
| **M23** | Dictionary cascading defaults | Audit `.get()` chains in boundary calculations to prevent "default value soup." |

## Workstream 4: Documentation and Metadata

| ID | Issue | Remediation Action |
|---|---|---|
| **M30** | Ordering dependencies | Document whether `line_index` reflects visual order or transcription order. |
| **M31** | Feature discrimination ranges | Create a technical note documenting the expected ranges for discriminative features. |
| **M32** | Profile extraction fallbacks | Document the source and limitations of `SIMULATED_PAGE_DATA` in `profile_extractor.py`. |
| **M33** | Typos in planning docs | Fix "EXUECTION" typos in Phase 5c and 5f filenames. |

---

## Execution Strategy

These tasks should be grouped by module to minimize context switching:
1.  **Metric/Hypothesis Layer:** M1, M5, M6, M10, M13, M14.
2.  **Storage/Query Layer:** M2, M11, M12, M30.
3.  **Core/Infrastructure:** M3, M4, M7, M21, M22, M23.
4.  **Documentation/Cleanup:** M31, M32, M33.
