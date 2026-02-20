# Phase 11 Fast-Kill Termination Report

## Decision

Fast-kill gate condition was met on February 20, 2026:

- Test A p-value >= 0.01
- Test B1 p-value >= 0.01

Per `planning/phase11_stroke/phase_11_execution_plan.md`, Stage 3 through Stage 5 are terminated.

## Follow-up Gap Closure: Include EVA `q`

A follow-up rerun was executed on February 20, 2026 to close the main schema gap:

- Added `q` to `src/phase11_stroke/schema.py` and reran Stage 1 + Stage 2.
- Skip rate dropped from ~11.45% to ~8.88% (fewer skipped transcription symbols).
- Gate outcome did not change.

Rerun results (with `q` included):

- Test A: `observed_partial_rho=0.0157`, `p=0.3073`, determination `null`
- Test B1: `B1_boundary_mi=0.1219`, `p=0.7111`, determination `null`

Conclusion after gap closure: fast-kill remains valid.

## Stage 2 Results

- **Test A (Clustering)**  
  - `observed_partial_rho`: `0.0160`  
  - `p_value`: `0.2924`  
  - determination: `null`  
  - artifact: `results/data/phase11_stroke/test_a_clustering.json`

- **Test B1 (Boundary transitions)**  
  - `B1_boundary_mi`: `0.0799`  
  - `B1_p_value`: `0.8441`  
  - determination: `null`  
  - artifact: `results/data/phase11_stroke/test_b_transitions.json`

Supplemental B metrics:

- `B2_intra_mi`: `1.0534` (`p=0.8199`, `null`)
- `B3_information_ratio`: `0.6316`

## Outcome Class

`STROKE_NULL`

Interpretation: under the Phase 11 test configuration, stroke-feature structure did not pass primary significance criteria in either core gate test. The STROKE scale is closed for this execution run.

## Reproducibility

- Test A run id: `9960f6a7-3e30-a89d-e13d-fa6ac90bf9f7`
- Test B run id: `14af948b-12e7-6e4f-a1d3-b8de561ef052`
- Extraction run id: `5574e7eb-265a-57d7-3a5d-66ee13bdac13`
- Seed: `42`
- Permutations: `10,000`

Rerun (with `q`) IDs:

- Test A run id: `b0d9b7cf-147c-70fb-085e-daba07dee767`
- Test B run id: `b782a670-3f28-6c13-017e-f4d3a1e8260a`
- Extraction run id: `74f85ac1-b69a-dd1d-8424-6225f44358c0`
