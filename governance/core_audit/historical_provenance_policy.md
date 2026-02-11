# Historical Provenance Policy (SK-M4 / SK-M4.5)

## Purpose

This policy constrains how historical run-traceability uncertainty is represented
and how strongly conclusions may claim provenance confidence.

Machine-readable policy:

- `configs/core_skeptic/sk_m4_provenance_policy.json`

Automated checker:

- `scripts/core_skeptic/check_provenance_uncertainty.py`

Canonical provenance-health artifact:

- `core_status/core_audit/provenance_health_status.json`

## Status Taxonomy

- `PROVENANCE_ALIGNED`: no unresolved historical provenance gaps under current policy thresholds.
- `PROVENANCE_QUALIFIED`: historical gaps remain but are explicitly bounded and policy-compliant.
- `PROVENANCE_BLOCKED`: thresholds or required markers are violated; provenance confidence claims are blocked.
- `INCONCLUSIVE_PROVENANCE_SCOPE`: evidence is insufficient to classify confidence safely.

## SK-M4.5 Historical Lanes

- `M4_5_ALIGNED`: provenance status and historical evidence support aligned confidence.
- `M4_5_QUALIFIED`: provenance remains qualified but synchronized and contract-entitled.
- `M4_5_BOUNDED`: historical uncertainty remains explicitly bounded by irrecoverable legacy gaps.
- `M4_5_BLOCKED`: provenance contract or threshold state is blocked.
- `M4_5_INCONCLUSIVE`: evidence is insufficient for deterministic lane assignment.

## Core Rules

1. Historical orphaned/backfilled run history must be explicitly quantified.
2. Closure-facing reports must include provenance-confidence qualifier text and
   reference the canonical provenance-health artifact.
3. Backfilled manifests must remain distinguishable (`manifest_backfilled=true`).
4. CI and release gates must fail if provenance-confidence requirements are not met.

## Canonical Artifact Contract

`core_status/core_audit/provenance_health_status.json` is the source of truth for:

1. Historical run-status distribution (`success`, `orphaned`, and related counts).
2. Provenance-confidence class and reason code.
3. Threshold-policy compliance state.
4. Residual uncertainty statement (`allowed_claim`).

Register synchronization artifact:

- `core_status/core_audit/provenance_register_sync_status.json`

This artifact is the source of truth for provenance register drift detection.

SK-M4.5 lane keys emitted in canonical artifacts:

- `core_status/core_audit/provenance_health_status.json`:
  - `m4_5_historical_lane`
  - `m4_5_residual_reason`
  - `m4_5_reopen_conditions`
  - `m4_5_data_availability_linkage`
  - `m4_4_historical_lane` (legacy mirror)
  - `m4_4_residual_reason` (legacy mirror)
  - `m4_4_reopen_conditions` (legacy mirror)
- `core_status/core_audit/provenance_register_sync_status.json`:
  - `provenance_health_m4_5_lane`
  - `provenance_health_m4_5_residual_reason`
  - `provenance_health_lane` (resolved lane, backward-compatible alias)
  - `provenance_health_residual_reason` (resolved residual, backward-compatible alias)

## Missing-Folio Non-Blocker Rule

- Missing folio objections route to SK-H3 by default and do not auto-block SK-M4.
- SK-M4 folio-based blocking requires objective provenance-contract incompleteness linkage in `m4_5_data_availability_linkage`.
- Approved irrecoverable-loss classifications are bounded constraints, not standalone SK-M4 blockers.

## Operational Contract Coupling (SK-M4.5)

Provenance confidence is coupled to operational gate health:

- Gate-health source: `core_status/core_audit/release_gate_health_status.json`
- If gate health is degraded, provenance confidence must not be escalated to
  `PROVENANCE_ALIGNED` unless coupling checks pass with explicit reason-code support.

Required contract-coupling reason-code family (degraded gate path):

- `PROVENANCE_CONTRACT_BLOCKED`
- `REGISTER_DRIFT_DETECTED`

Under degraded gate state, SK-M4.5 provenance lane must remain in:

- `M4_5_QUALIFIED`
- `M4_5_BOUNDED`

Legacy SK-M4.4 lane mirrors are retained for backward compatibility:

- `M4_4_QUALIFIED`
- `M4_4_BOUNDED`

## Register Synchronization Path

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_audit/sync_provenance_register.py
```

## Verification

```bash
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_audit/sync_provenance_register.py
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```
