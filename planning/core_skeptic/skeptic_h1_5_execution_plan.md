# Execution Plan: Skeptic Multimodal Robustness Closure (SK-H1.5)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`  
**Finding Target:** `SK-H1` (High, pass-5 residual)  
**Plan Date:** 2026-02-10  
**Attempt Context:** Fifth targeted remediation attempt for the SK-H1 class  
**Execution Policy:** Plan-only in this revision. Do not execute changes from this document yet.

---

## 1) Objective

Resolve pass-5 `SK-H1` as far as feasible by addressing the remaining residual directly:

- canonical multimodal decision is conclusive,
- but robustness remains mixed across registered lanes,
- so closure is still `H1_4_QUALIFIED` rather than aligned.

This plan is designed to prevent another “same issue, new pass” cycle by:

1. proving whether current robustness closure is feasible under existing matrix rules,
2. fixing any structural infeasibility in the robustness contract,
3. preserving strict claim boundaries if full alignment is still not supportable.

---

## 2) Pass-5 SK-H1 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_5.md`:

- `SK-H1 (High, narrowed): Canonical multimodal decision is conclusive, but registered-lane robustness remains mixed.`

Current canonical artifact evidence:

- `results/phase5_mechanism/anchor_coupling_confirmatory.json`
  - `status=CONCLUSIVE_NO_COUPLING`
  - `status_reason=adequacy_and_inference_support_no_coupling`
  - `h1_4_closure_lane=H1_4_QUALIFIED`
  - `h1_4_residual_reason=registered_lane_fragility`
  - `robustness.robustness_class=MIXED`
  - `robustness.agreement_ratio=0.333333`

Operational nuance:

- release-mode multimodal checker passes:
  - `python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release` -> PASS
- therefore, SK-H1 residual is not a gate wiring failure; it is a robustness-governance/evidence sufficiency issue.

---

## 3) Fifth-Attempt Retrospective (Core Repeat Pattern)

### 3.1 Prior attempts improved governance, not closure feasibility

H1.2/H1.3/H1.4 hardened:

- status taxonomy,
- lane semantics,
- checker and gate parity,
- claim-boundary language.

But pass-5 still reports the same substantive residual: mixed robustness.

### 3.2 Likely structural infeasibility in “aligned robustness”

Current registered matrix includes:

- `publication-default` (conclusive lane),
- `stability-probe-seed-2718` (inferential ambiguity lane),
- `adequacy-floor` (intentionally underpowered lane).

Current robust-class policy requires:

- full conclusive agreement ratio,
- zero ambiguity lanes,
- zero underpowered lanes.

If an intentionally underpowered lane is always included in robust-class scoring, `ROBUST` can become unreachable by construction, causing endless qualified outcomes.

### 3.3 Diagnostic lanes and entitlement lanes are not yet cleanly separated

Stress/diagnostic lanes are useful for falsification and guardrails, but should not necessarily be scored the same as entitlement lanes for publication closure.

### 3.4 Reopen criteria are present but may be operationally unattainable

Current reopen trigger:

- “registered lane matrix reaches robust class without inferential ambiguity”

If the matrix definition itself encodes inevitable ambiguity/underpower in included lanes, this trigger cannot fire without framework redesign.

---

## 4) Missing-Folio Non-Blocking Boundary (Required)

This plan explicitly prevents false SK-H1 blockage from irrecoverable-source constraints:

1. Missing folio pages are an SK-H3 external-constraint class by default.
2. SK-H1 is blocked by missing folios only if multimodal artifact status is explicitly data-geometry blocked (`BLOCKED_DATA_GEOMETRY`) and traceably linked to approved-lost source constraints.
3. If canonical multimodal status remains conclusive on policy-accepted available data, missing-folio objections cannot reopen SK-H1 by themselves.

Reference policy surface:

- `planning/core_skeptic/ADVERSARIAL_SKEPTIC_PLAYBOOK.md`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json`
- `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`

---

## 5) Scope and Non-Goals

## In Scope

- SK-H1 robustness residual only (multimodal coupling closure semantics),
- lane-feasibility proof for current robustness framework,
- matrix contract redesign if current closure criterion is structurally unreachable,
- checker/gate/report synchronization for any H1.5 lane changes,
- explicit anti-repeat governance artifacts.

## Out of Scope

- SK-C1 release sensitivity artifact production,
- SK-H3 full-data comparability remediation,
- SK-H2/M1 language entitlement changes beyond H1 dependency references,
- new external corpus acquisition.

---

## 6) Deterministic H1.5 Closure Framework

H1.5 defines explicit closure classes to avoid repeated ambiguity:

## Lane A: `H1_5_ALIGNED`

All true:

- canonical lane is conclusive and coherent,
- entitlement lane set (publication-relevant lanes) is robust,
- no unresolved inferential ambiguity in entitlement lanes,
- claim/report surfaces are aligned to aligned entitlement.

## Lane B: `H1_5_BOUNDED`

All true:

- entitlement lanes are aligned or qualified within configured thresholds,
- diagnostic/stress lanes remain non-conclusive by design,
- diagnostic non-conclusive outcomes are explicitly bounded and non-entitlement,
- claims remain constrained to bounded lane semantics.

## Lane C: `H1_5_QUALIFIED`

All true:

- canonical lane is conclusive,
- entitlement lanes still mixed/fragile after feasible remediation,
- residual is explicitly documented with objective reopen triggers.

## Lane D: `H1_5_BLOCKED`

Any true:

- multimodal core_status/robustness/checker contract incoherence,
- closure criterion remains structurally unreachable without unresolved policy contradiction,
- missing required artifacts or failed lane provenance parity.

## Lane E: `H1_5_INCONCLUSIVE`

Evidence insufficient to classify due incomplete runs or missing diagnostics.

---

## 7) Success Criteria (Exit Conditions)

SK-H1.5 execution is complete only when all are satisfied:

1. H1 feasibility phase2_analysis proves whether aligned closure is reachable under current matrix.
2. If unreachable, matrix/robustness contract is redesigned with explicit entitlement-vs-diagnostic lane split.
3. Multimodal artifact emits lane class and residual semantics consistent with policy/checkers.
4. Checker/gate/report boundaries are synchronized to H1.5 lane semantics.
5. Missing-folio objections are explicitly classified as non-blocking for SK-H1 unless direct data-geometry block criteria are met.
6. Regression tests lock the pass-5 failure mode and prevent semantic drift.
7. Governance artifacts capture decision rationale and reopen triggers.

---

## 8) Workstreams

## WS-H1.5-A: Baseline Freeze and Feasibility Proof

**Goal:** Freeze pass-5 SK-H1 state and determine whether current robust closure is mathematically/policy reachable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze canonical SK-H1 pass-5 tuple (status, lane, residual, robustness counts). | New `reports/core_skeptic/SK_H1_5_BASELINE_REGISTER.md` | Baseline frozen with run_id/timestamp and residual vectors. |
| A2 | Produce feasibility proof for current robust criteria against current lane registry. | New `reports/core_skeptic/SK_H1_5_FEASIBILITY_REGISTER.md` | Explicit `reachable` vs `unreachable` verdict with formal rationale. |
| A3 | Enumerate all residual vectors (seed ambiguity, adequacy-floor underpower, method variance). | same | Residual vectors mapped to remediation tasks. |
| A4 | Define objective blockers vs bounded residuals vs non-blockers. | same | Repeat reopen loops become auditable. |

### Verification

```bash
python3 - <<'PY'
import json
p='results/phase5_mechanism/anchor_coupling_confirmatory.json'
d=json.load(open(p))
r=d.get('results',{})
rob=r.get('robustness') or {}
print(r.get('status'), r.get('h1_4_closure_lane'), r.get('h1_4_residual_reason'))
print(rob.get('robustness_class'), rob.get('agreement_ratio'))
print(rob.get('lane_outcomes_considered'))
PY
```

---

## WS-H1.5-B: Lane Taxonomy and Matrix Contract Redesign

**Goal:** Eliminate structurally unreachable closure logic by separating entitlement and diagnostic lanes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Introduce lane classes: `entitlement`, `diagnostic`, `stress`. | `configs/core_skeptic/sk_h1_multimodal_policy.json` | Lane registry explicitly typed and versioned. |
| B2 | Define robust scoring to use entitlement lanes only; keep diagnostic lanes as bounded monitoring signals. | same + status policy | Robust closure becomes reachable when evidence warrants it. |
| B3 | Preserve anti-tuning constraints (no post-hoc publication lane switching). | same + governance register | Lane selection remains policy-pinned. |
| B4 | Add compatibility mapping for existing H1.4 lane semantics to avoid silent breakage. | policy + checker notes | Existing artifacts remain interpretable. |

### Verification

```bash
python3 - <<'PY'
import json
p='configs/core_skeptic/sk_h1_multimodal_policy.json'
d=json.load(open(p))
rm=d.get('robustness_matrix') or {}
print(rm.get('matrix_id'), rm.get('version'))
print(rm.get('publication_lane_id'))
print(rm.get('lane_registry'))
PY
```

---

## WS-H1.5-C: Robustness Evidence Expansion (Feasible, Non-Tuned)

**Goal:** Improve evidentiary strength across entitlement lanes without retrospective tuning.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define pre-registered seed band for entitlement lanes (for example 5-9 seeds) with fixed cohort size. | policy + execution status | Entitlement stability no longer hinges on one alternate seed. |
| C2 | Add method-variance entitlement lane(s) where feasible with fixed anchor methods. | policy + run outputs | Robustness covers method sensitivity, not only seed sensitivity. |
| C3 | Keep adequacy-floor as diagnostic lane only; no longer counted toward entitlement robust closure. | policy + checker | Underpowered lane remains informative but non-entitlement. |
| C4 | Add deterministic minimum evidence volume for declaring `H1_5_ALIGNED`. | status policy | Aligned class cannot be declared from sparse lane evidence. |

### Verification

```bash
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py --seed 42 --max-lines-per-cohort 1600
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py --seed 2718 --max-lines-per-cohort 1600
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py --seed 31415 --max-lines-per-cohort 1600
```

---

## WS-H1.5-D: Producer/Artifact Schema Hardening

**Goal:** Emit machine-checkable H1.5 semantics and lane partition details.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Add explicit H1.5 lane field (`h1_5_closure_lane`) and residual reason. | `src/phase5_mechanism/anchor_coupling.py`, `scripts/phase5_mechanism/run_5i_anchor_coupling.py` | H1.5 class is emitted deterministically. |
| D2 | Emit entitlement-vs-diagnostic lane outcomes separately. | artifact robustness block | Reviewer can distinguish closure lanes from stress lanes. |
| D3 | Emit feasibility metadata (`robust_closure_reachable`, `reason`). | artifact + register | “Impossible by construction” can be proven, not guessed. |
| D4 | Preserve backward-compatible H1.4 fields during transition. | artifact schema | Existing checkers/reports do not silently fail. |

### Verification

```bash
python3 - <<'PY'
import json
p='results/phase5_mechanism/anchor_coupling_confirmatory.json'
r=json.load(open(p)).get('results',{})
print(r.get('h1_4_closure_lane'), r.get('h1_5_closure_lane'))
rob=r.get('robustness') or {}
print(rob.get('entitlement_lane_outcomes'))
print(rob.get('diagnostic_lane_outcomes'))
PY
```

---

## WS-H1.5-E: Checker and Policy Semantic Parity

**Goal:** Enforce H1.5 semantics consistently in release/CI checker paths.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Extend H1 status policy for H1.5 lane classes and entitlement lane rules. | `configs/core_skeptic/sk_h1_multimodal_status_policy.json` | Lane mapping is explicit and machine-enforced. |
| E2 | Update multimodal checker for H1.5 contracts. | `scripts/core_skeptic/check_multimodal_coupling.py` | Checker rejects inconsistent entitlement/diagnostic semantics. |
| E3 | Add explicit “non-blocking H3 irrecoverable-source” guard in SK-H1 checker path. | checker + policy | Missing folio objections cannot silently block H1. |
| E4 | Ensure H1 checker remains independently inspectable when SK-C1 gate is degraded. | checker output + gate-health snapshot | H1 residual remains diagnosable under partial gate failure. |

### Verification

```bash
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode ci
python3 scripts/core_skeptic/check_multimodal_coupling.py --mode release
```

---

## WS-H1.5-F: Gate/Health/Report Synchronization

**Goal:** Keep gate-health and report language synchronized to H1.5 lane entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add H1.5 lane and feasibility fields to gate-health dependency snapshot. | `scripts/core_audit/build_release_gate_health_status.py` | Operational status surfaces H1.5 class deterministically. |
| F2 | Update claim-boundary register for H1.5 lane classes. | New `reports/core_skeptic/SK_H1_5_CLAIM_BOUNDARY_REGISTER.md` | Overreach detection remains explicit. |
| F3 | Update Phase 5/7 report wording for new lane semantics. | `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md`, `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md`, `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md`, `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md`, `reports/phase7_human/PHASE_7B_RESULTS.md` | Narrative entitlement matches machine lane state. |

### Verification

```bash
python3 scripts/core_audit/build_release_gate_health_status.py
rg -n "H1_5_|robustness|qualified|bounded|status-gated" \
  results/reports/phase5_mechanism/PHASE_5H_RESULTS.md \
  results/reports/phase5_mechanism/PHASE_5I_RESULTS.md \
  results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md \
  reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md \
  reports/phase7_human/PHASE_7B_RESULTS.md
```

---

## WS-H1.5-G: Regression Locking and Anti-Repeat Tests

**Goal:** Prevent a sixth recurrence of identical SK-H1 residual classification ambiguity.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add tests proving robust closure feasibility classification behavior. | `tests/phase5_mechanism/test_anchor_coupling.py`, `tests/phase5_mechanism/test_anchor_coupling_contract.py` | “Unreachable by construction” is test-detectable. |
| G2 | Add checker tests for entitlement-vs-diagnostic lane separation. | `tests/core_skeptic/test_multimodal_coupling_checker.py` | Misclassified diagnostic lanes fail. |
| G3 | Add contract tests for H1.5 markers in CI/pre-release/verify scripts and gate-health builder. | `tests/core_audit/test_ci_check_contract.py`, `tests/core_audit/test_pre_release_contract.py`, `tests/core_audit/test_verify_reproduction_contract.py`, `tests/core_audit/test_release_gate_health_status_builder.py` | Gate/report drift blocked in CI. |
| G4 | Add claim-boundary tests for H1.5 lane wording constraints. | `tests/phase7_human/test_phase7_claim_guardrails.py` | Over-claim patterns fail closed. |

### Verification

```bash
python3 -m pytest -q \
  tests/phase5_mechanism/test_anchor_coupling.py \
  tests/phase5_mechanism/test_anchor_coupling_contract.py \
  tests/core_skeptic/test_multimodal_coupling_checker.py \
  tests/phase7_human/test_phase7_claim_guardrails.py \
  tests/core_audit/test_ci_check_contract.py \
  tests/core_audit/test_pre_release_contract.py \
  tests/core_audit/test_verify_reproduction_contract.py \
  tests/core_audit/test_release_gate_health_status_builder.py
```

---

## WS-H1.5-H: Governance Closeout and Blocker Register

**Goal:** Produce explicit closure rationale and blocker transparency.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Create H1.5 decision record with final lane assignment and rationale. | New `reports/core_skeptic/SK_H1_5_DECISION_RECORD.md` | Final disposition is explicit and auditable. |
| H2 | Create H1.5 execution status report for implementation pass. | New `reports/core_skeptic/SKEPTIC_H1_5_EXECUTION_STATUS.md` | Command evidence and outcomes are traceable. |
| H3 | Add explicit blocker register distinguishing fixable vs non-fixable constraints. | same + `AUDIT_LOG.md` | Team stops retrying non-fixable paths blindly. |
| H4 | Link finding -> controls -> lane decision -> reopen triggers in core_audit log. | `AUDIT_LOG.md` | Anti-repeat traceability is complete. |

### Verification

```bash
rg -n "SK-H1.5|H1_5_|reopen|blocker|bounded|entitlement" \
  reports/core_skeptic \
  AUDIT_LOG.md \
  planning/core_skeptic/SKEPTIC_H1_5_EXECUTION_PLAN.md
```

---

## 9) Execution Order

1. WS-H1.5-A Baseline/Feasibility
2. WS-H1.5-B Lane Taxonomy Redesign
3. WS-H1.5-C Evidence Expansion
4. WS-H1.5-D Producer/Artifact Hardening
5. WS-H1.5-E Checker/Policy Parity
6. WS-H1.5-F Gate/Report Synchronization
7. WS-H1.5-G Regression Locking
8. WS-H1.5-H Governance Closeout

Rationale:

- prove feasibility before coding around symptoms,
- separate entitlement and diagnostic semantics before rerunning robustness judgments,
- lock tests and governance at the end to prevent repeat reopen cycles.

---

## 10) Decision Matrix for SK-H1.5

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Entitlement lanes robust and coherent; claims synchronized. | `H1_5_ALIGNED` | "Multimodal robustness supports aligned no-coupling closure within framework scope." |
| Entitlement lanes coherent; diagnostic lanes remain non-conclusive by design and bounded. | `H1_5_BOUNDED` | "Core multimodal conclusion is bounded and policy-qualified; stress lanes remain monitor signals." |
| Canonical lane conclusive but entitlement robustness remains mixed/fragile. | `H1_5_QUALIFIED` | "Multimodal conclusion remains qualified due unresolved entitlement-lane fragility." |
| Policy/artifact/checker incoherence or unresolved feasibility contradiction. | `H1_5_BLOCKED` | "SK-H1 remains blocked by robustness contract inconsistency." |
| Evidence incomplete for deterministic classification. | `H1_5_INCONCLUSIVE` | "SK-H1.5 remains provisional pending complete evidence." |

---

## 11) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H1.5-A Baseline/Feasibility | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline and feasibility registers emitted with explicit reachability verdict. |
| WS-H1.5-B Lane Taxonomy Redesign | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Entitlement/diagnostic/stress lane split codified in policy and producer schema. |
| WS-H1.5-C Evidence Expansion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Canonical lane rerun completed; bounded diagnostic evidence retained without post-hoc tuning. |
| WS-H1.5-D Producer/Artifact Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | H1.5 fields and feasibility metadata emitted with backward-compatible H1.4 fields. |
| WS-H1.5-E Checker/Policy Parity | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Checker enforces H1.5 lane semantics and non-blocking irrecoverable-folio guardrails. |
| WS-H1.5-F Gate/Report Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Gate-health dependency snapshot and Phase 5/7 report language updated to H1.5 semantics. |
| WS-H1.5-G Regression Locking | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Targeted phase5_mechanism/core_skeptic/core_audit/phase7_human test suite passes with H1.5 contracts. |
| WS-H1.5-H Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Decision, boundary, feasibility, and execution status artifacts published. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 12) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Robust closure remains mathematically unreachable under current matrix semantics. | High | High | Execute WS-A feasibility proof before reruns; redesign lane scoring in WS-B. |
| R2 | Diagnostic lanes are misused as entitlement blockers, forcing perpetual qualified state. | High | High | Split lane classes and enforce in checker/policy. |
| R3 | Missing-folio objections keep being misapplied to SK-H1. | Medium | Medium | Playbook and checker non-blocking criteria updates with explicit exception rules. |
| R4 | SK-C1 gate degradation masks SK-H1 progress visibility. | Medium | Medium | Maintain independent H1 status and gate-health dependency snapshot checks. |
| R5 | Report language drifts ahead of lane entitlement. | Medium | High | Expand claim-boundary markers and guardrail tests. |

---

## 13) Deliverables

Required deliverables for SK-H1.5 execution pass:

1. `reports/core_skeptic/SK_H1_5_BASELINE_REGISTER.md`
2. `reports/core_skeptic/SK_H1_5_FEASIBILITY_REGISTER.md`
3. updated H1 policy/checker/producer artifacts implementing entitlement-vs-diagnostic lane semantics
4. `reports/core_skeptic/SK_H1_5_CLAIM_BOUNDARY_REGISTER.md`
5. expanded H1.5 regression tests (phase5_mechanism/checker/core_audit/phase7_human surfaces)
6. `reports/core_skeptic/SK_H1_5_DECISION_RECORD.md`
7. `reports/core_skeptic/SKEPTIC_H1_5_EXECUTION_STATUS.md`
8. `AUDIT_LOG.md` linkage from pass-5 finding to H1.5 closure class

---

## 14) Closure Criteria

SK-H1 (pass-5 scope) can be considered closed for this cycle only if one is true:

1. `H1_5_ALIGNED`: entitlement lanes are robust and coherent with synchronized claims, or
2. `H1_5_BOUNDED`: entitlement lanes support bounded closure while diagnostic-lane non-conclusive outcomes remain explicitly non-entitlement and policy-guarded.

If neither condition is met, SK-H1 remains **OPEN** (`H1_5_QUALIFIED`, `H1_5_BLOCKED`, or `H1_5_INCONCLUSIVE`).
