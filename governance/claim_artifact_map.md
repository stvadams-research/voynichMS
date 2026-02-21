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
| 1 | Token repetition rate | 0.9003 | `run_baseline_assessment.py` | `results/data/phase3_synthesis/test_a_results.json` | `results.voynich_real.repetition_rate` | Also in Phase 2 final report |
| 2 | Glyph identity collapse at 5% perturbation | 37.5% | `run_phase_2_1.py` | Console output (line 259) | — | Hardcoded in script output string |
| 3 | Word boundary cross-source agreement | 75% | `run_phase_2_1.py` | Console output (line 274) | — | Below 80% threshold → WEAKLY_SUPPORTED |

---

## Phase 2 — Analysis

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 4 | Mapping stability score | 0.02 | `run_phase_2_2.py` | Phase 2 stress test output | `mapping_stability` | Outcome: COLLAPSED / Excluded |
| 5 | Information density z-score | 5.68 | `run_phase_2_2.py` | `results/reports/phase2_analysis/final_report_phase_2.md` | Section 2.2 | Relative to scrambled controls |

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
| 13 | Morphological consistency (Voynich) | 0.0711 | `run_morph.py` | `results/data/phase4_inference/morph_results.json` | `voynich_real.consistency` | Latin: 0.0846 |

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
| 29a | H(S\|Node) | 2.2720 bits | `run_5j_pilot.py` | `results/data/phase5_mechanism/dependency_scope/pilot_5j_results.json` | `Voynich (Real).h_node` | |
| 29b | H(S\|Node,Pos) | 0.7814 bits | `run_5j_pilot.py` | `results/data/phase5_mechanism/dependency_scope/pilot_5j_results.json` | `Voynich (Real).h_node_pos` | |
| 30 | Entropy reduction (5K) | 88.11% | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).residual.rel_reduction` | Raw: 0.8811 |
| 31a | H(S\|W,P) | 0.7869 bits | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).h_word_pos` | |
| 31b | H(S\|W,P,History) | 0.0936 bits | `run_5k_pilot.py` | `results/data/phase5_mechanism/parsimony/pilot_5k_results.json` | `Voynich (Real).h_word_pos_hist` | |
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
| 45 | Method K focal-depth correlation | 0.4114 | `run_stage5b_k_adjudication.py` | `results/data/phase10_admissibility/stage5b_k_adjudication.json` | `results.focal_depth.decision_correlation` | |
| 46 | Method K seed-band pass rate | 0.875 | `run_stage5b_k_adjudication.py` | `results/data/phase10_admissibility/stage5b_k_adjudication.json` | `results.seed_band.pass_rate` | Threshold: 0.750 |
| 47 | Method F confirmatory runs | 12 runs, 0 weakened | `run_stage5_high_roi.py` | `results/data/phase10_admissibility/stage5_high_roi_summary.json` | `results.method_f.confirmatory_runs` | |

---

## Phase 11 — Stroke Topology

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 48 | Test A Spearman rho | 0.0157 | `run_11b_cluster.py` | `results/data/phase11_stroke/test_a_clustering.json` | `results.partial_rho` | Determination: NULL (p=0.307) |
| 49 | Test B boundary MI | 0.1219 bits | `run_11c_transitions.py` | `results/data/phase11_stroke/test_b_transitions.json` | `results.boundary_mi` | Determination: NULL (p=0.711) |

---

## Phase 12 — Mechanical Slip Detection

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 50 | Mechanical slips detected | 202 | `run_12a_slip_detection.py` | `results/data/phase12_mechanical/slip_detection_results.json` | `results.total_slips_detected` | ZL-only canonical data; prior 914 included markup false positives |
| 51 | Slip permutation z-score | 9.47σ | `run_12g_slip_permutation.py` | `results/data/phase12_mechanical/slip_permutation_test.json` | `results.z_score` | 10K permutations, p < 0.0001 |
| 52 | Section structural correlation | 0.721 | `run_12d_matrix_alignment.py` | `results/data/phase12_mechanical/cross_section_analysis.json` | `results.structural_correlation` | Herbal vs Biological |

---

## Phase 14 — Voynich Engine (Mechanical Reconstruction)

| # | Claim | Value | Script | Output File | Key Path | Notes |
|---|-------|-------|--------|-------------|----------|-------|
| 53 | Drift admissibility (±1) | 38.11% | `run_14q_residual_analysis.py` | `results/data/phase14_machine/residual_analysis.json` | `results.categories.Admissible (Dist 0-1)` | 12,519 / 32,852 clamped tokens |
| 54 | Palette size | 7,717 | `run_14a_palette_solver.py --full` | `results/data/phase14_machine/full_palette_grid.json` | `results.num_tokens_mapped` | Full ZL clean vocabulary |
| 55 | Mirror corpus entropy fit | 87.57% | `run_14c_mirror_corpus.py` | `results/data/phase14_machine/mirror_corpus_validation.json` | `results.fit_score` | Real 10.88 bits, Synthetic 12.24 bits |
| 56 | Holdout admissibility (Herbal→Bio) | 10.81% | `run_14g_holdout_validation.py` | `results/data/phase14_machine/holdout_performance.json` | `results.drift.admissibility_rate` | 16.2σ above chance |
| 57 | Holdout z-score (drift) | 16.2σ | `run_14g_holdout_validation.py` | `results/data/phase14_machine/holdout_performance.json` | `results.drift.z_score` | Transition-only model |
| 58 | MDL: Lattice BPT | 15.98 | `run_14h_baseline_showdown.py` | `results/data/phase14_machine/baseline_comparison.json` | `results.models.Lattice (Ours).bpt` | Copy-Reset wins at 10.90 BPT |
| 59 | MDL: Copy-Reset BPT | 10.90 | `run_14h_baseline_showdown.py` | `results/data/phase14_machine/baseline_comparison.json` | `results.models.Copy-Reset.bpt` | Best full-corpus MDL |
| 60 | Copy-Reset holdout admissibility | 3.71% | `run_14u_copyreset_holdout.py` | `results/data/phase14_machine/copyreset_holdout.json` | `results.copy_reset.holdout_admissibility` | Lattice 2.9x better cross-section |
| 61 | Extreme jump rate | 47.25% | `run_14q_residual_analysis.py` | `results/data/phase14_machine/residual_analysis.json` | `results.categories.Extreme Jump (>10)` | Primary failure mode |
| 62 | Optimal window count | 50 | `run_14r_minimality_sweep.py` | `results/data/phase14_machine/minimality_sweep.json` | `results.optimal_k` | Complexity knee |

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

## Traceability Notes

1. **Static config values:** Repetition rate (0.9003) and mapping stability (0.02)
   are stored as static strings in `publication_config.yaml`, not dynamically
   resolved from JSON. The config comment says "updated to match Phase 2 Real
   value" — manually synchronized.

2. **Hardcoded chapter values:** Phase 6 and most Phase 5 table values are
   hardcoded in publication chapter markdown files, bypassing the placeholder
   injection pipeline. The `publication_config.yaml` defines data-source keys
   for these but the build log shows zero resolutions — the hardcoded values
   are what appear in the document.

3. **Phase 10 claims:** Quantitative Phase 10 outcomes appear in
   `results/reports/phase10_admissibility/PHASE_10_RESULTS.md` and
   `replicateResults.md`, not in the main publication chapters.

4. **Console-only claims:** Claims #2 (37.5% collapse) and #3 (75% agreement)
   are printed to console by `run_phase_2_1.py` but not stored in a JSON
   artifact. These cannot be programmatically verified without re-running the
   script and parsing stdout.

---

## Verification Status Summary

| Status | Count | Claims |
|---|---|---|
| **Fully verifiable** (JSON key path exists) | 63 | #1, #6-70 |
| **Console-only** (requires script re-run) | 2 | #2, #3 |
| **Report-only** (value in Markdown report, not JSON) | 2 | #4, #5 |
| **Static config** (manually synchronized) | 1 | #1 (also in config) |

All Phase 12-17 claims re-verified on 2026-02-21 using consistent ZL-only
canonical data pipeline (`load_canonical_lines()` with IVTFF sanitization).

### Recommended Fixes (future sprint)

- **Claims #2-3:** Modify `run_phase_2_1.py` to write glyph collapse and word
  boundary agreement values to a JSON output file alongside console output.
- **Claims #4-5:** Modify `run_phase_2_2.py` to include mapping stability score
  and information density z-score in a structured JSON output.

---

## Related Documents

- [THRESHOLDS_RATIONALE.md](THRESHOLDS_RATIONALE.md) — Why each threshold has
  its current value
- [PAPER_CODE_CONCORDANCE.md](PAPER_CODE_CONCORDANCE.md) — Paper sections mapped
  to code files and scripts
- [PHASE_10_METHODS_SUMMARY.md](PHASE_10_METHODS_SUMMARY.md) — Phase 10 method
  designs, defeat conditions, and outcomes
