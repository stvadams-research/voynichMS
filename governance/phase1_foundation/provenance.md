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

- `results/data/phase4_inference/lang_id_results.json`

the writer produces:

1. Run-scoped immutable snapshot:
   - `results/data/phase4_inference/by_run/lang_id_results.<run_id>.json`
2. Backward-compatible latest pointer:
   - `results/data/phase4_inference/lang_id_results.json`

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

Not every `run_*.py` script emits JSON artifacts. The project uses three script classes:

- `artifact-producing`: script writes provenance-wrapped outputs directly via `ProvenanceWriter`.
- `delegated-provenance`: script delegates artifact writing to a module that writes via `ProvenanceWriter`.
- `display-only`: console/report orchestration scripts with no JSON artifact contract.

Current display-only exemptions:

- `scripts/phase2_analysis/run_phase_2_1.py`
- `scripts/phase2_analysis/run_phase_2_3.py`
- `scripts/phase2_analysis/run_phase_2_4.py`
- `scripts/phase3_synthesis/run_phase_3.py`
- `scripts/phase3_synthesis/run_phase_3_1.py`

If any exempted script begins writing persistent JSON outputs, it must migrate to `ProvenanceWriter`.

Delegated provenance policy:

- `configs/core_audit/provenance_runner_contract.json`

Contract checker:

```bash
python3 scripts/core_audit/check_provenance_runner_contract.py --mode ci
python3 scripts/core_audit/check_provenance_runner_contract.py --mode release
```

Current delegated runner entry:

- `scripts/phase8_comparative/run_proximity_uncertainty.py` delegates to
  `src/phase8_comparative/mapping.py::run_analysis` (writer-backed).

## Status Artifact Policy

- `core_status/` is treated as transient local execution output.
- durable audit and publication artifacts belong in `reports/` or provenance-managed `results/.../by_run/`.
- `core_status/` should not be committed as release evidence.
- Verification artifacts under `core_status/by_run/verify_*.json` may be cleaned with:
  - `bash scripts/core_audit/cleanup_status_artifacts.sh dry-run`
  - `bash scripts/core_audit/cleanup_status_artifacts.sh legacy-report`
  - `bash scripts/core_audit/cleanup_status_artifacts.sh clean`
- Keep `core_status/core_audit/sensitivity_sweep.json` as the latest local/iterative sensitivity snapshot.
- Keep `core_status/core_audit/sensitivity_sweep_release.json` as the release-candidate sensitivity snapshot consumed by release gates.
- Pre-release checks fail if legacy verify artifacts still contain `provenance.status` fields.
- `core_status/phase3_synthesis/TURING_TEST_RESULTS.json` is used as strict preflight evidence for indistinguishability release checks.
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
  - `python3 scripts/core_audit/repair_run_statuses.py`
  - output report: `core_status/core_audit/run_status_repair_report.json`

This keeps historical uncertainty explicit without pretending manifest-level certainty.

Optional manifest backfill:

- To backfill missing `runs/<run_id>/run.json` files for historical rows, run:
  - `python3 scripts/core_audit/repair_run_statuses.py --backfill-missing-manifests`
- Backfilled manifests include `manifest_backfilled=true` so they remain distinguishable
  from original runtime-emitted manifests.
- Backfill is intended for provenance traceability and does not imply stronger
  historical certainty than the underlying DB row content.

Historical provenance confidence artifact:

- `core_status/core_audit/provenance_health_status.json`
- `core_status/core_audit/provenance_register_sync_status.json`

SK-M4/SK-M4.5 policy reference:

- `governance/HISTORICAL_PROVENANCE_POLICY.md`

The provenance-health artifact is the canonical machine-readable source for
`PROVENANCE_ALIGNED` vs `PROVENANCE_QUALIFIED` vs `PROVENANCE_BLOCKED`
classification in closure-facing claim governance.

SK-M4.5 lane semantics are emitted in the provenance artifact via
`m4_5_historical_lane`, with bounded residual governance for irrecoverable
historical gaps. A legacy mirror key (`m4_4_historical_lane`) is retained for
compatibility while downstream consumers migrate.

Register synchronization command path:

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_audit/sync_provenance_register.py
```

Operational coupling note:

- Provenance confidence claims are operationally contingent on gate-health state.
- Gate-health source: `core_status/core_audit/release_gate_health_status.json`.

## Failure Policy

- Results must be JSON-serializable.
- Missing active run context still writes provenance with `run_id: "none"` and UTC timestamp.
