# Audit Log

## 2026-02-10 - Audit 6 Remediation

Source plan: `planning/audit/AUDIT_6_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_6.md`

### Opened

- `RI-1`: Hardcoded/estimated metrics in `run_indistinguishability_test.py`.
- `RI-2`/`RI-3`/`RI-4`/`DOC-1`: Sensitivity artifacts and documentation mismatch.
- `MC-1`/`MC-2`: Stale run status persistence (`running` snapshots).
- `RI-5`/`MC-5`: Reproduction verifier mutates baseline DB and has narrow scope.
- `MC-3`/`MC-4`: Coverage confidence and missing sensitivity end-to-end checks.
- `RI-6`: Strict computed-mode policy needs stronger verification path.
- `INV-2`/`DOC-2`: Missing required `AUDIT_LOG.md`.

### Decisions

- Keep `run_id` immutable and unique; persist final run state via completion callbacks.
- Treat provenance result artifacts as immutable snapshots: omit mutable `status`.
- Preserve `status/` as transient outputs; add documented cleanup path.
- Enforce sensitivity artifact integrity checks in reproducibility verification.

### In Progress

- WS-A through WS-G execution tracked in `reports/audit/FIX_EXECUTION_STATUS_6.md`.

## 2026-02-10 - Audit 7 Remediation

Source plan: `planning/audit/AUDIT_7_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_7.md`

### Opened

- `MC-6`/`DOC-3`: verifier and CI could report success after partial verifier execution.
- `RI-9`: sensitivity artifacts were canonical but bounded and not release-grade evidence.
- `RI-8`/`RI-6`: indistinguishability path still depended on fallback/simulated profile behavior.
- `MC-2`/`ST-1`: historical stale run records and mixed legacy status artifacts.
- `INV-1`/`INV-3`: release baseline and transient artifact lifecycle hygiene gaps.

### Decisions

- Verification scripts must emit an explicit completion token and fail non-zero on partial execution.
- Sensitivity release evidence requires `mode=release` and full scenario execution (`executed == expected`).
- Missing-manifest historical runs are classified as `orphaned` and timestamp-closed for ambiguity reduction.
- Pre-release baseline checks are scriptable and must validate sensitivity release readiness and audit log presence.

### Execution Notes

- `scripts/verify_reproduction.sh` now handles unset `VIRTUAL_ENV` safely and emits `VERIFY_REPRODUCTION_COMPLETED`.
- `scripts/ci_check.sh` now requires verifier sentinel confirmation and defaults to stage-3 (50%) coverage gate.
- Full release-mode sensitivity sweep executed on `voynich_synthetic_grammar` (`17/17` scenarios).
- Strict indistinguishability run (`REQUIRE_COMPUTED=1`) now fails fast with explicit missing-page diagnostics.
- `scripts/audit/repair_run_statuses.py` reconciled stale rows: historical unknowns marked `orphaned`.

### In Progress / Residual

- Strict indistinguishability release execution remains blocked on missing real pharmaceutical page records in `voynich_real`.

## 2026-02-10 - Audit 8 Remediation

Source plan: `planning/audit/AUDIT_8_EXECUTION_PLAN.md`  
Source findings: `reports/audit/COMPREHENSIVE_AUDIT_REPORT_8.md`

### Opened

- `RI-10`: release checks allowed `INCONCLUSIVE` sensitivity artifacts to pass as release-ready.
- `RI-11`/`RI-12`: strict indistinguishability path blocked by missing real pages; fallback remained default outside strict mode.
- `MC-3`: six foundational modules at `0%` coverage.
- `MC-2R`/`ST-1`: historical orphan rows and legacy verify artifact semantics required clearer operational handling.
- `INV-1`: dirty release override had no required rationale.
- `DOC-4`: playbook expected root-level reference docs while repository used `docs/`.

### Decisions

- `release_evidence_ready` now means full release sweep plus conclusive robustness plus quality-gate pass.
- Release gates (`pre_release_check.sh`, `verify_reproduction.sh`) fail closed on `INCONCLUSIVE` sensitivity outcomes.
- Strict indistinguishability preflight is a first-class command path (`--preflight-only`) with explicit blocked artifact output.
- Dirty release overrides require explicit rationale (`DIRTY_RELEASE_REASON`).
- Root-level reference doc aliases are maintained for playbook contract compatibility.

### Execution Notes

- Full release-mode sensitivity sweep rerun completed (`17/17`) with:
  - `release_evidence_ready=false`
  - `robustness_decision=INCONCLUSIVE`
  - `quality_gate_passed=false`
- Pre-release and verification gates now fail as intended against inconclusive sensitivity evidence.
- Added targeted tests for prior 0%-coverage modules:
  - `core/logging`, `core/models`, `qc/anomalies`, `qc/checks`, `storage/filesystem`, `storage/interface`
- Coverage increased to `52.28%`; prior 0% modules now range from `80%` to `100%`.
- Legacy status artifact cleanup script now supports `legacy-report` and accurate zero-match reporting.

### In Progress / Residual

- Strict computed indistinguishability remains blocked by missing `10/18` pharmaceutical pages in `voynich_real`.
