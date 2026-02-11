# Execution Plan: Skeptic Provenance-Uncertainty Hardening (SK-M4)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-M4` (listed as Medium in source; treated here as credibility-critical hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. This plan now serves as implementation and verification trace.

---

## 1) Objective

Address `SK-M4` by turning historical provenance uncertainty into an explicitly bounded, machine-checkable evidence class that cannot be misread as silent certainty.

This plan targets the specific skeptic attack identified in the assessment:

1. Historical uncertainty is acknowledged in policy, but still visible in runtime state (`orphaned` rows).
2. Strong closure language can be framed as inconsistent with unresolved provenance uncertainty.
3. A skeptic can argue that unresolved historical traceability weakens confidence in terminal conclusions.

---

## 2) SK-M4 Problem Statement

From `SK-M4`:

- Provenance policy documents historical orphan handling and uncertainty framing:
  - `governance/PROVENANCE.md:98` through `governance/PROVENANCE.md:107`.
- Runtime metadata still includes orphaned historical rows (assessment observed `63`).

Core skeptic attack:

- "You retain acknowledged historical uncertainty while asserting strong closure in conclusions."

Primary contradiction locus:

- Historical provenance uncertainty is explicit, but closure-facing language may not always surface it with equivalent prominence.

Primary artifacts in scope:

- `governance/PROVENANCE.md`
- `data/voynich.db` (`runs` table status distribution)
- `core_status/core_audit/run_status_repair_report.json`

Secondary dependencies to align during execution:

- `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`
- `results/reports/FINAL_PHASE_3_3_REPORT.md`
- `README.md`
- `governance/governance/REPRODUCIBILITY.md`

---

## 3) Scope and Non-Goals

## In Scope

- Formal provenance-uncertainty taxonomy and allowed-claim boundaries.
- Canonical machine-readable provenance-health artifact for historical run-state confidence.
- Auditable register for orphaned/reconciled/backfilled run-history status.
- Guardrails to block provenance-overstated closure language in tracked docs.
- CI/release integration for provenance uncertainty policy compliance.
- Governance and audit traceability linking SK-M4 finding to controls.

## Out of Scope

- Reconstructing unavailable historical runtime evidence that does not exist.
- Treating backfilled manifests as equivalent to original runtime-emitted manifests.
- Re-running scientific inference phases solely to address provenance documentation risk.
- Re-adjudicating SK-C1/SK-H1/SK-H2/SK-H3/SK-M1/SK-M2/SK-M3 findings.

---

## 4) Success Criteria (Exit Conditions)

`SK-M4` is considered closed only if all criteria below are met:

1. Provenance uncertainty is represented in a canonical machine-readable artifact with explicit status taxonomy.
2. Historical run-state uncertainty (for example, `orphaned` rows) is quantified and traceable in a maintained register.
3. Closure-facing reports include required provenance-confidence qualifiers and source-of-truth links.
4. CI/release checks fail on missing provenance markers, banned over-absolute phrases, or missing required provenance artifacts.
5. Backfilled manifest records remain explicitly distinguishable from original manifests.
6. Audit trail links SK-M4 finding -> policy -> artifacts -> checks -> residual uncertainty statement.

---

## 5) Workstreams

## WS-M4-A: Provenance Uncertainty Policy and Taxonomy

**Goal:** Define formal status classes for historical provenance confidence and claim admissibility.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define provenance-confidence taxonomy (for example `PROVENANCE_ALIGNED`, `PROVENANCE_QUALIFIED`, `PROVENANCE_BLOCKED`, `INCONCLUSIVE_PROVENANCE_SCOPE`). | `governance/HISTORICAL_PROVENANCE_POLICY.md` (new) | Status classes and allowed claims are documented. |
| A2 | Define uncertainty triggers (orphaned rows, missing manifests, backfilled manifests, stale repair report). | same + config | Trigger matrix and severity thresholds are explicit. |
| A3 | Define machine-checkable policy schema (tracked governance/artifacts, required markers, banned patterns). | `configs/core_skeptic/sk_m4_provenance_policy.json` (new) | Policy JSON is parseable and versioned. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/core_skeptic/sk_m4_provenance_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-M4-B: Historical Provenance Inventory and Register

**Goal:** Produce an auditable register of historical provenance uncertainty and remediation state.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Inventory historical run-state evidence sources (DB rows, run manifests, repair reports). | `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md` (new) | All sources and confidence classes listed. |
| B2 | Classify each uncertainty class (`reconciled`, `orphaned`, `backfilled`, `unknown`). | same | Classification table complete and path-scoped. |
| B3 | Map remediation/monitoring actions with ownership and verification command path. | same | Actionable queue and verification map documented. |

### Verification

```bash
python3 scripts/core_audit/repair_run_statuses.py --report-path core_status/core_audit/run_status_repair_report.json
python3 - <<'PY'
import sqlite3
con=sqlite3.connect('data/voynich.db')
rows=con.execute("select status, count(*) from runs group by status order by status").fetchall()
print(rows)
con.close()
PY
```

---

## WS-M4-C: Canonical Provenance-Health Artifact

**Goal:** Establish a single machine-readable source of truth for historical provenance uncertainty status.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define canonical provenance-health schema (`status`, `reason_code`, counts, ratios, allowed_claim, last_reviewed). | `core_status/core_audit/provenance_health_status.json` (new or canonicalized) | Schema is stable and parseable. |
| C2 | Add deterministic artifact builder from DB + repair summary + manifest metadata. | `scripts/core_audit/build_provenance_health_status.py` (new) | Repeatable output with deterministic key fields. |
| C3 | Link closure-facing docs and policy docs to this artifact as source of provenance confidence. | tracked docs | All tracked docs reference canonical provenance health source. |

### Verification

```bash
python3 scripts/core_audit/build_provenance_health_status.py
python3 - <<'PY'
import json
d=json.load(open('core_status/core_audit/provenance_health_status.json'))
print(d.get('status'), d.get('reason_code'), d.get('orphaned_rows'))
PY
```

---

## WS-M4-D: Reconciliation and Backfill Operating Contract

**Goal:** Tighten operational handling so historical uncertainty is explicit, bounded, and non-ambiguous.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Extend repair workflow with explicit dry-run/reporting controls and uncertainty-ledger output. | `scripts/core_audit/repair_run_statuses.py` (update) | Repair operation is auditable before mutation. |
| D2 | Require explicit markers in backfilled manifests (`manifest_backfilled=true`, backfill timestamp/source). | `runs/<run_id>/run.json` backfill contract | Backfills remain distinguishable from runtime-emitted manifests. |
| D3 | Define release-policy thresholds for acceptable unresolved historical uncertainty (for example ratio and absolute bounds). | policy + pre-release checks | Uncertainty thresholds are explicit and enforceable. |

### Verification

```bash
python3 scripts/core_audit/repair_run_statuses.py --report-path core_status/core_audit/run_status_repair_report.json
rg -n "\"manifest_backfilled\": true" runs/*/run.json
```

---

## WS-M4-E: Claim-Scope Calibration for Provenance Uncertainty

**Goal:** Ensure closure-facing language cannot be interpreted as provenance certainty beyond evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Define required provenance qualifier block for closure-facing docs. | policy + docs | Required wording and markers standardized. |
| E2 | Calibrate closure/public summary language to include provenance-confidence caveat and source link. | `README.md`, `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md` | Tracked docs include explicit bounded provenance clause. |
| E3 | Standardize residual uncertainty statement so unresolved historical gaps are explicit but scoped. | same + skeptic report templates | No ambiguity about historical confidence bounds. |

### Verification

```bash
rg -n "provenance|historical uncertainty|orphaned|source of truth|provenance_health_status" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-M4-F: Automated Provenance-Uncertainty Guardrails

**Goal:** Prevent regression to provenance-overstated claims or missing uncertainty controls.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Implement SK-M4 checker for required markers, banned patterns, and artifact policy compliance. | `scripts/core_skeptic/check_provenance_uncertainty.py` (new) | Checker fails on SK-M4 violations in ci/release modes. |
| F2 | Add deterministic tests (pass/fail/allowlist/artifact-schema/threshold behavior). | `tests/core_skeptic/test_provenance_uncertainty_checker.py` (new) | Policy behavior is test-covered. |
| F3 | Integrate checker into CI/release gates and contract tests. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, audit contract tests | Guard runs automatically and is contract-locked. |

### Verification

```bash
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
python3 -m pytest -q tests/core_skeptic/test_provenance_uncertainty_checker.py
```

---

## WS-M4-G: Governance and Audit Traceability

**Goal:** Keep provenance-uncertainty decisions durable and externally auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-M4 reproducibility section with provenance-health generation and verification commands. | `governance/governance/REPRODUCIBILITY.md` | SK-M4 command path documented end-to-end. |
| G2 | Add SK-M4 execution status report template and fill during remediation pass. | `reports/core_skeptic/SKEPTIC_M4_EXECUTION_STATUS.md` (during execution) | Changes and checks are trace-complete. |
| G3 | Add audit-log trace entry mapping SK-M4 finding to controls and residual risks. | `AUDIT_LOG.md` | End-to-end traceability present. |

### Verification

```bash
rg -n "SK-M4|provenance uncertainty|provenance_health_status|check_provenance_uncertainty" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M4-A (policy/taxonomy)
2. WS-M4-B (inventory/register)
3. WS-M4-C (canonical provenance-health artifact)
4. WS-M4-D (repair/backfill operating contract)
5. WS-M4-E (claim-scope calibration)
6. WS-M4-F (automated guardrails and gate integration)
7. WS-M4-G (governance and audit traceability)

Rationale:

- Provenance claim calibration and automation should not proceed before taxonomy, thresholds, and canonical artifact contract are defined.

---

## 7) Decision Matrix for SK-M4 Provenance Status

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Historical uncertainty is quantified, policy-qualified, and closure language is aligned with canonical provenance artifact. | `PROVENANCE_ALIGNED` | "Historical provenance uncertainty is bounded and policy-compliant." |
| Uncertainty remains but is explicitly disclosed, source-linked, and within policy thresholds. | `PROVENANCE_QUALIFIED` | "Historical provenance is qualified with explicit uncertainty bounds." |
| Required provenance artifact/markers are missing, or closure language overstates certainty. | `PROVENANCE_BLOCKED` | "Provenance confidence claims are blocked pending remediation." |
| Evidence is incomplete to assign a reliable confidence class. | `INCONCLUSIVE_PROVENANCE_SCOPE` | "Provenance status remains provisional pending full reconciliation." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M4-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M4 taxonomy policy and machine-readable config. |
| WS-M4-B Inventory/Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added provenance uncertainty register and source inventory. |
| WS-M4-C Canonical Artifact | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added provenance-health builder and canonical status artifact. |
| WS-M4-D Reconciliation Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added dry-run repair mode and explicit backfill metadata markers. |
| WS-M4-E Claim Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added closure-facing provenance-confidence qualifiers and canonical source references. |
| WS-M4-F Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Implemented SK-M4 checker/tests and integrated into CI/release gates. |
| WS-M4-G Governance/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated reproducibility guidance, execution report, and audit trace entry. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Historical orphan uncertainty cannot be fully eliminated due missing legacy manifests. | High | Medium | Keep uncertainty explicit and bounded via canonical artifact + qualified claim class. |
| R2 | Backfilled manifests may be misread as original runtime evidence. | Medium | High | Require persistent `manifest_backfilled=true` marker and policy language. |
| R3 | Provenance checker may over-flag legitimate historical narrative contexts. | Medium | Medium | Add scoped allowlist behavior with explicit tests. |
| R4 | Repair/backfill operations could unintentionally mutate metadata without clear trace. | Medium | High | Add dry-run/report-first workflow and audit report output checks. |
| R5 | Claim calibration changes could conflict with SK-H2/SK-M1 phrasing controls. | Medium | Medium | Reuse shared claim-boundary terms and cross-check all policy checkers in CI. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M4 historical provenance policy and machine-readable config.
2. SK-M4 provenance register mapping uncertainty classes to actions.
3. Canonical provenance-health status artifact with explicit confidence class.
4. Hardened reconciliation/backfill operating contract and repair-report path.
5. Calibrated closure-facing provenance qualifiers in tracked docs.
6. SK-M4 checker and tests integrated into CI/release checks.
7. SK-M4 execution status report under `reports/core_skeptic/`.
8. Audit log entry documenting SK-M4 decisions and residual uncertainty.
