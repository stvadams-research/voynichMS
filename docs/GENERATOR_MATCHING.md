# GENERATOR MATCHING AND VALIDATION

**Project:** Voynich Manuscript – Identifiability Phase  
**Objective:** Define reproducible control matching without target leakage.

---

## 1. Policy Binding (SK-H3)

This document is policy-bound to:

- `docs/CONTROL_COMPARABILITY_POLICY.md`
- `configs/skeptic/sk_h3_control_comparability_policy.json`

SK-H3 requires explicit separation between:

- `matching_metrics` (used to fit controls), and
- `holdout_evaluation_metrics` (used to evaluate comparability quality).

Any overlap is treated as **target leakage**.

---

## 2. Matching Metrics (Fit Objective)

Matched generators are tuned on the following fit metrics only:

| matching_metrics | Target Value (ZL) | Tolerance |
|---|---|---|
| `repetition_rate` | 0.90 | ±0.05 |
| `information_density` | 5.68 | ±0.5 |
| `locality_radius` | 3.0 | ±1.0 |

These metrics constrain control-generation shape; they are not sufficient by themselves for inferential closure.

---

## 3. Holdout Evaluation Metrics (Inference Objective)

Comparability quality must additionally be assessed on untuned metrics:

| holdout_evaluation_metrics | Interpretation |
|---|---|
| `mean_word_length` | Verifies lexical-shape consistency outside fit objective. |
| `positional_entropy` | Verifies positional-symbol behavior outside fit objective. |

Holdout metrics are used to assign comparability status classes (`COMPARABLE_CONFIRMED`, `COMPARABLE_QUALIFIED`, etc.).

---

## 4. Class-Specific Generator Logic

### 4.1 Self-Citation Matcher (`self_citation`)
- **Mechanism:** Kernel selection + mutation.
- **Matching strategy:** Tune pool size/mutation over fit metrics only.

### 4.2 Table-Grille Matcher (`table_grille`)
- **Mechanism:** Component table traversal with deterministic jitter.
- **Matching strategy:** Tune table parameters over fit metrics only.

### 4.3 Mechanical Reuse Matcher (`mechanical_reuse`)
- **Mechanism:** Bounded per-page pools over grammar-compliant tokens.
- **Matching strategy:** Tune pool parameters over fit metrics only.

---

## 5. Validation Protocol

Before a generator class is considered comparability-ready:

1. Run deterministic matching audit:

```bash
python3 scripts/synthesis/run_control_matching_audit.py --preflight-only
```

2. Confirm no metric overlap leakage:

```bash
python3 scripts/skeptic/check_control_comparability.py --mode ci
```

3. For release-path verification, require artifact checks:

```bash
python3 scripts/skeptic/check_control_comparability.py --mode release
python3 scripts/skeptic/check_control_data_availability.py --mode release
```

---

## 6. Required Artifacts

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`
- `status/synthesis/control_matching_cards/*.json`
- `status/synthesis/TURING_TEST_RESULTS.json` (must include comparability block)

When strict preflight is blocked due missing source pages, the status artifact must explicitly declare:

- `evidence_scope=available_subset`
- `full_data_closure_eligible=false`
- `reason_code=DATA_AVAILABILITY`

This lane documents feasible available-subset comparability only; it is not equivalent to full-dataset closure.

---

**Status:** SK-H3 metric partitioning and leakage guardrails documented.  
**Next:** Maintain policy-compliant reruns via checker and release gates.
