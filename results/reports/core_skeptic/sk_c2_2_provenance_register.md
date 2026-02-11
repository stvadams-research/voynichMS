# SK-C2.2 Provenance Contract Register

Date: 2026-02-10  
Source plan: `planning/core_skeptic/SKEPTIC_C2_2_EXECUTION_PLAN.md`

## A1. Runner Inventory and Contract Classification

Runner inventory snapshot (`scripts/**/run_*.py`):

- total runner scripts: `38`
- display-only exemptions: `5`
- delegated-provenance runners: `1`
- direct provenance runners (expected `ProvenanceWriter` in script): `32`

Contract policy source:

- `configs/core_audit/provenance_runner_contract.json`

Delegated runner entry:

- `scripts/phase8_comparative/run_proximity_uncertainty.py` -> `src/phase8_comparative/mapping.py::run_analysis`

## A2. Comparative Uncertainty Provenance Path Trace

Flow:

1. `scripts/phase8_comparative/run_proximity_uncertainty.py` parses args and calls `run_analysis(...)`.
2. `src/phase8_comparative/mapping.py::run_analysis` computes uncertainty summary.
3. `src/phase8_comparative/mapping.py::run_analysis` writes uncertainty artifact via:
   - `ProvenanceWriter.save_results(uncertainty, output_uncertainty)`
4. Runner validates envelope shape (`provenance` + `results`) and returns summary.

Observed output after run:

- `results/phase7_human/phase_7c_uncertainty.json` contains both `provenance` and `results` top-level keys.

## A3. Root-Cause Classification

| Symptom | Classification | Evidence |
|---|---|---|
| CI provenance contract failed on `run_proximity_uncertainty.py`. | Checker-model gap (string-only contract heuristic). | `tests/core_audit/test_provenance_contract.py` previously required literal `ProvenanceWriter` in every non-exempt runner script. |
| Comparative runner was flagged despite provenance-wrapped output existing. | Delegated provenance path was valid but undocumented/unenforced. | `run_proximity_uncertainty.py` delegates writing to `src/phase8_comparative/mapping.py`, which already used `ProvenanceWriter`. |
| Skeptic could claim policy-vs-enforcement mismatch. | Contract centralization missing. | No policy-backed runner provenance checker existed before SK-C2.2 execution. |

Root-cause call:

- Primary: brittle test contract that did not model delegated provenance.
- Secondary: missing centralized policy/checker for runner-level provenance modes.

