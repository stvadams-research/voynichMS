# Phase 1: Foundation (Digital Ledgering)

## Intent
The objective of Phase 1 is to create a high-fidelity, "Assumption-Resistant" digital record of the Voynich Manuscript. This establishes the "Ground Truth" for all subsequent analysis by converting raw images into a structured database of tokens, lines, and regions.

## How to Replicate
Execute the standardized replication script:
```bash
python3 scripts/phase1_foundation/replicate.py
```

## Key Tests & Diagnostics
- **Acceptance Test**: Verifies that the SQL schema and RunManager are correctly tracking provenance.
*   **Database Population**: Ingestes the 222 folios of the manuscript and registers them as the `voynich_real` dataset.
*   **Destructive Audit**: Proves that the ledger is deterministic by attempting to break the structural mappings through re-ingestion.

## Expected Results
- A verified SQLite database at `data/voynich.db`.
- Identification of high-repetition tokens (establishing the 69.8% repetition baseline).
- Full provenance records for all data ingestion runs in `runs/`.
