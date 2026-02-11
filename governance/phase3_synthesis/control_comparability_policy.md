# Control Comparability Policy (SK-H3)

## Purpose

This policy constrains how control generators are matched and evaluated so control-based conclusions cannot be accused of circular tuning.

Machine-readable policies:

- `configs/core_skeptic/sk_h3_control_comparability_policy.json`
- `configs/core_skeptic/sk_h3_data_availability_policy.json`

Automated checkers:

- `scripts/core_skeptic/check_control_comparability.py`
- `scripts/core_skeptic/check_control_data_availability.py`

## Core Rules

1. Matching and evaluation metrics must be partitioned.
2. Overlap between matching metrics and holdout evaluation metrics is treated as target leakage.
3. Control normalization mode must be explicit and policy-approved.
4. Public conclusions using controls must be bounded by comparability status.
5. Missing comparability artifacts are release-path failures unless explicitly allowed by mode.

## Canonical Artifacts

- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json`

`CONTROL_COMPARABILITY_DATA_AVAILABILITY.json` is the canonical SK-H3.5 data-availability register and must include expected pages, available pages, missing pages, irrecoverability metadata, feasibility metadata, closure-lane metadata, and policy pass flags.

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
5. `available_subset_confidence`
6. `available_subset_diagnostics`
7. `available_subset_reproducibility`
8. `available_subset_confidence_provenance`
9. `missing_pages` / `missing_count`
10. `approved_lost_pages_policy_version`
11. `approved_lost_pages_source_note_path`
12. `irrecoverability`
13. `full_data_feasibility`
14. `full_data_closure_terminal_reason`
15. `full_data_closure_reopen_conditions`
16. `h3_4_closure_lane`
17. `h3_5_closure_lane`
18. `h3_5_residual_reason`
19. `h3_5_reopen_conditions`

## Data-Availability Contract (SK-H3.5)

When strict preflight identifies approved missing pages, comparability must remain blocked for full-data closure while still allowing bounded available-subset evidence.

Required semantics:

- `reason_code=DATA_AVAILABILITY`
- `evidence_scope=available_subset`
- `full_data_closure_eligible=false`
- `allowed_claim` must state that available-subset findings are non-conclusive.
- `approved_lost_pages_policy_version` must match the active SK-H3 data-availability policy.
- `approved_lost_pages_source_note_path` must point to the skeptic register used to justify approved lost pages.
- `full_data_feasibility` must be declared as either `feasible` or `irrecoverable`.
- `full_data_closure_terminal_reason` must explain why full-data closure is blocked or aligned.
- `full_data_closure_reopen_conditions` must define objective reopen triggers.
- `h3_4_closure_lane` must match the lane implied by status semantics.
- `h3_5_closure_lane` must be deterministic (`H3_5_ALIGNED`, `H3_5_TERMINAL_QUALIFIED`, `H3_5_BLOCKED`, `H3_5_INCONCLUSIVE`).
- `h3_5_residual_reason` must state why the H3.5 lane applies.
- `h3_5_reopen_conditions` must list objective reopen triggers.
- `irrecoverability` must include:
  - `recoverable`
  - `approved_lost`
  - `unexpected_missing`
  - `classification`

The approved-lost-page registry is policy-bound in `configs/core_skeptic/sk_h3_data_availability_policy.json`.
Current source note: `reports/core_skeptic/SK_H3_5_BASELINE_REGISTER.md`.

## Closure Lanes (SK-H3.4)

- `H3_4_ALIGNED`: full-dataset closure is feasible and policy checks are aligned.
- `H3_4_QUALIFIED`: full-dataset closure is infeasible because approved lost pages are irrecoverable; available_subset evidence can be qualified but remains non-conclusive.
- `H3_4_BLOCKED`: artifacts are inconsistent or freshness/parity checks fail.
- `H3_4_INCONCLUSIVE`: evidence is incomplete for lane assignment.

## Closure Lanes (SK-H3.5)

- `H3_5_ALIGNED`: full-data comparability is feasible and fully aligned.
- `H3_5_TERMINAL_QUALIFIED`: full-data closure is blocked by approved irrecoverable loss; available-subset evidence remains bounded.
- `H3_5_BLOCKED`: parity/freshness/contract coherence is broken.
- `H3_5_INCONCLUSIVE`: evidence is incomplete for deterministic lane assignment.

## Available-Subset Status Contract

- `AVAILABLE_SUBSET_QUALIFIED`: thresholds pass for bounded available-subset evidence.
- `AVAILABLE_SUBSET_UNDERPOWERED`: thresholds fail; subset evidence remains non-conclusive and insufficient.
- `TARGET_LEAKAGE`: subset evidence is blocked for leakage.

If `available_subset_reason_code=AVAILABLE_SUBSET_UNDERPOWERED`, then:

- `available_subset_status=INCONCLUSIVE_DATA_LIMITED`
- `available_subset_diagnostics.passes_thresholds=false`
- `full_data_closure_eligible=false`

## Claim Boundaries

If status is `NON_COMPARABLE_BLOCKED` due `DATA_AVAILABILITY`:

- Allowed: "full-dataset comparability is blocked by data availability; available-subset evidence is bounded and non-conclusive."
- Not allowed: language implying full-dataset control comparability closure.

If available-subset status is `AVAILABLE_SUBSET_UNDERPOWERED`:

- Allowed: "available-subset evidence is underpowered and cannot support closure claims."
- Not allowed: language implying subset adequacy or full-data closure eligibility.

## Enforcement Modes

- `ci`: enforce governance/policy integrity and artifact structure when artifacts are present.
- `release`: enforce governance/policy integrity and require all tracked artifacts and cross-artifact consistency.

## Verification

```bash
python3 scripts/phase3_synthesis/run_control_matching_audit.py --preflight-only
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```
