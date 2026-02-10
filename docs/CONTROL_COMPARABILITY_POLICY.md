# Control Comparability Policy (SK-H3)

## Purpose

This policy constrains how control generators are matched and evaluated so control-based conclusions cannot be accused of circular tuning.

Machine-readable policies:

- `configs/skeptic/sk_h3_control_comparability_policy.json`
- `configs/skeptic/sk_h3_data_availability_policy.json`

Automated checkers:

- `scripts/skeptic/check_control_comparability.py`
- `scripts/skeptic/check_control_data_availability.py`

## Core Rules

1. Matching and evaluation metrics must be partitioned.
2. Overlap between matching metrics and holdout evaluation metrics is treated as target leakage.
3. Control normalization mode must be explicit and policy-approved.
4. Public conclusions using controls must be bounded by comparability status.
5. Missing comparability artifacts are release-path failures unless explicitly allowed by mode.

## Canonical Artifacts

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- `status/synthesis/TURING_TEST_RESULTS.json`

`CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` is the canonical SK-H3.2 data-availability register and must include expected pages, available pages, missing pages, and policy pass flags.

## Comparability Status Taxonomy

- `COMPARABLE_CONFIRMED`: policy checks passed, holdout evidence sufficient.
- `COMPARABLE_QUALIFIED`: policy checks passed with explicit caveats.
- `INCONCLUSIVE_DATA_LIMITED`: evidence volume or runtime constraints insufficient.
- `NON_COMPARABLE_BLOCKED`: policy violation or structural blocker (for example `DATA_AVAILABILITY`).

Required status fields include:

1. `evidence_scope`
2. `full_data_closure_eligible`
3. `available_subset_status`
4. `available_subset_reason_code`
5. `missing_pages` / `missing_count`

## Data-Availability Contract (SK-H3.2)

When strict preflight identifies approved missing pages, comparability must remain blocked for full-data closure while still allowing bounded available-subset evidence.

Required semantics:

- `reason_code=DATA_AVAILABILITY`
- `evidence_scope=available_subset`
- `full_data_closure_eligible=false`
- `allowed_claim` must state that available-subset findings are non-conclusive.

The approved-lost-page registry is policy-bound in `configs/skeptic/sk_h3_data_availability_policy.json`.

## Claim Boundaries

If status is `NON_COMPARABLE_BLOCKED` due `DATA_AVAILABILITY`:

- Allowed: "full-dataset comparability is blocked by data availability; available-subset evidence is bounded and non-conclusive."
- Not allowed: language implying full-dataset control comparability closure.

## Enforcement Modes

- `ci`: enforce docs/policy integrity and artifact structure when artifacts are present.
- `release`: enforce docs/policy integrity and require all tracked artifacts and cross-artifact consistency.

## Verification

```bash
python3 scripts/synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/skeptic/check_control_comparability.py --mode ci
python3 scripts/skeptic/check_control_comparability.py --mode release
python3 scripts/skeptic/check_control_data_availability.py --mode ci
python3 scripts/skeptic/check_control_data_availability.py --mode release
```
