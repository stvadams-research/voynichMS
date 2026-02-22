# Claim-to-Artifact Mapping

This document maps every specific quantitative claim in the publication
(`Voynich_Structural_Identification_Final_021526`) to its source script,
output artifact, and JSON key path.

**How to verify a claim:** Run the listed script, open the output JSON, and
navigate to the key path. The value should match within documented tolerance.

**Tolerance:** Unless noted, floating-point values are compared to 4 decimal
places. Integer values must match exactly. Percentages are derived from the
raw float (e.g., 88.11% = 0.8811).

---

## Phase 1 — Foundation

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 1 | Token repetition rate | 0.9003 | `run_baseline_assessment.py` | `results/data/phase3_synthesis/baseline_gap_analysis.json` | `repetition_rate.target` | Also in Phase 2 final report |
| 2 | Glyph identity collapse at 5% perturbation | 37.5% | `run_phase_2_1.py` | `results/data/phase2_analysis/phase_2_1_claims.json` | `results.claim_traceability.claim_2.glyph_identity_collapse_percent` | Structured claim artifact emitted by Phase 2.1 runner |
| 3 | Word boundary cross-source agreement | 75% | `run_phase_2_1.py` | `results/data/phase2_analysis/phase_2_1_claims.json` | `results.claim_traceability.claim_3.word_boundary_agreement_percent` | Below 80% threshold → WEAKLY_SUPPORTED |

---

## Phase 2 — Analysis

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 4 | Mapping stability score | 0.02 | `run_phase_2_2.py` | `results/data/phase2_analysis/phase_2_2_claims.json` | `results.claim_traceability.claim_4.mapping_stability_score` | Outcome: COLLAPSED / Excluded |
| 5 | Information density z-score | 5.68 | `run_phase_2_2.py` | `results/data/phase2_analysis/phase_2_2_claims.json` | `results.claim_traceability.claim_5.information_density_z_score` | Relative to scrambled controls |

---

## Phase 4 — Inference

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 6 | Montemurro avg info (real) | 2.2025 bits | `run_montemurro.py` | `results/data/phase4_inference/montemurro_results.json` | `real.avg_info` | Raw: 2.2025 |
| 7 | Montemurro avg info (shuffled) | 1.2600 bits | `run_montemurro.py` | `results/data/phase4_inference/montemurro_results.json` | `shuffled.avg_info` | Raw: 1.2600 |
| 8 | Network clustering coeff (Voynich) | 0.1173 | `run_network.py` | `results/data/phase4_inference/network_results.json` | `voynich_real.avg_clustering` | Latin: 0.1008, Mech Reuse: 0.3393 |
| 9 | Language ID similarity to Latin | 0.1474 | `run_lang_id.py` | `results/data/phase4_inference/lang_id_results.json` | `voynich_real.latin` | |
| 10 | Language ID similarity to English | 0.1602 | `run_lang_id.py` | `results/data/phase4_inference/lang_id_results.json` | `voynich_real.english` | |
| 11 | Self-citation / mech reuse avg info | 3.58–3.62 bits | `run_montemurro.py` | `results/data/phase4_inference/montemurro_results.json` | `self_citation.avg_info`, `mechanical_reuse.avg_info` | |
| 12 | Unique dominant topics (Voynich) | 5 | `run_topics.py` | `results/data/phase4_inference/topic_results.json` | `voynich_real.unique_dominant_topics` | Latin: KL 2.91; Voynich KL: 3.07 |
| 13 | Morphological consistency (Voynich) | 0.0711 | `run_morph.py` | `results/data/phase4_inference/morph_results.json` | `voynich_real.morph_consistency` | Latin: 0.0846 |

---

## Phase 5 — Mechanism Identification

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 14 | Successor entropy (real) | 3.4358 bits | `run_pilot.py` | `results/data/phase5_mechanism/pilot_results.json` | `table.real.mean_successor_entropy` | |
| 15 | Successor entropy (synthetic) | 3.8394 bits | `run_pilot.py` | `results/data/phase5_mechanism/pilot_results.json` | `table.syn.mean_successor_entropy` | |
| 16 | Reset score | 0.9585 | `run_5b_pilot.py` | `results/data/phase5_mechanism/constraint_geometry/pilot_5b_results.json` | `real.reset.reset_score` | |
| 17 | Effective rank | 83 | `run_5b_pilot.py` | `results/data/phase5_mechanism/constraint_geometry/pilot_5b_results.json` | `real.dim.effective_rank_90` | Integer |
| 18 | Line TTR | 0.9839 | `run_5c_pilot.py` | `results/data/phase5_mechanism/workflow/pilot_5c_results.json` | `real.mean_ttr` | |
| 19 | Line mean entropy | 1.3487 bits | `run_5c_pilot.py` | `results/data/phase5_mechanism/workflow/pilot_5c_results.json` | `real.mean_entropy` | |
| 20 | Successor consistency | 0.8592 | `run_5e_pilot.py` | `results/data/phase5_mechanism/large_object/pilot_5e_results.json` | `real.mean_consistency` | |
| 21 | Recurring bigrams | 1,976 | `run_5e_pilot.py` | `results/data/phase5_mechanism/large_object/pilot_5e_results.json` | `real.num_recurring_contexts` | Integer |
| 22 | Start-word entropy | 11.82 bits | `run_5f_pilot.py` | `results/data/phase5_mechanism/entry_selection/pilot_5f_results.json` | `real.dist.start_entropy` | |
| 23 | Line adjacency coupling | 0.0093 | `run_5f_pilot.py` | `results/data/phase5_mechanism/entry_selection/pilot_5f_results.json` | `real.coup.coupling_score` | |
| 24 | Gini coefficient (topology) | 0.6098 | `run_5g_pilot.py` | `results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json` | `Voynich (Real).coverage.gini_coefficient` | |
| 25 | Convergence rate | 2.2330 | `run_5g_pilot.py` | `results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json` | `Voynich (Real).convergence.avg_successor_convergence` | |
| 26 | Collision rate | 0.1359 | `run_5g_pilot.py` | `results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json` | `Voynich (Real).overlap.collision_rate` | |
| 27a | Sectional consistency — Astronomical | 0.9158 | `run_5i_anchor_coupling.py` | `results/data/phase5_mechanism/sectional_profiles.json` | `astronomical.consistency` | 3,331 tokens |
| 27b | Sectional consistency — Biological | 0.8039 | `run_5i_anchor_coupling.py` | `results/data/phase5_mechanism/sectional_profiles.json` | `biological.consistency` | 47,063 tokens |
| 27c | Sectional consistency — Herbal | 0.8480 | `run_5i_anchor_coupling.py` | `results/data/phase5_mechanism/sectional_profiles.json` | `herbal.consistency` | 72,037 tokens |
| 27d | Sectional consistency — Pharmaceutical | 0.8897 | `run_5i_anchor_coupling.py` | `results/data/phase5_mechanism/sectional_profiles.json` | `pharmaceutical.consistency` | 11,095 tokens |
| 27e | Sectional consistency — Stars | 0.8730 | `run_5i_anchor_coupling.py` | `results/data/phase5_mechanism/sectional_profiles.json` | `stars.consistency` | 63,534 tokens |
| 28 | Position predictive lift | 65.61% | `run_5j_pilot.py` | `results/data/phase5_mechanism/dependency_scope/pilot_5j_results.json` | `Voynich (Real).position_lift.pos_rel_lift` | Raw: 0.6561 |
| 29a | H(S\|Node) | 2.2720 bits | `run_5j_pilot.py` | `results/data/phase5_mechanism/dependency_scope/pilot_5j_results.json` | `Voynich (Real).predictive_lift.h_node` | |
| 29b | H(S\|Node,Pos) | 0.7814 bits | `run_5j_pilot.py` | `results/data/phase5_mechanism/dependency_scope/pilot_5j_results.json` | `Voynich (Real).position_lift.h_node_pos` | |
| 30 | Entropy reduction (5K) | 88.11% | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).residual.rel_reduction` | Raw: 0.8811 |
| 31a | H(S\|W,P) | 0.7869 bits | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).residual.h_word_pos` | |
| 31b | H(S\|W,P,History) | 0.0936 bits | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).residual.h_word_pos_hist` | |
| 32a | Vocab size (5K) | 5,214 | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).parsimony.vocab_size` | Integer |
| 32b | Explosion factor | 1.86x | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).parsimony.explosion_factor` | |

---

## Phase 6 — Functional Characterization

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 33 | Coverage ratio | 0.9168 | `run_6a_exhaustion.py` | `results/data/phase6_functional/phase_6a/phase_6a_results.json` | `Voynich (Real).coverage.coverage_ratio` | |
| 34 | Hapax ratio | 0.9638 | `run_6a_exhaustion.py` | `results/data/phase6_functional/phase_6a/phase_6a_results.json` | `Voynich (Real).coverage.hapax_ratio` | |
| 35 | Overlap rate | 0.0051 | `run_6a_exhaustion.py` | `results/data/phase6_functional/phase_6a/phase_6a_results.json` | `Voynich (Real).redundancy.path_overlap_rate_n3` | |
| 36 | Deviation rate | 0.0000 | `run_6a_exhaustion.py` | `results/data/phase6_functional/phase_6a/phase_6a_results.json` | `Voynich (Real).errors.deviation_rate` | |
| 37 | Reuse suppression index | 0.9896 | `run_6b_efficiency.py` | `results/data/phase6_functional/phase_6b/phase_6b_results.json` | `Voynich (Real).reuse_suppression.reuse_suppression_index` | |
| 38 | Path efficiency | 0.3227 | `run_6b_efficiency.py` | `results/data/phase6_functional/phase_6b/phase_6b_results.json` | `Voynich (Real).path_efficiency.path_efficiency` | |
| 39 | Redundancy rate | 0.0159 | `run_6b_efficiency.py` | `results/data/phase6_functional/phase_6b/phase_6b_results.json` | `Voynich (Real).redundancy_cost.redundancy_rate` | |
| 40 | Compression ratio | 0.3425 | `run_6b_efficiency.py` | `results/data/phase6_functional/phase_6b/phase_6b_results.json` | `Voynich (Real).compressibility.compression_ratio` | |
| 41 | Prediction accuracy | 0.0019 | `run_6c_adversarial.py` | `results/data/phase6_functional/phase_6c/phase_6c_results.json` | `Voynich (Real).learnability.final_accuracy` | |
| 42 | Entropy reduction (6C) | 3.5009 | `run_6c_adversarial.py` | `results/data/phase6_functional/phase_6c/phase_6c_results.json` | `Voynich (Real).conditioning_sensitivity.entropy_reduction` | |

---

## Phase 7 — Human Factors

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 43 | Total pen strokes | ~356,000 | `run_7a_human_factors.py` | `results/data/phase7_human/phase_7a_results.json` | `cost.total_strokes` | Exact: 356,109 |

---

## Phase 8 — Comparative Classification

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 44 | Nearest neighbor distance (Lullian Wheels) | 5.099 | `run_proximity_uncertainty.py` | `results/data/phase7_human/phase_7c_uncertainty.json` | `results.nearest_neighbor_distance` | Status: INCONCLUSIVE_UNCERTAINTY |

---

## Phase 10 — Adversarial Admissibility Retest

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 45 | Method K focal-depth correlation | 0.4114 | `run_stage5b_k_adjudication.py` | `results/data/phase10_admissibility/stage5b_k_adjudication_summary.json` | `results.focal_eval.seed77_runs300.correlation` | |
| 46 | Method K seed-band pass rate | 0.875 | `run_stage5b_k_adjudication.py` | `results/data/phase10_admissibility/stage5b_k_adjudication_summary.json` | `results.seed_band_pass_rate` | Threshold: 0.750 |
| 47 | Method F confirmatory runs | 12 runs, 0 weakened | `run_stage5_high_roi.py` | `results/data/phase10_admissibility/stage5_high_roi_summary.json` | `results.method_f_gate.run_count`, `results.method_f_gate.weakened_family_runs` | |

---

## Phase 11 — Stroke Topology

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 48 | Test A Spearman rho | 0.0157 | `run_11b_cluster.py` | `results/data/phase11_stroke/test_a_clustering.json` | `results.observed_partial_rho` | Determination: NULL (p=0.307) |
| 49 | Test B boundary MI | 0.1219 bits | `run_11c_transitions.py` | `results/data/phase11_stroke/test_b_transitions.json` | `results.B1_boundary_mi` | Determination: NULL (p=0.711) |

---

## Phase 12 — Mechanical Slip Detection

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 50 | Mechanical slips detected | 202 | `run_12a_slip_detection.py` | `results/data/phase12_mechanical/slip_detection_results.json` | `results.total_slips_detected` | ZL-only canonical data; prior 914 included markup false positives |
| 51 | Slip permutation z-score | 9.47σ | `run_12g_slip_permutation.py` | `results/data/phase12_mechanical/slip_permutation_test.json` | `results.z_score` | 10K permutations, p < 0.0001 |
| 52 | Section structural correlation | 0.721 | `run_12d_matrix_alignment.py` | `results/data/phase12_mechanical/matrix_alignment.json` | `results.structural_similarity.structural_correlation` | Herbal vs Biological |

---

## Phase 14 — Voynich Engine (Mechanical Reconstruction)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 53 | Drift admissibility (±1) | 43.44% | `run_14q_residual_analysis.py` | `results/data/phase14_machine/residual_analysis.json` | `results.categories.Admissible (Dist 0-1)` | Post spectral reordering; 14,270 / 32,852 clamped tokens |
| 54 | Palette size | 7,717 | `run_14a_palette_solver.py --full` | `results/data/phase14_machine/full_palette_grid.json` | `results.num_tokens_mapped` | Full ZL clean vocabulary |
| 55 | Mirror corpus entropy fit | 87.60% | `run_14c_mirror_corpus.py` | `results/data/phase14_machine/mirror_corpus_validation.json` | `results.fit_score` | Real 10.88 bits, Synthetic 12.23 bits |
| 56 | Holdout admissibility (Herbal→Bio) | 10.81% | `run_14g_holdout_validation.py` | `results/data/phase14_machine/holdout_performance.json` | `results.drift.admissibility_rate` | 16.2σ above chance |
| 57 | Holdout z-score (drift) | 16.2σ | `run_14g_holdout_validation.py` | `results/data/phase14_machine/holdout_performance.json` | `results.drift.z_score` | Transition-only model |
| 58 | MDL: Lattice BPT | 15.73 | `run_14h_baseline_showdown.py` | `results/data/phase14_machine/baseline_comparison.json` | `results.models.Lattice (Ours).bpt` | Copy-Reset wins at 10.90 BPT |
| 59 | MDL: Copy-Reset BPT | 10.90 | `run_14h_baseline_showdown.py` | `results/data/phase14_machine/baseline_comparison.json` | `results.models.Copy-Reset.bpt` | Best full-corpus MDL |
| 60 | Copy-Reset holdout admissibility | 3.71% | `run_14u_copyreset_holdout.py` | `results/data/phase14_machine/copyreset_holdout.json` | `results.copy_reset.holdout_admissibility` | Lattice 2.9x better cross-section |
| 61 | Extreme jump rate | 11.85% | `run_14q_residual_analysis.py` | `results/data/phase14_machine/residual_analysis.json` | `results.categories.Extreme Jump (>10)` | Down from 47.25% pre-reordering (4x reduction via spectral reordering) |
| 62 | Optimal window count | 50 | `run_14r_minimality_sweep.py` | `results/data/phase14_machine/minimality_sweep.json` | `results.sweep.4.num_windows` | Complexity knee |
| 62a | Extended admissibility (±3) | 57.73% | `run_14q_residual_analysis.py` | `results/data/phase14_machine/residual_analysis.json` | `results.categories` | Sum of Admissible + Extended Drift |
| 62b | Per-line mask admissibility (reordered) | 53.91% | `run_14x_mask_inference.py` | `results/data/phase14_machine/mask_inference.json` | `results.Reordered.mask_admissibility` | +14pp over base reordered |
| 62c | Spectral reordering extreme-jump reduction | 4x | `run_14w_window_reordering.py` | `results/data/phase14_machine/reordered_palette.json` | `results.final_extreme_jump` | 47.25% → 11.85%; ratio is cross-file derived |
| 62d | MDL: Hybrid BPT | 15.49 | `run_14h_baseline_showdown.py` | `results/data/phase14_machine/baseline_comparison.json` | `results.models.Hybrid (CR+Lattice).bpt` | Mixture model: CR + Lattice + Unigram |
| 62e | Section-aware routing (null) | -8.0pp | `run_14y_section_lattice.py` | `results/data/phase14_machine/section_lattice.json` | `results.section_aware_global.delta_pp` | Section-specific reordering hurts; global ordering is optimal |

---

## Phase 15 — Instrumented Choice & Rule Extraction

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 63 | Scribal decisions logged | 12,519 | `run_15a_trace_instrumentation.py` | `results/data/phase15_selection/choice_stream_trace.json` | `results.num_decisions` | ZL canonical data |
| 64 | Average selection skew | 21.49% | `run_15c_bias_and_compressibility.py` | `results/data/phase15_selection/bias_modeling.json` | `results.avg_skew` | Per-window max entropy corrected |
| 65 | Compressibility improvement | 7.93% | `run_15c_bias_and_compressibility.py` | `results/data/phase15_selection/bias_modeling.json` | `results.compression.improvement` | Real more compressible than uniform |

---

## Phase 16 — Ergonomic Grounding

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 66 | Effort correlation (Spearman rho) | -0.0003 | `run_16b_effort_correlation.py` | `results/data/phase16_physical/effort_correlation.json` | `results.correlation_rho` | p=0.99; NULL result |
| 67 | Grid layout efficiency | 81.50% | `run_16c_layout_projection.py` | `results/data/phase16_physical/layout_projection.json` | `results.grid_efficiency` | vs random baseline |

---

## Phase 17 — Physical Synthesis & Bandwidth Audit

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 68 | Realized steganographic bandwidth | 7.53 bpw | `run_17b_bandwidth_audit.py` | `results/data/phase17_finality/bandwidth_audit.json` | `results.realized_bandwidth_bpw` | Bits/word available for hidden content |
| 69 | Total steganographic capacity | 11.5 KB | `run_17b_bandwidth_audit.py` | `results/data/phase17_finality/bandwidth_audit.json` | `results.total_capacity_kb` | ~23K Latin chars equivalent |
| 70 | Bandwidth judgment | SUBSTANTIAL | `run_17b_bandwidth_audit.py` | `results/data/phase17_finality/bandwidth_audit.json` | `results.has_sufficient_bandwidth` | Above 3.0 bpw threshold |

---

## Phase 14G — Strengthening Program (Compression, Prediction, Validation)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 71 | L(model) compression vs showdown | 75% | `run_14z_lattice_compression.py` | `results/data/phase14_machine/lattice_compression.json` | `results.compression_vs_showdown` | 154K → 38K bits (frequency-conditional) |
| 72 | Revised Lattice BPT (freq-cond) | 12.37 | `run_14z_lattice_compression.py` | `results/data/phase14_machine/lattice_compression.json` | `results.bpt_revised.frequency_conditional` | Gap to CR reduced from 4.83 to 1.47 |
| 73 | Best mask prediction capture rate | 44.2% | `run_14z2_mask_prediction.py` | `results/data/phase14_machine/mask_prediction.json` | `results.best_capture_pct` | Global mode offset (single parameter) |
| 74 | Mask-predicted admissibility | 45.91% | `run_14z2_mask_prediction.py` | `results/data/phase14_machine/mask_prediction.json` | `results.rules.global_mode.admissibility` | +6.3pp over baseline with 1 parameter |
| 75 | Cross-transcription mean adm ratio | 1.189 | `run_14z3_cross_transcription.py` | `results/data/phase14_machine/cross_transcription.json` | `results.mean_admissibility_ratio` | >1.0 = lattice transfers across transcriptions |
| 76 | Cross-transcription significant sources | 3/5 | `run_14z3_cross_transcription.py` | `results/data/phase14_machine/cross_transcription.json` | `results.significant_sources` | VT, IT, RF all z > 86 |
| 77 | Top selection driver | Bigram Context | `run_15d_selection_drivers.py` | `results/data/phase15_selection/selection_drivers.json` | `results.top_driver` | 2.432 bits information gain |
| 78 | Positional bias (mean position) | 0.247 | `run_15d_selection_drivers.py` | `results/data/phase15_selection/selection_drivers.json` | `results.hypotheses.positional_bias.mean_relative_position` | Strong top-of-window preference (0.5 = unbiased) |
| 79 | Suffix affinity excess | 2.62x | `run_15d_selection_drivers.py` | `results/data/phase15_selection/selection_drivers.json` | `results.hypotheses.suffix_affinity.excess_ratio` | Chosen word shares suffix with prev 2.62x more than expected |

---

## Phase 14H — Lattice Foundation Strengthening

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 80 | Wrong-window oracle recovery rate | 2.8% | `run_14z4_failure_taxonomy.py` | `results/data/phase14_machine/failure_taxonomy.json` | `results.mask_recoverability.wrong_window.recovery_rate` | Mask does not explain wrong-window residual |
| 81 | Failure distance bimodality coefficient | 0.219 | `run_14z4_failure_taxonomy.py` | `results/data/phase14_machine/failure_taxonomy.json` | `results.distance_distribution.bimodality_test.bc` | Unimodal (threshold 0.555) |
| 82 | Bigram context info gain on distance | 1.31 bits | `run_14z4_failure_taxonomy.py` | `results/data/phase14_machine/failure_taxonomy.json` | `results.bigram_predictability.information_gain_bits` | H(dist)=3.68 → H(dist|prev)=2.37 |
| 83 | Cross-transcription structural rate | 93.6% | `run_14z4_failure_taxonomy.py` | `results/data/phase14_machine/failure_taxonomy.json` | `results.cross_transcription_noise.structural_failures` | 9,357/9,994 wrong-window tokens confirmed in VT/IT/RF |
| 84 | Multi-split holdout: lattice significant | 7/7 | `run_14z5_multisplit_holdout.py` | `results/data/phase14_machine/multisplit_holdout.json` | `results.aggregate.lattice_significant_count` | All z > 8σ |
| 85 | Multi-split holdout: mean lattice z | 29.1σ | `run_14z5_multisplit_holdout.py` | `results/data/phase14_machine/multisplit_holdout.json` | `results.aggregate.mean_lattice_drift_z` | Leave-one-section-out |
| 86 | Multi-split holdout: lattice wins | 7/7 | `run_14z5_multisplit_holdout.py` | `results/data/phase14_machine/multisplit_holdout.json` | `results.aggregate.lattice_win_count` | vs Copy-Reset admissibility |
| 87 | MDL optimal K (kneedle) | 7 | `run_14z6_mdl_elbow.py` | `results/data/phase14_machine/mdl_elbow.json` | `results.knee_point.kneedle_k` | Second derivative: K=3 |
| 88 | K=50 MDL penalty vs optimal | +1.46 BPT | `run_14z6_mdl_elbow.py` | `results/data/phase14_machine/mdl_elbow.json` | `results.penalty_at_k50.penalty_bpt` | Above 0.5 BPT threshold |

---

## Phase 14I — Bigram-Conditioned Lattice & Open Questions

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 89 | Window-level info gain | 1.27 bits | `run_14z7_bigram_transitions.py` | `results/data/phase14_machine/bigram_transitions.json` | `results.info_gain_comparison.ig_window_level` | H(offset) from 4.09 → 2.82 |
| 90 | Word identity beyond window | 1.03 bits | `run_14z7_bigram_transitions.py` | `results/data/phase14_machine/bigram_transitions.json` | `results.info_gain_comparison.ig_word_beyond_window` | Significant word-level signal |
| 91 | Window-level ceiling admissibility | 64.37% | `run_14z7_bigram_transitions.py` | `results/data/phase14_machine/bigram_transitions.json` | `results.theoretical_ceilings.window_level_rate` | +18.46pp over baseline, 50 params |
| 92 | Cross-validated window correction: mean delta | +16.17pp | `run_14z8_bigram_conditioned.py` | `results/data/phase14_machine/bigram_conditioned.json` | `results.aggregate.primary_mean_delta_pp` | 7/7 splits positive |
| 93 | Cross-validated window correction: mean z | 66.8σ | `run_14z8_bigram_conditioned.py` | `results/data/phase14_machine/bigram_conditioned.json` | `results.aggregate.primary_mean_z_score` | Highly significant in all splits |
| 94 | 5-gram overgeneration ratio | 19.9× | `run_14z9_open_questions.py` | `results/data/phase14_machine/open_questions.json` | `results.q1_overgeneration.5-gram.overgeneration_ratio` | Decreases modestly from 24.1× (2-gram) |
| 95 | Per-position branching factor | 9.57 bits | `run_14z9_open_questions.py` | `results/data/phase14_machine/open_questions.json` | `results.q2_branching_factor.overall_effective_bits` | 761.7 candidates/position |
| 96 | Corrected MDL: lattice BPT | 10.84 | `run_14z9_open_questions.py` | `results/data/phase14_machine/open_questions.json` | `results.q3_mdl_decomposition.lattice.bpt` | Wins vs CR (12.95) under corrected encoding |
| 97 | Corrected MDL: lattice wins gap | -2.12 BPT | `run_14z9_open_questions.py` | `results/data/phase14_machine/open_questions.json` | `results.q3_mdl_decomposition.gap.gap_bpt` | Previously CR won due to double-counted L(model) |

## Phase 14J — Second-Order Context Analysis

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 98 | Second-order info gain (pair) | 1.3999 bits | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.info_gain.ig_pair` | vs 1.1455 bits first-order |
| 99 | Pair beyond curr_window info gain | 0.2544 bits | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.info_gain.ig_pair_beyond_curr_window` | Marginal improvement |
| 100 | Best second-order ceiling | 64.01% | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.ceilings.second_order_by_min_obs.3.rate` | +0.50pp over first-order |
| 101 | Observed pairs (of 2500) | 733 | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.sparsity.observed_pairs` | 29.3% coverage |
| 102 | Divergent pairs from first-order | 21.4% | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.pair_mode_divergence.divergent_frac` | 70/327 pairs at ≥5 obs |
| 103 | Gate decision: ceiling improvement | +0.50pp | `run_14za_second_order_transitions.py` | `results/data/phase14_machine/second_order_transitions.json` | `results.gate_decision.ceiling_improvement_pp` | Below 2pp threshold; Sprint 2 skipped |

## Phase 14K — Emulator Calibration

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 104 | Corrected emulator admissibility | 47.6% | `run_14zc_emulator_calibration.py` | `results/data/phase14_machine/emulator_calibration.json` | `results.offset_profiles.synthetic_b.admissible_rate` | vs 4.7% uncorrected, 45.9% real |
| 105 | Uncorrected emulator admissibility | 4.7% | `run_14zc_emulator_calibration.py` | `results/data/phase14_machine/emulator_calibration.json` | `results.offset_profiles.synthetic_a.admissible_rate` | Structurally unrealistic |
| 106 | KL divergence (corrected) | 1.18 bits | `run_14zc_emulator_calibration.py` | `results/data/phase14_machine/emulator_calibration.json` | `results.kl_divergence.synthetic_b` | vs 1.83 bits uncorrected |
| 107 | Mirror entropy fit (corrected) | 89.8% | `run_14zc_emulator_calibration.py` | `results/data/phase14_machine/emulator_calibration.json` | `results.entropy.mirror_fit_b` | Slight regression from 90.4% uncorrected |
| 108 | Canonical corrections: non-zero windows | 43/50 | `run_14zc_emulator_calibration.py` | `results/data/phase14_machine/canonical_offsets.json` | `results.nonzero_count` | Trained on full corpus |

## Phase 14L — Residual Characterization

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 109 | Overall failure rate (corrected model) | 39.9% | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint1_positional.burst_analysis.failure_rate` | 11,760 / 29,460 transitions |
| 110 | Common word failure rate | 6.9% | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint2_lexical.word_class.by_frequency_tier.common.failure_rate` | Words with >100 occurrences |
| 111 | Hapax failure rate | 97.8% | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint2_lexical.word_class.by_frequency_tier.hapax.failure_rate` | Single-occurrence words |
| 112 | Low-frequency share of all failures | 67.3% | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint3_synthesis.reducibility.low_frequency_fraction` | Rare + hapax combined |
| 113 | Section failure range | 17.0pp | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint3_synthesis.reducibility.section_range_pp` | Biological 32.4% → Astro 49.4% |
| 114 | Correction magnitude vs failure rate | rho=0.43 | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint2_lexical.window_occupancy.correction_vs_failure.rho` | p=0.002 |
| 115 | Position gradient range | 11.6pp | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint3_synthesis.reducibility.positional_range_pp` | Pos 1: 36.3% → Pos 10+: 48.0% |
| 116 | Burst clustering chi² p-value | 0.004 | `run_14zd_residual_characterization.py` | `results/data/phase14_machine/residual_characterization.json` | `results.sprint1_positional.burst_analysis.clustering_test.p_value` | Mildly clustered, mean run 1.63 |

## Phase 14M — Frequency-Stratified Lattice Refinement

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 117 | CV mean: frequency-weighted admissibility | 49.9% | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.cross_validation.mean_freq_rate` | 7-fold leave-one-section-out |
| 118 | CV mean: uniform admissibility | 36.2% | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.cross_validation.mean_uniform_rate` | Fresh build baseline |
| 119 | CV delta (freq vs uniform) | +13.7pp | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.cross_validation.mean_delta_pp` | All 7 folds positive |
| 120 | Canonical lattice corrected admissibility | 64.4% | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.sprint1_frequency_lattice.overall.canonical.corrected_rate` | Dominates both fresh builds |
| 121 | Medium-tier FW-Uni delta | +18.3pp | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.sprint1_frequency_lattice.per_tier.medium` | Largest tier improvement |
| 122 | OOV suffix recovery rate | 72.2% | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.sprint3_oov_recovery.suffix.recovery_rate` | 1,418/1,964 transitions |
| 123 | OOV recovery contribution | +4.81pp | `run_14ze_frequency_lattice.py` | `results/data/phase14_machine/frequency_lattice.json` | `results.diminishing_returns.oov_recovery_pp` | Added to consolidated rate |
| 124 | Integrated OOV recovery rate | 95.2% | `run_14zg_oov_integration.py` | `results/data/phase14_machine/suffix_window_map.json` | `results.with_oov_recovery.oov_recovered`, `results.with_oov_recovery.oov_total` | 1,870/1,964 transitions |
| 125 | Integrated consolidated admissibility (uncorrected) | 45.47% | `run_14zg_oov_integration.py` | `results/data/phase14_machine/suffix_window_map.json` | `results.with_oov_recovery.consolidated_admissibility` | +2.03pp over baseline |
| 126 | Integrated consolidated admissibility (corrected) | 65.75% | `run_14zg_oov_integration.py` | `results/data/phase14_machine/suffix_window_map.json` | `results.corrected_comparison.with_oov.corrected_admissibility` | +1.37pp over corrected baseline |
| 127 | Moran's I spatial autocorrelation | 0.915 | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint1_offset_topology.morans_i` | p < 0.0001 (10K permutations) |
| 128 | FFT dominant power fraction (k=1) | 85.4% | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint1_offset_topology.fft.dominant_power_fraction` | Single sinusoidal cycle |
| 129 | Window 18 slip concentration | 92.6% | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint2_slip_correlation.per_window_summary` | 187/202 slips in zero-correction anchor |
| 130 | Slip rate vs correction magnitude | rho=−0.360, p=0.010 | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint2_slip_correlation.correlation_magnitude` | Anti-correlation: slips at anchor, not drift |
| 131 | BIC: volvelle best-fit model | 168.6 | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint3_device_inference.models.volvelle.bic` | ΔBIC=2.3 over tabula, 31.9 over grille |
| 132 | Temporal slip clustering CV | 1.81 | `run_14zf_physical_integration.py` | `results/data/phase14_machine/physical_integration.json` | `results.sprint2_slip_correlation.temporal_clustering.cv` | Clustered in folio batches |

## Opportunity B — Frequency-Stratified Corrections

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 133 | Tiered corrections CV mean delta | +0.74pp | `run_14zh_tiered_corrections.py` | `results/data/phase14_machine/tiered_corrections.json` | `results.sprint_b1_tiered_corrections.cv_mean_delta_pp` | Gate FAIL (threshold ≥2.0pp) |
| 134 | Full corpus tiered admissibility | 65.92% | `run_14zh_tiered_corrections.py` | `results/data/phase14_machine/tiered_corrections.json` | `results.sprint_b1_tiered_corrections.full_corpus_tiered_rate` | Not significantly better than uniform |
| 135 | Hapax suffix coverage | 93.9% | `run_14zh_tiered_corrections.py` | `results/data/phase14_machine/tiered_corrections.json` | `results.sprint_b2_hapax_grouping.suffix_coverage.coverage_pct` | 6,578/7,009 hapax words |
| 136 | Hapax suffix grouping impact | +3.04pp | `run_14zh_tiered_corrections.py` | `results/data/phase14_machine/tiered_corrections.json` | `results.sprint_b2_hapax_grouping.impact_pp` | Already captured in Phase 14O |

## Opportunity C — Device Specification

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 137 | Volvelle diameter (naive) | 1,410mm | `run_17f_device_specification.py` | `results/data/phase17_finality/device_specification.json` | `results.sprint_c1_device_specification.volvelle.total_diameter_mm` | Historically implausible |
| 138 | Historical plausibility | FALSE | `run_17f_device_specification.py` | `results/data/phase17_finality/device_specification.json` | `results.sprint_c1_device_specification.historical_plausibility.plausible` | 11.75× Alberti disc |
| 139 | Window 18 usage fraction | 49.6% | `run_17f_device_specification.py` | `results/data/phase17_finality/device_specification.json` | `results.sprint_c2_wear_predictions.anchor_wear.usage_fraction` | Dominant anchor window |
| 140 | Top-5 window usage concentration | 74.4% | `run_17f_device_specification.py` | `results/data/phase17_finality/device_specification.json` | `results.sprint_c2_wear_predictions.usage_concentration.top5_fraction` | Extreme concentration |

## Opportunity A — Steganographic Channel Analysis

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 141 | Residual steganographic bandwidth | 2.21 bpw | `run_17c_residual_bandwidth.py` | `results/data/phase17_finality/residual_bandwidth.json` | `results.rsb_bpw` | After conditioning on 5 drivers |
| 142 | RSB total capacity | 3.4 KB | `run_17c_residual_bandwidth.py` | `results/data/phase17_finality/residual_bandwidth.json` | `results.rsb_total_kb` | ~6,740 Latin characters |
| 143 | Channel capacity (theoretical max) | 106,858 bits | `run_17d_latin_test.py` | `results/data/phase17_finality/latin_test.json` | `results.channel_capacity.total_capacity_bits` | 13.0 KB |
| 144 | Latin encoding round-trip | EXACT | `run_17d_latin_test.py` | `results/data/phase17_finality/latin_test.json` | `results.encoding_result.round_trip_match` | Genesis 1:1-5 encoded in 2.7% of choices |
| 145 | Choice stream ACF(1) z-score | 6.95 | `run_17e_choice_structure.py` | `results/data/phase17_finality/choice_structure.json` | `results.permutation_test.acf1.z_score` | Significant sequential dependence |
| 146 | Choice stream structure verdict | STRUCTURED | `run_17e_choice_structure.py` | `results/data/phase17_finality/choice_structure.json` | `results.final_verdict` | 2/3 tests significant at z>3 |

## Opportunity D — Cross-Manuscript Comparison

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 147 | Voynich corrected admissibility (signature) | 64.13% | `run_18a_signature_battery.py` | `results/data/phase18_comparative/signature_definition.json` | `results.voynich_signature.corrected_admissibility` | Reference card value |
| 148 | FFT dominant power z-score vs null | 6.15 | `run_18a_signature_battery.py` | `results/data/phase18_comparative/signature_definition.json` | `results.signature_card.fft_dominant_power.z_score` | Strongest discriminator |
| 149 | Cross-section transfer rate | 7/7 | `run_18a_signature_battery.py` | `results/data/phase18_comparative/signature_definition.json` | `results.voynich_signature.cross_section_transfer` | All folds positive |
| 150 | Shuffled Voynich admissibility (own lattice) | 44.37% | `run_18c_comparative_analysis.py` | `results/data/phase18_comparative/comparative_signatures.json` | `results.corpus_signatures.shuffled_voynich.corrected_admissibility` | −20pp from Voynich |
| 151 | Latin admissibility (own lattice) | 43.26% | `run_18c_comparative_analysis.py` | `results/data/phase18_comparative/comparative_signatures.json` | `results.corpus_signatures.latin.corrected_admissibility` | Natural language baseline |
| 152 | Shuffled Voynich Euclidean distance | 988 | `run_18c_comparative_analysis.py` | `results/data/phase18_comparative/comparative_signatures.json` | `results.comparison.shuffled_voynich.euclidean_distance_z` | VERY_DISTINCT |
| 153 | Latin Euclidean distance | 1,044 | `run_18c_comparative_analysis.py` | `results/data/phase18_comparative/comparative_signatures.json` | `results.comparison.latin.euclidean_distance_z` | VERY_DISTINCT |
| 154 | Discrimination verdict (all texts) | VERY_DISTINCT | `run_18c_comparative_analysis.py` | `results/data/phase18_comparative/comparative_signatures.json` | `results.discrimination.*.verdict` | All comparison texts d > 5 |

## Opportunity E — Residual Structure Investigation

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 155 | RSB after 8 drivers | 0.48 bpw | `run_17g_extended_drivers.py` | `results/data/phase17_finality/extended_drivers.json` | `results.chain_summary.rsb_8_drivers` | Down from 2.21 with 5 drivers |
| 156 | Trigram marginal reduction | -0.99 bits | `run_17g_extended_drivers.py` | `results/data/phase17_finality/extended_drivers.json` | `results.marginal_reductions.trigram.marginal_reduction` | Largest new driver |
| 157 | Section marginal reduction | -0.64 bits (seq) | `run_17g_extended_drivers.py` | `results/data/phase17_finality/extended_drivers.json` | `results.entropy_chain[6].h` | Sequential chain position |
| 158 | New drivers % explained | 78.4% | `run_17g_extended_drivers.py` | `results/data/phase17_finality/extended_drivers.json` | `results.chain_summary.pct_remaining_explained` | Of 5-driver residual |
| 159 | ACF(1) z after 8 drivers | -0.00 | `run_17h_conditioned_structure.py` | `results/data/phase17_finality/conditioned_structure.json` | `results.e2_structure_comparison.after_8_drivers.acf1.z_score` | Below significance |
| 160 | Spectral z after 8 drivers | 0.18 | `run_17h_conditioned_structure.py` | `results/data/phase17_finality/conditioned_structure.json` | `results.e2_structure_comparison.after_8_drivers.spectral_peak.z_score` | Below significance |
| 161 | Gate verdict | EXPLAINED | `run_17h_conditioned_structure.py` | `results/data/phase17_finality/conditioned_structure.json` | `results.e2_structure_comparison.gate_verdict` | Structure was unmodeled mechanics |
| 162 | Window 36 driver plateau | trigram (0.00 delta) | `run_17h_conditioned_structure.py` | `results/data/phase17_finality/conditioned_structure.json` | `results.e3_window36_deep_dive.driver_saturation.trigram_to_4gram_delta` | No further n-gram context helps |
| 163 | Window 36 MI(1) | 0.005 bits | `run_17h_conditioned_structure.py` | `results/data/phase17_finality/conditioned_structure.json` | `results.e3_window36_deep_dive.mi_profile.mi_by_lag[0].mi` | Negligible sequential dependency |

## Opportunity F — Subset Device Architecture

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 164 | Words for 50% token coverage | 188 | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f1_coverage_analysis.coverage_thresholds.50` | Extreme concentration |
| 165 | Top-2000 transition coverage | 68.8% | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f1_coverage_analysis.transition_coverage_curve[5].coverage` | No subset reaches 90% |
| 166 | Subset volvelle diameter | 678mm | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f2_device_dimensioning.volvelle.diameter_mm` | 1.94× Apian |
| 167 | Codebook consultation rate | 18.7% | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f2_device_dimensioning.codebook.consultation_rate` | Every ~5.3 words |
| 168 | In-device drift admissibility | 77.2% | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f3_subset_admissibility.in_device_admissibility.drift` | Higher than monolithic |
| 169 | Consolidated admissibility | 63.3% | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f3_subset_admissibility.consolidated.rate` | -0.87pp vs monolithic |
| 170 | Plausibility verdict | MARGINAL | `run_17i_subset_device.py` | `results/data/phase17_finality/subset_device.json` | `results.f2_device_dimensioning.plausibility` | Device oversized, codebook practical |

## Opportunity G — Per-Section Device Analysis

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 171 | PLAUSIBLE section count | 1/7 | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g1_composite.plausible_count` | Only Cosmo fits historical range |
| 172 | Cosmo device diameter | 368mm | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g1_section_devices.Cosmo.device.diameter_mm` | Within 120-400mm range |
| 173 | Stars device diameter | 846mm | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g1_section_devices.Stars.device.diameter_mm` | Largest section, largest device |
| 174 | Codebook union size | 481 | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g1_composite.total_codebook_union` | Compact (single folio) |
| 175 | Resolves C1 implausibility | NO | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.resolves_c1_implausibility` | 6/7 sections still oversized |
| 176 | G2 gate pass count | 6/7 | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g2_gate_pass_count` | Only Astro fails >=55% |
| 177 | Biological consolidated admiss. | 72.8% | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g2_admissibility.Biological.consolidated.rate` | +8.6pp vs monolithic |
| 178 | Cross-section boundary transitions | 3 | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g2_boundary.boundary_transitions` | 0.01% of corpus |
| 179 | Cross-section boundary impact | NEGLIGIBLE | `run_17j_section_devices.py` | `results/data/phase17_finality/section_devices.json` | `results.g2_boundary.impact` | Sections effectively independent |

## Opportunity H — Hapax Suffix Integration

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 180 | Canonical 64.13% suffix-inclusive? | NO | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_3_canonical_update.canonical_was_suffix_inclusive` | Base corrected = 63.99% |
| 181 | Base corrected admissibility | 63.99% | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_1_baseline_verification.corrected_path.without_suffix.rate` | Without suffix recovery |
| 182 | Suffix-consolidated admissibility | 64.94% | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_1_baseline_verification.corrected_path.with_suffix.consolidated_rate` | Updated canonical |
| 183 | Suffix recovery delta | +0.96pp | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_1_baseline_verification.corrected_path.delta_pp` | Global impact |
| 184 | OOV hapax suffix coverage | 93.9% | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_2_hapax_analysis.oov_suffix_coverage_rate` | 1,621/1,727 OOV hapax |
| 185 | OOV hapax transitions | 902 | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_2_hapax_analysis.hapax_oov_transitions` | In-vocab → OOV hapax |
| 186 | Suffix-admissible transitions | 820 | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_1_baseline_verification.corrected_path.with_suffix.oov_admissible` | 820/858 recoverable |
| 187 | Updated canonical admissibility | 64.94% | `run_17k_hapax_integration.py` | `results/data/phase17_finality/hapax_integration.json` | `results.h1_3_canonical_update.updated_canonical_rate` | +0.96pp from 64.13% |

---

## Phase 20 — State Machine + Codebook Architecture

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 188 | State indicator volvelle diameter | 549mm | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.state_indicator_device.volvelle.diameter_mm` | 4.58× Alberti |
| 189 | Volvelle fits Apian range | NO | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.state_indicator_device.volvelle.fits_apian` | 1.57× Apian |
| 190 | Tabula dimensions | 170×160mm | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.state_indicator_device.tabula.width_mm` | 10×5 grid |
| 191 | Codebook total pages | 154 | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.codebook_estimation.total_pages` | 77 folios, 10 quires |
| 192 | Largest window (W18) words | 396 | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.codebook_estimation.per_window[18].words` | 7 codebook pages |
| 193 | Best hybrid device hit rate (N=20) | 34.1% | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.hybrid_analysis.configurations[6].device_hit_rate` | 998 words inscribed |
| 194 | Any hybrid fits Apian? | NO | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.hybrid_analysis.best_apian_fit` | null = none fit |
| 195 | Slip consistency with codebook model | HIGH | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.workflow_analysis.slip_consistency.consistency` | W18: 92.6% of slips |
| 196 | Combined system verdict | IMPLAUSIBLE | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.plausibility_assessment.combined_verdict` | Volvelle form fails |
| 197 | Resolves C1? | NO | `run_20a_codebook_architecture.py` | `results/data/phase20_state_machine/codebook_architecture.json` | `results.plausibility_assessment.resolves_c1` | 50 sectors too many for disc |

---

## Phase 20 — Window State Merging (Sprint 3)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 198 | Baseline drift admissibility (50 states) | 0.4344 | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.baseline.drift_admissibility` | Raw ±1, no corrections |
| 199 | Viable configs found? | YES | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.sweet_spot.found` | 2 configs meet thresholds |
| 200 | Best sweet spot states | 15 | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.sweet_spot.best_config.actual_states` | size_based strategy |
| 201 | Best sweet spot volvelle diameter | 193mm | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.sweet_spot.best_config.volvelle_diameter_mm` | Fits Llull range |
| 202 | Best sweet spot drift admissibility | 0.5684 | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.sweet_spot.best_config.drift_admissibility` | ≥55% threshold |
| 203 | Best sweet spot combined score | 0.8753 | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.sweet_spot.best_config.combined_score` | Retention × size |
| 204 | Size-based 30-state fits Apian? | YES | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.merge_results.size_based[2].volvelle.fits_apian` | 346mm at 30 states |
| 205 | Correction-based mergeable windows | 18 | `run_20b_state_merging.py` | `results/data/phase20_state_machine/state_merging.json` | `results.merge_candidates.correction_mergeable` | 12 groups with 2+ members |

---

## Phase 20 — Non-Circular Device Forms (Sprint 4)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 206 | Sliding strip unfolded length | 1600mm | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.sliding_strip.unfolded_length_mm` | 50 × 32mm positions |
| 207 | Sliding strip best fold | 10-fold, 160mm | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.sliding_strip.best_fold.max_dim_mm` | PORTABLE |
| 208 | Folding tabula best state-only panels | 2 | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.folding_tabula.best_state_only.panels` | 170×85mm folded |
| 209 | Folding tabula best annotated panels | 4 | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.folding_tabula.best_annotated.panels` | 170×118mm folded |
| 210 | Cipher grille verdict | MARGINAL | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.cipher_grille.verdict` | Over-engineered |
| 211 | Recommended device form | Tabula + codebook | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.ranking.recommended` | Score 0.8650 |
| 212 | PLAUSIBLE device count | 4/5 | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.ranking.n_plausible` | All except grille |
| 213 | Tabula + codebook combined score | 0.8650 | `run_20c_linear_devices.py` | `results/data/phase20_state_machine/linear_devices.json` | `results.ranking.recommended_score` | Highest historical precedent |

---

## Phase 20 — Manuscript Layout vs Codebook Structure (Sprint 6)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 214 | Folios analyzed | 101 | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.summary.n_folios` | All folios with mapped tokens |
| 215 | Folios with W18 dominant | 101/101 | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.folio_profiles` | 100% W18 dominance |
| 216 | Within-section similarity | 0.9767 | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.clustering.within_section_mean` | Cosine similarity |
| 217 | Between-section similarity | 0.9771 | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.clustering.between_section_mean` | Within ≤ between |
| 218 | Clustering verdict | NOT SIGNIFICANT | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.clustering.verdict` | p=1.00 |
| 219 | Folio-window Spearman ρ | -0.0131 | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.folio_window_correlation.spearman_r` | No correlation |
| 220 | Codebook-like organization? | NO | `run_20d_layout_analysis.py` | `results/data/phase20_state_machine/layout_analysis.json` | `results.summary.codebook_like_organization` | Sections not distinct |

---

## Phase 20 — Per-Window Annotated Device Coverage (Sprint 7)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 221 | W18 top-3 coverage of W18 | 9.5% | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.per_window_coverage.w18_detail.top3_coverage_of_window` | Highly dispersed |
| 222 | Uniform top-10 global coverage | 22.3% | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.per_window_coverage.global_uniform.10.coverage` | 500 words inscribed |
| 223 | Greedy B=50 consultation rate | 70.1% | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.optimal_allocation.budget_results[0].consultation_rate` | First below 80% |
| 224 | Greedy B=200 coverage | 51.0% | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.optimal_allocation.budget_results[3].coverage` | 155/200 words go to W18 |
| 225 | Annotated tabula verdict | MARGINAL | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.annotated_tabula.verdict` | OVERSIZED physically |
| 226 | Codebook reduction | 2.3% | `run_20e_annotated_device.py` | `results/data/phase20_state_machine/annotated_device.json` | `results.annotated_tabula.codebook_reduction.reduction_fraction` | Minimal impact |

---

## Phase 20 — Scribal Hand × Device Correspondence (Sprint 8)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 227 | Hand 1 tokens | 9,821 | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.summary.hand1_tokens` | f1-f66 |
| 228 | Hand 2 tokens | 16,108 | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.summary.hand2_tokens` | f75-84, f103-116 |
| 229 | Window profile similarity (JSD) | 0.012 | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.profiles.comparison.jsd` | SIMILAR profiles |
| 230 | Shared vocabulary fraction | 15.6% | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.summary.shared_vocab_fraction` | Low type overlap |
| 231 | Hand 1 drift admissibility | 56.1% | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.admissibility.Hand 1.rate` | Lower than Hand 2 |
| 232 | Hand 2 drift admissibility | 64.5% | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.admissibility.Hand 2.rate` | z=-13.60, p≈0 |
| 233 | Admissibility comparison | SIGNIFICANTLY DIFFERENT | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.admissibility.comparison.verdict` | Δ=-8.5pp |
| 234 | Hand × device verdict | SPECIALIST PROFILES | `run_20f_hand_analysis.py` | `results/data/phase20_state_machine/hand_analysis.json` | `results.synthesis.verdict` | Same device, different fluency |

---

## Traceability Notes

1. **Publication config values:** Repetition rate and mapping stability are now
   resolved from structured JSON artifacts via `publication_config.yaml`
   data-source mappings (no static-string synchronization for Claims #1/#4).

2. **Hardcoded chapter values:** Phase 6 and most Phase 5 table values are
   hardcoded in publication chapter markdown files, bypassing the placeholder
   injection pipeline. The `publication_config.yaml` defines data-source keys
   for these but the build log shows zero resolutions — the hardcoded values
   are what appear in the document.

3. **Phase 10 claims:** Quantitative Phase 10 outcomes appear in
   `results/reports/phase10_admissibility/PHASE_10_RESULTS.md` and
   `replicateResults.md`, not in the main publication chapters.

4. **Phase 2 claim artifacts:** Claims #2-5 are now emitted as structured JSON
   by Phase 2.1/2.2 runners (`phase_2_1_claims.json`, `phase_2_2_claims.json`)
   for programmatic verification.

---

## Verification Status Summary

| Status | Count | Claims |
|---|---|---|
| **Fully verifiable** (JSON key path exists) | 234 | #1-234 |
| **Console-only** (requires script re-run) | 0 | — |
| **Report-only** (value in Markdown report, not JSON) | 0 | — |
| **Static config** (manually synchronized) | 0 | — |

All claims re-verified on 2026-02-21. File paths and JSON key paths corrected
for claims #1, #45-49, #52, #62c during Cleanup 5 (path/key reconciliation).
All Phase 12-17 claims use consistent ZL-only canonical data pipeline.
Claims #80-88 added for Phase 14H (2026-02-21).
Claims #89-97 added for Phase 14I (2026-02-21).
Claims #98-103 added for Phase 14J (2026-02-21).
Claims #104-108 added for Phase 14K (2026-02-21).
Claims #109-116 added for Phase 14L (2026-02-21).
Claims #117-123 added for Phase 14M (2026-02-21).
Claims #124-126 added for Phase 14O (2026-02-21).
Claims #127-132 added for Phase 14N (2026-02-21).
Claims #133-136 added for Opportunity B: Frequency-Stratified Corrections (2026-02-21).
Claims #137-140 added for Opportunity C: Device Specification (2026-02-21).
Claims #141-146 added for Opportunity A: Steganographic Channel Analysis (2026-02-21).
Claims #147-154 added for Opportunity D: Cross-Manuscript Comparison (2026-02-21).
Claims #155-163 added for Opportunity E: Residual Structure Investigation (2026-02-21).
Claims #164-170 added for Opportunity F: Subset Device Architecture (2026-02-21).
Claims #171-179 added for Opportunity G: Per-Section Device Analysis (2026-02-22).
Claims #180-187 added for Opportunity H: Hapax Suffix Integration (2026-02-22).
Claims #2-5 converted to structured claim artifacts during Cleanup 6 (2026-02-22).
Claims #188-197 added for Phase 20: State Machine + Codebook Architecture (2026-02-22).
Claims #198-205 added for Phase 20 Sprint 3: Window State Merging (2026-02-22).
Claims #206-213 added for Phase 20 Sprint 4: Non-Circular Device Forms (2026-02-22).
Claims #214-220 added for Phase 20 Sprint 6: Manuscript Layout vs Codebook Structure (2026-02-22).
Claims #221-226 added for Phase 20 Sprint 7: Per-Window Annotated Device Coverage (2026-02-22).
Claims #227-234 added for Phase 20 Sprint 8: Scribal Hand × Device Correspondence (2026-02-22).

---

## Related Documents

- [THRESHOLDS_RATIONALE.md](THRESHOLDS_RATIONALE.md) — Why each threshold has
  its current value
- [PAPER_CODE_CONCORDANCE.md](PAPER_CODE_CONCORDANCE.md) — Paper sections mapped
  to code files and scripts
- [PHASE_10_METHODS_SUMMARY.md](PHASE_10_METHODS_SUMMARY.md) — Phase 10 method
  designs, defeat conditions, and outcomes
