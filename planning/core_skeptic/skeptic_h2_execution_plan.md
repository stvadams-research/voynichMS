# Execution Plan: Skeptic Claim-Scope Calibration (SK-H2)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-H2` (listed as High in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. Status table and execution report reflect implementation outcomes.

---

## 1) Objective

Address `SK-H2` by aligning public-facing conclusions with the project’s bounded non-claims, so external readers cannot credibly argue that headline language overstates what the evidence supports.

This plan targets the specific contradiction identified in the assessment:

1. Non-claim boundaries exist in technical summaries.
2. Public/summary language in key files remains categorical or terminal.
3. Skeptic can claim overreach even when underlying methods are sound.

---

## 2) SK-H2 Problem Statement

From `SK-H2`:

- Bounded non-claims are present in `results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md` (`what this does not claim` section).
- Public-facing statements still include categorical language:
  - `README.md` ("Language Hypothesis Falsified")
  - `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` ("PROJECT TERMINATED (Exhaustive)", "scientifically unjustified")
  - `results/reports/FINAL_PHASE_3_3_REPORT.md` ("semantically empty procedural system")

Core core_skeptic attack:

- "You preserve non-claims in technical sections but publish categorical conclusions in headline text."

---

## 3) Scope and Non-Goals

## In Scope

- Claim-scope policy for public-facing conclusion language.
- Alignment of top-level public statements with bounded evidence.
- Claim traceability between headline conclusions and supporting artifacts.
- Automated guardrails to prevent future overreach wording regressions.
- Tests and documentation updates for the above.

## Out of Scope

- Re-running empirical experiments.
- Mechanism/model changes for SK-H1, SK-H3, or SK-M* (except minor wording dependencies).
- Historical interpretation, intent attribution, or semantic reconstruction.

---

## 4) Success Criteria (Exit Conditions)

`SK-H2` is considered closed only if all conditions below are met:

1. Public conclusions use scope-bounded language consistent with project non-claims.
2. Categorical falsification/termination wording is replaced with evidence-qualified equivalents unless explicitly justified by policy.
3. Every strong claim in targeted public docs maps to explicit supporting evidence references.
4. A canonical claim-boundary policy exists and is referenced by README/closure summaries.
5. CI/test guardrails fail on banned or unqualified claim-language patterns in tracked docs.
6. Audit trace clearly records claim-scope calibration decisions and boundaries.

---

## 5) Workstreams

## WS-H2-A: Claim Boundary Policy and Taxonomy

**Goal:** Define standardized claim strength and allowed wording by evidence class.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define claim-strength taxonomy (`CONCLUSIVE_WITHIN_SCOPE`, `QUALIFIED`, `INCONCLUSIVE`, `DEFERRED`). | `governance/CLAIM_BOUNDARY_POLICY.md` (new) | Taxonomy and examples documented. |
| A2 | Define policy exceptions and prohibited phrasing list (for public docs). | `configs/core_skeptic/sk_h2_claim_language_policy.json` (new) | Policy machine-readable and versioned. |
| A3 | Define required disclaimer/non-claim block for public summary documents. | same + docs | Required block text and placement rules are explicit. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/core_skeptic/sk_h2_claim_language_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-H2-B: Claim Inventory and Traceability Matrix

**Goal:** Build a complete map of public claims, current wording risk, and supporting evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Enumerate claims in priority docs (README, closure statements, final reports). | `reports/core_skeptic/SK_H2_CLAIM_REGISTER.md` (new) | All target claims listed with severity tags. |
| B2 | Add evidence links and boundary tags per claim. | same | Each claim has evidence refs and scope tag. |
| B3 | Mark overreach candidates requiring rewrite. | same | Remediation list is explicit and actionable. |

### Verification

```bash
rg -n "Language Hypothesis Falsified|PROJECT TERMINATED|scientifically unjustified|semantically empty" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-H2-C: Public-Facing Language Calibration

**Goal:** Rewrite over-strong claims into evidence-bounded statements without weakening core findings.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Calibrate README "Key Findings" wording to avoid categorical falsification phrasing. | `README.md` | Claims are bounded and evidence-cited. |
| C2 | Reframe closure statement from absolute terminal language to conditional framework-bounded closure. | `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md` | Reopening criteria and scope are first-class, not contradictory. |
| C3 | Rephrase final Phase 3.3 summary sentence to avoid semantic absolutism while preserving structural conclusion. | `results/reports/FINAL_PHASE_3_3_REPORT.md` | Language becomes scope-qualified and consistent with non-claims. |
| C4 | Ensure Phase 5 non-claims are referenced from calibrated public docs. | `README.md`, closure docs | Public docs explicitly point to non-claim section. |

### Verification

```bash
rg -n "falsified|PROJECT TERMINATED|scientifically unjustified|semantically empty" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md \
  results/reports/phase5_mechanism/PHASE_5_FINAL_FINDINGS_SUMMARY.md
```

---

## WS-H2-D: Evidence-Linked Conclusion Blocks

**Goal:** Prevent "headline-only" claims by requiring structured conclusion blocks tied to evidence.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Define required conclusion block template (claim, scope, evidence links, non-claim boundary). | `governance/CLAIM_BOUNDARY_POLICY.md` | Template is documented and reused. |
| D2 | Apply template to top-level conclusion documents. | `README.md`, `results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md`, `results/reports/FINAL_PHASE_3_3_REPORT.md` | Conclusion sections use uniform schema. |
| D3 | Add "what this does not claim" section where missing in public summaries. | targeted docs | Boundary text present and consistent. |

### Verification

```bash
rg -n "What this does not claim|Scope|Evidence|Boundary" \
  README.md \
  results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md \
  results/reports/FINAL_PHASE_3_3_REPORT.md
```

---

## WS-H2-E: Automated Guardrails and CI Enforcement

**Goal:** Make claim-scope policy enforceable and regression-resistant.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Add claim-policy checker script (pattern and boundary checks). | `scripts/core_skeptic/check_claim_boundaries.py` (new) | Script exits non-zero on violations. |
| E2 | Add tests for checker and known policy violations/allowances. | `tests/core_skeptic/test_claim_boundary_checker.py` (new) | Deterministic coverage for pass/fail paths. |
| E3 | Integrate checker in CI or pre-release path. | `scripts/ci_check.sh` and/or `scripts/core_audit/pre_release_check.sh` | Guard runs automatically in verification path. |
| E4 | Add allowlist phase5_mechanism for intentionally strong wording with explicit evidence tags. | policy config + checker | Exceptions are explicit and auditable. |

### Verification

```bash
python3 scripts/core_skeptic/check_claim_boundaries.py
python3 -m pytest -q tests/core_skeptic/test_claim_boundary_checker.py
```

---

## WS-H2-F: Documentation and Governance Alignment

**Goal:** Ensure contributors understand and consistently apply claim-scope rules.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Update reproducibility/governance docs with claim-boundary policy references. | `governance/governance/REPRODUCIBILITY.md`, relevant governance docs | Contributor path includes policy usage. |
| F2 | Add core_skeptic-execution summary documenting SK-H2 remediation rationale. | `reports/core_skeptic/SKEPTIC_H2_EXECUTION_STATUS.md` (during execution) | Full change log and residual risks recorded. |
| F3 | Add core_audit log entry tying wording calibration to SK-H2 finding. | `AUDIT_LOG.md` | Traceability from finding -> policy -> edits -> tests. |

### Verification

```bash
rg -n "SK-H2|claim boundary|scope|non-claim" docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-H2-A (policy/taxonomy first)
2. WS-H2-B (claim inventory and evidence mapping)
3. WS-H2-C (text calibration)
4. WS-H2-D (template/structure normalization)
5. WS-H2-E (automation and CI guardrails)
6. WS-H2-F (governance/governance traceability)

Rationale:

- Do not rewrite language before policy and traceability structure are defined.

---

## 7) Decision Matrix for SK-H2 Claim Classification

| Classification | Allowed Wording Pattern | Requirement |
|---|---|---|
| `CONCLUSIVE_WITHIN_SCOPE` | "Under tested structural diagnostics..." | Must include explicit scope limits and evidence refs. |
| `QUALIFIED` | "Evidence is consistent with..." | Must include caveat or unresolved alternatives. |
| `INCONCLUSIVE` | "Current evidence is insufficient to conclude..." | Must avoid definitive verbs. |
| `DEFERRED` | "Requires external/non-textual evidence..." | Must cite reopening criteria. |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-H2-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added claim-boundary taxonomy doc and machine-readable policy config. |
| WS-H2-B Claim Inventory | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added SK-H2 claim register with evidence links and remediation mapping. |
| WS-H2-C Language Calibration | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Calibrated README, closure statement, and final Phase 3.3 wording to scope-bounded language. |
| WS-H2-D Evidence-Linked Blocks | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added explicit non-claim/scope blocks and evidence references in public summaries. |
| WS-H2-E Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added checker script, tests, and CI invocation for claim-boundary policy enforcement. |
| WS-H2-F Docs/Governance | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated reproducibility docs, core_audit log, and core_skeptic execution status report. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Over-correction dilutes legitimate findings into vague language. | Medium | Medium | Use claim taxonomy and evidence-linked templates, not blanket softening. |
| R2 | Inconsistent edits across docs create new contradictions. | High | High | Use claim register + structured conclusion template. |
| R3 | Guardrails generate false positives on legitimate technical terms. | Medium | Medium | Add scoped allowlist and tests for accepted phrasing. |
| R4 | Future docs bypass policy and reintroduce overreach language. | Medium | High | Integrate checker into CI/pre-release and add governance references. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. `SK-H2` claim-boundary policy and machine-readable config.
2. Claim register with evidence traceability for public-facing conclusions.
3. Calibrated language in SK-H2 cited docs (`README`, closure statement, Phase 3.3 final).
4. Automated checker and tests enforcing claim-scope policy.
5. Execution status report under `reports/core_skeptic/`.
6. Audit log trace entry documenting rationale and residual risk.
