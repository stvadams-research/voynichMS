# Closure Conditionality Policy (SK-M1)

## Purpose

This policy prevents contradictory closure language across phase8_comparative and summary reports.

Machine-readable policy:

- `configs/core_skeptic/sk_m1_closure_policy.json`

Automated checker:

- `scripts/core_skeptic/check_closure_conditionality.py`

## Closure Status Taxonomy

- `CONDITIONAL_CLOSURE_ALIGNED`: closure language is framework-bounded and explicitly reopenable.
- `CONDITIONAL_CLOSURE_QUALIFIED`: closure language is mostly aligned with minor wording caveats.
- `CONTRADICTORY_CLOSURE_BLOCKED`: one or more tracked docs contain terminal wording that conflicts with reopening criteria.
- `INCONCLUSIVE_CLOSURE_SCOPE`: evidence or policy markers are insufficient to classify closure posture.

## Required Closure Markers

Tracked closure documents must include:

1. Framework-bounded closure wording (not terminal universal closure).
2. Direct linkage to `governance/REOPENING_CRITERIA.md`.
3. Explicit reopening criteria section or equivalent marker.

## Prohibited Patterns

The policy blocks language that implies irreversible closure while reopening criteria exist, including:

- absolute exhaustion phrasing ("No further amount ..."),
- unqualified terminal closure ("formally closed"),
- terminal-phase wording that conflicts with explicit reopenability.

## Enforcement

- CI: `python3 scripts/core_skeptic/check_closure_conditionality.py --mode ci`
- Pre-release: `python3 scripts/core_skeptic/check_closure_conditionality.py --mode release`

## Operational Entitlement Coupling (SK-M1.2)

Closure class is constrained by canonical gate health:

- `core_status/core_audit/release_gate_health_status.json`

Gate-dependent closure entitlement:

- `GATE_HEALTH_OK` -> `CONDITIONAL_CLOSURE_ALIGNED` phrasing allowed.
- `GATE_HEALTH_DEGRADED` -> closure wording must remain `CONDITIONAL_CLOSURE_QUALIFIED` and explicitly operationally contingent.

Downgrade reason-code family:

- `GATE_CONTRACT_BLOCKED`
- `SENSITIVITY_RELEASE_CONTRACT_BLOCKED`
- `PROVENANCE_RUNNER_RELEASE_CONTRACT_BLOCKED`

## Deterministic H2.4 Lane Coupling

Closure conditionality is now coupled to H2.4 entitlement lanes:

- `H2_4_ALIGNED` -> closure class must be `CONDITIONAL_CLOSURE_ALIGNED`.
- `H2_4_QUALIFIED` -> closure class must be `CONDITIONAL_CLOSURE_QUALIFIED`.

Gate-health freshness is enforced from the canonical gate-health artifact.
If the artifact is stale or lane/class mapping is inconsistent, closure
conditionality checks must fail.

## Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_skeptic/check_closure_conditionality.py --mode ci
python3 scripts/core_skeptic/check_closure_conditionality.py --mode release
```
