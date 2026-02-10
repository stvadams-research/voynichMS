# SK-M4.4 Baseline Register

Date: 2026-02-10  
Plan: `planning/skeptic/SKEPTIC_M4_4_EXECUTION_PLAN.md`  
Source assessment: `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`

## Pass-4 Finding Freeze

Assessment finding frozen for this remediation cycle:

- `SK-M4 (Medium): Provenance governance is synchronized and policy-coupled, but historical confidence remains qualified.`
- Evidence references from assessment:
  - `status/audit/provenance_health_status.json:3`
  - `status/audit/provenance_health_status.json:4`
  - `status/audit/provenance_health_status.json:19`
  - `status/audit/provenance_health_status.json:43`
  - `status/audit/provenance_health_status.json:48`
  - `status/audit/provenance_register_sync_status.json:4`
  - `status/audit/provenance_register_sync_status.json:5`
  - `status/audit/provenance_register_sync_status.json:26`

## Canonical Baseline Snapshot

Primary source: `status/audit/provenance_health_status.json`

- `version`: `2026-02-10-m4.4`
- `status`: `PROVENANCE_QUALIFIED`
- `reason_code`: `HISTORICAL_ORPHANED_ROWS_PRESENT`
- `m4_4_historical_lane`: `M4_4_BOUNDED`
- `m4_4_residual_reason`: `historical_orphaned_rows_irrecoverable_with_current_source_scope`
- `recoverability_class`: `HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `total_runs`: `239`
- `orphaned_rows`: `63`
- `orphaned_ratio`: `0.263598`
- `missing_manifests`: `0`
- `backfilled_manifests`: `63`
- `threshold_policy_pass`: `true`
- `contract_coupling_pass`: `true`
- `contract_health_status`: `GATE_HEALTH_DEGRADED`
- `contract_health_reason_code`: `GATE_CONTRACT_BLOCKED`

Sync source: `status/audit/provenance_register_sync_status.json`

- `status`: `IN_SYNC`
- `drift_detected`: `false`
- `drift_by_status`: `{orphaned: 0, success: 0}`
- `provenance_health_lane`: `M4_4_BOUNDED`
- `health_orphaned_rows`: `63`
- `register_orphaned_rows`: `63`
- `contract_coupling_state`: `COUPLED_DEGRADED`

## Residual Vector Decomposition

| Residual Vector | Baseline Evidence | Diagnosis |
|---|---|---|
| `historical_orphaned` | `orphaned_rows=63`, `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT` | Historical orphan rows remain explicit and bounded. |
| `recoverability_gap` | `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED` | Backfilled manifests improve traceability, but historical certainty remains non-aligned under source limits. |
| `entitlement_gap` | `contract_health_status=GATE_HEALTH_DEGRADED` | Provenance confidence cannot be promoted beyond qualified/bounded while gate health is degraded. |
| `reopen_governance_gap` | prior passes repeatedly reopened SK-M4 | Deterministic SK-M4.4 lane + objective reopen triggers are required to prevent repeat-loop findings. |

## Objective Reopen Triggers and Anti-Repeat Exclusions

Reopen SK-M4.4 only if at least one trigger is true:

1. Provenance drift trigger: `status/audit/provenance_register_sync_status.json` reports `drift_detected=true` or non-zero parity drift.
2. Threshold trigger: provenance threshold checks fail (`threshold_policy_pass=false`) or freshness limits are exceeded.
3. Contract-coupling trigger: gate/provenance coupling becomes incoherent (`contract_coupling_pass=false`, missing reason-code family, or disallowed lane under degraded gate health).
4. Recoverability trigger: source scope changes such that orphan rows can be fully reconciled under policy thresholds.

Do not reopen on unchanged bounded evidence:

- `status=PROVENANCE_QUALIFIED`
- `m4_4_historical_lane=M4_4_BOUNDED`
- `drift_detected=false`
- parity and freshness checks passing
- unchanged historical source scope constraints
