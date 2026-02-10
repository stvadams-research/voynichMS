# Execution Plan: Skeptic Comparative Uncertainty Closure Hardening (SK-M2.5)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`  
**Finding Target:** `SK-M2` (Medium, pass-5 residual)  
**Plan Date:** 2026-02-10  
**Attempt Context:** Fifth targeted remediation attempt for SK-M2  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Address all SK-M2 issues that are technically fixable in a fifth pass, while preventing another repeat cycle where the same bounded uncertainty is reopened without new evidence.

This pass has two mandatory outcomes:

1. fix any remaining SK-M2 contract/coherence defects (schema, checker, report, gate, policy parity),
2. explicitly classify non-fixable constraints and keep them from being misfiled as SK-M2 blockers.

---

## 2) Pass-5 SK-M2 Problem Statement

From `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`:

- `SK-M2 (Medium): Comparative uncertainty remains bounded and explicitly inconclusive.`
- Evidence references in the assessment:
  - `results/human/phase_7c_uncertainty.json:37`
  - `results/human/phase_7c_uncertainty.json:38`
  - `results/human/phase_7c_uncertainty.json:288`
  - `results/human/phase_7c_uncertainty.json:294`
  - `results/human/phase_7c_uncertainty.json:309`
  - `results/human/phase_7c_uncertainty.json:310`
  - `results/human/phase_7c_uncertainty.json:323`

Current canonical SK-M2 snapshot (latest artifact state):

- `status=INCONCLUSIVE_UNCERTAINTY`
- `reason_code=TOP2_IDENTITY_FLIP_DOMINANT`
- `nearest_neighbor=Lullian Wheels`
- `nearest_neighbor_stability=0.4565`
- `jackknife_nearest_neighbor_stability=0.8333`
- `rank_stability=0.4565`
- `m2_4_closure_lane=M2_4_BOUNDED`
- `top2_gap.ci95_lower=0.0263`
- `m2_4_residual_reason` currently unresolved/empty (`None`) and should be treated as a contract defect if reproducible.

Residual skeptic leverage:

- comparative direction exists, but confidence entitlement is still instability-bounded.

---

## 3) Fifth-Attempt Retrospective (Why SK-M2 Keeps Reappearing)

### 3.1 M2.4 governance improved structure, not entitlement class

Pass-4 introduced `M2_4_BOUNDED`, diagnostic blocks, and checker hardening, but did not cross the stability thresholds needed for stronger comparative closure.

### 3.2 Residual fragility remains structurally stable

Top-2 identity volatility and rank instability continue across registered perturbation behavior. This points to persistent comparative uncertainty rather than a single-run anomaly.

### 3.3 Contract drift risk still exists in residual semantics

Even with lane fields present, missing or weak residual-reason semantics (for example null reason fields) can reopen the issue in governance despite unchanged quantitative evidence.

### 3.4 SK-C1 gate degradation can obscure SK-M2 progress

Release sensitivity artifact gaps remain SK-C1 blockers; SK-M2 must remain independently auditable so its status does not get conflated with SK-C1 operational blockers.

---

## 4) Missing-Folio Non-Blocker Boundary for SK-M2 (Required)

This pass explicitly enforces the following:

1. Approved irrecoverable missing folios are, by default, an SK-H3 data-availability constraint and **not** an SK-M2 comparative-uncertainty blocker.
2. SK-M2 may only be blocked by folio/page loss if SK-M2 artifacts explicitly show comparative-input validity failure caused by missing source pages.
3. Repeating missing-folio objections without SK-M2-specific comparative validity impact is not a new SK-M2 blocker.
4. Any unresolved missing-folio argument must be routed to SK-H3 terminal-qualified governance unless objective SK-M2 causal linkage is demonstrated.

This is not a waiver:

- all fixable SK-M2 defects must still be remediated.

---

## 5) Scope and Non-Goals

## In Scope

- SK-M2 comparative uncertainty artifact, policy, checker, gate, and report coherence.
- Deterministic closure semantics for pass-5 SK-M2 governance.
- Explicit anti-repeat reopen triggers for unchanged bounded evidence.
- Explicit non-fixable vs fixable blocker taxonomy.

## Out of Scope

- SK-C1 release sensitivity artifact production.
- SK-H3 full-data comparability remediation.
- SK-H1/H2/M1/M3/M4 remediation except dependency references.
- New semantic decipherment claims.

---

## 6) Deterministic SK-M2.5 Closure Framework

SK-M2.5 preserves M2.4 compatibility while adding deterministic pass-5 closure classes.

## Lane A: `M2_5_ALIGNED`

All true:

- comparative stability thresholds are met at confirmed class,
- rank and top-2 diagnostics are robust,
- claim/report/gate surfaces are fully aligned.

## Lane B: `M2_5_QUALIFIED`

All true:

- directional comparative signal is stable at qualified class,
- uncertainty remains bounded but not collapse-prone,
- claims remain strictly qualified.

## Lane C: `M2_5_BOUNDED`

All true:

- status remains inconclusive/uncertainty-bounded,
- dominant fragility signal is explicit and reproducible,
- residual reason and reopen triggers are complete and machine-checkable,
- narrative is bounded and non-overreaching.

## Lane D: `M2_5_BLOCKED`

Any true:

- missing required uncertainty contract fields,
- policy/checker/report/gate incoherence,
- unresolved parity or freshness failures across canonical surfaces.

## Lane E: `M2_5_INCONCLUSIVE`

Evidence is incomplete to classify the lane deterministically.

---

## 7) Success Criteria (Exit Conditions)

SK-M2.5 is complete only when all are true:

1. lane decision is deterministic (`M2_5_ALIGNED`, `M2_5_QUALIFIED`, or `M2_5_BOUNDED`),
2. fixable SK-M2 contract defects are remediated,
3. missing-folio objections are correctly non-blocking for SK-M2 unless objective causal linkage is shown,
4. residual reason + reopen triggers are explicit and non-null,
5. claim/report/gate surfaces are coherent with lane entitlement.

---

## 8) Workstreams

## WS-M2.5-A: Baseline Re-Freeze and Contradiction Scan

**Goal:** Freeze pass-5 SK-M2 evidence and identify any remaining fixable contradictions.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-5 SK-M2 tuple from canonical uncertainty artifact. | New `reports/skeptic/SK_M2_5_BASELINE_REGISTER.md` | Baseline has reproducible state tuple and provenance metadata. |
| A2 | Scan parity across uncertainty artifact, checker expectations, and report claims. | same | Contradiction list is explicit (empty or actionable). |
| A3 | Classify each contradiction as fixable contract defect vs non-fixable external constraint. | same | Blocker taxonomy is explicit and auditable. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('results/human/phase_7c_uncertainty.json')).get('results', {})
print(r.get('status'), r.get('reason_code'), r.get('m2_4_closure_lane'))
print(r.get('nearest_neighbor_stability'), r.get('jackknife_nearest_neighbor_stability'), r.get('rank_stability'))
print((r.get('top2_gap') or {}).get('ci95_lower'))
print(r.get('m2_4_residual_reason'), r.get('m2_4_reopen_triggers'))
PY
```

---

## WS-M2.5-B: Residual-Reason Contract Completion

**Goal:** Eliminate null/ambiguous residual reason semantics and harden reopen logic.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Enforce non-null residual reason for bounded/inconclusive SK-M2 states. | producer + policy + checker | Null residual reason cannot pass CI/release checks. |
| B2 | Normalize reopen trigger schema and required trigger classes. | producer + checker + tests | Reopen triggers are deterministic and complete. |
| B3 | Add explicit lane-to-residual mapping table in policy/docs. | policy/docs | Lane semantics are auditable and stable. |

### Verification

```bash
python3 scripts/skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/skeptic/check_comparative_uncertainty.py --mode release
```

---

## WS-M2.5-C: Fragility Signal Decomposition Hardening

**Goal:** Make `TOP2_IDENTITY_FLIP_DOMINANT` diagnosis maximally explanatory and repeatable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Validate dominant fragility signal derivation against raw metrics. | `src/comparative/mapping.py` + tests | Dominant-signal mapping is deterministic and justified. |
| C2 | Add additional diagnostics if needed (identity flip regime segmentation, entropy/margin co-movement summaries). | same | Artifact explains why closure class is bounded. |
| C3 | Fail closed when fragility diagnostics are incomplete or incompatible with reason code. | checker/tests | Incoherent reason/diagnostics cannot ship. |

### Verification

```bash
python3 scripts/comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 - <<'PY'
import json
r=json.load(open('results/human/phase_7c_uncertainty.json')).get('results', {})
print(r.get('reason_code'))
print(r.get('fragility_diagnostics'))
PY
```

---

## WS-M2.5-D: Matrix Robustness and Testability Path

**Goal:** Preserve release-depth rigor while ensuring repeatable, lower-cost testability.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Re-validate registered matrix definitions and profile gating (`smoke`, `standard`, `release-depth`). | policy + runner | Matrix is pre-registered and anti-tuning safe. |
| D2 | Require profile-tagged evidence traces in SK-M2 outputs. | runner + artifact schema | Every result is attributable to a registered profile. |
| D3 | Add explicit matrix consistency checks for lane drift and reason drift across profiles. | checker/tests | Lane/reason drift is visible and fail-closed where required. |

### Verification

```bash
python3 scripts/comparative/run_proximity_uncertainty.py --profile smoke --seed 42
python3 scripts/comparative/run_proximity_uncertainty.py --profile standard --seed 42
python3 scripts/comparative/run_proximity_uncertainty.py --profile release-depth --seed 42
```

---

## WS-M2.5-E: Missing-Folio Non-Blocker Enforcement

**Goal:** Ensure SK-M2 cannot be repeatedly blocked by SK-H3-style missing-page objections.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add explicit SK-M2 missing-folio non-blocker criterion to skeptic playbook. | `planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md` | Playbook unambiguously routes generic missing-folio objections away from SK-M2. |
| E2 | Add SK-M2 checker-side assertion for data-availability objections (only block on objective comparative validity linkage). | SK-M2 checker/policy/tests | Unsupported missing-folio blocking arguments are rejected. |
| E3 | Record non-fixable blocker taxonomy in SK-M2 governance artifacts. | SK-M2 decision/status docs | Repeat-loop ambiguity is removed. |

### Verification

```bash
rg -n "missing folio|approved-lost|SK-M2|non-blocking|data-availability" planning/skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md
```

---

## WS-M2.5-F: Claim-Boundary and Report Coherence

**Goal:** Prevent narrative overreach beyond uncertainty entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Build SK-M2.5 claim-boundary register with lane-specific allowed/disallowed language. | New `reports/skeptic/SK_M2_5_CLAIM_BOUNDARY_REGISTER.md` | Claim scope is explicit and testable. |
| F2 | Synchronize comparative reports and summaries to SK-M2.5 lane semantics. | comparative reports/docs | No conclusive language for bounded/inconclusive lane. |
| F3 | Add/extend marker checks for required uncertainty-qualified phrasing. | checker/policy/tests | Missing boundary language fails closed. |

### Verification

```bash
rg -n "INCONCLUSIVE_UNCERTAINTY|M2_4_BOUNDED|M2_5_|provisional|bounded|non-conclusive|allowed_claim" \
  reports/comparative docs
```

---

## WS-M2.5-G: Pipeline/Gate Contract Parity

**Goal:** Keep SK-M2 status independently auditable even when SK-C1 is degraded.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Ensure CI, pre-release, and verify scripts enforce upgraded SK-M2 contract checks. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | SK-M2 parity checks cannot be bypassed. |
| G2 | Ensure gate-health dependency snapshot carries decisive SK-M2 lane/reason fields. | `scripts/audit/build_release_gate_health_status.py` | Gate snapshot includes SK-M2 governance state. |
| G3 | Separate SK-M2 verdict from SK-C1 operational failure in execution status reporting. | status docs | SK-M2 outcomes remain clear under SK-C1 degradation. |

### Verification

```bash
bash scripts/ci_check.sh
bash scripts/verify_reproduction.sh
bash scripts/audit/pre_release_check.sh
python3 scripts/audit/build_release_gate_health_status.py
```

---

## WS-M2.5-H: Regression Locking and Governance Closeout

**Goal:** Produce a complete anti-repeat closeout package for pass 5.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Add SK-M2.5 regression tests for residual reason completeness and lane determinism. | SK-M2 tests + audit contract tests | Regression suite fails if pass-5 semantics drift. |
| H2 | Add decision record with fixable vs non-fixable blocker ledger. | New `reports/skeptic/SK_M2_5_DECISION_RECORD.md` | Blocker classification is explicit and stable. |
| H3 | Add execution status report with command evidence and outcomes. | New `reports/skeptic/SKEPTIC_M2_5_EXECUTION_STATUS.md` | Full pass-5 traceability exists. |
| H4 | Link SK-M2.5 finding -> controls -> blockers -> reopen triggers in audit log. | `AUDIT_LOG.md` | Repeat-loop traceability is auditable. |

### Verification

```bash
python3 -m pytest -q \
  tests/comparative/test_mapping_uncertainty.py \
  tests/skeptic/test_comparative_uncertainty_checker.py \
  tests/audit/test_ci_check_contract.py \
  tests/audit/test_pre_release_contract.py \
  tests/audit/test_verify_reproduction_contract.py
```

---

## 9) Execution Order

1. WS-M2.5-A Baseline + contradiction scan  
2. WS-M2.5-B Residual-reason contract completion  
3. WS-M2.5-C Fragility decomposition hardening  
4. WS-M2.5-D Matrix robustness + testability  
5. WS-M2.5-E Missing-folio non-blocker enforcement  
6. WS-M2.5-F Claim/report boundary sync  
7. WS-M2.5-G Pipeline/gate parity  
8. WS-M2.5-H Regression + governance closeout

Rationale:

- first freeze truth and defect taxonomy,
- then fix core uncertainty contract defects,
- then enforce anti-repeat boundaries and pipeline parity,
- then close with tests and governance evidence.

---

## 10) Decision Matrix for SK-M2.5

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Confirmed stability thresholds pass and parity is coherent. | `M2_5_ALIGNED` | "Comparative direction is robustly supported under registered uncertainty controls." |
| Qualified thresholds pass with bounded caveats. | `M2_5_QUALIFIED` | "Comparative signal is directionally supported with explicit uncertainty qualifications." |
| Inconclusive status with complete bounded diagnostics and coherent claims. | `M2_5_BOUNDED` | "Comparative claim remains bounded and non-conclusive due registered instability diagnostics." |
| Contract mismatch/parity failure. | `M2_5_BLOCKED` | "SK-M2 remains process-blocked pending contract repair." |
| Evidence incomplete. | `M2_5_INCONCLUSIVE` | "SK-M2.5 lane provisional pending complete evidence." |

---

## 11) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M2.5-A Baseline + Contradiction Scan | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline freeze and blocker taxonomy delivered in `reports/skeptic/SK_M2_5_BASELINE_REGISTER.md`. |
| WS-M2.5-B Residual-Reason Contract Completion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Non-null residual semantics enforced for M2.4/M2.5 in producer, policy, checker, and gate scripts. |
| WS-M2.5-C Fragility Decomposition Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Dominant fragility signal coherence preserved and checker-enforced against reason-code drift. |
| WS-M2.5-D Matrix Robustness + Testability | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Profile-tagged uncertainty output (`parameters.run_profile`) added and enforced by checker parity checks. |
| WS-M2.5-E Missing-Folio Non-Blocker Enforcement | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added objective-linkage guardrails to prevent unsupported folio-based SK-M2 blocking. |
| WS-M2.5-F Claim/Report Boundary Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Comparative reports/docs synchronized to `M2_5_BOUNDED` entitlement language. |
| WS-M2.5-G Pipeline/Gate Contract Parity | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | CI/pre-release/verify and release gate-health builder now enforce and project SK-M2.5 fields. |
| WS-M2.5-H Regression + Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Targeted pytest suite passed; decision/status artifacts and audit-log linkage produced. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 12) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Fifth pass still repeats same bounded residual without clearer closure semantics. | High | High | Add explicit M2.5 lane + residual reason + reopen contract. |
| R2 | Missing-folio objections get incorrectly mapped to SK-M2 and reopen resolved work. | Medium | High | Playbook + checker criteria for SK-M2 non-blocking folio rule. |
| R3 | SK-C1 gate degradation obscures SK-M2 progress in operations. | Medium | Medium | Keep SK-M2 checks independently visible and statused. |
| R4 | Report language overreaches beyond uncertainty entitlement. | Medium | High | Claim-boundary register + marker enforcement. |
| R5 | Diagnostic reason code and fragility block drift out of sync. | Medium | High | Checker fail-closed on reason/diagnostic incoherence. |

---

## 13) Deliverables

Required deliverables for SK-M2.5 execution pass:

1. `reports/skeptic/SK_M2_5_BASELINE_REGISTER.md`
2. `reports/skeptic/SK_M2_5_CLAIM_BOUNDARY_REGISTER.md`
3. `reports/skeptic/SK_M2_5_DECISION_RECORD.md`
4. `reports/skeptic/SKEPTIC_M2_5_EXECUTION_STATUS.md`
5. Updated SK-M2 producer/checker/policy/gate/report surfaces with deterministic pass-5 closure semantics
6. `AUDIT_LOG.md` linkage of SK-M2 pass-5 finding -> blocker class -> closure lane -> reopen triggers

---

## 14) Closure Criteria

SK-M2 (pass-5 scope) is considered closed for this cycle only if one is true:

1. `M2_5_ALIGNED`,
2. `M2_5_QUALIFIED`,
3. `M2_5_BOUNDED` with complete residual/reopen governance and explicit non-overreach.

If none is satisfied, SK-M2 remains open (`M2_5_BLOCKED` or `M2_5_INCONCLUSIVE`).
