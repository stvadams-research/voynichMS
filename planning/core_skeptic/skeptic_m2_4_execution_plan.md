# Execution Plan: Skeptic Comparative Uncertainty Closure and Confidence-Robustness (SK-M2.4)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`  
**Finding Target:** `SK-M2` (Medium, pass-4 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. See `reports/core_skeptic/SKEPTIC_M2_4_EXECUTION_STATUS.md` for command evidence and outcomes.

---

## 1) Objective

Address the pass-4 `SK-M2` residual as fully as feasible while preventing another repeated reassessment loop on the same unresolved confidence pattern.

This plan targets two simultaneous goals:

1. attempt to improve comparative confidence with methodologically valid, pre-registered diagnostics, and
2. if conclusive confidence is still not supportable, harden SK-M2 into a deterministic bounded state with explicit anti-overreach and anti-repeat governance.

---

## 2) Pass-4 SK-M2 Problem Statement

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_4.md`:

- `SK-M2 (Medium): Comparative uncertainty remains explicitly inconclusive.`
- Reported evidence points to:
  - `results/phase7_human/phase_7c_uncertainty.json:35` (`INCONCLUSIVE_UNCERTAINTY`)
  - `results/phase7_human/phase_7c_uncertainty.json:36` (`TOP2_GAP_FRAGILE`)
  - `results/phase7_human/phase_7c_uncertainty.json:37` (provisional claim boundary)
  - `results/phase7_human/phase_7c_uncertainty.json:40`
  - `results/phase7_human/phase_7c_uncertainty.json:42`
  - `results/phase7_human/phase_7c_uncertainty.json:50`

Current canonical state snapshot:

- `status=INCONCLUSIVE_UNCERTAINTY`
- `reason_code=TOP2_GAP_FRAGILE`
- `nearest_neighbor=Lullian Wheels`
- `nearest_neighbor_stability=0.4565`
- `jackknife_nearest_neighbor_stability=0.8333`
- `rank_stability=0.4565`
- `top2_gap.ci95_lower=0.0263`

Skeptic leverage that remains valid:

- comparative direction exists, but confidence remains non-conclusive.

---

## 3) Fourth-Attempt Retrospective (Why M2.2 Still Left Residual)

This fourth attempt explicitly addresses the repeat pattern seen after M2.2:

1. **Schema/checker completeness improved, but inferential class did not.**  
   M2.2 added richer fields, reason checks, and matrix registration, yet all observed lanes remained inconclusive.

2. **Residual is stable across registered seeds/iteration lanes.**  
   Prior matrix behavior indicates the blocker is structural confidence fragility, not one noisy lane.

3. **Reason-code granularity is still too coarse for closure governance.**  
   `TOP2_GAP_FRAGILE` currently collapses multiple plausible causes, making actionability and anti-repeat closure weaker.

4. **No terminal bounded lane was formalized for irreducible confidence limits.**  
   Without a deterministic bounded closure class, SK-M2 keeps reopening with equivalent evidence.

---

## 4) Scope and Non-Goals

## In Scope

- SK-M2 confidence and uncertainty semantics for pass-4 residual.
- Comparative uncertainty policy, artifact schema, checker, and report boundary alignment.
- Diagnostic decomposition of top-2 fragility into measurable sub-causes.
- Deterministic closure-lane governance preventing repeated ambiguous outcomes.
- CI/release contract hardening for SK-M2 parity.

## Out of Scope

- SK-C1 release sensitivity remediation.
- SK-H1/H2/H3 and SK-M1/M3/M4 remediation except explicit dependency references.
- Introduction of new decipherment claims or semantic interpretation claims.

---

## 5) Deterministic SK-M2.4 Closure Framework

To avoid a fifth cycle on unchanged evidence, SK-M2.4 uses explicit closure lanes:

## Lane A: Confidence-Aligned (`M2_4_ALIGNED`)

Allowed only when all are true:

- `status=STABILITY_CONFIRMED`
- all confirmed thresholds pass (`nearest`, `jackknife`, `rank`, `margin`, `top2_gap_ci95_lower`)
- comparative reports and summaries use only aligned claim language
- checker/test/pipeline parity holds in CI and release modes

## Lane B: Directional Qualified (`M2_4_QUALIFIED`)

Allowed only when all are true:

- `status=DISTANCE_QUALIFIED`
- qualified thresholds pass consistently
- reason-code and allowed-claim mapping is deterministic
- report language stays strictly uncertainty-qualified

## Lane C: Bounded Non-Conclusive (`M2_4_BOUNDED`)

Allowed only when all are true:

- `status=INCONCLUSIVE_UNCERTAINTY`
- confidence fragility is decomposed and explicitly evidenced
- anti-overreach claim boundaries are fully enforced
- decision record states objective reopen triggers (what new evidence would change lane)

## Disallowed Ambiguous State

If lane predicates are unmet or inconsistent:

- `M2_4_BLOCKED` (policy/checker/report mismatch), or
- `M2_4_INCONCLUSIVE` (insufficient evidence to classify lane).

---

## 6) Success Criteria (Exit Conditions)

SK-M2.4 is complete only when all are satisfied:

1. A deterministic lane result (`M2_4_ALIGNED`, `M2_4_QUALIFIED`, or `M2_4_BOUNDED`) is machine-derived.
2. `TOP2_GAP_FRAGILE` is decomposed into explicit measurable diagnostics and reason taxonomy.
3. Artifact schema captures confidence diagnosis fields required for reproducible lane assignment.
4. Narrative/report claim boundaries are synchronized to lane entitlement.
5. CI/release/repro pipelines enforce SK-M2 semantics without bypass.
6. Governance artifacts include objective reopen conditions to prevent repetitive reassessment on unchanged evidence.

---

## 7) Workstreams

## WS-M2.4-A: Baseline Freeze and Residual Decomposition

**Goal:** Lock pass-4 SK-M2 evidence and map each residual vector to concrete controls.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Freeze pass-4 SK-M2 tuple (status, reason, key metrics, claim class, evidence links). | New `reports/core_skeptic/SK_M2_4_BASELINE_REGISTER.md` | Baseline reflects canonical artifact and assessment references. |
| A2 | Decompose residual vectors (`rank_instability`, `top2_gap_fragility`, `margin_sensitivity`, `model_assumption_risk`). | same | Each vector has mapped control/test path. |
| A3 | Define objective disconfirmability/reopen triggers for SK-M2 lane transitions. | same + decision section | Reopen conditions are explicit and non-interpretive. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('results/phase7_human/phase_7c_uncertainty.json')).get('results', {})
print(r.get('status'), r.get('reason_code'), r.get('allowed_claim'))
print(r.get('nearest_neighbor_stability'), r.get('jackknife_nearest_neighbor_stability'), r.get('rank_stability'))
print((r.get('top2_gap') or {}).get('ci95_lower'))
PY
```

---

## WS-M2.4-B: Diagnostic Depth Expansion for Confidence Fragility

**Goal:** Separate causes currently collapsed into `TOP2_GAP_FRAGILE`.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Add diagnostic metrics for ranking volatility drivers (for example rank-entropy deltas, top-2 identity flips, margin variance). | `src/phase8_comparative/mapping.py` | Artifact includes machine-readable fragility decomposition block. |
| B2 | Add confidence-sensitivity diagnostics across perturbation families (bootstrap-only, jackknife-only, combined). | same + runner output | Distinct perturbation impacts are measurable and comparable. |
| B3 | Add explicit uncertainty diagnostic section in report output. | `reports/phase8_comparative/PROXIMITY_ANALYSIS.md` renderer path | Reports expose why status is bounded. |

### Verification

```bash
python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 2000 --seed 42
python3 - <<'PY'
import json
r=json.load(open('results/phase7_human/phase_7c_uncertainty.json')).get('results', {})
print('has_rank_components', isinstance(r.get('rank_stability_components'), dict))
print('has_top2_gap', isinstance(r.get('top2_gap'), dict))
print('has_metric_validity', isinstance(r.get('metric_validity'), dict))
PY
```

---

## WS-M2.4-C: Registered Confidence Matrix 2.0 (Anti-Tuning)

**Goal:** Improve testability and reproducibility while preserving anti-p-hacking constraints.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Define updated registered matrix lanes (seeds, iteration bands, perturbation profiles) in policy before execution. | `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json` | Matrix definition is pre-registered and versioned. |
| C2 | Add publication-lane selection rule hierarchy (validity -> stability class -> reproducibility) and prohibit outcome-tuned lane pick. | New `reports/core_skeptic/SK_M2_4_METHOD_SELECTION.md` | Selection protocol is deterministic and auditable. |
| C3 | Define tiered run strategy (`smoke`, `standard`, `release-depth`) for repeatable evaluation and fast iteration. | policy + runner args/docs | Testability path exists without conflating with release-depth conclusions. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json'))
print('version', p.get('version'))
print('has_matrix', 'registered_confidence_matrix' in p)
print('has_thresholds', 'thresholds' in p)
PY
```

---

## WS-M2.4-D: Policy and Reason-Taxonomy Hardening

**Goal:** Make SK-M2 status transitions and residual reasons precise and actionable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Expand reason-code taxonomy for inconclusive outcomes (for example `TOP2_IDENTITY_FLIP_DOMINANT`, `MARGIN_VOLATILITY_DOMINANT`, `RANK_ENTROPY_HIGH`). | `configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json` | Residual classes are diagnostically specific. |
| D2 | Require deterministic `allowed_claim` strings per core_status/reason class. | policy + artifact emitter | Claim entitlement is machine-gated. |
| D3 | Add explicit policy for when `M2_4_BOUNDED` is valid closure vs when SK-M2 remains blocked. | policy + docs | Anti-repeat lane semantics are enforceable. |

### Verification

```bash
python3 - <<'PY'
import json
r=json.load(open('results/phase7_human/phase_7c_uncertainty.json')).get('results', {})
print('status', r.get('status'))
print('reason', r.get('reason_code'))
print('allowed_claim', r.get('allowed_claim'))
PY
```

---

## WS-M2.4-E: Checker and Pipeline Enforcement Upgrade

**Goal:** Ensure policy/report/artifact coherence is fail-closed.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Extend SK-M2 checker for new reason taxonomy, lane derivation, and bounded-closure rules. | `scripts/core_skeptic/check_comparative_uncertainty.py` | Checker rejects ambiguous/non-entitled outcomes. |
| E2 | Add checker tests for edge cases (taxonomy mismatch, lane mismatch, incomplete diagnostics, stale/missing fields). | `tests/core_skeptic/test_comparative_uncertainty_checker.py` | New regression classes are test-locked. |
| E3 | Ensure CI/release/repro scripts enforce upgraded SK-M2 checker semantics in parity. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | No pipeline path bypasses SK-M2.4 checks. |

### Verification

```bash
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode ci
python3 scripts/core_skeptic/check_comparative_uncertainty.py --mode release
python3 -m pytest -q tests/core_skeptic/test_comparative_uncertainty_checker.py tests/core_audit/test_ci_check_contract.py tests/core_audit/test_pre_release_contract.py tests/core_audit/test_verify_reproduction_contract.py
```

---

## WS-M2.4-F: Comparative Narrative and Claim-Boundary Synchronization

**Goal:** Prevent report language from outrunning uncertainty entitlement.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Align comparative reports to lane-bound allowed/disallowed statements. | `reports/phase8_comparative/PROXIMITY_ANALYSIS.md`, `reports/phase8_comparative/PHASE_B_SYNTHESIS.md`, `reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md`, `reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md` | Narrative is fully status-entitled. |
| F2 | Update comparative uncertainty policy docs with SK-M2.4 lane semantics and reopen conditions. | `governance/COMPARATIVE_UNCERTAINTY_POLICY.md` | Documentation matches checker behavior. |
| F3 | Add explicit bound statements for `M2_4_BOUNDED` outcome to preempt overclaiming. | governance/reports + register | Bounded outcome is technically clear and reproducible. |

### Verification

```bash
rg -n "INCONCLUSIVE_UNCERTAINTY|DISTANCE_QUALIFIED|STABILITY_CONFIRMED|allowed_claim|uncertainty-qualified|phase_7c_uncertainty.json" \
  reports/phase8_comparative/PROXIMITY_ANALYSIS.md \
  reports/phase8_comparative/PHASE_B_SYNTHESIS.md \
  reports/phase8_comparative/PHASE_B_BOUNDARY_STATEMENT.md \
  reports/phase8_comparative/PHASE8_FINAL_FINDINGS_SUMMARY.md \
  governance/COMPARATIVE_UNCERTAINTY_POLICY.md
```

---

## WS-M2.4-G: Governance Closeout and Anti-Repeat Controls

**Goal:** Provide a complete, auditable SK-M2 closure package for this fourth attempt.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-M2.4 claim-boundary and diagnostic registers. | New `reports/core_skeptic/SK_M2_4_CLAIM_BOUNDARY_REGISTER.md`, `reports/core_skeptic/SK_M2_4_DIAGNOSTIC_MATRIX.md` | Residual rationale and allowed claims are auditable. |
| G2 | Add SK-M2.4 decision record with selected lane and reopen triggers. | New `reports/core_skeptic/SK_M2_4_DECISION_RECORD.md` | Future reassessment can distinguish new regressions from unchanged bounded evidence. |
| G3 | Add execution status template path and audit-log linkage requirement. | `reports/core_skeptic/SKEPTIC_M2_4_EXECUTION_STATUS.md` (during execution), `AUDIT_LOG.md` | Full traceability from finding -> controls -> lane state. |

### Verification

```bash
rg -n "SK-M2.4|M2_4_|TOP2_GAP_FRAGILE|INCONCLUSIVE_UNCERTAINTY|allowed_claim|reopen" \
  planning/core_skeptic \
  reports/core_skeptic \
  AUDIT_LOG.md
```

---

## 8) Execution Order

1. WS-M2.4-A Baseline Freeze  
2. WS-M2.4-B Diagnostic Depth Expansion  
3. WS-M2.4-C Registered Matrix 2.0  
4. WS-M2.4-D Policy and Reason-Taxonomy Hardening  
5. WS-M2.4-E Checker/Pipeline Enforcement  
6. WS-M2.4-F Narrative/Claim-Boundary Synchronization  
7. WS-M2.4-G Governance Closeout

Rationale:

- freeze and decompose first,
- improve diagnosability and registered evaluation second,
- enforce policy/checker parity third,
- finalize governance and anti-repeat controls last.

---

## 9) Decision Matrix for SK-M2.4

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Confirmed thresholds pass with coherent artifact/report/pipeline semantics. | `M2_4_ALIGNED` | "Comparative nearest-neighbor confidence is uncertainty-qualified and stability-supported under policy thresholds." |
| Qualified thresholds pass but confirmed thresholds fail; claims remain bounded and coherent. | `M2_4_QUALIFIED` | "Comparative signal is directional with explicit uncertainty qualification and reopen conditions." |
| Inconclusive status persists but diagnostics are complete, bounded, and anti-overreach governance is satisfied. | `M2_4_BOUNDED` | "Comparative outcome remains non-conclusive with explicit quantified limits; no stronger claim is entitled." |
| Policy/checker/report mismatch or missing diagnostics prevents deterministic lane assignment. | `M2_4_BLOCKED` | "SK-M2 remains unresolved due comparative uncertainty contract incoherence." |
| Evidence is incomplete for lane decision. | `M2_4_INCONCLUSIVE` | "SK-M2.4 state remains provisional pending required diagnostic evidence." |

Execution outcome: `M2_4_BOUNDED`.

---

## 10) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M2.4-A Baseline Freeze | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Baseline and residual decomposition captured in `reports/core_skeptic/SK_M2_4_BASELINE_REGISTER.md`. |
| WS-M2.4-B Diagnostic Expansion | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added fragility decomposition + lane fields in `src/phase8_comparative/mapping.py` and regenerated canonical artifact/report. |
| WS-M2.4-C Matrix 2.0 | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Executed 9-lane registered matrix (`/tmp/m2_4_sweep/summary.json`) and documented selection in `reports/core_skeptic/SK_M2_4_METHOD_SELECTION.md`. |
| WS-M2.4-D Policy Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Upgraded SK-M2 policy with lane semantics, expanded reason taxonomy, and M2.4 artifact contracts. |
| WS-M2.4-E Checker/Pipeline | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Extended checker for lane and fragility-signal coherence; targeted checker/core_audit tests pass. |
| WS-M2.4-F Narrative Sync | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Comparative docs updated with `M2_4_BOUNDED` uncertainty boundaries and canonical artifact linkage. |
| WS-M2.4-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-M2.4 diagnostic, boundary, decision, and execution status reports. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 11) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | SK-M2 continues to reopen with unchanged evidence because closure semantics remain ambiguous. | High | High | Add deterministic lane model with explicit `M2_4_BOUNDED` governance and reopen triggers. |
| R2 | Diagnostic expansion introduces complexity without improving actionability. | Medium | Medium | Require each new metric to map to reason-code decisions and checker rules. |
| R3 | Updated matrix design is interpreted as outcome-tuning. | Medium | High | Pre-register matrix and lane-selection rule before execution; preserve anti-tuning constraints. |
| R4 | Report language drifts beyond status entitlement after future edits. | Medium | High | Expand required markers + checker coverage across all comparative surfaces. |
| R5 | CI/release checker parity drifts, allowing mode-specific semantic gaps. | Medium | High | Lock parity with audit contract tests and shared invocation ordering. |

---

## 12) Deliverables

Required deliverables for SK-M2.4 execution pass:

1. `reports/core_skeptic/SK_M2_4_BASELINE_REGISTER.md`
2. `reports/core_skeptic/SK_M2_4_DIAGNOSTIC_MATRIX.md`
3. `reports/core_skeptic/SK_M2_4_METHOD_SELECTION.md`
4. `reports/core_skeptic/SK_M2_4_CLAIM_BOUNDARY_REGISTER.md`
5. `reports/core_skeptic/SK_M2_4_DECISION_RECORD.md`
6. policy/checker/test updates for SK-M2.4 lane and taxonomy enforcement
7. synchronized comparative docs for SK-M2.4 claim boundaries
8. `reports/core_skeptic/SKEPTIC_M2_4_EXECUTION_STATUS.md`
9. `AUDIT_LOG.md` linkage entry for SK-M2.4 execution and lane decision

---

## 13) Closure Criteria

SK-M2 (pass-4 scope) can be considered closed for this cycle only if one of these is true:

1. `M2_4_ALIGNED`: confidence thresholds and narrative entitlement are fully aligned, or
2. `M2_4_QUALIFIED`: directional confidence is policy-qualified and fully bounded, or
3. `M2_4_BOUNDED`: non-conclusive outcome is fully decomposed, policy-entitled, and governed by objective reopen triggers.

If none are satisfied, SK-M2 remains **OPEN**.
