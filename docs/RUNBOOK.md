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

## 7. Verification and Tests

```bash
python3 -m pytest tests/ -v
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
```

## 8. Key Configuration

- `REQUIRE_COMPUTED=1`: fail when fallback placeholders are hit in strict mode.
- Seed handling: current scripts are deterministic primarily via internal seeded
  constructors and `active_run(config={"seed": 42, ...})`.

## 9. SK-H3 Control Comparability

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

## 10. SK-H1 Multimodal Coupling

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
