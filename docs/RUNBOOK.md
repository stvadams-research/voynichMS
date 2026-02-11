# Engineering Runbook

## 1. Environment Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Baseline Data Initialization

```bash
python3 scripts/foundation/acceptance_test.py
```

## 3. Phase 2 Execution (Admissibility and Anomaly Tracks)

Run in order:

```bash
python3 scripts/analysis/run_phase_2_1.py
python3 scripts/analysis/run_phase_2_2.py
python3 scripts/analysis/run_phase_2_3.py
python3 scripts/analysis/run_phase_2_4.py
```

## 4. Phase 3 Execution (Synthesis and Validation)

```bash
python3 scripts/synthesis/extract_grammar.py
python3 scripts/synthesis/run_phase_3.py
python3 scripts/synthesis/run_test_a.py
python3 scripts/synthesis/run_test_b.py
python3 scripts/synthesis/run_test_c.py
python3 scripts/synthesis/run_indistinguishability_test.py
python3 scripts/synthesis/run_baseline_assessment.py
```

## 5. Phase 4-6 Execution (Mechanism and Inference)

### Mechanism pilots

```bash
python3 scripts/mechanism/run_5b_pilot.py
python3 scripts/mechanism/run_5c_pilot.py
python3 scripts/mechanism/run_5d_pilot.py
python3 scripts/mechanism/run_5e_pilot.py
python3 scripts/mechanism/run_5f_pilot.py
python3 scripts/mechanism/run_5g_pilot.py
python3 scripts/mechanism/run_5j_pilot.py
python3 scripts/mechanism/run_5k_pilot.py
python3 scripts/mechanism/run_pilot.py
```

### Inference runners

```bash
python3 scripts/inference/build_corpora.py
python3 scripts/inference/run_lang_id.py
python3 scripts/inference/run_montemurro.py
python3 scripts/inference/run_morph.py
python3 scripts/inference/run_network.py
python3 scripts/inference/run_topics.py
```

## 6. Phase 7 Execution (Human/Codicological)

```bash
python3 scripts/human/run_7a_human_factors.py
python3 scripts/human/run_7b_codicology.py
python3 scripts/human/run_7c_comparative.py
```

## 7. Phase 8 Execution (Visualization and Publication)

### Visualization

```bash
# General usage
visualization foundation token-frequency voynich_real
visualization analysis sensitivity-sweep status/audit/sensitivity_sweep.json
visualization inference lang-id results/phase_4/lang_id_results.json
```

### Publication Drafting

```bash
# Assemble the latest draft from chapter stubs and data
python3 scripts/preparation/assemble_draft.py
```

The master draft will be generated at `planning/preparation/DRAFT_MASTER.md`.

## 8. Verification and Tests

```bash
python3 -m pytest tests/ -v
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
python3 scripts/skeptic/check_claim_entitlement_coherence.py --mode release
```

## 8. SK-C1 Release Sensitivity Sequence

Use this sequence before release-path checks:

```bash
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real --preflight-only
python3 scripts/analysis/run_sensitivity_sweep.py --mode release --dataset-id voynich_real
python3 scripts/audit/check_sensitivity_artifact_contract.py --mode release
```

Operational notes:

- Progress heartbeat: `status/audit/sensitivity_progress.json`
- Preflight status: `status/audit/sensitivity_release_preflight.json`
- Checkpoint/resume state: `status/audit/sensitivity_checkpoint.json`
- To force a fresh run: add `--no-resume`

## 9. Key Configuration

- `REQUIRE_COMPUTED=1`: fail when fallback placeholders are hit in strict mode.
- Seed handling: current scripts are deterministic primarily via internal seeded
  constructors and `active_run(config={"seed": 42, ...})`.

## 10. SK-H3 Control Comparability

Use this sequence before SK-H3-sensitive release claims:

```bash
python3 scripts/synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
python3 scripts/skeptic/check_control_comparability.py --mode ci
python3 scripts/skeptic/check_control_comparability.py --mode release
python3 scripts/skeptic/check_control_data_availability.py --mode ci
python3 scripts/skeptic/check_control_data_availability.py --mode release
```

Claims based on control comparisons must be bounded by
`status/synthesis/CONTROL_COMPARABILITY_STATUS.json`.
Data-availability scope must be read from
`status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` before any
full-closure language is used.

SK-H3.4 minimum semantic checks before release claims:

- `evidence_scope=available_subset` implies `full_data_closure_eligible=false`.
- `available_subset_reason_code=AVAILABLE_SUBSET_UNDERPOWERED` implies non-conclusive underpowered subset evidence.
- `approved_lost_pages_policy_version` and `approved_lost_pages_source_note_path` must match across both SK-H3 artifacts.
- `irrecoverability.classification` must be consistent across both SK-H3 artifacts.
- `full_data_feasibility`, `full_data_closure_terminal_reason`, and `full_data_closure_reopen_conditions` must match across both SK-H3 artifacts.
- `h3_4_closure_lane` must match across both SK-H3 artifacts and align with scope/feasibility semantics.
- `h3_5_closure_lane`, `h3_5_residual_reason`, and `h3_5_reopen_conditions` must match across both SK-H3 artifacts and remain deterministic.

## 11. SK-H1 Multimodal Coupling

Use this sequence before any illustration/layout coupling claim:

```bash
python3 scripts/mechanism/audit_anchor_coverage.py
python3 scripts/mechanism/run_5i_anchor_coupling.py
python3 scripts/skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/skeptic/check_multimodal_coupling.py --mode release
```

Claims must be bounded by:

- `results/mechanism/anchor_coupling_confirmatory.json` -> `results.status`
- `results/mechanism/anchor_coupling_confirmatory.json` -> `results.allowed_claim`
- `results/mechanism/anchor_coupling_confirmatory.json` -> `results.h1_4_closure_lane`
- `results/mechanism/anchor_coupling_confirmatory.json` -> `results.robustness.robustness_class`

SK-H1.4 minimum semantic checks before release claims:

- Conclusive status + `robustness_class=ROBUST` must map to `h1_4_closure_lane=H1_4_ALIGNED`.
- Conclusive status + `robustness_class in {MIXED, FRAGILE}` must map to `h1_4_closure_lane=H1_4_QUALIFIED`.
- `h1_4_reopen_conditions` must be present and non-empty.
- For `H1_4_QUALIFIED`, claim language must include: robustness remains qualified across registered lanes.
