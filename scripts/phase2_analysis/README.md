# Phase 2: Analysis & Admissibility

## Intent
Phase 2 determines which classes of explanation (Natural Language, Cipher, Procedural) are structurally permitted by the data. The core finding is that natural language explanations are **inadmissible** due to the manuscript's extreme mapping fragility and lack of redundancy.

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase2_analysis/replicate.py
```

## Key Tests & Diagnostics
*   **Admissibility Mapping**: Tests the manuscript against 6 distinct explanation classes.
*   **Perturbation Tests**: Measures "Mapping Stability"—how the structure breaks under character shifts. (Voynich score: 0.02 vs. Language baseline: 0.85).
*   **Information Density**: Calculates the Z-score relative to random noise (Voynich Z: 5.68).

## Expected Results
*   **Kill Rule Activation**: Formal rejection of linguistic and cipher-based models.
*   **Sensitivity Report**: A summary of parameter robustness in `results/reports/phase2_analysis/sensitivity_results.md`.
*   **Consensus Findings**: Data confirming that non-semantic systems are sufficient to explain the observed anomalies.
