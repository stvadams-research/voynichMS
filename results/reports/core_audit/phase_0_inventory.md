# Phase 0: Inventory and Orientation

## 0.1 Executable Paths (Entry Points)

Identified the following scripts with `if __name__ == "__main__":` blocks, indicating they are intended entry points:

### Functional Analysis
- `scripts/phase6_functional/run_6c_adversarial.py`
- `scripts/phase6_functional/run_6b_efficiency.py`
- `scripts/phase6_functional/run_6a_exhaustion.py`

### Human Factors
- `scripts/phase7_human/run_7a_human_factors.py`
- `scripts/phase7_human/run_7c_comparative.py`
- `scripts/phase7_human/run_7b_codicology.py`

### Inference
- `scripts/phase4_inference/run_morph.py`
- `scripts/phase4_inference/run_network.py`
- `scripts/phase4_inference/run_lang_id.py`
- `scripts/phase4_inference/run_montemurro.py`
- `scripts/phase4_inference/run_topics.py`
- `scripts/phase4_inference/build_corpora.py`

### Synthesis
- `scripts/phase3_synthesis/run_test_c.py`
- `scripts/phase3_synthesis/run_test_b.py`
- `scripts/phase3_synthesis/run_indistinguishability_test.py`
- `scripts/phase3_synthesis/extract_grammar.py`
- `scripts/phase3_synthesis/run_baseline_assessment.py`
- `scripts/phase3_synthesis/run_test_a.py`
- `scripts/phase3_synthesis/run_phase_3.py`
- `scripts/phase3_synthesis/run_phase_3_1.py`

### Analysis (Phase 2)
- `scripts/phase2_analysis/run_phase_2_2.py`
- `scripts/phase2_analysis/run_phase_2_3.py`
- `scripts/phase2_analysis/run_phase_2_4.py`
- `scripts/phase2_analysis/demo_phase_2_1.py`
- `scripts/phase2_analysis/run_phase_2_1.py`

### Mechanism (Phase 5)
- `scripts/phase5_mechanism/run_5i_sectional_profiling.py`
- `scripts/phase5_mechanism/run_pilot.py`
- `scripts/phase5_mechanism/generate_all_anchors.py`
- `scripts/phase5_mechanism/run_5j_pilot.py`
- `scripts/phase5_mechanism/run_5k_pilot.py`
- `scripts/phase5_mechanism/categorize_sections.py`
- `scripts/phase5_mechanism/run_5i_anchor_coupling.py`
- `scripts/phase5_mechanism/run_5f_pilot.py`
- `scripts/phase5_mechanism/run_5g_pilot.py`
- `scripts/phase5_mechanism/run_5b_pilot.py`
- `scripts/phase5_mechanism/run_5c_pilot.py`
- `scripts/phase5_mechanism/generate_all_regions.py`
- `scripts/phase5_mechanism/run_5i_lattice_overlap.py`
- `scripts/phase5_mechanism/run_5e_pilot.py`
- `scripts/phase5_mechanism/run_5d_pilot.py`

### Foundation
- `scripts/phase1_foundation/acceptance_test.py`
- `scripts/phase1_foundation/run_destructive_audit.py`
- `scripts/phase1_foundation/populate_glyphs.py`
- `scripts/phase1_foundation/populate_database.py`
- `scripts/phase1_foundation/debug_import.py`
- `src/phase1_foundation/cli/main.py`

### Utilities
- `src/phase8_comparative/mapping.py`

## 0.2 File Inventory

A full file listing has been generated and reviewed. Key observations:
- Heavy reliance on `scripts/` directory for execution.
- Source code structured in `src/` with clear submodules (`phase2_analysis`, `phase1_foundation`, `phase5_mechanism`, etc.).
- `data/` directory contains `raw`, `derived`, `phase4_inference`, `qc`.
- Configuration scattered in `configs/`.

