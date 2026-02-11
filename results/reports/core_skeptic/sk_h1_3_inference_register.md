# SK-H1.3 Inference Register

Date: 2026-02-10  
Plan: `planning/core_skeptic/SKEPTIC_H1_3_EXECUTION_PLAN.md`  
Assessment source: `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_3.md`

## Objective

Separate adequacy failure from inferential ambiguity at the status layer and verify machine-checkable coherence between:

- `results.status`
- `results.status_reason`
- `results.adequacy.pass` / `results.adequacy.blocked`
- `results.inference.decision`

## Baseline (Pass-3 Residual)

Prior pass-3 baseline (`run_id=23ac26fe-d2b2-d437-570f-e87bbab32411`) had:

- `status=INCONCLUSIVE_UNDERPOWERED`
- `status_reason=inferential_ambiguity`
- `adequacy.pass=true`

This represented semantic conflation: adequacy passed, but status label encoded underpower.

## H1.3 Status Taxonomy Applied

New SK-H1 status classes:

- `INCONCLUSIVE_UNDERPOWERED`: adequacy thresholds not met.
- `INCONCLUSIVE_INFERENTIAL_AMBIGUITY`: adequacy passes, inference remains inconclusive.

Coherence enforcement is configured in:

- `configs/core_skeptic/sk_h1_multimodal_status_policy.json` (`coherence_policy`)
- `scripts/core_skeptic/check_multimodal_coupling.py`

## Confirmatory Matrix (Executed)

| Run ID | Seed | Max Lines | Status | Status Reason | Adequacy Pass | Inference Decision | Delta | p-value |
|---|---:|---:|---|---|---|---|---:|---:|
| `741db1ce-bdb0-44e8-6cc7-aec70ae8b30f` | 42 | 1600 | `CONCLUSIVE_NO_COUPLING` | `adequacy_and_inference_support_no_coupling` | `True` | `NO_COUPLING` | 0.0013 | 0.8842 |
| `5c1101f4-0254-f55c-d9e1-ef7d58d7b463` | 2718 | 1600 | `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` | `inferential_ambiguity` | `True` | `INCONCLUSIVE` | 0.0246 | 0.7545 |
| `2daabb6d-08f6-0cd7-ab29-e384ff2adeef` | 42 | 20 | `INCONCLUSIVE_UNDERPOWERED` | `adequacy_thresholds_not_met` | `False` | `INCONCLUSIVE` | -0.5000 | 0.4711 |

Canonical publication artifact was restored to policy defaults after matrix execution:

- `results/phase5_mechanism/anchor_coupling_confirmatory.json`
- `run_id=741db1ce-bdb0-44e8-6cc7-aec70ae8b30f`

## Residual Ambiguity Factors and Closure Tests

| Factor | Current State | Closure Test |
|---|---|---|
| Adequacy-vs-inference status conflation | Closed by explicit status split + checker coherence rules | `python3 scripts/core_skeptic/check_multimodal_coupling.py --mode ci` / `--mode release` |
| Inference stability across seeds (same lane) | Not fully closed (`seed=42` conclusive; `seed=2718` ambiguous) | Keep seed-lane matrix in governance and avoid unqualified generalization |
| Adequacy underpower detectability | Closed (small-cohort run deterministically maps to `INCONCLUSIVE_UNDERPOWERED`) | Verify adequacy thresholds via artifact + coherence checker |

## Allowed / Disallowed Claim Boundary

Allowed now:

- Report the current status class from `results/phase5_mechanism/anchor_coupling_confirmatory.json`.
- Distinguish adequacy failures from inferential ambiguity in all SK-H1 outputs.

Disallowed:

- Treat `adequacy.pass=true` + `inference=INCONCLUSIVE` as `INCONCLUSIVE_UNDERPOWERED`.
- Use categorical coupling/no-coupling claims when emitted status is non-conclusive.
