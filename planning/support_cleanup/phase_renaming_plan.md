# Phase Renaming and Standardization Plan

## 1. Objective
Standardize the naming convention for all research phases across the repository to ensure chronological sorting, consistency, and clarity.

## 2. Naming Convention
All phase-related directories in `src/`, `scripts/`, `configs/`, `planning/`, and `results/reports/` will follow the pattern:
`phase[N]_[name]` (e.g., `phase1_foundation`).

## 3. Phase Mapping
| Phase | Original Name | New Standardized Name |
|---|---|---|
| 1 | phase1_foundation | phase1_foundation |
| 2 | phase2_analysis | phase2_analysis |
| 3 | phase3_synthesis | phase3_synthesis |
| 4 | phase4_inference | phase4_inference (replaces phase_4) |
| 5 | phase5_mechanism | phase5_mechanism |
| 6 | phase6_functional | phase6_functional |
| 7 | phase7_human | phase7_human |
| 8 | phase8_comparative | phase8_comparative |
| 9 | phase9_conjecture | phase9_conjecture |

## 4. Support and Governance Directories
These will be renamed to provide clarity and prevent alphabetical intermingling with research phases:
- `core_audit` -> `core_audit`
- `core_skeptic` -> `core_skeptic`
- `support_visualization` -> `support_visualization`
- `support_preparation` -> `support_preparation`
- `support_cleanup` -> `support_cleanup`
- `archive_legacy` -> `archive_legacy`

## 5. Implementation Steps

### Phase 1: Directory Renaming
Use `git mv` (where possible) or `mv` to rename directories across:
- `src/`
- `scripts/`
- `configs/`
- `planning/`
- `results/reports/`

### Phase 2: Codebase Ripple Effect (Imports)
Update all Python imports using a bulk `sed` operation:
- `from phase1_foundation...` -> `from phase1_foundation...`
- `import phase2_analysis...` -> `import phase2_analysis...`
- (And so on for all 9 phases and 4 core support modules)

### Phase 3: Script and Config Path Updates
Update all hardcoded string paths in:
- `scripts/*.sh`
- `src/**/*.py`
- `configs/**/*.json`
- `pyproject.toml` (especially entry points)

### Phase 4: Documentation Integrity
Update internal Markdown links in `planning/` and `governance/`.

## 6. Verification
1.  Run `phase1_foundation status` (if entry point is updated).
2.  Run `pytest`.
3.  Run `scripts/support_preparation/generate_publication.py` to ensure it can still find all reports.
