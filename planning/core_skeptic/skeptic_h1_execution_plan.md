# Execution Plan: Skeptic Multimodal Hardening (SK-H1)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-H1` (listed as High in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status table and execution report reflect implementation outcomes.

---

## 1) Objective

Address `SK-H1` by converting image/layout coupling evidence from mixed exploratory signals into a clearly classified, reproducible, and skeptically defensible result.

This plan targets three specific weaknesses called out in the assessment:

1. Phase 5H anchoring imbalance (`Unanchored` sample effectively unusable in report).
2. Phase 5I proximity result framed as exploratory/preliminary.
3. Phase 7 summary language stronger than the multimodal evidence grade.

---

## 2) SK-H1 Problem Statement

From `SK-H1`:

- `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md` reports near-total anchor imbalance and explicitly notes geometry needs refinement.
- `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` marks layout/illustration coupling as preliminary.
- `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md` states no significant adaptation to illustration proximity as if decisively settled.

Core skeptic attack:

- "Image coupling was underpowered or exploratory, but downstream conclusions are categorical."

---

## 3) Scope and Non-Goals

## In Scope

- Anchor generation and anchor-cohort construction for proximity analysis.
- Phase 5I anchor coupling method hardening from exploratory to confirmatory status.
- Evidence status taxonomy (`conclusive`, `inconclusive`, `blocked`) for multimodal claims.
- Cross-document claim alignment in Phase 5H, 5I, final Phase 5 synthesis, and Phase 7 summary.
- Automated tests and reproducibility contract for multimodal outputs.

## Out of Scope

- Semantics, decipherment, or illustration interpretation.
- Topology collapse questions (DAG vs lattice) unless directly needed for coupling metrics.
- Non-SK-H1 skeptic items (SK-H2, SK-H3, SK-M*), except wording touchpoints required to remove direct contradiction.

---

## 4) Success Criteria (Exit Conditions)

`SK-H1` is considered closed only if all criteria below are satisfied:

1. Multimodal analysis explicitly declares one of:
   - `CONCLUSIVE_NO_COUPLING`
   - `CONCLUSIVE_COUPLING_PRESENT`
   - `INCONCLUSIVE_UNDERPOWERED`
   - `BLOCKED_DATA_GEOMETRY`
2. Reported conclusion cannot be stronger than the status class.
3. Data adequacy checks are machine-enforced before any conclusive claim:
   - minimum recurring-context count per group,
   - minimum anchored/unanchored balance ratio,
   - minimum number of pages contributing to each cohort.
4. Confirmatory result includes uncertainty metrics (confidence interval and permutation-based p-value or equivalent non-parametric evidence).
5. Phase 5H, Phase 5I, and Phase 7 language is internally consistent with the same multimodal status artifact.
6. Tests fail closed when required status fields are missing or non-conclusive.

---

## 5) Workstreams

## WS-H1-A: Evidence Contract and Status Taxonomy

**Goal:** Define what "decisively closed" means, and encode it in machine-readable policy.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define multimodal status taxonomy and escalation rules. | `governance/SENSITIVITY_ANALYSIS.md` or new `governance/MULTIMODAL_COUPLING_POLICY.md` | Status classes and claim limits documented. |
| A2 | Add policy config for adequacy thresholds and significance criteria. | `configs/core_skeptic/sk_h1_multimodal_policy.json` (new) | Script reads policy; defaults are explicit and versioned. |
| A3 | Define canonical output contract for multimodal result artifact. | `results/phase5_mechanism/anchor_coupling_confirmatory.json` (new canonical) | Artifact contains status, adequacy diagnostics, and inference fields. |

### Verification

```bash
python3 - <<'PY'
import json
cfg=json.load(open('configs/core_skeptic/sk_h1_multimodal_policy.json'))
print(sorted(cfg.keys()))
PY
```

---

## WS-H1-B: Anchor Geometry and Cohort Construction Repair

**Goal:** Eliminate the "anchored vs unanchored imbalance" failure mode.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Extend anchor generation to support explicit method variants (thresholds/modes) with provenance tags. | `scripts/phase5_mechanism/generate_all_anchors.py` | Multiple anchor methods can be generated/referenced deterministically. |
| B2 | Add anchor coverage audit utility (token coverage, page coverage, cohort ratio). | `scripts/phase5_mechanism/audit_anchor_coverage.py` (new) | Coverage report produced before coupling analysis. |
| B3 | Replace binary anchored/unanchored partition with distance/region-aware cohort builder and matched sampling option. | `scripts/phase5_mechanism/run_5i_anchor_coupling.py` or new shared module under `src/phase5_mechanism` | Cohorts satisfy adequacy thresholds or fail with explicit status. |
| B4 | Persist adequacy diagnostics (counts, ratios, pages, recurring contexts) to artifact and report table. | `results/phase5_mechanism/anchor_coupling_confirmatory.json`, `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` | Readers can see why status is conclusive vs inconclusive. |

### Verification

```bash
python3 scripts/phase5_mechanism/generate_all_anchors.py --threshold 0.05
python3 scripts/phase5_mechanism/generate_all_anchors.py --threshold 0.10
python3 scripts/phase5_mechanism/audit_anchor_coverage.py
```

---

## WS-H1-C: Confirmatory Coupling Analysis Upgrade

**Goal:** Move from exploratory delta metrics to confirmatory inference with explicit uncertainty.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add bootstrap CI for anchored-vs-unanchored consistency delta. | `scripts/phase5_mechanism/run_5i_anchor_coupling.py` | Artifact includes `delta_ci_low`, `delta_ci_high`. |
| C2 | Add permutation or label-shuffle test for coupling significance. | same | Artifact includes `p_value` and test configuration. |
| C3 | Add power/adequacy gate: if thresholds not met, force `INCONCLUSIVE_UNDERPOWERED`. | same + policy config | Script cannot emit conclusive state when underpowered. |
| C4 | Add null-control diagnostics (matched random anchors preserving cohort sizes). | same | Report includes observed-vs-null effect comparison. |
| C5 | Publish confirmatory report section with explicit non-claims. | `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` and `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` | Multimodal section references status artifact and uncertainty. |

### Verification

```bash
python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py
python3 - <<'PY'
import json
d=json.load(open('results/phase5_mechanism/anchor_coupling_confirmatory.json'))
print(d['status'], d['adequacy'])
PY
```

---

## WS-H1-D: Cross-Phase Consistency with Phase 7

**Goal:** Ensure Phase 7 summary language is downstream of multimodal evidence status, not stronger.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Add explicit multimodal-status ingestion into Phase 7B/summary assembly path. | `scripts/phase7_human/run_7b_codicology.py`, `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md` generation flow | Phase 7 summary states conclusive/inconclusive status correctly. |
| D2 | Remove unconditional wording like "no significant adaptation" when status is inconclusive or blocked. | `reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md` | Claim text becomes conditional and evidence-bounded. |
| D3 | Add "evidence grade" subsection in Phase 7 summary for image/layout coupling. | same | Reader sees direct strength rating and reason. |

### Verification

```bash
python3 scripts/phase7_human/run_7b_codicology.py
rg -n "illustration|coupling|inconclusive|conclusive" reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md
```

---

## WS-H1-E: Report and Claim-Language Calibration

**Goal:** Remove internal contradictions between pilot limitations and final framing.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Reclassify `PHASE_5H_RESULTS.md` as pilot/inconclusive where adequacy fails. | `results/reports/phase5_mechanism/PHASE_5H_RESULTS.md` | Report no longer claims decisive proximity outcome from underpowered split. |
| E2 | Align `PHASE_5I_RESULTS.md` conclusion with confirmatory status artifact. | `results/reports/phase5_mechanism/PHASE_5I_RESULTS.md` | Conclusion includes explicit confidence/uncertainty language. |
| E3 | Update final Phase 5 synthesis section to prevent overgeneralization. | `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` | Multimodal paragraph reflects status class and constraints. |
| E4 | Add skeptic-facing trace note describing SK-H1 closure logic and remaining unknowns. | `reports/core_skeptic/SKEPTIC_H1_EXECUTION_STATUS.md` (during execution) | Closure rationale is auditable. |

### Verification

```bash
rg -n "exploratory|preliminary|inconclusive|conclusive|no significant adaptation" \
  results/reports/phase5_mechanism/PHASE_5H_RESULTS.md \
  results/reports/phase5_mechanism/PHASE_5I_RESULTS.md \
  results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md \
  reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md
```

---

## WS-H1-F: Test and Contract Hardening

**Goal:** Prevent regression to underpowered-but-categorical multimodal claims.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add unit tests for cohort adequacy checks and status mapping. | `tests/phase5_mechanism/test_anchor_coupling.py` (new) | Underpowered inputs map to inconclusive/block states. |
| F2 | Add script-level contract tests for mandatory output fields. | `tests/phase5_mechanism/test_anchor_coupling_contract.py` (new) | Missing CI/p-value/status fields fail tests. |
| F3 | Add report-language guard tests to prevent categorical claims on inconclusive artifacts. | `tests/phase7_human/test_phase7_claim_guardrails.py` (new) | Text-generation/report tests fail if wording exceeds evidence class. |
| F4 | Integrate tests into CI command path. | `scripts/ci_check.sh` and/or pytest selection docs | CI catches SK-H1 regressions automatically. |

### Verification

```bash
python3 -m pytest -q tests/phase5_mechanism/test_anchor_coupling.py \
  tests/phase5_mechanism/test_anchor_coupling_contract.py \
  tests/phase7_human/test_phase7_claim_guardrails.py
```

---

## WS-H1-G: Reproducibility and Operator Guidance

**Goal:** Make multimodal reruns deterministic and auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add reproducibility section for anchor-method generation and confirmatory run sequence. | `governance/governance/REPRODUCIBILITY.md` | Operator can run end-to-end multimodal pipeline from docs. |
| G2 | Document runtime progress/status outputs for long runs. | `governance/governance/REPRODUCIBILITY.md`, script console/progress behavior | Operators can distinguish long-running vs stalled states. |
| G3 | Record SK-H1 closure entry and artifact pointers in audit log. | `AUDIT_LOG.md` | Audit trail ties implementation to skeptic finding. |

### Verification

```bash
rg -n "SK-H1|anchor coupling|multimodal|illustration proximity" docs AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-H1-A (evidence contract first)
2. WS-H1-B (data adequacy and cohort integrity)
3. WS-H1-C (confirmatory statistics and status gating)
4. WS-H1-D (Phase 7 downstream consistency)
5. WS-H1-E (report language calibration)
6. WS-H1-F (tests/contracts)
7. WS-H1-G (repro docs + audit trace)

Rationale:

- Do not update conclusions before the contract, adequacy checks, and confirmatory method exist.

---

## 7) Decision Matrix for Final SK-H1 Outcome

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Adequacy pass + inferential pass + effect near zero | `CONCLUSIVE_NO_COUPLING` | "No robust image/layout coupling detected under tested criteria." |
| Adequacy pass + inferential pass + non-trivial effect | `CONCLUSIVE_COUPLING_PRESENT` | "Coupling signal detected; mechanism may be modulated by physical context." |
| Adequacy fail but data available | `INCONCLUSIVE_UNDERPOWERED` | "Current data partition insufficient for conclusive coupling inference." |
| Geometry/data constraints prevent valid cohorts | `BLOCKED_DATA_GEOMETRY` | "Coupling test blocked by anchor geometry/data constraints; claim deferred." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H1-A Evidence Contract | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added status taxonomy, policy file, and canonical confirmatory artifact contract. |
| WS-H1-B Geometry/Cohorts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added coverage audit script and ratio-based line cohort construction with method selection controls. |
| WS-H1-C Confirmatory Upgrade | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added bootstrap CI, permutation test, adequacy gates, and fail-closed status mapping. |
| WS-H1-D Phase 7 Consistency | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Phase 7B now ingests multimodal status artifact and reports evidence grade explicitly. |
| WS-H1-E Language Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated Phase 5H/5I/final summary and Phase 7 wording to avoid over-strong claims. |
| WS-H1-F Tests/Contracts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added phase5_mechanism/phase7_human guardrail tests and validated targeted suites. |
| WS-H1-G Repro/Audit Trace | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added reproducibility/policy docs, audit log traceability, and execution status report. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Anchor geometry still yields weak unanchored cohorts even after refinement. | Medium | High | Fail closed to `BLOCKED_DATA_GEOMETRY`; downgrade claims instead of forcing conclusion. |
| R2 | Threshold choices appear tuned to desired outcome. | Medium | High | Pre-register policy values in config before rerun; log all threshold sweeps with provenance. |
| R3 | Report language drifts from artifact status in later edits. | High | Medium | Add contract tests guarding wording against status class. |
| R4 | Additional compute burden slows iteration and causes operator confusion. | Medium | Medium | Add progress output and checkpointed artifacts; document reduced-cost dry runs. |

---

## 10) Deliverables

Required deliverables for the execution pass:

1. Policy and contract for SK-H1 multimodal status.
2. Updated anchor coupling pipeline with adequacy checks and confirmatory inference.
3. Canonical multimodal artifact with status, uncertainty, and diagnostics.
4. Aligned Phase 5H/5I/Phase 7 language bounded by evidence status.
5. New tests preventing underpowered categorical claims.
6. Execution summary in `reports/core_skeptic/SKEPTIC_H1_EXECUTION_STATUS.md`.
