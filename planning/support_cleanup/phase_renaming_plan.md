# Phase Renaming and Standardization Plan

## 1. Objective
Standardize the naming convention for all research phases across the repository to ensure chronological sorting, consistency, and clarity.

## 2. Naming Convention
All phase-related directories in `src/`, `scripts/`, `configs/`, `planning/`, and `results/reports/` will follow the pattern:
`phase[N]_[name]` (e.g., `foundation`).

## 3. Phase Mapping
| Phase | Original Name | New Standardized Name |
|---|---|---|
| 1 | foundation | foundation |
| 2 | analysis | analysis |
| 3 | synthesis | synthesis |
| 4 | inference | inference (replaces phase_4) |
| 5 | mechanism | mechanism |
| 6 | functional | functional |
| 7 | human | human |
| 8 | comparative | comparative |
| 9 | conjecture | conjecture |

## 4. Support and Governance Directories
These will be renamed to provide clarity and prevent alphabetical intermingling with research phases:
- `audit` -> `audit`
- `skeptic` -> `skeptic`
- `visualization` -> `visualization`
- `preparation` -> `preparation`
- `cleanup` -> `cleanup`
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
- `from foundation...` -> `from foundation...`
- `import analysis...` -> `import analysis...`
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
1.  Run `foundation status` (if entry point is updated).
2.  Run `pytest`.
3.  Run `scripts/support_preparation/generate_publication.py` to ensure it can still find all reports.
