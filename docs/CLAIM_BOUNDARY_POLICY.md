# Claim Boundary Policy (SK-H2)

## Purpose

This policy constrains public-facing conclusion language so claim strength does not exceed evidentiary scope.

Machine-readable policy:

- `configs/skeptic/sk_h2_claim_language_policy.json`

Automated checker:

- `scripts/skeptic/check_claim_boundaries.py`

## Claim Strength Taxonomy

- `CONCLUSIVE_WITHIN_SCOPE`: conclusion is supported under explicitly stated diagnostics and data scope.
- `QUALIFIED`: evidence is directional but includes unresolved alternatives or caveats.
- `INCONCLUSIVE`: current evidence cannot justify a directional conclusion.
- `DEFERRED`: conclusion requires additional evidence classes (for example external grounding).

## Required Public Conclusion Template

Use this structure in public summary documents:

1. Claim statement (scope-bounded)
2. Scope statement ("within tested structural/computational diagnostics...")
3. Evidence links (specific report paths)
4. Non-claim boundary block
5. Reopening/deferred criteria (if closure language is used)

## Guardrails

1. Do not use categorical falsification/termination language without explicit policy authorization.
2. Keep "what this does not claim" text adjacent to high-level conclusions.
3. Strong claims must include at least one direct evidence artifact reference.
4. CI should fail on banned phrases and missing required markers in tracked docs.

## Cross-Policy Constraint (SK-H3)

When claims rely on control comparability, claim strength must not exceed the
current SK-H3 comparability status in:

- `status/synthesis/CONTROL_COMPARABILITY_STATUS.json`

If comparability is `NON_COMPARABLE_BLOCKED` or `INCONCLUSIVE_DATA_LIMITED`,
public language must remain non-terminal and explicitly caveated.

## Operational Entitlement Coupling (SK-H2.2 / SK-M1.2)

Claim strength is additionally bounded by canonical gate-health status in:

- `status/audit/release_gate_health_status.json`

Gate-dependent entitlement rule:

- `GATE_HEALTH_OK` -> `CONCLUSIVE_WITHIN_SCOPE` claims permitted (still framework-bounded).
- `GATE_HEALTH_DEGRADED` -> claim language must remain at most `QUALIFIED` and explicitly operationally contingent.

Required reason-code family for entitlement downgrade:

- `GATE_CONTRACT_BLOCKED`
- `SENSITIVITY_CONTRACT_BLOCKED`
- `PROVENANCE_RUNNER_CONTRACT_BLOCKED`

## Deterministic H2.4 Lanes

SK-H2.4 introduces deterministic closure lanes derived from
`status/audit/release_gate_health_status.json`:

- `H2_4_ALIGNED`: gate health is healthy and claim class may be `CONCLUSIVE_WITHIN_SCOPE`.
- `H2_4_QUALIFIED`: gate health is degraded and claim class must remain `QUALIFIED`.
- `H2_4_BLOCKED` / `H2_4_INCONCLUSIVE`: policy/coherence/freshness mismatch states.

Gate-health freshness is fail-closed via policy timestamp constraints; stale
gate artifacts must block claim entitlement.

## Verification

```bash
python3 scripts/audit/build_release_gate_health_status.py
python3 scripts/skeptic/check_claim_boundaries.py --mode ci
python3 scripts/skeptic/check_claim_boundaries.py --mode release
```
