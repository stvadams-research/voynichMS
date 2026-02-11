# Report Coherence Policy (SK-M3)

## Purpose

This policy prevents internal contradictions between report-level determinations,
method-status tables, and operational entitlement posture.

Machine-readable policy:

- `configs/core_skeptic/sk_m3_report_coherence_policy.json`

Automated checker:

- `scripts/core_skeptic/check_report_coherence.py`

## Status Taxonomy

- `COHERENCE_ALIGNED`: final determinations and method-status tables are consistent.
- `COHERENCE_QUALIFIED`: legacy caveats remain but are explicitly archival-labeled.
- `COHERENCE_BLOCKED`: contradictory status claims exist in tracked reports.
- `INCONCLUSIVE_COHERENCE_SCOPE`: insufficient status evidence for alignment.

## Core Rules

1. A tracked report must not state final determination while retaining unresolved
   method rows marked `PENDING`, unless clearly marked archival.
2. Phase-level method status must reference canonical index:
   `results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json`.
3. Legacy status blocks are allowed only with explicit archival markers.
4. Public closure/summary docs must include operational entitlement markers
   tied to canonical gate-health source.
5. CI and release checks must fail on contradictory status patterns.

## Canonical Artifact

`results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json` is the source of truth for:

1. Method execution status.
2. Method determination class.
3. Last coherence review metadata.

`core_status/core_audit/release_gate_health_status.json` is the source of truth for:

1. Operational gate-health class.
2. Allowed claim/closure entitlement class.
3. Gate-level failure reasons.

## Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_skeptic/check_report_coherence.py --mode ci
python3 scripts/core_skeptic/check_report_coherence.py --mode release
```
