# SK-H1.2 Adequacy Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_H1_2_EXECUTION_PLAN.md`  
Assessment source: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`

## Policy Thresholds

Source policy: `configs/skeptic/sk_h1_multimodal_policy.json`

- `min_lines_per_cohort`: 40
- `min_pages_per_cohort`: 8
- `min_recurring_contexts_per_cohort`: 80
- `min_balance_ratio`: 0.20

## Baseline Decomposition

| Stage | Artifact | Status | Adequacy Pass | Key Adequacy Signal |
|---|---|---|---|---|
| Pre-remediation blocked run | `results/mechanism/by_run/anchor_coupling_confirmatory.66ae6392-77e5-83ce-26fc-5964538e6623.json` | `BLOCKED_DATA_GEOMETRY` | `False` | 0 anchored/unanchored lines and pages (`geometry_or_data_block`) |
| Pre-remediation underpowered run | `results/mechanism/by_run/anchor_coupling_confirmatory.60e0aee0-5742-9386-1bc0-45fcc9311ddb.json` | `INCONCLUSIVE_UNDERPOWERED` | `False` | recurring contexts below policy minimum (`24/40 < 80`) |

Root bottleneck in pass-2 residual state: recurring-context adequacy at default small cohort construction.

## Registered Method Sweep (Adequacy-First)

Sweep summary source: `/tmp/h1_2_sweep/summary.json`  
Per-run artifacts: `results/mechanism/by_run/anchor_coupling_confirmatory.<run_id>.json`

| Method | Run ID | Status | Adequacy Pass | Lines A/U | Recurring Contexts A/U | Delta | p-value |
|---|---|---|---|---|---|---|---|
| `geometric_v1_t001` | `1e8812fc-432e-c177-00b8-cfeba6b9349f` | `CONCLUSIVE_NO_COUPLING` | `True` | 1200/1200 | 192/187 | -0.0062 | 0.5868 |
| `geometric_v1_t005` | `24f63141-2b48-73a9-f190-ee3bf4b26b34` | `CONCLUSIVE_NO_COUPLING` | `True` | 1200/1200 | 192/187 | -0.0062 | 0.5868 |
| `geometric_v1_t010` | `de4447fa-70df-8929-2053-0b8a7d61181d` | `INCONCLUSIVE_UNDERPOWERED` | `True` | 1200/1200 | 202/171 | +0.0451 | 0.5702 |
| `geometric_v1_t015` | `80c11ee5-5a43-4633-e3b6-0c283ab2bd46` | `INCONCLUSIVE_UNDERPOWERED` | `True` | 1200/1200 | 202/171 | +0.0451 | 0.5702 |

Adequacy outcome from sweep:

- Adequacy recovered for all tested methods at 1200/1200 cohort lines.
- Failure mode shifted from adequacy shortfall to inference ambiguity for higher-threshold methods.

## Stability Envelope (Selected Method)

Stability source: `/tmp/h1_2_stability/*.json` and `/tmp/h1_2_stability/summary.json`  
Selected method lane: `geometric_v1_t001`

| Tag | Run ID | Status | Adequacy Pass | Lines A/U | Recurring Contexts A/U | Delta | p-value |
|---|---|---|---|---|---|---|---|
| `s42_l800` | `7650d159-224f-445d-c617-cc99e2815658` | `CONCLUSIVE_NO_COUPLING` | `True` | 800/800 | 99/108 | +0.0050 | 0.6926 |
| `s42_l1200` | `4cf9d8d9-7154-b74d-4040-17e4aa97f2de` | `CONCLUSIVE_NO_COUPLING` | `True` | 1200/1200 | 192/187 | -0.0062 | 0.5609 |
| `s42_l1600` | `d4f1c0de-6004-03b4-361e-be468da02ee4` | `CONCLUSIVE_NO_COUPLING` | `True` | 1600/1600 | 305/289 | +0.0013 | 0.8842 |
| `s2718_l1200` | `58dcb298-0069-1156-b7d4-68405dea433b` | `CONCLUSIVE_NO_COUPLING` | `True` | 1200/1200 | 205/191 | +0.0058 | 0.5489 |
| `s314_l1200` | `0eb36348-d72d-6b0d-4ff3-f6953db4eebc` | `INCONCLUSIVE_UNDERPOWERED` | `True` | 1200/1200 | 247/187 | +0.0535 | 0.0958 |
| `s314_l1600` | `c9bf7a72-8792-b615-3b06-5e55f8ab1e7d` | `INCONCLUSIVE_UNDERPOWERED` | `True` | 1600/1600 | 329/288 | +0.0280 | 0.5808 |
| `s2718_l1600` | `23ac26fe-d2b2-d437-570f-e87bbab32411` | `INCONCLUSIVE_UNDERPOWERED` | `True` | 1600/1600 | 323/284 | +0.0246 | 0.7545 |

## Adequacy Attempt Log and Result

1. Blocked cohort geometry and recurring-context shortfall were remediated through method lane selection and larger matched cohorts.
2. Adequacy is now policy-passing in all tracked SK-H1.2 confirmatory lanes.
3. Residual uncertainty is no longer adequacy-driven; it is inferentially ambiguous in a subset of seeds.

Conclusion: adequacy recovery is complete for SK-H1.2; closure risk is now inferential stability, not data sufficiency.
