# Phase 6: Functional Analysis

## Intent
Phase 6 evaluates the "Algorithmic Efficiency" of the manuscript's production mechanism. We test the hypothesis that the system was designed for manual human operation by measuring its ergonomic optimization and adversarial robustness.

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase6_functional/replicate.py
```

## Key Tests & Diagnostics
*   **Exhaustion Testing**: Measures how many unique lines can be generated before the lattice requires a reset.
*   **Ergonomic Optimization**: Evaluates the physical effort required to traverse the identified constraint lattice.
*   **Adversarial Robustness**: Tests whether minor mechanical errors in the lattice traversal lead to detectable structural collapse.

## Expected Results
*   **Functional report**: A substantive Word document in `results/publication/phase6_report.docx`.
*   **Optimization Scores**: Data proving that the manuscript's structure is optimized for manual execution by a single human scribe.
