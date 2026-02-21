# Changelog

All notable changes to the Voynich Manuscript Structural Analysis project.

## [Unreleased] - Cleanup Sprint (2026-02-20)

### Added
- 237 new unit tests across Phases 4, 5, 6, and 10 (595 total passing)
- `session_scope()` context manager on `MetadataStore` for safe session handling
- `--seed` and `--output-dir` argparse flags on Phase 2-7 entry-point scripts
- `governance/DEVELOPER_GUIDE.md` covering metric, phase, and test authoring
- `governance/GLOSSARY.md`, `governance/REPLICATION_GUIDE.md`
- Inline math documentation for Montemurro KL-divergence, Parsimony entropy, ClusterTightness
- Debug logging for unparseable lines in `EVAParser`

### Fixed
- Boolean truthiness bug in `mapping_stability.py` (collapsed threshold comparison)
- Removed simulated-logic fallbacks across 10 files (prior audit)
- Bare `except:` clauses replaced with specific exception types

### Changed
- Renamed `phase12_replicate` to `support_replicate` for clarity
- Standardized `sys.exit(0)` on all Phase 2-3 script entry points
- Documented "orphaned" scripts (`demo_phase_2_1.py`, `run_phase_3_1.py`) with purpose notes

## [Phase 11] - 2026-02-20

### Added
- Stroke topology analysis with fast-kill gate
- Number pattern checker

## [Phase 10] - 2026-02-18

### Added
- Stages 1-5 admissibility pipeline (Methods F/G/H/I/J/K)
- Stage 5b targeted adjudication for Method K
- Multi-seed robustness gates for all methods

### Results
- Method F (generation vs encoding): passed robustness gates
- Methods H/I (typology + cross-linguistic): executed
- Method J (steganographic extraction): robustly weakened under strict controls
- Method K (residual gap anatomy): did not hold strict weakened status across seeds

## [Phase 4 Expansion] - 2026-02-17

### Added
- Bounded diagnostics expansion: Kolmogorov/compression, NCD, image/music encoding controls
- Boundary-persistence modeling with parameter sweeps
- Out-of-sample folio and section holdout benchmarks
- Section-specific override support (herbal:0.10:0.65:0.05)

### Results
- Boundary-persistence signal stable on order constraints (no collapse)
- Herbal-only override improved section-holdout order wins from 22/30 to 27/30

## [Publication] - 2026-02-10 to 2026-02-15

### Added
- Zenodo DOI and citation metadata
- LLM-documented data sources
- Credits and acknowledgments
- Publication generation pipeline

### Fixed
- Redesigned publication process (previously flawed)

## [Phases 6-7] - 2026-02-08

### Added
- Phase 6: Formal system analysis, lattice traversal, adversarial testing
- Phase 7: Human factors, production ergonomics, scribe analysis

## [Audit] - 2026-02-08 to 2026-02-09

### Added
- 5-phase comprehensive code audit
- Skeptic enhancement rounds (10 total)

### Fixed
- Programmatic code cleanup pass
- Simulated logic removal across 10 files

## [Phases 2-3] - 2026-02-07

### Added
- Phase 2: Stress tests (mapping stability, information preservation, locality)
- Phase 3: Constrained Markov synthesis, gap continuation, equivalence testing

## [Phase 1] - 2026-02-06

### Added
- Initial project structure with multi-phase architecture
- EVA transcription parser (IVTFF format)
- MetadataStore (SQLAlchemy + SQLite)
- Foundation metrics library (RepetitionRate, ClusterTightness, InformationDensity)
- Run provenance system
- RandomnessController (FORBIDDEN/SEEDED/UNRESTRICTED modes)
