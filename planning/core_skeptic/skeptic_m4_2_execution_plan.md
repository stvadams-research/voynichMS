# Execution Plan: Skeptic Provenance Confidence Closure (SK-M4.2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-M4` (pass-2 residual, Medium)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and closeout artifacts updated.

---

## 1) Objective

Address pass-2 `SK-M4` residuals by attempting to tighten historical provenance confidence as far as feasible, while preserving explicit fail-closed uncertainty boundaries where legacy gaps are irrecoverable.

This plan targets three pass-2 residual classes:

1. Provenance remains `PROVENANCE_QUALIFIED` (bounded, not eliminated).
2. Provenance register/report drift exists (stale snapshot mismatch).
3. Provenance confidence narrative is still vulnerable when operational contracts fail.

Desired endpoint:

1. a provenance-confidence state that is internally coherent, machine-checked, and current, and  
2. a deterministic policy path to either upgraded confidence or bounded qualified closure.

---

## 2) SK-M4 Problem Statement (Pass 2)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Positive progress:
  - Provenance uncertainty framing is explicit in top-level docs.
  - Canonical provenance-health artifact exists and is policy-gated.
- Residual state:
  - `core_status/core_audit/provenance_health_status.json` reports `PROVENANCE_QUALIFIED`.
  - Runtime DB spot-check shows unresolved historical orphan rows (`orphaned=63`).
  - Register drift: `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md` snapshot lags runtime counts (`success=133` vs runtime `success=135` in assessment).

Cross-finding dependency from same pass:

- Provenance-runner contract failure (SK-C2) materially weakens provenance-confidence credibility even if SK-M4 framing is present.

Core skeptic leverage:

- "Uncertainty is explicit, but provenance confidence remains qualified and some provenance summaries drift or decouple from runtime policy state."

---

## 3) Scope and Non-Goals

## In Scope

- SK-M4 pass-2 provenance-confidence residual closure strategy.
- Elimination of stale provenance register/report drift.
- Stronger coupling between provenance-confidence claims and operational contract health.
- Canonical artifact/source-of-truth alignment and checker/test hardening.
- Governance/core_audit traceability for M4.2 decisions and residual risk.

## Out of Scope

- Reconstructing unavailable historical runtime evidence that cannot be recovered.
- Broad rework of non-provenance skeptic findings (SK-H1/H2/H3, SK-M1/M2/M3), except dependency integration.
- Claiming `PROVENANCE_ALIGNED` by wording alone without metric/contract support.

---

## 4) Success Criteria (Exit Conditions)

`SK-M4` pass-2 residual is considered closed only when all criteria below are satisfied:

1. Provenance register and summaries are generated/synchronized from canonical provenance-health data (no stale count drift).
2. Provenance confidence class and allowed-claim language are deterministic and reason-code-specific.
3. Provenance confidence posture is contract-coupled to runner/gate integrity (cannot overstate confidence while provenance contract is failing).
4. CI/release checks fail closed on provenance drift, stale artifacts, or claim/capability mismatch.
5. Closure-facing reports remain no stronger than current provenance confidence class.
6. Audit trace links pass-2 SK-M4 residual -> controls -> resulting confidence class.

---

## 5) Workstreams

## WS-M4.2-A: Residual Baseline and Drift Inventory

**Goal:** Convert pass-2 SK-M4 residual into explicit measurable gaps.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Snapshot current provenance-health metrics (status, reason_code, orphaned/success counts, threshold pass). | `core_status/core_audit/provenance_health_status.json` | Baseline values are frozen for M4.2 cycle. |
| A2 | Compare provenance register/report snapshots to runtime/canonical counts. | `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md`, DB/runtime checks | Drift table identifies stale fields and magnitude. |
| A3 | Classify each gap as data irrecoverability vs synchronization/process gap. | New `reports/core_skeptic/SK_M4_2_GAP_REGISTER.md` | Every residual has remediation lever and owner. |

### Verification

```bash
python3 scripts/core_audit/build_provenance_health_status.py
python3 - <<'PY'
import json, sqlite3
p=json.load(open('core_status/core_audit/provenance_health_status.json'))
print(p.get('status'), p.get('reason_code'), p.get('orphaned_rows'))
con=sqlite3.connect('data/voynich.db')
print(con.execute("select status,count(*) from runs group by status order by status").fetchall())
con.close()
PY
```

---

## WS-M4.2-B: Canonical Synchronization Contract (No-Drift Provenance Reporting)

**Goal:** Remove stale register drift by enforcing canonical-source synchronization.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define canonical-source precedence for provenance counts and class labels. | `governance/HISTORICAL_PROVENANCE_POLICY.md` | Source-of-truth hierarchy is explicit. |
| B2 | Add/extend generator or sync script for provenance register snapshots. | New `scripts/core_audit/sync_provenance_register.py` (or equivalent) | Register values are reproducibly generated from canonical sources. |
| B3 | Add staleness metadata fields (`generated_utc`, `source_snapshot`) to register/report outputs. | `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md` | Drift is detectable and auditable. |

### Verification

```bash
python3 scripts/core_audit/sync_provenance_register.py
rg -n "generated_utc|source_snapshot|orphaned_rows|success" reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md
```

---

## WS-M4.2-C: Provenance Confidence and Contract-Health Coupling

**Goal:** Ensure provenance confidence claims are entitlement-limited by operational provenance contract integrity.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define policy rule linking SK-M4 confidence class to runner-contract/gate-health outcomes. | `configs/core_skeptic/sk_m4_provenance_policy.json` | Policy includes contract-coupled downgrade logic. |
| C2 | Add reason-code taxonomy for coupled failures (`PROVENANCE_CONTRACT_BLOCKED`, `REGISTER_DRIFT_DETECTED`, etc.). | same + docs | Downgrades are machine-readable and narrative-stable. |
| C3 | Align SK-M4 artifact output with coupling reasons and allowed claim class constraints. | `core_status/core_audit/provenance_health_status.json` schema/producer path | Confidence class cannot overstate under failed contract posture. |

### Verification

```bash
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```

---

## WS-M4.2-D: Recovery Attempt Path for Qualified Provenance

**Goal:** Attempt feasible reduction of qualified uncertainty without fabricating certainty.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Re-run reconciliation/backfill audit in dry-run and classify residual orphan rows by recoverability class. | `core_status/core_audit/run_status_repair_report.json`, new recoverability section | Residual rows are stratified into recoverable vs irrecoverable classes. |
| D2 | Apply only policy-approved reconciliation actions and record delta. | repair workflow + provenance health artifact | Any confidence improvement is measured and reproducible. |
| D3 | If irrecoverable residual remains, codify bounded closure criteria and non-upgrade conditions. | `governance/HISTORICAL_PROVENANCE_POLICY.md` + register | `PROVENANCE_QUALIFIED` remains explicit and justified, not ambiguous. |

### Verification

```bash
python3 scripts/core_audit/repair_run_statuses.py --dry-run --report-path core_status/core_audit/run_status_repair_report.json
python3 scripts/core_audit/build_provenance_health_status.py
```

---

## WS-M4.2-E: Closure/Report Coherence Calibration for Pass 2

**Goal:** Keep closure-facing language aligned with current SK-M4 class and residual constraints.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Re-validate provenance-confidence language in closure/public docs against canonical artifact class. | `README.md`, `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md`, `governance/PROVENANCE.md` | No document exceeds current provenance entitlement. |
| E2 | Add/refresh explicit pass-2 residual statement where needed (qualified, bounded, current). | same | Residual uncertainty is explicit and source-linked. |
| E3 | Ensure skeptic-facing provenance register references are current and synchronized. | `reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md` | Skeptic evidence trail is no longer stale. |

### Verification

```bash
rg -n "PROVENANCE_QUALIFIED|provenance_health_status|historical provenance|qualified" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md \
  governance/PROVENANCE.md \
  reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md
```

---

## WS-M4.2-F: Guardrails and Regression Tests

**Goal:** Prevent recurrence of SK-M4 pass-2 residual classes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Extend SK-M4 checker for register-drift and contract-coupling rules. | `scripts/core_skeptic/check_provenance_uncertainty.py` | Checker fails closed on stale/split provenance semantics. |
| F2 | Add tests for stale register mismatch, artifact age, and contract-coupled downgrade behavior. | `tests/core_skeptic/test_provenance_uncertainty_checker.py` | Residual cases are regression-locked. |
| F3 | Ensure CI/pre-release/reproduction contracts include new M4.2 checks and markers. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh`, audit contract tests | Pipeline blocks provenance over-claim regressions. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_provenance_uncertainty_checker.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-M4.2-G: Governance and Closeout Traceability

**Goal:** Preserve an auditable pass-2 SK-M4 closure trail.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Create M4.2 execution status template/report path. | New `reports/core_skeptic/SKEPTIC_M4_2_EXECUTION_STATUS.md` | Execution can be documented consistently. |
| G2 | Update reproducibility/guidance docs for canonical SK-M4.2 command path. | `governance/governance/REPRODUCIBILITY.md` | Repro path includes synchronization and confidence checks. |
| G3 | Add audit-log linkage requirement for SK-M4.2 findings and final class. | `AUDIT_LOG.md` | End-to-end traceability is complete. |

### Verification

```bash
rg -n "SK-M4.2|provenance_health_status|sync_provenance_register|check_provenance_uncertainty" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M4.2-A (baseline and gap inventory)
2. WS-M4.2-B (canonical synchronization contract)
3. WS-M4.2-C (contract-health coupling)
4. WS-M4.2-D (recovery attempt path)
5. WS-M4.2-E (closure/report coherence calibration)
6. WS-M4.2-F (guardrails/tests)
7. WS-M4.2-G (governance closeout)

Rationale:

- Fix source-of-truth drift and policy semantics before recalibrating narrative or adding stricter gate checks.

---

## 7) Decision Matrix for SK-M4.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Provenance confidence is synchronized, contract-coupled, and threshold-aligned with no unresolved drift. | `M4_2_ALIGNED` | "Historical provenance confidence is aligned and operationally coherent." |
| Provenance remains historically qualified but fully synchronized, explicit, and policy-coherent. | `M4_2_QUALIFIED` | "Historical provenance remains qualified with explicit bounded uncertainty and coherent controls." |
| Drift/contract mismatch or over-assertive provenance language persists. | `M4_2_BLOCKED` | "SK-M4 remains blocked by provenance confidence incoherence." |
| Insufficient evidence to classify confidence coherence after remediation. | `M4_2_INCONCLUSIVE` | "SK-M4.2 status is provisional pending fuller provenance reconciliation evidence." |

Execution outcome: `M4_2_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M4.2-A Baseline/Gap Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `reports/core_skeptic/SK_M4_2_GAP_REGISTER.md` with baseline, drift classes, and residual categories. |
| WS-M4.2-B Sync Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added `scripts/core_audit/sync_provenance_register.py` and canonical sync artifact generation path. |
| WS-M4.2-C Contract Coupling | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended M4 policy/checker and provenance-health builder with gate-health coupling semantics. |
| WS-M4.2-D Recovery Path | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Re-ran dry-run repair and refreshed provenance health/register artifacts with recoverability classification. |
| WS-M4.2-E Report Coherence | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Re-synchronized `SK_M4_PROVENANCE_REGISTER.md` and updated provenance policy docs for pass-2 residual clarity. |
| WS-M4.2-F Guardrails/Tests | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added checker logic/tests for contract coupling and register drift; updated CI/pre-release/verify contracts. |
| WS-M4.2-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added M4.2 execution status report and audit-log trace linkage. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Historical orphan uncertainty cannot be fully eliminated because original runtime manifests are irrecoverable. | High | Medium | Prefer qualified bounded closure with explicit irrecoverability classes. |
| R2 | Register/report synchronization remains manual and drifts again. | Medium | High | Enforce generated register path and staleness checks in CI/release. |
| R3 | Contract-coupling introduces policy conflicts with other skeptic gates. | Medium | Medium | Reuse shared reason-code taxonomy and add contract tests for compatibility. |
| R4 | Attempted reconciliation changes metadata unexpectedly. | Medium | High | Use dry-run/report-first workflow and diff-based review before mutation. |
| R5 | Narrative softening obscures valid conclusions. | Low | Medium | Use class-based claim gating rather than blanket language reduction. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M4.2 gap register with drift and recoverability classification.
2. Canonical synchronization path for provenance register/report values.
3. Extended SK-M4 policy and checker rules for contract-coupled confidence.
4. Updated provenance-health + register coherence with current counts.
5. Calibrated closure/public provenance statements aligned to current class.
6. M4.2 checker/test/gate contract hardening.
7. M4.2 execution status report under `reports/core_skeptic/`.
8. Audit-log trace linking pass-2 SK-M4 residual to resulting outcome class.

---

## 11) Closure Criteria

`SK-M4` pass-2 residual is closed only when:

1. Provenance confidence class and counts are synchronized across canonical artifact and skeptic register artifacts.
2. Provenance confidence entitlement is operationally coupled to contract/gate integrity.
3. Public closure language is no stronger than the current SK-M4 class.
4. CI/release/reproduction checks detect and block stale or over-assertive provenance confidence regressions.
