# Phase 0: Inventory and Orientation

## 0.1 Executable Paths (Entry Points)

Identified the following scripts with `if __name__ == "__main__":` blocks, indicating they are intended entry points:

### Functional Analysis
- `scripts/functional/run_6c_adversarial.py`
- `scripts/functional/run_6b_efficiency.py`
- `scripts/functional/run_6a_exhaustion.py`

### Human Factors
- `scripts/human/run_7a_human_factors.py`
- `scripts/human/run_7c_comparative.py`
- `scripts/human/run_7b_codicology.py`

### Inference
- `scripts/inference/run_morph.py`
- `scripts/inference/run_network.py`
- `scripts/inference/run_lang_id.py`
- `scripts/inference/run_montemurro.py`
- `scripts/inference/run_topics.py`
- `scripts/inference/build_corpora.py`

### Synthesis
- `scripts/synthesis/run_test_c.py`
- `scripts/synthesis/run_test_b.py`
- `scripts/synthesis/run_indistinguishability_test.py`
- `scripts/synthesis/extract_grammar.py`
- `scripts/synthesis/run_baseline_assessment.py`
- `scripts/synthesis/run_test_a.py`
- `scripts/synthesis/run_phase_3.py`
- `scripts/synthesis/run_phase_3_1.py`

### Analysis (Phase 2)
- `scripts/analysis/run_phase_2_2.py`
- `scripts/analysis/run_phase_2_3.py`
- `scripts/analysis/run_phase_2_4.py`
- `scripts/analysis/demo_phase_2_1.py`
- `scripts/analysis/run_phase_2_1.py`

### Mechanism (Phase 5)
- `scripts/mechanism/run_5i_sectional_profiling.py`
- `scripts/mechanism/run_pilot.py`
- `scripts/mechanism/generate_all_anchors.py`
- `scripts/mechanism/run_5j_pilot.py`
- `scripts/mechanism/run_5k_pilot.py`
- `scripts/mechanism/categorize_sections.py`
- `scripts/mechanism/run_5i_anchor_coupling.py`
- `scripts/mechanism/run_5f_pilot.py`
- `scripts/mechanism/run_5g_pilot.py`
- `scripts/mechanism/run_5b_pilot.py`
- `scripts/mechanism/run_5c_pilot.py`
- `scripts/mechanism/generate_all_regions.py`
- `scripts/mechanism/run_5i_lattice_overlap.py`
- `scripts/mechanism/run_5e_pilot.py`
- `scripts/mechanism/run_5d_pilot.py`

### Foundation
- `scripts/foundation/acceptance_test.py`
- `scripts/foundation/run_destructive_audit.py`
- `scripts/foundation/populate_glyphs.py`
- `scripts/foundation/populate_database.py`
- `scripts/foundation/debug_import.py`
- `src/foundation/cli/main.py`

### Utilities
- `src/comparative/mapping.py`

## 0.2 File Inventory

A full file listing has been generated and reviewed. Key observations:
- Heavy reliance on `scripts/` directory for execution.
- Source code structured in `src/` with clear submodules (`analysis`, `foundation`, `mechanism`, etc.).
- `data/` directory contains `raw`, `derived`, `inference`, `qc`.
- Configuration scattered in `configs/`.

