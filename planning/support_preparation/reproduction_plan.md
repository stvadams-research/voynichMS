# Publication Reproduction Plan

This document serves as the master instruction set for generating the high-fidelity research summary. By executing this plan, we can synthesize the current state of all project findings into a 20-30 page, academic-grade Microsoft Word document.

## 1. Prerequisites
The generator requires the `python-docx` library to handle complex Word formatting and image embedding.
```bash
pip install python-docx
```

## 2. Generation Command
To regenerate the full research summary, execute the following command from the project root:
```bash
python3 scripts/support_preparation/generate_publication.py
```

## 3. Output Location
To prevent project clutter, all outputs are directed to:
`results/reports/publication/Voynich_Research_Summary_Draft.docx`

## 4. Methodology: The Narrative Synthesis
The generator does not just copy-paste; it performs a **synthesized extraction** across three distinct layers:

### A. Narrative Flow (The Inverted Pyramid)
Every chapter is automatically structured to move from accessibility to rigor:
1.  **Headline**: A bold, scientifically defensible discovery.
2.  **Executive Concept**: A layman-friendly analogy explaining the "Why."
3.  **Technical Evidence**: Long-form extraction of math, tables, and logic from phase-specific reports.

### B. Data Sources
The script dynamically pulls substance from the following authoritative records:
- **Phase 2 (Analysis)**: `results/reports/phase2_analysis/FINAL_REPORT_PHASE_2.md`
- **Phase 4 (Inference)**: `results/reports/phase4_inference/PHASE_4_CONCLUSIONS.md`
- **Phase 5 (Mechanism)**: `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md`
- **Visuals**: Latest PNGs from `results/reports/visuals/`.

## 5. Maintenance and Customization
*   **To change the narrative**: Update the `layman` and `headline` strings within `scripts/support_preparation/generate_publication.py`.
*   **To add new research phases**: Update the `generate()` method in the script to include new `add_chapter()` calls pointing to your latest `.md` reports.
*   **To update the Markdown Master**: Run `python3 scripts/support_preparation/assemble_draft.py` to get a unified `.md` version in the same output directory.

## 6. Verification Checklist
- [ ] Document exceeds 20 pages in length.
- [ ] Repetition Rate distribution plot is embedded.
- [ ] Language ID False Positive chart is embedded.
- [ ] "Implicit Constraint Lattice" is identified as the terminal phase5_mechanism.
