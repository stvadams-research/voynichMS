# Execution Plan: Low-Severity Audit Remediation (L1 - L18)

This plan outlines the actions required to resolve the 18 low-severity issues identified in the `COMPREHENSIVE_AUDIT_REPORT.md`. These issues primarily concern code style, maintainability, and minor polish.

---

## Workstream 1: Maintenance and Polish

| ID | Issue | Remediation Action |
|---|---|---|
| **L1** | Hardcoded seeds in simulators | Replace `seed=42` with a configurable parameter or move to `phase1_foundation/config.py`. |
| **L2** | False positive TEMP matches | Rename variables/comments containing "TEMP" (e.g., temporal, template) to avoid core_audit noise. |
| **L3** | Print-based QC stubs | Replace `print("Generating...")` in `qc/reporting.py` with standard `logging` or removal. |
| **L4** | Style inconsistencies | Align whitespace and docstring formatting across the `phase5_mechanism/` submodules. |
| **L5** | Redundant comments | Remove legacy comments referring to `_run_simulated()` methods that have been deleted. |

## Workstream 2: Documentation Minor

| ID | Issue | Remediation Action |
|---|---|---|
| **L10** | Acknowledged arbitrary thresholds | Formalize "TODO: justify this" comments into a central "Calibration Notes" document. |
| **L11** | Glossary update | Add "MetricResult" and "HypothesisResult" definitions to `governance/GLOSSARY.md`. |
| **L12** | Command help text | Refine `typer` help strings in `phase1_foundation/cli/main.py` for clarity. |

---

## Execution Strategy

Low-priority items should be addressed during periodic maintenance windows or as "scouting" tasks during more significant refactors.

1.  **Refactoring:** L1, L2, L4.
2.  **Infrastructure Polish:** L3, L5, L12.
3.  **Documentation Polish:** L10, L11.
