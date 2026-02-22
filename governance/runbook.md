# Engineering Runbook

> **Single-command replication:** `python3 scripts/support_preparation/replicate_all.py`
> covers all 18 release-canonical phases (Phases 1-17 and 20) end-to-end. For full
> external reproduction guide (including data acquisition and claim traceability),
> see `replicateResults.md`. For release-canonical vs exploratory scope,
> see `governance/RELEASE_SCOPE.md`.
>
> **Exploratory opt-in:** `python3 scripts/support_preparation/replicate_all.py --include-exploratory`
> appends exploratory phases (18-19). Orchestration order and aliases are
> defined in `configs/project/phase_manifest.json`.

## 1. Environment Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-lock.txt   # exact pins for reproducibility
pip install -e .
```

## 2. Phase 1: Foundation (Data Initialization)

```bash
python3 scripts/phase1_foundation/acceptance_test.py
python3 scripts/phase1_foundation/populate_database.py
python3 scripts/phase1_foundation/run_destructive_audit.py
```

## 3. Phase 2: Analysis (Admissibility and Anomaly Tracks)

```bash
python3 scripts/phase2_analysis/run_phase_2_1.py
python3 scripts/phase2_analysis/run_phase_2_2.py
python3 scripts/phase2_analysis/run_phase_2_3.py
python3 scripts/phase2_analysis/run_phase_2_4.py
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke
```

## 4. Phase 3: Synthesis (Generative Reconstruction and Validation)

```bash
python3 scripts/phase3_synthesis/extract_grammar.py
python3 scripts/phase3_synthesis/run_phase_3.py
python3 scripts/phase3_synthesis/run_test_a.py --seed 42
python3 scripts/phase3_synthesis/run_test_b.py
python3 scripts/phase3_synthesis/run_test_c.py
python3 scripts/phase3_synthesis/run_indistinguishability_test.py
python3 scripts/phase3_synthesis/run_control_matching_audit.py
python3 scripts/phase3_synthesis/run_baseline_assessment.py
```

## 5. Phase 4: Inference (Method Evaluation)

```bash
python3 scripts/phase4_inference/build_corpora.py
python3 scripts/phase4_inference/run_lang_id.py
python3 scripts/phase4_inference/run_montemurro.py
python3 scripts/phase4_inference/run_network.py
python3 scripts/phase4_inference/run_morph.py
python3 scripts/phase4_inference/run_topics.py
```

## 6. Phase 5: Mechanism (Constraint Lattice Identification)

```bash
python3 scripts/phase5_mechanism/run_pilot.py
python3 scripts/phase5_mechanism/run_5b_pilot.py
python3 scripts/phase5_mechanism/run_5c_pilot.py
python3 scripts/phase5_mechanism/run_5d_pilot.py
python3 scripts/phase5_mechanism/run_5e_pilot.py
python3 scripts/phase5_mechanism/run_5f_pilot.py
python3 scripts/phase5_mechanism/run_5g_pilot.py
python3 scripts/phase5_mechanism/run_5j_pilot.py
python3 scripts/phase5_mechanism/run_5k_pilot.py
python3 scripts/phase5_mechanism/generate_all_anchors.py --dataset-id voynich_real --method-name geometric_v1 --threshold 0.10
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
```

## 7. Phase 6: Functional (Efficiency and Adversarial Evaluation)

```bash
python3 scripts/phase6_functional/run_6a_exhaustion.py
python3 scripts/phase6_functional/run_6b_efficiency.py
python3 scripts/phase6_functional/run_6c_adversarial.py
```

## 8. Phase 7: Human (Codicological Constraints)

```bash
python3 scripts/phase7_human/run_7a_human_factors.py
python3 scripts/phase7_human/run_7b_codicology.py
python3 scripts/phase7_human/run_7c_comparative.py
```

## 9. Phase 8: Comparative (Historical Artifact Proximity)

```bash
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
```

## 10. Phase 9: Conjecture (Speculative Synthesis)

Phase 9 is a synthesis phase. Its per-phase `replicate.py` orchestrates any
necessary steps. No additional manual scripts beyond `replicate_all.py`.

## 11. Phase 10: Admissibility Retest (Adversarial)

```bash
python3 scripts/phase10_admissibility/run_stage1_hjk.py --seed 42
python3 scripts/phase10_admissibility/run_stage1b_jk_replication.py --seeds 42,77,101
python3 scripts/phase10_admissibility/run_stage2_gi.py --seed 42
python3 scripts/phase10_admissibility/run_stage3_f.py --seed 42
python3 scripts/phase10_admissibility/run_stage4_synthesis.py
python3 scripts/phase10_admissibility/run_stage5_high_roi.py
python3 scripts/phase10_admissibility/run_stage5b_k_adjudication.py
```

## 12. Phase 11: Stroke Topology (Fast-Kill Gate)

```bash
python3 scripts/phase11_stroke/run_11a_extract.py
python3 scripts/phase11_stroke/run_11b_cluster.py --seed 42 --permutations 10000
python3 scripts/phase11_stroke/run_11c_transitions.py --seed 42 --permutations 10000
```

## 13. Visualization and Publication

```bash
python3 -m support_visualization.cli.main foundation token-frequency voynich_real
python3 -m support_visualization.cli.main foundation repetition-rate voynich_real
python3 -m support_visualization.cli.main analysis sensitivity-sweep core_status/core_audit/sensitivity_sweep.json
python3 -m support_visualization.cli.main synthesis gap-analysis core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json
python3 -m support_visualization.cli.main inference lang-id results/data/phase4_inference/lang_id_results.json
python3 scripts/support_preparation/generate_publication.py
```

## 14. Verification and Tests

```bash
python3 -m pytest tests/ -v
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
python3 scripts/core_skeptic/check_claim_entitlement_coherence.py --mode release
```

## 15. SK-C1 Release Sensitivity Sequence

Use this sequence before release-path checks:

```bash
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
python3 scripts/core_audit/check_sensitivity_artifact_contract.py --mode release
```

Operational notes:

- Progress heartbeat: `core_status/core_audit/sensitivity_progress.json`
- Preflight status: `core_status/core_audit/sensitivity_release_preflight.json`
- Checkpoint/resume state: `core_status/core_audit/sensitivity_checkpoint.json`
- To force a fresh run: add `--no-resume`

## 16. Key Configuration

- `REQUIRE_COMPUTED=1`: fail when fallback placeholders are hit in strict mode.
- Seed handling: current scripts are deterministic primarily via internal seeded
  constructors and `active_run(config={"seed": 42, ...})`.

## 17. SK-H3 Control Comparability

Use this sequence before SK-H3-sensitive release claims:

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/phase3_synthesis/run_indistinguishability_test.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

Claims based on control comparisons must be bounded by
`core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`.
Data-availability scope must be read from
`core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` before any
full-closure language is used.

SK-H3.4 minimum semantic checks before release claims:

- `evidence_scope=available_subset` implies `full_data_closure_eligible=false`.
- `available_subset_reason_code=AVAILABLE_SUBSET_UNDERPOWERED` implies non-conclusive underpowered subset evidence.
- `approved_lost_pages_policy_version` and `approved_lost_pages_source_note_path` must match across both SK-H3 artifacts.
- `irrecoverability.classification` must be consistent across both SK-H3 artifacts.
- `full_data_feasibility`, `full_data_closure_terminal_reason`, and `full_data_closure_reopen_conditions` must match across both SK-H3 artifacts.
- `h3_4_closure_lane` must match across both SK-H3 artifacts and align with scope/feasibility semantics.
- `h3_5_closure_lane`, `h3_5_residual_reason`, and `h3_5_reopen_conditions` must match across both SK-H3 artifacts and remain deterministic.

## 18. SK-H1 Multimodal Coupling

Use this sequence before any illustration/layout coupling claim:

```bash
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release
```

Claims must be bounded by:

- `results/data/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.status`
- `results/data/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.allowed_claim`
- `results/data/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.h1_4_closure_lane`
- `results/data/phase5_mechanism/anchor_coupling_confirmatory.json` -> `results.robustness.robustness_class`

SK-H1.4 minimum semantic checks before release claims:

- Conclusive status + `robustness_class=ROBUST` must map to `h1_4_closure_lane=H1_4_ALIGNED`.
- Conclusive status + `robustness_class in {MIXED, FRAGILE}` must map to `h1_4_closure_lane=H1_4_QUALIFIED`.
- `h1_4_reopen_conditions` must be present and non-empty.
- For `H1_4_QUALIFIED`, claim language must include: robustness remains qualified across registered lanes.

## 19. Phase 10 Detailed Workflows (with full flags)

For detailed Phase 10 execution with full flags (e.g. scan resolution,
permutation counts), see the commands below. The simplified versions in
Section 11 are used by `replicate_all.py`.

```bash
python3 scripts/phase10_admissibility/run_stage1_hjk.py
python3 scripts/phase10_admissibility/run_stage1b_jk_replication.py --seeds 42,77,101 --target-tokens 30000 --method-j-null-runs 100 --method-k-runs 100
python3 scripts/phase10_admissibility/run_stage2_gi.py --scan-resolution folios_2000 --scan-fallbacks folios_full,tiff,folios_1000 --image-max-side 1400 --method-g-permutations 1000 --method-i-bootstrap 500 --method-i-min-languages 12 --language-token-cap 50000
python3 scripts/phase10_admissibility/run_stage3_f.py --target-tokens 30000 --param-samples-per-family 10000 --null-sequences 1000 --perturbations-per-candidate 12 --max-outlier-probes 12 --null-block-min 2 --null-block-max 12 --symbol-alphabet-size 64
python3 scripts/phase10_admissibility/run_stage4_synthesis.py
```

Canonical Phase 10 outputs:
- `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
- `results/reports/phase10_admissibility/PHASE_10_CLOSURE_UPDATE.md`
- `results/data/phase10_admissibility/stage4_synthesis.json`
- `results/data/phase10_admissibility/stage4_execution_status.json`
