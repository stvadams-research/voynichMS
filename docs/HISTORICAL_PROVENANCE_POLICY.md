# Historical Provenance Policy (SK-M4)

## Purpose

This policy constrains how historical run-traceability uncertainty is represented
and how strongly conclusions may claim provenance confidence.

Machine-readable policy:

- `configs/skeptic/sk_m4_provenance_policy.json`

Automated checker:

- `scripts/skeptic/check_provenance_uncertainty.py`

Canonical provenance-health artifact:

- `status/audit/provenance_health_status.json`

## Status Taxonomy

- `PROVENANCE_ALIGNED`: no unresolved historical provenance gaps under current policy thresholds.
- `PROVENANCE_QUALIFIED`: historical gaps remain but are explicitly bounded and policy-compliant.
- `PROVENANCE_BLOCKED`: thresholds or required markers are violated; provenance confidence claims are blocked.
- `INCONCLUSIVE_PROVENANCE_SCOPE`: evidence is insufficient to classify confidence safely.

## Core Rules

1. Historical orphaned/backfilled run history must be explicitly quantified.
2. Closure-facing reports must include provenance-confidence qualifier text and
   reference the canonical provenance-health artifact.
3. Backfilled manifests must remain distinguishable (`manifest_backfilled=true`).
4. CI and release gates must fail if provenance-confidence requirements are not met.

## Canonical Artifact Contract

`status/audit/provenance_health_status.json` is the source of truth for:

1. Historical run-status distribution (`success`, `orphaned`, and related counts).
2. Provenance-confidence class and reason code.
3. Threshold-policy compliance state.
4. Residual uncertainty statement (`allowed_claim`).

Register synchronization artifact:

- `status/audit/provenance_register_sync_status.json`

This artifact is the source of truth for provenance register drift detection.

## Source-of-Truth Precedence

When provenance counts differ across surfaces, resolve in this order:

1. Runtime DB status counts (`data/voynich.db`, `runs` table).
2. Canonical provenance-health artifact (`status/audit/provenance_health_status.json`).
3. Skeptic register markdown snapshot (`reports/skeptic/SK_M4_PROVENANCE_REGISTER.md`).

The skeptic register must be generated/synchronized from canonical artifacts and
must include `generated_utc` + `source_snapshot` markers.

## Operational Contract Coupling (SK-M4.2)

Provenance confidence is coupled to operational gate health:

- Gate-health source: `status/audit/release_gate_health_status.json`
- If gate health is degraded, provenance confidence must not be escalated to
  `PROVENANCE_ALIGNED` unless coupling checks pass with explicit reason-code support.

Required contract-coupling reason-code family:

- `PROVENANCE_CONTRACT_BLOCKED`
- `REGISTER_DRIFT_DETECTED`

## Register Synchronization Path

```bash
python3 scripts/audit/build_release_gate_health_status.py
python3 scripts/audit/build_provenance_health_status.py
python3 scripts/audit/sync_provenance_register.py
```

## Verification

```bash
python3 scripts/audit/build_provenance_health_status.py
python3 scripts/audit/sync_provenance_register.py
python3 scripts/skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/skeptic/check_provenance_uncertainty.py --mode release
```
