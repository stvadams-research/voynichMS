# Reproducibility Guide

This guide documents the command path to reproduce Phases 2 through 7 using the
current repository scripts.

## 1. Environment Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Data and Schema Initialization

```bash
python3 scripts/foundation/acceptance_test.py
```

## 3. Phase 2 (Analysis) Reproduction

```bash
python3 scripts/analysis/run_phase_2_1.py
python3 scripts/analysis/run_phase_2_2.py
python3 scripts/analysis/run_phase_2_3.py
python3 scripts/analysis/run_phase_2_4.py
```

## 4. Phase 3 (Synthesis) Reproduction

```bash
python3 scripts/synthesis/extract_grammar.py
python3 scripts/synthesis/run_phase_3.py
python3 scripts/synthesis/run_test_a.py
python3 scripts/synthesis/run_test_b.py
python3 scripts/synthesis/run_test_c.py
python3 scripts/synthesis/run_indistinguishability_test.py
python3 scripts/synthesis/run_baseline_assessment.py
```

## 5. Phase 4-6 (Mechanism and Inference) Reproduction

### Mechanism pilots (Phase 5 family)

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

## 6. Phase 7 (Human/Codicological) Reproduction

```bash
python3 scripts/human/run_7a_human_factors.py
python3 scripts/human/run_7b_codicology.py
python3 scripts/human/run_7c_comparative.py
```

## 7. Seed and Determinism Notes

- Most scripts encode deterministic seed usage internally (commonly `seed=42`
  via `active_run(config=...)` and seeded constructors), rather than exposing
  `--seed` CLI flags.
- For strict fallback enforcement during reruns:

```bash
export REQUIRE_COMPUTED=1
```

## 8. Automated Verification

Use both checks after a clean reproduction run:

```bash
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
```
