# Execution Plan: Skeptic Control-Comparability Hardening (SK-H3)

**Source Assessment:** `reports/skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-H3` (listed as High in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status tracker and execution report reflect implementation outcomes.

---

## 1) Objective

Address `SK-H3` by making control comparability auditable, symmetric, and resistant to the skeptic claim that controls are tuned to desired outcomes and then reused as evidence.

This plan specifically targets the two weaknesses called out in the assessment:

1. Metric-targeted control tuning to Voynich-like signatures.
2. Known normalization asymmetry (controls bypass EVA parsing).

---

## 2) SK-H3 Problem Statement

From `SK-H3`:

- Control matching is currently defined as explicit tuning to Voynich targets (tokens, z-score, repetition, locality, grammar) in `docs/GENERATOR_MATCHING.md:9` through `docs/GENERATOR_MATCHING.md:17`, with class-specific tuning steps in `docs/GENERATOR_MATCHING.md:25`, `docs/GENERATOR_MATCHING.md:29`, and `docs/GENERATOR_MATCHING.md:33`.
- Methods reference currently documents a known asymmetry where controls bypass normalization logic in `docs/METHODS_REFERENCE.md:75` through `docs/METHODS_REFERENCE.md:83`.

Core skeptic attack:

- "Controls are tuned to look like Voynich, then used to argue Voynich is non-semantic."

---

## 3) Scope and Non-Goals

## In Scope

- Control-comparability policy and anti-circularity guardrails.
- Separation of matching metrics from downstream evaluation metrics.
- Normalization symmetry or equivalence proof for control pipelines.
- Deterministic provenance for control parameter search/tuning.
- CI/tests that fail closed when comparability requirements are not met.
- Report/documentation alignment for comparability caveats and status.

## Out of Scope

- New semantic-decipherment claims.
- Reframing SK-H2 public claim language beyond SK-H3 touchpoints.
- Multimodal/image coupling remediation (SK-H1), except where shared policy references are needed.
- Major model-family redesign not required to establish comparability auditability.

---

## 4) Success Criteria (Exit Conditions)

`SK-H3` is considered closed only if all criteria below are met:

1. Matching metrics and evaluation metrics are explicitly partitioned and versioned.
2. Controls cannot be declared comparable unless untuned holdout metrics pass predefined thresholds.
3. Control token normalization path is symmetric with real-data normalization, or equivalence is demonstrated with enforced tests and bounded applicability.
4. Every matched control class includes deterministic search provenance (candidate space, seed, selected parameters, and rejection history).
5. Report conclusions that rely on controls are bounded by an explicit comparability status artifact.
6. CI/pre-release checks fail when comparability policy checks fail or required evidence artifacts are missing.

---

## 5) Workstreams

## WS-H3-A: Comparability Policy and Taxonomy

**Goal:** Define what "comparable control" means and encode anti-circularity rules.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define comparability taxonomy and anti-circularity constraints (match/eval split, leakage prohibition). | `docs/CONTROL_COMPARABILITY_POLICY.md` (new) | Policy doc defines classes, disallowed patterns, and closure rules. |
| A2 | Add machine-readable SK-H3 policy config (required artifacts, thresholds, leakage checks, normalization mode policy). | `configs/skeptic/sk_h3_control_comparability_policy.json` (new) | Policy is parseable and versioned. |
| A3 | Define canonical comparability artifact contract. | `status/synthesis/CONTROL_COMPARABILITY_STATUS.json` (new canonical output schema) | Required fields documented and testable. |

### Verification

```bash
python3 - <<'PY'
import json
p = json.load(open('configs/skeptic/sk_h3_control_comparability_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-H3-B: Match vs Evaluate Metric Decoupling

**Goal:** Eliminate metric-target leakage by separating fit metrics from adjudication metrics.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Define `matching_metrics` vs `holdout_evaluation_metrics` in policy/config and docs. | `docs/GENERATOR_MATCHING.md`, new policy config | Docs no longer imply same metrics are used both to fit and to conclude. |
| B2 | Update indistinguishability/control evaluation flow to consume metric partitions from config. | `scripts/synthesis/run_indistinguishability_test.py`, `src/synthesis/indistinguishability.py` | Runtime outputs separate fit and holdout scorecards. |
| B3 | Add explicit "target leakage check" output in results artifact. | `status/synthesis/TURING_TEST_RESULTS.json`, `status/synthesis/CONTROL_COMPARABILITY_STATUS.json` | Artifacts expose whether any conclusion metric was used during tuning. |

### Verification

```bash
rg -n "matching_metrics|holdout_evaluation_metrics|leakage" \
  docs/GENERATOR_MATCHING.md \
  scripts/synthesis/run_indistinguishability_test.py \
  src/synthesis/indistinguishability.py
```

---

## WS-H3-C: Normalization Symmetry Closure

**Goal:** Resolve or tightly bound the known parser asymmetry between real and control data.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Add configurable normalization mode to control generators (`parser`, `pre_normalized_with_assertions`). | `src/foundation/controls/self_citation.py`, `src/foundation/controls/table_grille.py`, `src/foundation/controls/mechanical_reuse.py`, `src/foundation/controls/synthetic.py` | Control generation emits normalization provenance and mode. |
| C2 | Add parser-symmetry/equivalence tests validating control token canonicalization assumptions. | `tests/foundation/test_controls.py`, `tests/synthesis/test_run_indistinguishability_runner.py` | Tests fail if bypass mode emits out-of-policy forms. |
| C3 | Update methods documentation to replace "known confound" with explicit bounded condition and enforcement path. | `docs/METHODS_REFERENCE.md` | Confound becomes enforced condition with fallback behavior and status impact. |

### Verification

```bash
python3 -m pytest -q tests/foundation/test_controls.py tests/synthesis/test_run_indistinguishability_runner.py
rg -n "normalization|EVAParser|comparability" docs/METHODS_REFERENCE.md
```

---

## WS-H3-D: Deterministic Tuning Provenance and Auditability

**Goal:** Make control tuning reproducible and skeptic-auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Implement a control-matching audit runner that logs candidate parameter sets, score vectors, and selected config per class. | `scripts/synthesis/run_control_matching_audit.py` (new) | Reproducible search trace generated with seed and policy hash. |
| D2 | Emit class-level matching cards (inputs, search budget, selected params, rejected near-misses). | `status/synthesis/control_matching_cards/*.json` (new) | Each control class has a deterministic card artifact. |
| D3 | Add high-level audit summary consumed by release/reporting paths. | `status/synthesis/CONTROL_COMPARABILITY_STATUS.json` | Summary includes comparability grade and blockers. |

### Verification

```bash
python3 scripts/synthesis/run_control_matching_audit.py --preflight-only
python3 - <<'PY'
import json
d = json.load(open('status/synthesis/CONTROL_COMPARABILITY_STATUS.json'))
print(d.get('status'), d.get('comparability_grade'))
PY
```

---

## WS-H3-E: Adversarial Comparability Stress Checks

**Goal:** Demonstrate that conclusions are robust on untuned checks and uncertainty-aware.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add holdout-based comparability stress battery (not used in tuning). | `src/synthesis/indistinguishability.py`, `scripts/synthesis/run_indistinguishability_test.py` | Holdout pass/fail included in final status. |
| E2 | Add uncertainty reporting (bootstrap CIs and/or permutation diagnostics) for key separation claims. | same + report outputs | Comparability claims include uncertainty envelope and not just point estimates. |
| E3 | Add fail-closed status mapping for underpowered or leakage-tainted outcomes. | `status/synthesis/CONTROL_COMPARABILITY_STATUS.json` + script logic | Conclusive labels blocked when comparability evidence is insufficient. |

### Verification

```bash
python3 scripts/synthesis/run_indistinguishability_test.py --preflight-only
rg -n "holdout|bootstrap|permutation|comparability_grade|leakage" \
  status/synthesis/CONTROL_COMPARABILITY_STATUS.json \
  status/synthesis/TURING_TEST_RESULTS.json
```

---

## WS-H3-F: Reporting and Narrative Alignment

**Goal:** Ensure public and technical docs cannot overstate control-based inference quality.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Update generator matching doc to explicitly distinguish "fit objective" vs "inference objective." | `docs/GENERATOR_MATCHING.md` | No wording implies tuned-metric reuse as independent evidence. |
| F2 | Add explicit SK-H3 comparability section in methodology and reproducibility docs. | `docs/METHODS_REFERENCE.md`, `docs/REPRODUCIBILITY.md` | Operators can reproduce comparability checks end-to-end. |
| F3 | Add skeptic execution status template for SK-H3 remediation tracking. | `reports/skeptic/SKEPTIC_H3_EXECUTION_STATUS.md` (during execution) | Findings-to-fixes traceability is auditable. |

### Verification

```bash
rg -n "comparability|holdout|target leakage|normalization symmetry|SK-H3" \
  docs/GENERATOR_MATCHING.md \
  docs/METHODS_REFERENCE.md \
  docs/REPRODUCIBILITY.md \
  reports/skeptic
```

---

## WS-H3-G: Policy Guardrails and CI Enforcement

**Goal:** Prevent regression into unbounded tuning or asymmetry drift.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| G1 | Add SK-H3 checker validating required artifacts, marker fields, leakage flags, and banned narrative patterns. | `scripts/skeptic/check_control_comparability.py` (new) | Checker fails on policy violations. |
| G2 | Add dedicated SK-H3 tests for checker behavior and artifact schema conformance. | `tests/skeptic/test_control_comparability_checker.py` (new) | Deterministic pass/fail coverage for policy paths. |
| G3 | Integrate SK-H3 checker into CI/release checks. | `scripts/ci_check.sh`, `scripts/audit/pre_release_check.sh` | CI path enforces SK-H3 guardrails by default. |

### Verification

```bash
python3 scripts/skeptic/check_control_comparability.py
python3 -m pytest -q tests/skeptic/test_control_comparability_checker.py
```

---

## WS-H3-H: Governance and Audit Trace

**Goal:** Maintain traceability from skeptic finding to closure evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| H1 | Add SK-H3 execution trace section to audit log with decisions and residual risks. | `AUDIT_LOG.md` | Audit entry links policy, code, artifacts, and tests. |
| H2 | Add claim-boundary cross-reference when control comparability is non-conclusive. | `docs/CLAIM_BOUNDARY_POLICY.md` (if needed) | Public claims cannot exceed comparability status. |
| H3 | Add runbook note on acceptable evidence classes for control-based conclusions. | `docs/RUNBOOK.md` and/or `docs/REPRODUCIBILITY.md` | Operator guidance reflects enforced policy. |

### Verification

```bash
rg -n "SK-H3|comparability|target leakage|normalization symmetry" AUDIT_LOG.md docs
```

---

## 6) Execution Order

1. WS-H3-A (policy and contract first)
2. WS-H3-B (metric decoupling)
3. WS-H3-C (normalization symmetry closure)
4. WS-H3-D (tuning provenance and status artifacts)
5. WS-H3-E (holdout/uncertainty stress checks)
6. WS-H3-F (reporting alignment)
7. WS-H3-G (automated guardrails)
8. WS-H3-H (governance traceability)

Rationale:

- Do not run or rewrite conclusions before policy, metric partitioning, and comparability status contracts exist.

---

## 7) Decision Matrix for SK-H3 Comparability Outcome

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Match/eval split pass + normalization symmetry pass + holdout pass + uncertainty acceptable | `COMPARABLE_CONFIRMED` | "Control comparability is sufficient for bounded structural inference under current policy." |
| Core pass but one bounded caveat (for example partial normalization equivalence or borderline holdout variance) | `COMPARABLE_QUALIFIED` | "Control comparability is acceptable with explicit caveats; claims remain bounded." |
| Leakage detected OR normalization asymmetry unresolved OR required artifacts missing | `NON_COMPARABLE_BLOCKED` | "Control-based inferential claim blocked pending comparability remediation." |
| Data adequacy or compute evidence insufficient for status assignment | `INCONCLUSIVE_DATA_LIMITED` | "Comparability status inconclusive under current evidence volume." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H3-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-H3 policy doc and machine-readable configuration. |
| WS-H3-B Metric Decoupling | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added explicit matching vs holdout metric partitions and leakage fields in synthesis outputs. |
| WS-H3-C Normalization Symmetry | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added control normalization modes with parser-symmetry assertions and tests. |
| WS-H3-D Provenance/Audit Artifacts | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added deterministic control matching audit runner and class-card artifacts. |
| WS-H3-E Holdout/Uncertainty Stress | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added holdout metrics and comparability status mapping to Turing artifact flow. |
| WS-H3-F Reporting Alignment | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated matching/method/repro/runbook docs with SK-H3 constraints and workflow. |
| WS-H3-G Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-H3 checker/tests and integrated ci/release enforcement paths. |
| WS-H3-H Governance Trace | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added claim-boundary cross-policy note, audit-log trace, and execution status report. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Over-constraining match/eval separation removes legitimate comparability signal and reduces utility. | Medium | Medium | Use pre-registered policy with explicit rationale per metric class and keep holdout set minimal but independent. |
| R2 | Normalization symmetry changes alter historical baseline behavior and trigger broad metric drift. | Medium | High | Add mode-gated rollout with equivalence tests and explicit status downgrade path. |
| R3 | Provenance artifacts become large/noisy and hard to audit manually. | Medium | Medium | Add summarized comparability status artifact plus per-class cards for deep drill-down. |
| R4 | Guardrails are bypassed in ad-hoc runs, reintroducing skeptic attack surface. | Medium | High | Enforce checker in CI and pre-release scripts; require status artifact for report generation. |
| R5 | Compute cost of full comparability retesting slows iteration. | Medium | Medium | Keep `--preflight-only` and reduced-profile dry-run path for quick policy validation before full reruns. |

---

## 10) Deliverables

Required deliverables for the execution pass:

1. SK-H3 comparability policy document and machine-readable config.
2. Match-vs-evaluate metric partitioning implemented and auditable.
3. Normalization symmetry/equivalence enforcement for controls.
4. Deterministic control-tuning provenance artifacts and summary status.
5. Holdout and uncertainty-aware comparability diagnostics.
6. CI/pre-release guardrails with dedicated tests.
7. SK-H3 execution status report under `reports/skeptic/`.
