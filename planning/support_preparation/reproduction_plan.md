# Publication Reproduction Plan

This document serves as the master protocol for synthesizing the project's research into a high-fidelity, peer-review-ready summary. 

## 1. Prerequisites
The generator utilizes the `python-docx` engine to handle academic-grade Word formatting and automated image embedding.
```bash
pip install python-docx
```

## 2. Execution Command
To synthesize the full research draft, execute the following command:
```bash
python3 scripts/support_preparation/generate_publication.py
```

## 3. Standardized Output
All synthesized reports are centralized in the results archive to prevent project root contamination:
`results/publication/voynich_research_summary_draft.docx`

## 4. Methodology: Academic Synthesis
The publication engine follows an **Assumption-Resistant Narrative** structure, ensuring that each phase builds an epistemic barrier against speculative translation.

### A. The Structural Hierarchy
Every chapter is synthesized using a three-tier information model:
1.  **Phase Headline**: A scientifically defensible, data-backed discovery.
2.  **Executive Abstract**: A high-level contextual summary defining the "So What?" of the phase results.
3.  **Technical Evidence**: A rigorous extraction of mathematical frameworks, data tables, and logical proofs from phase-specific reports.

### B. Authoritative Data Sources
The engine pulls technical substance from the following canonical records:
- **Phase 2 (Analysis)**: `results/reports/phase2_analysis/final_report_phase_2.md`
- **Phase 4 (Inference)**: `results/reports/phase4_inference/phase_4_conclusions.md`
- **Phase 5 (Mechanism)**: `results/reports/phase5_mechanism/phase_5_final_findings_summary.md`
- **Visual Evidence**: Latest analytical plots from `results/visuals/`.

## 5. System Maintenance
*   **Narrative Control**: To refine the academic tone or headlines, modify the `get_chapters()` dictionary within `scripts/support_preparation/generate_publication.py`.
*   **Modular Reporting**: To generate a report for a single phase (e.g., Phase 5), use the `--phase` flag:
    `python3 scripts/support_preparation/generate_publication.py --phase 5`

## 6. Scientific Verification Checklist
- [ ] Document adheres to the "Structure-First, Solution-Last" philosophy.
- [ ] Technical deep-dives include primary metrics (e.g., 5.68 Z-score, 88.11% entropy collapse).
- [ ] Visualizations are embedded with centered captions and correct figure references.
- [ ] No speculative "translation" claims are present in the technical chapters.
