# Paper-Code Concordance

Maps sections of the publication paper to the source code, scripts, and result
files that produce the data and claims in each section.

**Paper:** *Structural Identification of the Voynich Manuscript: An
Assumption-Resistant Framework for Non-Semantic Analysis*

For individual claim-to-JSON mappings, see
[claim_artifact_map.md](claim_artifact_map.md).

---

## Chapter 3: Foundational Ledger

Corpus statistics and distributional profile of the Voynich token stream.

| Section | Topic | Script | Source Module | Result File |
|---|---|---|---|---|
| 3.1 | Corpus statistics | `phase1_foundation/populate_database.py` | `phase1_foundation/storage/metadata.py` | `data/voynich.db` (pages, tokens tables) |
| 3.2 | Token repetition rate | `phase3_synthesis/run_baseline_assessment.py` | `phase1_foundation/metrics/library.py` (RepetitionRate) | `results/data/phase3_synthesis/test_a_results.json` |
| 3.2 | Zipfian distribution | `phase4_inference/run_network.py` | `phase4_inference/network_features/analyzer.py` | `results/data/phase4_inference/network_results.json` |

**Figures:** `results/visuals/phase1_foundation/*_repetition_rate_dist_*.png`

---

## Chapter 4: Structural Exclusion

Mapping stability, perturbation analysis, and exclusion of linguistic/cipher models.

| Section | Topic | Script | Source Module | Result File |
|---|---|---|---|---|
| 4.1 | Glyph identity collapse | `phase2_analysis/run_phase_2_1.py` | `phase2_analysis/stress_tests/mapping_stability.py` | Console output (Claims #2-3) |
| 4.2 | Mapping stability score | `phase2_analysis/run_phase_2_2.py` | `phase2_analysis/stress_tests/mapping_stability.py` | Phase 2 stress test JSON |
| 4.3 | Information density z-score | `phase2_analysis/run_phase_2_2.py` | `phase2_analysis/stress_tests/information_preservation.py` | `results/reports/phase2_analysis/final_report_phase_2.md` |
| 4.4 | Sensitivity analysis | `phase2_analysis/run_sensitivity_sweep.py` | `phase2_analysis/stress_tests/` (all) | `results/data/phase2_analysis/sensitivity_sweep/` |

**Figures:** `results/visuals/phase2_analysis/*_sensitivity_*.png`
**Note:** Claims #2-3 (glyph collapse 37.5%, word boundary 75%) are console-only output from `run_phase_2_1.py`.

---

## Chapter 5: Generative Reconstruction

Grammar extraction, gap analysis, and generative sufficiency.

| Section | Topic | Script | Source Module | Result File |
|---|---|---|---|---|
| 5.1 | Grammar extraction | `phase3_synthesis/extract_grammar.py` | `phase3_synthesis/generators/grammar.py` | `results/data/phase3_synthesis/` |
| 5.2 | Gap analysis | `phase3_synthesis/run_phase_3.py` | `phase3_synthesis/gap_continuation.py` | `results/data/phase3_synthesis/test_a_results.json` |
| 5.3 | Indistinguishability | `phase3_synthesis/run_phase_3.py` | `phase3_synthesis/indistinguishability.py` | `results/data/phase3_synthesis/` |
| 5.4 | Constraint formalization | `phase3_synthesis/run_phase_3.py` | `phase3_synthesis/refinement/constraint_formalization.py` | `results/reports/phase3_synthesis/` |

---

## Chapter 6: Inference Evaluation (Noise Floor)

Method evaluation, false-positive calibration, and diagnosticity assessment.

| Section | Topic | Script | Source Module | Result File | Claims |
|---|---|---|---|---|---|
| 6.1 | Montemurro-Zanette | `phase4_inference/run_montemurro.py` | `phase4_inference/info_clustering/montemurro.py` | `results/data/phase4_inference/montemurro_results.json` | #6, #11 |
| 6.2 | Network analysis (WAN) | `phase4_inference/run_network.py` | `phase4_inference/network_features/analyzer.py` | `results/data/phase4_inference/network_results.json` | #8 |
| 6.3 | Language identification | `phase4_inference/run_lang_id.py` | `phase4_inference/lang_id_transforms/analyzer.py` | `results/data/phase4_inference/lang_id_results.json` | #9, #10 |
| 6.4 | Topic modeling | `phase4_inference/run_topics.py` | `phase4_inference/topic_models/` | `results/data/phase4_inference/topic_results.json` | #12 |
| 6.5 | Morphological induction | `phase4_inference/run_morph.py` | `phase4_inference/morph_induction/analyzer.py` | `results/data/phase4_inference/morph_results.json` | #13 |

**Figures:** `results/visuals/phase4_inference/*_lang_id_comparison.png`

---

## Chapter 7: Mechanism Identification (Phase 5, 11 sub-stages)

| Sub-stage | Topic | Script | Source Module | Result File | Claims |
|---|---|---|---|---|---|
| 5A | Identifiability pilot | `run_pilot.py` | `phase5_mechanism/` | `pilot_results.json` | #14-15 |
| 5B | Reset dynamics | `run_5b_pilot.py` | `constraint_geometry/` | `constraint_geometry/pilot_5b_results.json` | #16-17 |
| 5C | Workflow reconstruction | `run_5c_pilot.py` | `workflow/` | `workflow/pilot_5c_results.json` | #18-19 |
| 5D | Deterministic grammar | — | `deterministic_grammar/` | Reports only | — |
| 5E | Successor consistency | `run_5e_pilot.py` | `large_object/` | `large_object/pilot_5e_results.json` | #20-21 |
| 5F | Entry selection | `run_5f_pilot.py` | `entry_selection/` | `entry_selection/pilot_5f_results.json` | #22-23 |
| 5G | Topology collapse | `run_5g_pilot.py` | `topology_collapse/` | `topology_collapse/pilot_5g_results.json` | #24-26 |
| 5I | Sectional stability | `run_5i_anchor_coupling.py` | `anchor_coupling.py` | `sectional_profiles.json` | #27a-e |
| 5J | Position sensitivity | `run_5j_pilot.py` | `dependency_scope/` | `dependency_scope/pilot_5j_results.json` | #28-29b |
| 5K | Final collapse | `run_5k_pilot.py` | `parsimony/` | `parsimony/pilot_5k_results.json` | #30-32b |

All scripts in `scripts/phase5_mechanism/`. All source in `src/phase5_mechanism/`.
All results in `results/data/phase5_mechanism/`.

**Figures:** `results/publication/assets/reset_signature.png`,
`lattice_determinism.png`, `topology_comparison.png`, `sectional_stability.png`

---

## Chapter 8: Functional Characterization (Phase 6, 3 sub-stages)

| Sub-stage | Topic | Script | Source Module | Result File | Claims |
|---|---|---|---|---|---|
| 6A | Coverage & exhaustion | `run_6a_exhaustion.py` | `formal_system/analyzer.py` | `phase_6a/phase_6a_results.json` | #33-36 |
| 6B | Efficiency audit | `run_6b_efficiency.py` | `efficiency/metrics.py` | `phase_6b/phase_6b_results.json` | #37-40 |
| 6C | Adversarial profile | `run_6c_adversarial.py` | `adversarial/metrics.py` | `phase_6c/phase_6c_results.json` | #41-42 |

All scripts in `scripts/phase6_functional/`. All source in `src/phase6_functional/`.
All results in `results/data/phase6_functional/`.

**Figure:** `results/publication/assets/novelty_convergence.png`

---

## Chapter 9: Scribal Hand Analysis (Phase 7, 3 sub-stages)

| Sub-stage | Topic | Script | Source Module | Result File | Claims |
|---|---|---|---|---|---|
| 7A | Human factors | `run_7a_human_factors.py` | `phase7_human/ergonomics.py` | `phase_7a_results.json` | #43 |
| 7B | Codicology | `run_7b_codicology.py` | `phase7_human/quire_analysis.py`, `scribe_coupling.py` | `phase_7b_results.json` | — |
| 7C | Comparative analysis | `run_7c_comparative.py`, `run_proximity_uncertainty.py` | `phase7_human/comparative.py` | `phase_7c_results.json`, `phase_7c_uncertainty.json` | #44 |

All scripts in `scripts/phase7_human/`. All source in `src/phase7_human/`.
All results in `results/data/phase7_human/`.

---

## Chapter 10: Comparative Classification (Phase 8)

| Topic | Script | Source Module | Result File |
|---|---|---|---|
| Artifact morphospace | `run_proximity_uncertainty.py` | `phase8_comparative/mapping.py` | `results/data/phase8_comparative/` |
| Case files | — | — | `results/reports/phase8_comparative/casefiles/` |

**Figure:** `results/publication/assets/radar_comparison.png`

---

## Phase 10: Admissibility Retest (separate from main paper chapters)

See [PHASE_10_METHODS_SUMMARY.md](PHASE_10_METHODS_SUMMARY.md) for method
details.

| Stage | Methods | Script | Result Files | Claims |
|---|---|---|---|---|
| Stage 1 | H, J, K | `run_stage1_hjk.py` | `method_h_typology.json`, `method_j_steganographic.json`, `method_k_residual_gap.json` | — |
| Stage 1b | J, K replication | `run_stage1b_jk_replication.py` | `stage1b_jk_multiseed_replication.json` | — |
| Stage 2 | G, I | `run_stage2_gi.py` | `method_g_text_illustration.json`, `method_i_cross_linguistic.json` | — |
| Stage 3 | F | `run_stage3_f.py` | `method_f_reverse_mechanism.json` | #47 |
| Stage 5 | High-ROI confirmatory | `run_stage5_high_roi.py` | `stage5_high_roi_summary.json` | — |
| Stage 5b | K adjudication | `run_stage5b_k_adjudication.py` | `stage5b_k_adjudication_summary.json` | #45-46 |

All scripts in `scripts/phase10_admissibility/`. All source in `src/phase10_admissibility/`.
All results in `results/data/phase10_admissibility/`.

---

## Phase 11: Stroke Topology (fast-kill terminated)

| Test | Script | Source Module | Result File |
|---|---|---|---|
| Feature extraction | `run_11a_extract.py` | `phase11_stroke/features.py` | `test_a_clustering.json` |
| Clustering | `run_11b_cluster.py` | `phase11_stroke/clustering.py` | `test_a_clustering.json` |
| Transitions | `run_11c_transitions.py` | `phase11_stroke/transitions.py` | Transition matrices |

All scripts in `scripts/phase11_stroke/`. All source in `src/phase11_stroke/`.
Result: STROKE_NULL (fast-kill triggered, partial rho = 0.016, p = 0.307).

---

## Known Data Availability Gaps

### Console-Only Claims (no JSON artifact)
- **Claim #2:** Glyph identity collapse (37.5%) — `run_phase_2_1.py` line 259
- **Claim #3:** Word boundary agreement (75%) — `run_phase_2_1.py` line 274

### Hardcoded in Publication Config
- `phase1.repetition_rate = "0.9003"` — static string in `publication_config.yaml`
- `phase2.mapping_stability = "0.02"` — static string in `publication_config.yaml`

### Hardcoded in Chapter Markdown
Phase 5 and Phase 6 table values are embedded as markdown tables in chapter
content files (`07_mechanism_identification.md`, `08_functional_characterization.md`)
rather than dynamically resolved from JSON via the placeholder pipeline.
This is an intentional design choice per `claim_artifact_map.md` lines 134-137.
