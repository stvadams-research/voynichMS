# Cleanup Execution Plan: Structural Integrity & De-Cluttering

## 1. Vision and Objective
This project has grown organically through multiple research phases (Foundation to Publication). While this growth represents progress, it has introduced structural inconsistencies, duplicate reporting paths, and naming irregularities. 

The objective of this cleanup pass is to transition from an "Experiment-Active" structure to a "Publication-Ready" architecture without losing historical context or reproducibility.

## 2. Identified Inconsistencies and Clutter

### A. Reporting Path Fragmentation
- **Issue**: There are two top-level reporting directories: `/reports/` and `/results/reports/`.
- **Target**: Consolidate all human-readable findings into `/results/reports/`.
- **Logic**: `/results/` should be the canonical sink for all output artifacts (Data, Reports, Visuals).

### B. Naming Conventions in Planning
- **Issue**: Files in `/planning/` follow multiple formats (e.g., `Phase 2.1_Execution Plan.md` vs `PHASE_5b_EXECUTION_PLAN.md`).
- **Target**: Standardize to `PHASE_[X]_[NAME]_PLAN.md`.

### C. Documentation Redundancy
- **Issue**: High-level guides (Reproducibility, Methods) exist both at the root and in `/docs/`.
- **Target**: Keep the root files as the canonical "entry points" and ensure `/docs/` contains specialized, low-level technical documentation (e.g., `ARCHITECTURE.md`, `RUNBOOK.md`).

### D. Orphaned and Legacy Plans
- **Issue**: Numerous execution plans in `/planning/audit/` and `/planning/skeptic/` may no longer reflect the final project state.
- **Target**: Audit these files. Move completed/obsolete plans to an `/archive/` directory to preserve provenance without cluttering the active workspace.

## 3. Structural Targets (The "After" State)

```text
voynich/
├── src/                # Library code
├── scripts/            # Executables
├── configs/            # Parameter files
├── docs/               # Technical specs (High-level)
├── results/            # ALL outputs (Reports, Data, Visuals, Publication)
│   ├── reports/        # Consolidated research papers
│   ├── data/           # Derived datasets
│   └── visuals/        # Unified plot storage
├── planning/           # ACTIVE execution plans
│   ├── archive/        # COMPLETED/LEGACY plans
│   └── [layer_name]/   # Current phase plans
└── tests/              # Enforcement
```

## 4. Execution Strategy

### Phase 1: Consolidation (Reports)
1.  Move contents of root `/reports/` into `/results/reports/`.
2.  Update any scripts or internal links that reference the old `/reports/` path.
3.  Remove the empty root `/reports/` directory.

### Phase 2: Standardizing Planning
1.  Apply `snake_case` naming to all files in `/planning/`.
2.  Identify "Terminal" plans (those whose phases are marked 'Completed' in the Roadmap).
3.  Move Terminal plans into `/planning/archive/` while retaining their subdirectory structure.

### Phase 3: Root Cleanup
1.  Ensure all transient drafts (e.g., `.docx` or `.tmp` files) are moved to `/results/reports/publication/` or deleted if redundant.
2.  Verify `.gitignore` prevents future leakage of these files into the root.

### Phase 4: Path Integrity Audit
1.  Run a project-wide search for internal Markdown links.
2.  Fix any broken links resulting from the move.
3.  Verify that `generate_publication.py` and `assemble_draft.py` still function with the consolidated paths.

## 5. Safety Guardrails
- **No Deletion of Logic**: This plan explicitly avoids deleting code (`src/`, `scripts/`, `tests/`) or primary result data (`data/`, `runs/`).
- **Atomic Renames**: Use `git mv` where possible to preserve file history.
- **Verification First**: Every move must be followed by a link-integrity check.

## 6. Next Steps
1. [ ] Final review of the "After" state architecture.
2. [ ] Identify any hardcoded paths in the codebase that rely on the root `/reports/` directory.
3. [ ] Commence Phase 1 (Report Consolidation).
