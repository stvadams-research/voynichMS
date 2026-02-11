# Phase 3: Synthesis & Structural Sufficiency

## Intent
Phase 3 tests the hypothesis that the Voynich Manuscript is a "Process, not a Message." We attempt to "reverse-engineer" the manuscript's internal algorithm and generate synthetic pages that match the real manuscript's statistical signatures.

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase3_synthesis/replicate.py
```

## Key Tests & Diagnostics
*   **Grammar Extraction**: Automated derivation of glyph-level transition rules.
*   **The Turing Test**: A quantitative comparison between `voynich_real` and `synthesis_baseline` datasets.
*   **Gap Analysis**: Measures the mathematical "distance" between real and synthetic repetition rates and locality.

## Expected Results
*   **Successful Continuation**: Proof that a non-semantic generator can produce structurally admissible text.
*   **Indistinguishability Score**: A final report in `results/reports/phase3_synthesis/` showing that the generator successfully replicates the manuscript's anomalies without knowing its "meaning."
