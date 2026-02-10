# Execution Plan: Medium-Severity Audit Remediation (M2 Series)

This plan addresses terminology and clarity risks identified in `COMPREHENSIVE_AUDIT_REPORT_2.md`.

## Issue M1: Terminology Inconsistency in CLI
**Finding:** Command arguments use "Word" and "Token" interchangeably in `cli/main.py`, violating the project's conceptual distinction.
**Remediation:**
1. Audit all `typer` commands in `src/foundation/cli/main.py`.
2. Standardize all transcription-related arguments to use `token_id` or `token_str`.
3. Standardize all image-segmentation arguments to use `word_id`.
4. Update `help` strings to explicitly mention the "Token (Transcript) vs Word (Visual)" distinction.
