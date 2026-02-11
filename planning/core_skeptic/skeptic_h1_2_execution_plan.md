# Execution Plan: Skeptic Multimodal Residual Closure (SK-H1.2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`  
**Finding Target:** `SK-H1` (High, pass-2 residual)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and closeout artifacts updated.

---

## 1) Objective

Address the pass-2 `SK-H1` residual by attempting to resolve multimodal illustration/layout coupling conclusively where feasible, while preserving fail-closed evidence governance if adequacy cannot be satisfied.

This plan targets the remaining core_skeptic challenge:

- "You now acknowledge ambiguity correctly, but the image-text case is still not decisively closed."

Desired endpoint:

1. conclusive SK-H1 coupling outcome (`CONCLUSIVE_NO_COUPLING` or `CONCLUSIVE_COUPLING_PRESENT`) if adequacy and phase4_inference criteria are met, or
2. governance-complete bounded outcome (`INCONCLUSIVE_UNDERPOWERED` or `BLOCKED_DATA_GEOMETRY`) with explicit evidence limits and anti-overreach safeguards.

---

## 2) SK-H1 Problem Statement (Pass 2)

From `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10_2.md`:

- Coupling status remains non-conclusive:
  - `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> `status=INCONCLUSIVE_UNDERPOWERED`
  - `results/phase5_mechanism/anchor_coupling_confirmatory.json` -> no conclusive claim allowed
- Reports are now bounded and non-overreaching:
  - `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md`
  - `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md`
  - `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` (conclusion caveats)

Current residual condition:

- Policy and claim guardrails exist, but adequacy/power shortfalls prevent decisive multimodal closure.

---

## 3) Scope and Non-Goals

## In Scope

- SK-H1 residual closure strategy for underpowered multimodal coupling evidence.
- Anchor geometry/method search and cohort-construction improvements to increase adequacy.
- Confirmatory phase4_inference hardening (uncertainty, stability, and practical-effect interpretation).
- Status/report synchronization for conclusive vs non-conclusive multimodal outcomes.
- Gate/test contracts to prevent categorical claims on underpowered runs.

## Out of Scope

- Semantic decipherment claims.
- SK-C1/SK-C2/SK-H3/SK-M* remediations except dependency notes required for execution order.
- Acquisition of new external manuscript data not currently present in source artifacts.

---

## 4) Success Criteria (Exit Conditions)

`SK-H1` pass-2 residual is considered closed only when all criteria below are satisfied:

1. Multimodal adequacy diagnostics are reproducible and machine-validated per policy.
2. At least one policy-registered anchor/method lane has been explored with deterministic provenance and phase8_comparative adequacy evidence.
3. Final multimodal status is deterministic and auditable:
   - conclusive (if criteria met), or
   - explicitly bounded non-conclusive (if criteria not met).
4. Downstream reporting cannot exceed status class (Phase 5H/5I/Phase 7 coherence).
5. CI/release contracts prevent over-claim regressions for underpowered/blocked multimodal outputs.
6. Execution trace documents what was attempted, what failed/passed, and why closure is or is not conclusive.

---

## 5) Workstreams

## WS-H1.2-A: Residual Baseline and Adequacy Decomposition

**Goal:** Convert the broad "underpowered" label into a precise adequacy-gap matrix.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Capture baseline SK-H1 status and adequacy details from confirmatory artifact. | `results/phase5_mechanism/anchor_coupling_confirmatory.json` | Baseline status + adequacy gaps recorded. |
| A2 | Build adequacy decomposition table (lines/pages/contexts/balance) for anchored and unanchored cohorts. | New `reports/core_skeptic/SK_H1_2_ADEQUACY_REGISTER.md` | Per-metric bottlenecks identified with thresholds. |
| A3 | Link each failing adequacy dimension to candidate remediation levers (anchor method, sampling, cohort policy). | same | Remediation mapping prepared for sweeps. |

### Verification

```bash
python3 - <<'PY'
import json
p='results/phase5_mechanism/anchor_coupling_confirmatory.json'
r=json.load(open(p)).get('results',{})
print(r.get('status'), r.get('status_reason'))
print(r.get('adequacy',{}).get('reasons',[]))
PY
```

---

## WS-H1.2-B: Anchor-Method Search and Coverage Expansion

**Goal:** Determine whether underpower is remediable with feasible geometry/method changes.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define registered anchor-method sweep matrix (thresholds/method variants/relation filters) before reruns. | `configs/core_skeptic/sk_h1_multimodal_policy.json` and/or new sweep config | Sweep matrix is explicit and versioned pre-run. |
| B2 | Run coverage core_audit per candidate method and collect comparable adequacy metrics. | `core_status/phase5_mechanism/anchor_coverage_audit.json` + by-run snapshots | Candidate ranking by adequacy gain produced. |
| B3 | Select best feasible method by adequacy-first criteria (not desired phase4_inference outcome). | New `reports/core_skeptic/SK_H1_2_METHOD_SELECTION.md` | Selection rationale is anti-tuning and auditable. |

### Verification

```bash
python3 scripts/phase5_mechanism/generate_all_anchors.py --dataset-id voynich_real --method-name geometric_v1 --threshold 0.05
python3 scripts/phase5_mechanism/generate_all_anchors.py --dataset-id voynich_real --method-name geometric_v1 --threshold 0.10
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
```

---

## WS-H1.2-C: Cohort Construction and Adequacy Recovery

**Goal:** Improve recurring-context adequacy while preserving policy integrity.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Introduce/validate cohort-construction options that can increase recurring-context support (within policy constraints). | `scripts/phase5_mechanism/run_5i_anchor_coupling.py`, `src/phase5_mechanism/anchor_coupling.py` | Cohort builder exposes deterministic, policy-compliant options. |
| C2 | Add adequacy-attempt log per candidate setting (what improved, what remained failing). | New `results/phase5_mechanism/by_run/*` metadata + `reports/core_skeptic/SK_H1_2_ADEQUACY_REGISTER.md` | Clear pass/fail history per adequacy dimension. |
| C3 | If adequacy remains unmet, classify irreducible limits and trigger bounded non-conclusive path. | `results/phase5_mechanism/anchor_coupling_confirmatory.json` | Non-conclusive outcome is evidence-complete and defensible. |

### Verification

```bash
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
python3 - <<'PY'
import json
r=json.load(open('results/phase5_mechanism/anchor_coupling_confirmatory.json')).get('results',{})
print('status', r.get('status'))
print('adequacy_pass', r.get('adequacy',{}).get('pass'))
print('reasons', r.get('adequacy',{}).get('reasons',[]))
PY
```

---

## WS-H1.2-D: Confirmatory Inference and Decision Robustness

**Goal:** Ensure final SK-H1 outcome is statistically and practically interpretable, not threshold-fragile.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Expand stability checks for CI/p-value sensitivity across seeds/sampling variants. | `results/phase5_mechanism/by_run/` outputs + summary report | Inference stability envelope documented. |
| D2 | Add practical-effect interpretation guardrail (small-effect/noise band governance). | `configs/core_skeptic/sk_h1_multimodal_policy.json` and reports | Decision logic captures both significance and practical magnitude. |
| D3 | Record conclusive eligibility rule outcome explicitly (`why conclusive` vs `why not`). | `results/phase5_mechanism/anchor_coupling_confirmatory.json` | Deterministic decision trace present. |

### Verification

```bash
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
python3 - <<'PY'
import json
r=json.load(open('results/phase5_mechanism/anchor_coupling_confirmatory.json')).get('results',{})
print(r.get('status'), r.get('phase4_inference',{}).get('decision'), r.get('effect',{}).get('p_value'))
PY
```

---

## WS-H1.2-E: Status-to-Report Coherence and Claim Boundaries

**Goal:** Ensure all SK-H1 narrative outputs mirror the emitted multimodal status class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Align Phase 5H and 5I narrative language with final SK-H1 status (conclusive vs inconclusive/blocked). | `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md`, `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` | No narrative exceeds status entitlement. |
| E2 | Align Phase 7 summary language with status-gated multimodal claim strength. | `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md` | Categorical coupling claims only appear on conclusive outcomes. |
| E3 | Add SK-H1.2 coherence checks and required markers for status-gated language. | Checker/test updates under `tests/phase7_human` and/or `tests/phase5_mechanism` | Regression tests fail on over-claim text under non-conclusive status. |

### Verification

```bash
rg -n "illustration|coupling|inconclusive|conclusive|status-gated|underpowered" \
  results/reports/phase5_mechanism/PHASE_5H_RESULTS.md \
  results/reports/phase5_mechanism/PHASE_5I_RESULTS.md \
  reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md
```

---

## WS-H1.2-F: Contract/Gate Hardening for Multimodal Residuals

**Goal:** Prevent future regressions where underpowered multimodal evidence is reported as decisive.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add/extend contract tests for required SK-H1 status, adequacy, and phase4_inference fields. | `tests/phase5_mechanism/test_anchor_coupling_contract.py`, related tests | Artifact schema and status mapping are enforced. |
| F2 | Add/extend claim-guard tests keyed to multimodal status class. | `tests/phase7_human/test_phase7_claim_guardrails.py` | Non-conclusive status blocks categorical language. |
| F3 | Integrate/confirm SK-H1 checks in CI/release paths where applicable. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh`, `scripts/verify_reproduction.sh` | Pipeline catches SK-H1 overreach automatically. |

### Verification

```bash
python3 -m pytest -q \
  tests/phase5_mechanism/test_anchor_coupling.py \
  tests/phase5_mechanism/test_anchor_coupling_contract.py \
  tests/phase7_human/test_phase7_claim_guardrails.py
```

---

## WS-H1.2-G: Governance Traceability and Closeout

**Goal:** Preserve an auditable chain from pass-2 finding to final SK-H1.2 decision.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-H1.2 adequacy and method-selection registers. | `reports/core_skeptic/SK_H1_2_ADEQUACY_REGISTER.md`, `reports/core_skeptic/SK_H1_2_METHOD_SELECTION.md` | Attempt history and rationale documented. |
| G2 | Add SK-H1.2 execution status report with evidence summary and residual risks. | `reports/core_skeptic/SKEPTIC_H1_2_EXECUTION_STATUS.md` (during execution) | End-state and evidence quality explicitly recorded. |
| G3 | Add core_audit-log entry linking SK-H1 pass-2 residual to implemented controls and final decision. | `AUDIT_LOG.md` | Trace complete and file-referenced. |

### Verification

```bash
rg -n "SK-H1.2|INCONCLUSIVE_UNDERPOWERED|BLOCKED_DATA_GEOMETRY|CONCLUSIVE_" AUDIT_LOG.md reports/core_skeptic planning/core_skeptic
```

---

## 6) Execution Order

1. WS-H1.2-A (baseline/adequacy decomposition)
2. WS-H1.2-B (anchor-method sweep and coverage ranking)
3. WS-H1.2-C (cohort adequacy recovery)
4. WS-H1.2-D (phase4_inference robustness)
5. WS-H1.2-E (core_status/report coherence)
6. WS-H1.2-F (contract/gate hardening)
7. WS-H1.2-G (traceability closeout)

Rationale:

- Attempt to improve adequacy first; only then decide whether conclusive closure is feasible or bounded non-conclusive closure is the defensible endpoint.

---

## 7) Decision Matrix for SK-H1.2

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Adequacy passes and confirmatory phase4_inference supports null-coupling under policy thresholds. | `H1_2_ALIGNED` | "No robust image/layout coupling detected under tested criteria." |
| Adequacy passes and confirmatory phase4_inference supports coupling signal under policy thresholds. | `H1_2_ALIGNED` | "A coupling signal is detected under tested criteria, with uncertainty bounds." |
| Adequacy remains below threshold, or adequacy recovers but phase4_inference is stability-fragile across registered seeds/lanes; governance/report contracts are complete. | `H1_2_QUALIFIED` | "Image/layout coupling remains non-conclusive under current evidence envelope." |
| Artifact semantics, report language, or gate checks are inconsistent with status class. | `H1_2_BLOCKED` | "SK-H1.2 remains unresolved due multimodal contract incoherence." |
| Evidence is insufficient to classify whether adequacy failure is remediable. | `H1_2_INCONCLUSIVE` | "SK-H1.2 provisional pending deeper adequacy phase2_analysis." |

Execution outcome: `H1_2_QUALIFIED`.

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H1.2-A Baseline/Adequacy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added adequacy decomposition and attempt history: `reports/core_skeptic/SK_H1_2_ADEQUACY_REGISTER.md`. |
| WS-H1.2-B Method/Coverage Sweep | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Ran registered method sweep; selected lane documented in `reports/core_skeptic/SK_H1_2_METHOD_SELECTION.md`. |
| WS-H1.2-C Cohort Recovery | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated policy defaults to selected lane and larger cohort sizing (`configs/core_skeptic/sk_h1_multimodal_policy.json`). |
| WS-H1.2-D Inference Robustness | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Stability envelope documented; residual classified as inferential ambiguity under mixed-seed behavior. |
| WS-H1.2-E Status/Report Coherence | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated Phase 5H/5I and Phase 7 summary language to explicit status-gated non-conclusive posture. |
| WS-H1.2-F Contract/Gate Hardening | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added multimodal checker/policy and integrated it in CI/pre-release/repro paths with contract tests. |
| WS-H1.2-G Governance Closeout | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-H1.2 execution status report and core_audit trace entry. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Underpower is structurally irreducible with current source data and anchor geometry. | High | High | Prefer governance-complete bounded closure (`H1_2_QUALIFIED`) over forced conclusions. |
| R2 | Anchor-method sweeps become outcome-seeking tuning rather than adequacy-first diagnostics. | Medium | High | Pre-register sweep matrix and selection criteria before confirmatory reruns. |
| R3 | Report language drifts from status artifact after edits/reruns. | Medium | High | Add status-keyed claim guard tests and gate checks. |
| R4 | Increased rerun matrix raises compute/runtime burden and delays iteration. | Medium | Medium | Use staged sweep (coverage-first, then confirmatory reruns for top candidates). |
| R5 | Mixed evidence (borderline adequacy, borderline effect) creates unstable decisions across seeds. | Medium | Medium | Add stability envelope reporting and deterministic decision criteria in policy. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-H1.2 adequacy register with bottleneck decomposition.
2. Registered anchor-method sweep and selection rationale.
3. Updated confirmatory multimodal artifact with deterministic status decision evidence.
4. Report/summary coherence updates tied to status class.
5. SK-H1.2 contract and gate regression tests.
6. SK-H1.2 execution status report under `reports/core_skeptic/`.
7. Audit-log trace entry linking pass-2 finding to implemented controls.

---

## 11) Closure Criteria

`SK-H1` pass-2 residual is closed only when:

1. Adequacy/phase4_inference status is reproducible and policy-valid.
2. Downstream claim language is no stronger than emitted status.
3. CI/release contract checks prevent SK-H1 over-claim regressions.
4. Final outcome is either conclusive under policy or explicitly bounded as non-conclusive with full governance evidence.
