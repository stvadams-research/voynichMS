# Multimodal Coupling Policy (SK-H1)

## Purpose

This policy defines when illustration/layout coupling claims are conclusive.

Canonical policy source:

- `configs/core_skeptic/sk_h1_multimodal_policy.json`
- `configs/core_skeptic/sk_h1_multimodal_status_policy.json`

Canonical result artifact:

- `results/phase5_mechanism/anchor_coupling_confirmatory.json`

## Status Taxonomy

The coupling artifact must emit exactly one status:

- `CONCLUSIVE_NO_COUPLING`
- `CONCLUSIVE_COUPLING_PRESENT`
- `INCONCLUSIVE_UNDERPOWERED`
- `INCONCLUSIVE_INFERENTIAL_AMBIGUITY`
- `BLOCKED_DATA_GEOMETRY`

## H1.4 Closure Lanes

The artifact must also emit `h1_4_closure_lane`:

- `H1_4_ALIGNED`: conclusive status with robust matrix alignment.
- `H1_4_QUALIFIED`: conclusive canonical lane but robustness remains mixed/fragile across registered lanes.
- `H1_4_INCONCLUSIVE`: non-conclusive status.
- `H1_4_BLOCKED`: blocked status.

Required robustness classes:

- `ROBUST`
- `MIXED`
- `FRAGILE`

## Guardrails

1. Conclusive statuses are only allowed when adequacy thresholds pass.
2. `INCONCLUSIVE_UNDERPOWERED` is reserved for adequacy-threshold failures.
3. `INCONCLUSIVE_INFERENTIAL_AMBIGUITY` is reserved for adequacy-pass + inference-inconclusive runs.
4. Adequacy must include minimum line count, page count, recurring contexts, and balance ratio.
5. Conclusive claims must include uncertainty metrics:
   - bootstrap confidence interval for delta consistency
   - permutation-test p-value
6. Any non-conclusive status forbids categorical "no adaptation" or "coupling proven" language.
7. If `h1_4_closure_lane=H1_4_QUALIFIED`, claims must explicitly state that robustness remains qualified across registered lanes.

## Repro Steps

```bash
python3 scripts/phase5_mechanism/generate_all_anchors.py --dataset-id voynich_real --method-name geometric_v1 --threshold 0.10
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release
```

## Evidence Consumer Rule

Downstream summaries (for example Phase 7 findings) must not make stronger claims than the emitted status.
For H1.4-qualified outcomes, summaries must include robustness class and closure-lane qualifiers.
