# Provenance and Output Policy

This document defines how execution outputs are written and how run identity is managed.

## Run Identity

- `run_id`: unique per execution instance (prevents overwrite collisions).
- `experiment_id`: deterministic seed-linked identifier for grouping comparable runs.
- `run_nonce`: execution nonce used to separate repeated same-seed invocations.

`run_id` and `experiment_id` are recorded in run config/provenance.

## Output Writing Contract

Runner scripts should use `foundation.core.provenance.ProvenanceWriter` for JSON results.

For an output target like:

- `results/phase_4/lang_id_results.json`

the writer produces:

1. Run-scoped immutable snapshot:
   - `results/phase_4/by_run/lang_id_results.<run_id>.json`
2. Backward-compatible latest pointer:
   - `results/phase_4/lang_id_results.json`

The payload format is:

```json
{
  "provenance": {
    "run_id": "...",
    "git_commit": "...",
    "timestamp": "...",
    "seed": 42,
    "experiment_id": "..."
  },
  "results": { "...": "..." }
}
```

Notes:

- Result-artifact provenance intentionally omits a mutable run `status` field.
- Final run status is authoritative in:
  - `runs/<run_id>/run.json`
  - `runs` table in metadata DB
- This avoids stale `"running"` snapshots in immutable result artifacts.

## Consumer Guidance

- For longitudinal auditing and artifact retention, consume `by_run/`.
- For existing tooling expecting fixed filenames, consume latest-pointer files.

## Script Classification

Not every `run_*.py` script emits JSON artifacts. The project uses two script classes:

- `artifact-producing`: must write provenance-wrapped outputs via `ProvenanceWriter`.
- `display-only`: console/report orchestration scripts with no JSON artifact contract.

Current display-only exemptions:

- `scripts/analysis/run_phase_2_1.py`
- `scripts/analysis/run_phase_2_3.py`
- `scripts/analysis/run_phase_2_4.py`
- `scripts/synthesis/run_phase_3.py`
- `scripts/synthesis/run_phase_3_1.py`

If any exempted script begins writing persistent JSON outputs, it must migrate to `ProvenanceWriter`.

## Status Artifact Policy

- `status/` is treated as transient local execution output.
- durable audit and publication artifacts belong in `reports/` or provenance-managed `results/.../by_run/`.
- `status/` should not be committed as release evidence.
- Verification artifacts under `status/by_run/verify_*.json` may be cleaned with:
  - `bash scripts/audit/cleanup_status_artifacts.sh dry-run`
  - `bash scripts/audit/cleanup_status_artifacts.sh legacy-report`
  - `bash scripts/audit/cleanup_status_artifacts.sh clean`
- Keep `status/audit/sensitivity_sweep.json` as the latest machine-readable sensitivity snapshot.
- Pre-release checks fail if legacy verify artifacts still contain `provenance.status` fields.
- `status/synthesis/TURING_TEST_RESULTS.json` is used as strict preflight evidence for indistinguishability release checks.
  - Required: `strict_computed=true`.
  - If strict preflight cannot proceed because required source pages are unavailable/lost, use:
    - `status: "BLOCKED"`
    - `reason_code: "DATA_AVAILABILITY"`
    - `preflight.missing_count` and `preflight.missing_pages`.

Retention guideline:

- Keep only the latest verification snapshots needed for active debugging.
- Before release packaging, clean transient verification files and preserve durable evidence in `reports/`.

## Historical Run Rows Without Manifests

Some historical `runs` table rows may predate reliable `runs/<run_id>/run.json` generation.
When stale rows are found with no manifest:

- classify as `orphaned` (instead of `running`)
- set `timestamp_end` to `timestamp_start` to avoid open-ended run ambiguity
- record reconciliation summary via:
  - `python3 scripts/audit/repair_run_statuses.py`
  - output report: `status/audit/run_status_repair_report.json`

This keeps historical uncertainty explicit without pretending manifest-level certainty.

Optional manifest backfill:

- To backfill missing `runs/<run_id>/run.json` files for historical rows, run:
  - `python3 scripts/audit/repair_run_statuses.py --backfill-missing-manifests`
- Backfilled manifests include `manifest_backfilled=true` so they remain distinguishable
  from original runtime-emitted manifests.
- Backfill is intended for provenance traceability and does not imply stronger
  historical certainty than the underlying DB row content.

## Failure Policy

- Results must be JSON-serializable.
- Missing active run context still writes provenance with `run_id: "none"` and UTC timestamp.
