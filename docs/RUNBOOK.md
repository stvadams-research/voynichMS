# Engineering Runbook

## 1. Environment Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Reproducing Baselines

### Phase 2: Admissibility and Stress Tests
```bash
# Run the full Phase 2 pipeline
python3 scripts/analysis/run_phase_2_1.py
python3 scripts/analysis/run_phase_2_2.py
python3 scripts/analysis/run_phase_2_3.py
python3 scripts/analysis/run_phase_2_4.py
```

### Phase 3: Synthesis and Testing
```bash
# Run the baseline gap analysis
python3 scripts/synthesis/run_baseline_assessment.py

# Extract grammar
python3 scripts/synthesis/extract_grammar.py

# Run Indistinguishability Test
python3 scripts/synthesis/run_indistinguishability_test.py
```

## 3. Running Tests
```bash
pytest tests/
```

## 4. Key Configuration
- `REQUIRE_COMPUTED=1`: Enforces no simulation fallbacks.
- `seed`: Most scripts accept a `--seed` argument for determinism.
