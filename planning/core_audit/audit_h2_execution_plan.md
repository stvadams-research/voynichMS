# Execution Plan: High-Severity Audit Remediation (H2 Series)

This plan addresses high-severity logic errors and silent failure modes identified in `COMPREHENSIVE_AUDIT_REPORT_2.md`.

## Issue H1: Boolean Truthiness Bug in Mapping Stability
**Finding:** `if (a and b and c)` fails in `mapping_stability.py:113` when any stability score is correctly 0.0.
**Remediation:**
1. Locate the logic block calculating `overall_stability`.
2. Replace the truthiness check with explicit `is not None` checks:
   `if all(v is not None for v in [avg_seg, avg_ord, avg_omit])`.
3. Verify via unit test that a 0.0 score correctly propagates through `min()`.

## Issue H2: Silent Exception Swallowing in Metrics
**Finding:** `except Exception: continue` in `metrics/library.py` drops corrupted data without notifying the user or logs.
**Remediation:**
1. Identify all instances of silent `continue` or `pass` in `src/phase1_foundation/metrics/`.
2. Implement scoped logging using `logger.warning()` or `logger.error()`.
3. Include the item identifier (e.g., `embedding_id`) in the log message to assist in debugging corrupted data assets.
