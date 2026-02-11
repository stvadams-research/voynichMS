# Next Steps: Project Refinement & Academic Polish

This document identifies high-value engineering and research gaps that, if addressed, would significantly enhance the academic quality and skeptic-proofing of the Voynich Manuscript project.

## 1. Publication Enhancements (High Priority)

### A. Formal Citation Management (BibTeX Integration)
*   **Gap**: Currently, research references are stored in a flat Markdown file. Academic publications require a standardized bibliography (e.g., APA or Chicago style).
*   **Feature**: Implement a `support_research/references.bib` or `.json` file and update `generate_publication.py` to automatically append a "References" section with properly formatted citations.

### B. Native Word Table Rendering
*   **Gap**: The publication generator currently renders technical data tables as plain text blocks.
*   **Feature**: Use the `python-docx` Table API to render results (like the Phase 5 Mechanism Comparison) as native, high-fidelity Word tables with professional formatting.

## 2. Technical and Integrity Gaps (Security & Rigor)

### A. Schema Migration Governance (Alembic)
*   **Gap**: As research enters Phase 8 (Comparative), the database schema (`data/voynich.db`) may need to evolve to support new metadata.
*   **Feature**: Fully implement Alembic migrations within `src/phase1_foundation/storage/` to ensure that database changes are version-controlled and reproducible across environments.

### B. Automated End-to-End Replication (CI/CD)
*   **Gap**: While `replicate_all.py` exists, it is not currently triggered by the CI pipeline (`scripts/ci_check.sh`).
*   **Feature**: Add a "Smoke Test" mode to `replicate_all.py` that runs a subset of all 9 phases on every Pull Request to ensure that code changes never break the narrative flow or data integrity.

## 3. Advanced Diagnostic Features (The "Wow" Factor)

### A. Interactive Lattice Explorer
*   **Gap**: The "Implicit Constraint Lattice" is the project's core discovery, but it is currently represented as static entropy scores.
*   **Feature**: Create a lightweight web-based or Plotly-based tool that allows a researcher to "traverse" the lattice, seeing the deterministic successors for any given bigram and position. This would be a powerful tool for visual peer review.

### B. Cross-Scribe Stability Mapping
*   **Gap**: We have established sectional stability (Phase 5I), but a granular mapping of mechanism stability across different "Hands" (Scribes) would provide the final "Kill Step" for any remaining authorial theories.
