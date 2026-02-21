# Execution Plan: Skeptic Historical Provenance Confidence Closure (SK-M4.4)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
**Finding Target:** `SK-M4` (Medium, pass-4 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. See `reports/core_skeptic/SKEPTIC_M4_4_EXECUTION_STATUS.md` for command evidence and outcomes.

---

## 1) Objective

Address the pass-4 `SK-M4` residual as fully as feasible on this fourth attempt by making historical provenance confidence:

1. deterministic and machine-auditable,
2. explicitly bounded where historical irrecoverability persists, and
3. non-repeatable under unchanged evidence (anti-reopen safeguards).

This plan is designed to prevent a fifth cycle where SK-M4 is re-reported for the same bounded historical condition despite synchronized controls.

---

## 2) Pass-4 SK-M4 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`:

- `SK-M4 (Medium): Provenance governance is synchronized and policy-coupled, but historical confidence remains qualified.`
- Evidence references:
  - `core_status/core_audit/provenance_health_status.json:3` (`PROVENANCE_QUALIFIED`)
  - `core_status/core_audit/provenance_health_status.json:4`
  - `core_status/core_audit/provenance_health_status.json:19` (`orphaned_rows=63`)
  - `core_status/core_audit/provenance_health_status.json:43`
  - `core_status/core_audit/provenance_health_status.json:48` (`contract_coupling_pass=true`)
  - `core_status/core_audit/provenance_register_sync_status.json:4` (`IN_SYNC`)
  - `core_status/core_audit/provenance_register_sync_status.json:5` (`drift_detected=false`)
  - `core_status/core_audit/provenance_register_sync_status.json:26` (`COUPLED_DEGRADED`)

Skeptic leverage:

- provenance drift is controlled, but historical certainty remains explicitly bounded.

Current canonical SK-M4 state snapshot:

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `orphaned_rows=63`
- `threshold_policy_pass=true`
- `contract_coupling_pass=true`
- register sync `status=IN_SYNC` and `drift_detected=false`

---

## 3) Fourth-Attempt Retrospective (Why M4.2 Still Left Residual)

This fourth-attempt plan explicitly addresses repeat patterns that remained after M4.2:

1. **Synchronization was solved; certainty class was not.**  
   M4.2 fixed drift and coupling, but SK-M4 still reopens because `PROVENANCE_QUALIFIED` is interpreted as unresolved rather than bounded.

2. **Irrecoverability is described but not yet terminally encoded for anti-repeat closure.**  
   Historical orphan rows remain quantified, yet closure criteria do not fully distinguish irrecoverable bounded state from actionable regression.

3. **Cross-surface confidence semantics can still drift by interpretation.**  
   Even with checker coverage, skeptic reassessment can reopen unless lane-level provenance confidence classes are explicit and report-entitled.

4. **Objective reopen triggers for SK-M4 are under-specified.**  
   Without strict trigger conditions, unchanged evidence can repeatedly produce the same finding.

---

## 4) Scope and Non-Goals

## In Scope

- SK-M4 pass-4 historical provenance confidence closure semantics.
- Provenance-health and register-sync artifact parity/freshness and confidence-lane derivation.
- Historical-orphan irrecoverability classification and bounded confidence governance.
- Checker/pipeline/report policy coupling for SK-M4 anti-overreach.
- Governance artifacts for anti-repeat reopen criteria.

## Out of Scope

- SK-C1 release sensitivity remediation.
- Non-SK-M4 skeptic classes (H1/H2/H3/M1/M2/M3) except direct dependency references.
- Fabricating legacy provenance certainty for irrecoverable historical rows.

---

## 5) Deterministic SK-M4.4 Closure Framework

To prevent repeat loops, SK-M4.4 uses explicit closure lanes:

## Lane A: Fully Aligned Historical Confidence (`M4_4_ALIGNED`)

Allowed only when all are true:

- `provenance_health.status=PROVENANCE_ALIGNED`
- orphan/manifest/running thresholds pass with no irrecoverable residual blockers
- register sync is in-sync with zero drift
- contract coupling and gate-health parity are fully consistent

## Lane B: Qualified but Synchronized (`M4_4_QUALIFIED`)

Allowed only when all are true:

- `provenance_health.status=PROVENANCE_QUALIFIED`
- `threshold_policy_pass=true`
- register sync `status=IN_SYNC` and `drift_detected=false`
- coupling checks pass and required reason-codes are present
- public claims are explicitly bounded to qualified confidence

## Lane C: Bounded Historical Irrecoverability (`M4_4_BOUNDED`)

Allowed only when all are true:

- residual orphan class is explicitly classified as historically irrecoverable under current source constraints
- recovery path attempts are documented and no policy-approved reconciliation remains
- bounded confidence claims are deterministic and reopenable only under objective triggers

## Disallowed Ambiguous State

If lane predicates are not met:

- `M4_4_BLOCKED` (drift/coupling/claim mismatch), or
- `M4_4_INCONCLUSIVE` (insufficient evidence for lane assignment).

---

## 6) Success Criteria (Exit Conditions)

SK-M4.4 is complete only when:

1. one deterministic lane (`M4_4_ALIGNED`, `M4_4_QUALIFIED`, or `M4_4_BOUNDED`) is machine-derived,
2. historical residuals are decomposed into recoverable vs irrecoverable classes,
3. freshness and parity checks across provenance artifacts are fail-closed,
4. report/doc claim boundaries are synchronized to lane entitlement,
5. CI/release/reproduction gates enforce SK-M4.4 semantics consistently,
6. decision record includes objective reopen triggers that block repeat findings on unchanged evidence.

---

## 7) Workstreams

## WS-M4.4-A: Baseline Freeze and Residual Decomposition

**Goal:** Freeze pass-4 SK-M4 state and classify all residual vectors.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze canonical pass-4 SK-M4 tuple and evidence references. | New `reports/core_skeptic/SK_M4_4_BASELINE_REGISTER.md` | Baseline captures status, reason, counts, sync/coupling state, evidence links. |
| A2 | Decompose residual into vectors (`historical_orphaned`, `recoverability_gap`, `entitlement_gap`, `reopen_governance_gap`). | same | Every vector has mapped controls and tests. |
| A3 | Define objective SK-M4 reopen conditions and anti-repeat exclusions. | same + decision section | Reopen criteria are explicit and non-interpretive. |

### Verification

```bash
python3 - <<'PY'
import json
h=json.load(open('core_status/core_audit/provenance_health_status.json')).get('results', {})
s=json.load(open('core_status/core_audit/provenance_register_sync_status.json')).get('results', {})
print(h.get('status'), h.get('reason_code'), h.get('orphaned_rows'))
print(h.get('threshold_policy_pass'), h.get('contract_coupling_pass'))
print(s.get('status'), s.get('drift_detected'), s.get('recoverability_class'))
PY
```

---

## WS-M4.4-B: Historical Irrecoverability and Recovery-Ceiling Formalization

**Goal:** Convert historical uncertainty from narrative caveat into terminal machine-enforced classification.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add explicit SK-M4.4 recoverability class taxonomy in policy (`RECOVERABLE`, `IRRECOVERABLE_BOUNDED`, `UNKNOWN`). | `configs/core_skeptic/sk_m4_provenance_policy.json` | Recoverability lane is machine-readable and required. |
| B2 | Extend provenance-health artifact with `m4_4_historical_lane`, `m4_4_residual_reason`, and `m4_4_reopen_conditions`. | `scripts/core_audit/build_provenance_health_status.py` | Lane can be derived directly from canonical artifact. |
| B3 | Require documented recovery attempt evidence for `M4_4_BOUNDED` eligibility. | policy + register templates | Bounded closure requires reproducible failed-recovery record. |

### Verification

```bash
python3 scripts/core_audit/build_provenance_health_status.py
python3 - <<'PY'
import json
r=json.load(open('core_status/core_audit/provenance_health_status.json')).get('results', {})
print(r.get('m4_4_historical_lane'), r.get('m4_4_residual_reason'))
print(r.get('m4_4_reopen_conditions'))
PY
```

---

## WS-M4.4-C: Synchronization and Freshness Hardening

**Goal:** Ensure SK-M4 confidence cannot be asserted from stale or mismatched provenance snapshots.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add age/freshness checks for both provenance-health and sync artifacts. | `configs/core_skeptic/sk_m4_provenance_policy.json`, checker | Stale provenance artifacts fail closed. |
| C2 | Add strict parity checks for core_status/reason/rows between health and sync artifacts where applicable. | `scripts/core_skeptic/check_provenance_uncertainty.py` | Semantic mismatch cannot pass silently. |
| C3 | Add deterministic stale/mismatch reason-codes for SK-M4.4 diagnostics. | checker + artifact outputs | Failures are actionable and non-ambiguous. |

### Verification

```bash
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```

---

## WS-M4.4-D: Contract-Coupled Confidence Entitlement

**Goal:** Tighten mapping from gate-health state to allowed provenance-confidence claim class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Define lane-bound allowed claim classes under degraded vs healthy gate state. | `configs/core_skeptic/sk_m4_provenance_policy.json` | Claim class cannot exceed gate-coupled entitlement. |
| D2 | Add check for consistency between `contract_health_status`, `contract_reason_codes`, and SK-M4 lane. | checker + health builder | Contract semantics are coherent and auditable. |
| D3 | Require explicit reason-code family for degraded/coupled qualified states. | policy + checker | Qualified states are diagnosable and repeatable. |

### Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```

---

## WS-M4.4-E: Report and Doc Claim-Boundary Synchronization

**Goal:** Ensure all closure-facing provenance language matches SK-M4.4 lane entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add SK-M4.4 boundary markers to tracked docs and skeptic register surfaces. | `README.md`, `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/phase3_synthesis/final_phase_3_3_report.md`, `governance/PROVENANCE.md`, `governance/HISTORICAL_PROVENANCE_POLICY.md`, `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md` | No document exceeds lane-entitled confidence class. |
| E2 | Add required bounded-language clauses for `M4_4_BOUNDED` and `M4_4_QUALIFIED`. | same | Qualified/bounded states are explicit and reproducible. |
| E3 | Ban deterministic historical-certainty phrasing unless `M4_4_ALIGNED`. | policy marker rules + checker | Over-assertive language becomes test-detectable. |

### Verification

```bash
rg -n "M4_4_|PROVENANCE_QUALIFIED|PROVENANCE_ALIGNED|bounded|core_status/core_audit/provenance_health_status.json" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/phase3_synthesis/final_phase_3_3_report.md \
  governance/PROVENANCE.md \
  governance/HISTORICAL_PROVENANCE_POLICY.md \
  reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md
```

---

## WS-M4.4-F: Checker, Pipeline, and Regression Locking

**Goal:** Prevent recurrence of SK-M4 residual through test-enforced contracts.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend checker for SK-M4.4 lane derivation, freshness, and parity checks. | `scripts/core_skeptic/check_provenance_uncertainty.py` | Checker fails on stale, mismatched, or over-entitled states. |
| F2 | Add tests for lane mismatch, stale artifacts, parity mismatch, and claim entitlement drift. | `tests/core_skeptic/test_provenance_uncertainty_checker.py`, `tests/core_audit/test_sync_provenance_register.py` | SK-M4.4 regressions are test-locked. |
| F3 | Ensure CI/pre-release/verify scripts enforce the same SK-M4.4 contract sequence. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, audit contract tests | No gate path bypasses SK-M4.4 enforcement. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_provenance_uncertainty_checker.py \
  tests/core_audit/test_sync_provenance_register.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-M4.4-G: Governance Closeout and Anti-Repeat Controls

**Goal:** Produce complete governance artifacts so unchanged bounded evidence does not trigger repeated remediation loops.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-M4.4 baseline/diagnostic/claim-boundary registers. | New `reports/core_skeptic/SK_M4_4_BASELINE_REGISTER.md`, `reports/core_skeptic/SK_M4_4_DIAGNOSTIC_MATRIX.md`, `reports/core_skeptic/SK_M4_4_CLAIM_BOUNDARY_REGISTER.md` | Residual rationale and allowed claims are auditable. |
| G2 | Add SK-M4.4 decision record with selected lane and objective reopen triggers. | New `reports/core_skeptic/SK_M4_4_DECISION_RECORD.md` | Reassessment can distinguish unchanged bounded state vs true regression. |
| G3 | Add execution status template path and audit-log linkage requirements. | `reports/core_skeptic/SKEPTIC_M4_4_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | End-to-end traceability from finding -> controls -> lane state. |

### Verification

```bash
rg -n "SK-M4.4|M4_4_|PROVENANCE_QUALIFIED|HISTORICAL_ORPHANED_ROWS_PRESENT|reopen" \
  planning/core_skeptic \
  reports/core_skeptic \
  AUDIT_LOG.md
```

---

## 8) Execution Order

1. WS-M4.4-A Baseline Freeze  
2. WS-M4.4-B Irrecoverability Formalization  
3. WS-M4.4-C Freshness/Parity Hardening  
4. WS-M4.4-D Contract-Coupled Entitlement  
5. WS-M4.4-E Report/Doc Synchronization  
6. WS-M4.4-F Checker/Pipeline/Test Locking  
7. WS-M4.4-G Governance Closeout

Rationale:

- freeze and classify residual first,
- formalize lane semantics and artifact contracts second,
- then enforce with checkers/tests/gates,
- and close with anti-repeat governance artifacts.

---

## 9) Decision Matrix for SK-M4.4

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Provenance health, sync, freshness, and contract coupling all support aligned certainty. | `M4_4_ALIGNED` | "Historical provenance confidence is aligned and operationally coherent." |
| Provenance remains qualified but fully synchronized and contract-entitled. | `M4_4_QUALIFIED` | "Historical provenance confidence remains qualified with bounded, policy-coherent uncertainty." |
| Historical irrecoverability is explicitly proven and bounded with complete diagnostics. | `M4_4_BOUNDED` | "Historical provenance confidence remains bounded by irrecoverable historical gaps; stronger certainty is not entitled." |
| Drift/coupling/freshness/claim mismatches persist. | `M4_4_BLOCKED` | "SK-M4 remains unresolved due provenance confidence incoherence." |
| Evidence is incomplete for deterministic lane assignment. | `M4_4_INCONCLUSIVE` | "SK-M4.4 status remains provisional pending complete provenance evidence." |

---

## 10) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M4.4-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline and residual decomposition captured in `reports/core_skeptic/SK_M4_4_BASELINE_REGISTER.md`. |
| WS-M4.4-B Irrecoverability Formalization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M4.4 lane and residual fields to `scripts/core_audit/build_provenance_health_status.py` and regenerated canonical provenance status artifact. |
| WS-M4.4-C Freshness/Parity Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added fail-closed freshness and cross-artifact parity checks in `scripts/core_skeptic/check_provenance_uncertainty.py`. |
| WS-M4.4-D Contract Entitlement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Policy/checker enforce degraded-gate lane entitlement and contract-coupling coherence. |
| WS-M4.4-E Report/Doc Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated SK-M4.4 markers/boundaries in tracked docs and synchronized `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md`. |
| WS-M4.4-F Checker/Pipeline/Test Lock | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended SK-M4 checker/tests; targeted provenance and audit contract suites pass. |
| WS-M4.4-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M4.4 baseline, diagnostic, claim-boundary, decision, and execution-status governance artifacts. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 11) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | SK-M4 continues to reopen on unchanged bounded historical evidence. | High | High | Add deterministic SK-M4.4 lanes with objective reopen triggers. |
| R2 | Historical orphan rows are misinterpreted as sync failures rather than irrecoverable residuals. | Medium | High | Explicit recoverability taxonomy and bounded-lane criteria. |
| R3 | Artifact freshness drift causes stale confidence assertions. | Medium | High | Add strict age/parity checks in checker and gates. |
| R4 | Report language exceeds qualified/bounded entitlement. | Medium | High | Required markers + banned patterns + checker enforcement. |
| R5 | Contract-coupling semantics diverge between policy/checker and gate-health artifacts. | Medium | Medium | Enforce cross-artifact parity tests and reason-code alignment. |

---

## 12) Deliverables

Required deliverables for SK-M4.4 execution pass:

1. `reports/core_skeptic/SK_M4_4_BASELINE_REGISTER.md`
2. `reports/core_skeptic/SK_M4_4_DIAGNOSTIC_MATRIX.md`
3. `reports/core_skeptic/SK_M4_4_CLAIM_BOUNDARY_REGISTER.md`
4. `reports/core_skeptic/SK_M4_4_DECISION_RECORD.md`
5. policy/checker updates for SK-M4.4 lane/freshness/parity enforcement
6. synchronized SK-M4.4 claim-boundary language across tracked governance/reports
7. regression tests and gate-contract updates for SK-M4.4 semantics
8. `reports/core_skeptic/SKEPTIC_M4_4_EXECUTION_STATUS.md`
9. `AUDIT_LOG.md` linkage entry from pass-4 SK-M4 finding to resulting SK-M4.4 lane

---

## 13) Closure Criteria

SK-M4 (pass-4 scope) can be considered closed for this cycle only if one is true:

1. `M4_4_ALIGNED`: aligned historical provenance confidence with full policy/gate coherence,
2. `M4_4_QUALIFIED`: qualified historical confidence is fully synchronized and contract-entitled, or
3. `M4_4_BOUNDED`: irrecoverable historical residual is explicitly bounded, machine-diagnosed, and governed by objective reopen triggers.

If none of these conditions are met, SK-M4 remains **OPEN**.
