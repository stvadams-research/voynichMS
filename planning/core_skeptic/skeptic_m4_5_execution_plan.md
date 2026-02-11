# Execution Plan: Skeptic Historical Provenance Confidence Closure (SK-M4.5)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`  
**Finding Target:** `SK-M4` (Medium, pass-5 residual)  
**Plan Date:** 2026-02-10  
**Attempt Context:** Fifth targeted remediation attempt for SK-M4  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Address all SK-M4 issues that are technically fixable in a fifth pass while preventing repeat cycles where the same bounded historical confidence state is reopened without new evidence.

This pass has four mandatory outcomes:

1. close remaining SK-M4 contract/coherence gaps across artifact, checker, gate, and report surfaces,
2. classify residual historical confidence limits into fixable vs non-fixable classes,
3. enforce anti-repeat reopen triggers for unchanged bounded historical evidence,
4. ensure missing-folio objections are routed correctly and do not repeatedly mis-block SK-M4.

---

## 2) Pass-5 SK-M4 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`:

- `SK-M4 (Medium): Provenance is synchronized and lane-governed, but historical confidence remains bounded.`

Assessment evidence references:

- `core_status/core_audit/provenance_health_status.json:3`
- `core_status/core_audit/provenance_health_status.json:4`
- `core_status/core_audit/provenance_health_status.json:19`
- `core_status/core_audit/provenance_health_status.json:25`
- `core_status/core_audit/provenance_health_status.json:26`
- `core_status/core_audit/provenance_health_status.json:56`
- `core_status/core_audit/provenance_register_sync_status.json:4`
- `core_status/core_audit/provenance_register_sync_status.json:5`
- `core_status/core_audit/provenance_register_sync_status.json:13`
- `core_status/core_audit/provenance_register_sync_status.json:35`

Current canonical SK-M4 snapshot (from status artifacts):

- `status=PROVENANCE_QUALIFIED`
- `reason_code=HISTORICAL_ORPHANED_ROWS_PRESENT`
- `orphaned_rows=63`
- `recoverability_class=HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED`
- `m4_4_historical_lane=M4_4_BOUNDED`
- `m4_4_residual_reason=historical_orphaned_rows_irrecoverable_with_current_source_scope`
- `threshold_policy_pass=true`
- `contract_coupling_pass=true`
- register sync remains `IN_SYNC` with `drift_detected=false`

Skeptic leverage still open:

- provenance governance is strong, but historical certainty remains explicitly bounded rather than aligned.

---

## 3) Fifth-Attempt Retrospective (Why SK-M4 Reappears)

### 3.1 Synchronization solved integrity, not confidence entitlement class

SK-M4.4 solved drift/coupling and standardized bounded semantics, but pass-5 still surfaces SK-M4 because historical confidence remains qualified.

### 3.2 Historical orphan residual is structurally persistent

`orphaned_rows=63` and bounded recoverability class remain stable under current source scope.

### 3.3 Anti-repeat governance remains incomplete unless explicitly codified

Without strict reopen triggers and non-fixable taxonomy, the same bounded state keeps re-entering execution queues.

### 3.4 Cross-domain blocker mixing still risks reopening SK-M4

SK-C1 release evidence failures and SK-H3 missing-folio constraints can be misinterpreted as SK-M4 defects unless boundaries are explicit.

---

## 4) Missing-Folio Non-Blocker Boundary for SK-M4 (Required)

This pass enforces:

1. Missing folios are SK-H3 data-availability constraints by default, not SK-M4 blockers.
2. SK-M4 can be blocked by folio loss only when provenance artifacts/checkers show objective provenance-contract incompleteness caused by missing pages not already classified as approved irrecoverable loss.
3. Repeating approved-lost-page objections without new provenance-contract impact is not a new SK-M4 blocker.
4. SK-M4 reopening on folio grounds requires objective trigger evidence (classification change, parity/freshness break, or new primary source evidence).

This is not a waiver:

- all fixable SK-M4 defects must still be remediated.

---

## 5) Scope and Non-Goals

## In Scope

- SK-M4 provenance-health and register-sync contract coherence.
- Deterministic SK-M4.5 lane semantics and reopen triggers.
- Freshness/parity/coupling enforcement for provenance confidence status.
- Explicit fixable vs non-fixable blocker taxonomy for SK-M4.
- Claim-boundary synchronization across SK-M4 report/doc surfaces.

## Out of Scope

- SK-C1 release sensitivity artifact production.
- SK-H3 full-data comparability remediation.
- SK-H1/H2/M1/M2/M3 remediation except direct dependency references.

---

## 6) Deterministic SK-M4.5 Closure Framework

SK-M4.5 preserves M4.4 compatibility while adding deterministic pass-5 closure semantics.

## Lane A: `M4_5_ALIGNED`

All true:

- provenance confidence is aligned,
- sync parity/freshness/coupling checks all pass,
- no bounded historical residual remains.

## Lane B: `M4_5_QUALIFIED`

All true:

- provenance status remains qualified,
- synchronization and coupling are coherent,
- residual is bounded and correctly claim-limited.

## Lane C: `M4_5_BOUNDED`

All true:

- historical residual is explicitly irrecoverable under current source scope,
- artifact/checker/gate/report parity remains coherent,
- residual reason + reopen triggers are complete and machine-checkable.

## Lane D: `M4_5_BLOCKED`

Any true:

- contract field incompleteness,
- freshness/parity mismatch,
- entitlement/claim boundary incoherence,
- unresolved coupling contradictions.

## Lane E: `M4_5_INCONCLUSIVE`

Evidence is incomplete to deterministically classify the lane.

---

## 7) Success Criteria (Exit Conditions)

SK-M4.5 is complete only when all are true:

1. deterministic SK-M4.5 lane classification is present,
2. all fixable SK-M4 contract/coherence defects are remediated,
3. missing-folio objections are correctly non-blocking for SK-M4 unless objective provenance linkage is shown,
4. residual reason + reopen triggers are explicit and non-null,
5. claim/report/gate surfaces are coherent with lane entitlement,
6. non-fixable residuals are explicitly documented to prevent repeat remediation loops.

---

## 8) Workstreams

## WS-M4.5-A: Baseline Re-Freeze and Contradiction Scan

**Goal:** Freeze pass-5 SK-M4 evidence and identify remaining fixable contradictions.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-5 SK-M4 tuple and source evidence references. | New `reports/core_skeptic/SK_M4_5_BASELINE_REGISTER.md` | Baseline state and evidence map are reproducible. |
| A2 | Scan provenance health, register sync, and release gate-health dependency snapshot for semantic contradictions. | same | Contradiction list is explicit (empty or actionable). |
| A3 | Classify each contradiction as fixable SK-M4 defect vs non-fixable external constraint. | same | Blocker taxonomy is explicit and auditable. |

### Verification

```bash
python3 - <<'PY'
import json
h=json.load(open('core_status/core_audit/provenance_health_status.json'))
s=json.load(open('core_status/core_audit/provenance_register_sync_status.json'))
g=json.load(open('core_status/core_audit/release_gate_health_status.json'))
print(h.get('status'), h.get('reason_code'), h.get('m4_4_historical_lane'))
print(s.get('status'), s.get('drift_detected'), s.get('provenance_health_lane'))
print(g.get('results', {}).get('status'), g.get('results', {}).get('reason_code'))
PY
```

---

## WS-M4.5-B: Historical Residual and Recoverability Formalization

**Goal:** Make bounded historical confidence semantics explicit, deterministic, and anti-repeat.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add pass-5 lane semantics (`m4_5_historical_lane`, `m4_5_residual_reason`, `m4_5_reopen_conditions`) while preserving M4.4 compatibility. | provenance health builder + policy + checker | Deterministic SK-M4.5 lane is machine-enforced. |
| B2 | Add explicit mapping table from recoverability class to lane entitlement. | policy/docs | Residual classification is auditable and stable. |
| B3 | Require non-null residual reason for all non-aligned lanes. | checker/tests | Null residual semantics cannot pass CI/release checks. |

### Verification

```bash
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```

---

## WS-M4.5-C: Missing-Folio Non-Blocker Enforcement for SK-M4

**Goal:** Prevent repeated SK-M4 reopening from SK-H3-style missing-page objections.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add explicit SK-M4 missing-folio non-blocker criterion to core_skeptic playbook and SK-M4 policy where absent. | `planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md`, SK-M4 policy | Playbook/policy routing is unambiguous. |
| C2 | Add SK-M4 checker assertion: folio-based blocking requires objective provenance-contract linkage evidence. | checker + tests | Unsupported folio blockers fail closed. |
| C3 | Record non-fixable missing-folio blocker taxonomy in SK-M4 governance artifacts. | SK-M4 decision/status docs | Repeat-loop ambiguity is removed. |

### Verification

```bash
rg -n "SK-M4|folio|irrecoverable|non-block" planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode ci
```

---

## WS-M4.5-D: Freshness, Parity, and Coupling Hardening

**Goal:** Ensure SK-M4 cannot assert confidence from stale/mismatched artifacts.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Enforce freshness windows and reasoned stale-failure diagnostics across provenance health/sync artifacts. | SK-M4 policy/checker | Stale artifacts fail closed with actionable reason-codes. |
| D2 | Enforce strict parity for core_status/reason/lane/orphan counts across provenance artifacts. | checker/tests | Cross-artifact mismatches cannot ship silently. |
| D3 | Keep contract-coupling semantics coherent with release gate-health dependency snapshot. | builder + checker + tests | Coupling contradictions are machine-detectable. |

### Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
python3 scripts/core_audit/build_provenance_health_status.py
python3 scripts/core_audit/sync_provenance_register.py
python3 scripts/core_skeptic/check_provenance_uncertainty.py --mode release
```

---

## WS-M4.5-E: Claim-Boundary and Report Coherence

**Goal:** Prevent narrative overreach beyond bounded provenance entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Build SK-M4.5 claim-boundary register with lane-specific allowed/disallowed language. | New `reports/core_skeptic/SK_M4_5_CLAIM_BOUNDARY_REGISTER.md` | Claim scope is explicit and testable. |
| E2 | Synchronize SK-M4-facing governance/reports/registers to SK-M4.5 lane semantics. | README/results/governance/reports/core_skeptic surfaces | No deterministic certainty language in bounded/qualified lanes. |
| E3 | Add/extend marker checks for required bounded-language clauses. | checker/policy/tests | Missing boundary language fails closed. |

### Verification

```bash
rg -n "M4_5_|PROVENANCE_QUALIFIED|bounded|qualified|core_status/core_audit/provenance_health_status.json" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md \
  governance/PROVENANCE.md \
  governance/HISTORICAL_PROVENANCE_POLICY.md \
  reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md
```

---

## WS-M4.5-F: Pipeline/Gate Contract Parity

**Goal:** Keep SK-M4 independently auditable even while SK-C1 remains degraded.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Ensure CI, pre-release, and verify scripts enforce upgraded SK-M4.5 checks consistently. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | SK-M4 parity checks cannot be bypassed. |
| F2 | Ensure release gate-health dependency snapshot carries decisive SK-M4 lane/reason fields. | `scripts/core_audit/build_release_gate_health_status.py` | SK-M4 governance state is visible in gate snapshots. |
| F3 | Separate SK-M4 bounded historical residual from SK-C1 release-evidence failures in status reporting. | SK-M4 status docs | SK-M4 outcomes remain clear under SK-C1 degradation. |

### Verification

```bash
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
bash scripts/core_audit/pre_release_check.sh
python3 scripts/core_audit/build_release_gate_health_status.py
```

---

## WS-M4.5-G: Regression Locking and Governance Closeout

**Goal:** Produce a complete anti-repeat closeout package for pass 5.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-M4.5 regression tests for lane determinism, residual completeness, and missing-folio guard behavior. | SK-M4 tests + core_audit contract tests | Regression suite fails if pass-5 semantics drift. |
| G2 | Add decision record with fixable vs non-fixable blocker ledger. | New `reports/core_skeptic/SK_M4_5_DECISION_RECORD.md` | Blocker classification is explicit and stable. |
| G3 | Add execution status report template with command evidence matrix and blocker outcomes. | New `reports/core_skeptic/SKEPTIC_M4_5_EXECUTION_STATUS.md` | Full pass-5 traceability exists. |
| G4 | Link SK-M4.5 finding -> controls -> blockers -> reopen triggers in `AUDIT_LOG.md`. | `AUDIT_LOG.md` | Repeat-loop traceability is auditable. |

### Verification

```bash
python3 -m pytest -q \
  tests/core_skeptic/test_provenance_uncertainty_checker.py \
  tests/core_audit/test_sync_provenance_register.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_release_gate_health_status_builder.py
```

---

## 9) Execution Order

1. WS-M4.5-A Baseline + contradiction scan  
2. WS-M4.5-B Historical residual formalization  
3. WS-M4.5-C Missing-folio non-blocker enforcement  
4. WS-M4.5-D Freshness/parity/coupling hardening  
5. WS-M4.5-E Claim/report boundary synchronization  
6. WS-M4.5-F Pipeline/gate parity  
7. WS-M4.5-G Regression + governance closeout

Rationale:

- freeze truth and classify blockers first,
- then fix deterministic contract surfaces,
- then harden anti-repeat rules and gate parity,
- then close with tests and governance artifacts.

---

## 10) Decision Matrix for SK-M4.5

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Full provenance integrity and historical confidence align under canonical policy. | `M4_5_ALIGNED` | "Historical provenance confidence is aligned and operationally coherent." |
| Confidence remains qualified but synchronized/coupled with bounded residual. | `M4_5_QUALIFIED` | "Historical provenance confidence is qualified with explicit bounded uncertainty." |
| Historical irrecoverability is explicit, coherent, and reopenable. | `M4_5_BOUNDED` | "Historical provenance confidence remains bounded by irrecoverable source constraints." |
| Contract mismatch/parity/freshness/coherence failure. | `M4_5_BLOCKED` | "SK-M4 remains process-blocked pending contract repair." |
| Evidence incomplete for deterministic lane assignment. | `M4_5_INCONCLUSIVE` | "SK-M4.5 lane remains provisional pending complete evidence." |

---

## 11) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M4.5-A Baseline + Contradiction Scan | NOT STARTED | Codex | - | - | Pass-5 baseline freeze and contradiction classification pending. |
| WS-M4.5-B Historical Residual Formalization | NOT STARTED | Codex | - | - | M4.5 lane/residual/reopen contract hardening pending. |
| WS-M4.5-C Missing-Folio Non-Blocker Enforcement | NOT STARTED | Codex | - | - | SK-M4 folio-boundary controls pending. |
| WS-M4.5-D Freshness/Parity/Coupling Hardening | NOT STARTED | Codex | - | - | Cross-artifact parity/freshness lock pending. |
| WS-M4.5-E Claim/Report Boundary Sync | NOT STARTED | Codex | - | - | Lane-bound narrative synchronization pending. |
| WS-M4.5-F Pipeline/Gate Contract Parity | NOT STARTED | Codex | - | - | SK-M4 path parity under CI/release/repro pending. |
| WS-M4.5-G Regression + Governance Closeout | NOT STARTED | Codex | - | - | Tests and governance package pending. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 12) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Fifth pass repeats same bounded residual without clearer closure semantics. | High | High | Add explicit M4.5 lane + residual reason + reopen contract. |
| R2 | Missing-folio objections are misrouted to SK-M4 and reopen resolved work. | Medium | High | Playbook + checker criteria for SK-M4 non-blocking folio rule. |
| R3 | SK-C1 degradation obscures SK-M4 progress. | Medium | Medium | Keep SK-M4 checks independently visible and statused. |
| R4 | Report language overreaches bounded provenance entitlement. | Medium | High | Claim-boundary register + marker enforcement. |
| R5 | Provenance health and sync artifacts drift semantically while passing basic checks. | Medium | High | Fail-closed parity/freshness checks and regression locking. |

---

## 13) Deliverables

Required deliverables for SK-M4.5 execution pass:

1. `reports/core_skeptic/SK_M4_5_BASELINE_REGISTER.md`
2. `reports/core_skeptic/SK_M4_5_CLAIM_BOUNDARY_REGISTER.md`
3. `reports/core_skeptic/SK_M4_5_DECISION_RECORD.md`
4. `reports/core_skeptic/SKEPTIC_M4_5_EXECUTION_STATUS.md`
5. Updated SK-M4 producer/checker/policy/gate/report surfaces with deterministic pass-5 closure semantics.
6. `AUDIT_LOG.md` linkage of SK-M4 pass-5 finding -> blocker class -> closure lane -> reopen triggers.

---

## 14) Blocker Taxonomy (Execution-Time Required)

During execution, every open item must be explicitly classified as one of:

1. **Fixable SK-M4 defect:** can be remediated by policy/checker/artifact/gate/report changes.
2. **Non-fixable bounded SK-M4 residual:** objective historical irrecoverability persists under current source scope.
3. **Out-of-scope external blocker:** belongs to another core_skeptic class (for example SK-C1 or SK-H3), documented with explicit routing and no SK-M4 misclassification.

No unresolved item may remain unclassified.

---

## 15) Closure Criteria

SK-M4 (pass-5 scope) is considered closed for this cycle only if one is true:

1. `M4_5_ALIGNED`,
2. `M4_5_QUALIFIED`,
3. `M4_5_BOUNDED` with complete residual/reopen governance and explicit non-overreach.

If none is satisfied, SK-M4 remains open (`M4_5_BLOCKED` or `M4_5_INCONCLUSIVE`).
