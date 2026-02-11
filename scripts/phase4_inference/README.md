# Phase 4: Inference Admissibility

## Intent
Phase 4 does not ask "What does the book mean?" but rather "Are the methods used to find meaning valid?" We prove that widely-cited decipherment tools often find high-confidence matches in complete random noise, establishing a statistical "Noise Floor" that invalidates many existing "solutions."

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase4_inference/replicate.py
```

## Key Tests & Diagnostics
*   **Flexible Transform Analysis**: Shows how AI-based language ID tools "find" Latin or Hebrew in gibberish controls.
*   **Montemurro Diagnostics**: Evaluates keyword-clustering claims against algorithmic noise.
*   **False Positive Rate (FPR)**: Establishes that a confidence score of < 0.70 is statistically indistinguishable from random chance.

## Expected Results
*   **Method Admissibility Matrix**: A report in `results/reports/phase4_inference/` classifying which inference methods are diagnostic and which are "pattern-finding machines."
*   **Statistical Noise Floor**: Quantitative data proving that Voynich language scores fall below the threshold of significance.
