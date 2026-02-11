# Phase 5: Mechanism Identification

## Intent
Phase 5 identifies the "Engine" that produced the Voynich Manuscript. By eliminating competing mechanical families (static grids, simple Markov pools), we identified a single survivor: the **Implicit Constraint Lattice**. This proves the manuscript is a rule-evaluated deterministic system with strict line resets.

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase5_mechanism/replicate.py
```

## Key Tests & Diagnostics
*   **Entropy Collapse**: Proves that `(Word, Position, History)` removes 88% of text uncertainty.
*   **Collision Testing**: Shows that identical bigrams in different sections yield consistent successors.
*   **Line Reset Analysis**: Measures the "Reset Score" (~0.95), proving the machine clears its state at every line boundary.

## Expected Results
*   **Mechanism Statement**: A formal identification of the manuscript's production class in `results/reports/phase5_mechanism/`.
*   **Lattice Topology Map**: Data defining the implicit constraints that govern successor choice.
