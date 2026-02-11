# Codebase Inventory

**Date:** 2026-02-07
**Status:** Initial Audit

## 1. Source Modules (`src/`)

### Foundation Layer (`src/phase1_foundation/`)
- **Core:** `core/` (IDs, random, geometry) - CRITICAL
- **Storage:** `storage/` (MetadataStore, SQLite, filesystem) - CRITICAL
- **CLI:** `cli/` (Main entry point) - CRITICAL
- **Metrics:** `metrics/` (RepetitionRate, ClusterTightness) - CRITICAL
- **Hypotheses:** `hypotheses/` (Destructive hypotheses) - CRITICAL
- **Controls:** `controls/` (Scramblers, synthetic) - CRITICAL
- **Regions:** `regions/` (Graph, embeddings, dummy) - *Review `dummy.py`*
- **Segmentation:** `segmentation/` (Dummy implementations) - *Review `dummy.py`*
- **Alignment:** `alignment/` (Engine) - CRITICAL
- **Anchors:** `anchors/` (Engine) - CRITICAL
- **Runs:** `runs/` (Context, manager) - CRITICAL
- **Transcription:** `transcription/` (Parsers) - CRITICAL
- **Configs:** `configs/` (Logging, loaders) - CRITICAL
- **Analysis:** `phase2_analysis/` (Sensitivity, stability) - CRITICAL
- **Decisions:** `decisions/` (Registry) - CRITICAL
- **QC:** `qc/` (Anomalies, checks) - *Verify usage*

### Analysis Layer (`src/phase2_analysis/`)
- **Admissibility:** `admissibility/` (Manager) - CRITICAL (Phase 2.1)
- **Anomaly:** `anomaly/` (Constraint, capacity, semantic) - CRITICAL (Phase 2.4)
- **Models:** `models/` (Constructed system, visual grammar) - CRITICAL (Phase 2.3)
- **Stress Tests:** `stress_tests/` (Info preservation, locality) - CRITICAL (Phase 2.2)

### Synthesis Layer (`src/phase3_synthesis/`)
- **Generators:** `generators/` (GrammarBased) - CRITICAL (Phase 3.2)
- **Refinement:** `refinement/` (Feature discovery, etc.) - *Verify usage*
- `text_generator.py`: Main generator logic - CRITICAL
- `profile_extractor.py`: Section profiling - CRITICAL
- `gap_continuation.py`: Gap filling logic - CRITICAL
- `indistinguishability.py`: Turing test logic - CRITICAL

## 2. Dependencies
- Managed via `pyproject.toml` (setuptools).
- Key libs: `sqlalchemy`, `pydantic`, `typer`, `rich`, `numpy`, `scikit-learn` (implied by usage, check toml).

## 3. Entry Points
- CLI: `src/phase1_foundation/cli/main.py`
- Scripts: `scripts/` directory (various runner scripts)

## 4. Candidates for Cleanup/Deprecation
- `src/phase1_foundation/regions/dummy.py`: "Dummy" implementations might belong in tests or be renamed "Reference".
- `src/phase1_foundation/segmentation/dummy.py`: Same as above.
- `src/phase3_synthesis/refinement/`: Verify if these complex refinement modules are actually used in the current pipeline or if they were from an earlier iteration.
- `runs/`: Contains many old runs. Should be archived or cleaned up after baseline capture.
