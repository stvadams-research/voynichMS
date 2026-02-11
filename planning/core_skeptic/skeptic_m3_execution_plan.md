# Execution Plan: Skeptic Documentation-Coherence Hardening (SK-M3)

**Source Assessment:** `reports/core_skeptic/ADVERSARIAL_SKEPTIC_ASSESSMENT_2026-02-10.md`  
**Finding Target:** `SK-M3` (listed as Medium in source; treated here as critical-path hardening)  
**Plan Date:** 2026-02-10  
**Execution Policy:** Executed on 2026-02-10. This plan now serves as implementation and verification trace.

---

## 1) Objective

Address `SK-M3` by eliminating internal report-status contradictions so summary determinations, method tables, and status labels are coherent and auditable.

This plan targets the specific inconsistency identified in the assessment:

1. A report can state full completion and final determination.
2. The same report can still include residual "PENDING" method rows.
3. A core_skeptic can frame this as self-contradiction and undermine higher-level conclusions.

---

## 2) SK-M3 Problem Statement

From `SK-M3`:

- `results/reports/phase4_inference/PHASE_4_RESULTS.md` gives a full final determination but still includes a residual "PENDING" status table for methods B-E in `results/reports/phase4_inference/PHASE_4_RESULTS.md:160` through `results/reports/phase4_inference/PHASE_4_RESULTS.md:163`.

Core core_skeptic attack:

- "If your own report contradicts itself, why trust stronger claims?"

Primary contradiction locus:

- `results/reports/phase4_inference/PHASE_4_RESULTS.md` (final determination + stale pending table).

Secondary coherence dependencies to verify during execution:

- `results/reports/phase4_inference/PHASE_4_CONCLUSIONS.md`
- `results/reports/phase4_inference/PHASE_4_5_METHOD_CONDITION_MAP.md`
- `results/reports/phase4_inference/PHASE_4_METHOD_MAP.md`
- downstream references that inherit Phase 4 status language.

---

## 3) Scope and Non-Goals

## In Scope

- Report-status coherence policy (status vocabulary, allowed transitions, archival labeling).
- Cross-document consistency between method outcomes and phase-level determinations.
- Remediation of stale residual status blocks in Phase 4 reporting artifacts.
- Canonical status index for method-level completion/admissibility state.
- Automated checks to prevent contradictory status language in tracked docs.
- Governance/core_audit traceability for SK-M3 coherence decisions.

## Out of Scope

- Re-running phase4_inference experiments to change quantitative method outcomes.
- Re-adjudicating SK-C1/SK-H1/SK-H2/SK-H3/SK-M1/SK-M2 evidence classes.
- Semantic-claim expansion beyond existing admissibility boundaries.
- Major report-style redesign unrelated to coherence and status consistency.

---

## 4) Success Criteria (Exit Conditions)

`SK-M3` is considered closed only if all criteria below are met:

1. No tracked report simultaneously states final determination and unresolved `PENDING` method states without explicit archival framing.
2. Phase 4 method status tables are mutually consistent across tracked reports.
3. A canonical status vocabulary and transition policy are documented and machine-checkable.
4. Tracked docs include required coherence markers (for example, "archival snapshot" where legacy state is intentionally preserved).
5. CI/release checks fail on contradictory status patterns in tracked files.
6. Audit trail links SK-M3 finding -> policy -> report edits -> verification outcomes.

---

## 5) Workstreams

## WS-M3-A: Report Coherence Policy and Taxonomy

**Goal:** Define how report-status statements are allowed to coexist.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| A1 | Define status taxonomy (for example `COMPLETE`, `ARCHIVAL_SNAPSHOT`, `SUPERSEDED`, `IN_PROGRESS`). | `governance/REPORT_COHERENCE_POLICY.md` (new) | Status classes and examples documented. |
| A2 | Define contradiction patterns (final determination + unresolved pending rows) and allowed exceptions. | `configs/core_skeptic/sk_m3_report_coherence_policy.json` (new) | Machine-readable policy created and versioned. |
| A3 | Define required markers for archival/legacy blocks to prevent ambiguity. | same + docs | Marker contract documented for tracked reports. |

### Verification

```bash
python3 - <<'PY'
import json
p=json.load(open('configs/core_skeptic/sk_m3_report_coherence_policy.json'))
print(sorted(p.keys()))
PY
```

---

## WS-M3-B: Contradiction Inventory and Register

**Goal:** Build an auditable register of coherence contradictions and remediations.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| B1 | Inventory status-bearing tables/sections in tracked Phase 4 artifacts. | `reports/core_skeptic/SK_M3_COHERENCE_REGISTER.md` (new) | All tracked status blocks listed. |
| B2 | Classify each block as consistent, stale, or intentionally archival. | same | Each row has explicit coherence status. |
| B3 | Map remediation action and owner/path for each stale contradiction. | same | Actionable remediation queue established. |

### Verification

```bash
rg -n "PENDING|COMPLETE|DETERMINATION|Final Conclusion|Status" \
  results/reports/phase4_inference/PHASE_4_RESULTS.md \
  results/reports/phase4_inference/PHASE_4_CONCLUSIONS.md \
  results/reports/phase4_inference/PHASE_4_5_METHOD_CONDITION_MAP.md
```

---

## WS-M3-C: Phase 4 Report Normalization

**Goal:** Remove or explicitly reframe contradictory status sections.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| C1 | Remediate contradictory residual status table in `PHASE_4_RESULTS.md`. | `results/reports/phase4_inference/PHASE_4_RESULTS.md` | No unresolved stale `PENDING` rows conflict with final determination. |
| C2 | Harmonize status language between Phase 4 result/conclusion artifacts. | `results/reports/phase4_inference/PHASE_4_CONCLUSIONS.md`, `results/reports/phase4_inference/PHASE_4_5_METHOD_CONDITION_MAP.md` | Method-state framing is consistent across docs. |
| C3 | Add explicit archival labels where legacy tables are retained for historical traceability. | same | Legacy intent is explicit and non-contradictory. |
| C4 | Ensure final conclusion wording references canonical method-state source. | same + supporting docs | Single source of truth linkage added. |

### Verification

```bash
rg -n "PENDING|ARCHIVAL_SNAPSHOT|SUPERSEDED|DETERMINATION|Final Conclusion" \
  results/reports/phase4_inference/PHASE_4_RESULTS.md \
  results/reports/phase4_inference/PHASE_4_CONCLUSIONS.md \
  results/reports/phase4_inference/PHASE_4_5_METHOD_CONDITION_MAP.md
```

---

## WS-M3-D: Canonical Method-Status Index

**Goal:** Create a single machine-readable status artifact for report consumers.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| D1 | Define canonical Phase 4 method status schema. | `results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json` (new) | Schema + status rows are present and parseable. |
| D2 | Populate method-level outcome and coherence metadata (method, determination, status_source, last_reviewed). | same | All methods A-E included with coherent status fields. |
| D3 | Link docs to canonical status index to reduce table drift. | `results/reports/phase4_inference/PHASE_4_RESULTS.md`, related docs | Docs reference status index as source of truth. |

### Verification

```bash
python3 - <<'PY'
import json
d=json.load(open('results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json'))
print(sorted(d.keys()), len(d.get('methods', [])))
PY
```

---

## WS-M3-E: Automated Coherence Guardrails

**Goal:** Prevent future report-status contradictions.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| E1 | Implement SK-M3 checker for contradictory status patterns and required coherence markers. | `scripts/core_skeptic/check_report_coherence.py` (new) | Checker exits non-zero on SK-M3 violations. |
| E2 | Add SK-M3 checker tests (pass/fail/allowlist/artifact-schema). | `tests/core_skeptic/test_report_coherence_checker.py` (new) | Deterministic policy coverage exists. |
| E3 | Integrate SK-M3 checker into CI/release scripts. | `scripts/ci_check.sh`, `scripts/core_audit/pre_release_check.sh` | Guard runs automatically in ci/release modes. |

### Verification

```bash
python3 scripts/core_skeptic/check_report_coherence.py --mode ci
python3 scripts/core_skeptic/check_report_coherence.py --mode release
python3 -m pytest -q tests/core_skeptic/test_report_coherence_checker.py
```

---

## WS-M3-F: Governance and Audit Traceability

**Goal:** Ensure SK-M3 coherence decisions remain durable and auditable.

| ID | Task | Target Artifacts | Completion Signal |
|---|---|---|---|
| F1 | Add SK-M3 section to reproducibility/governance docs with coherence verification commands. | `governance/governance/REPRODUCIBILITY.md` | SK-M3 verification path documented. |
| F2 | Add SK-M3 execution status report template for remediation pass. | `reports/core_skeptic/SKEPTIC_M3_EXECUTION_STATUS.md` (during execution) | Full change/test trace recorded. |
| F3 | Add core_audit log entry mapping SK-M3 finding to coherence controls and residual risk. | `AUDIT_LOG.md` | End-to-end traceability present. |

### Verification

```bash
rg -n "SK-M3|report coherence|PHASE_4_STATUS_INDEX|check_report_coherence" \
  docs reports AUDIT_LOG.md
```

---

## 6) Execution Order

1. WS-M3-A (policy and taxonomy first)
2. WS-M3-B (contradiction inventory and register)
3. WS-M3-C (Phase 4 report normalization)
4. WS-M3-D (canonical method-status index)
5. WS-M3-E (automated guardrails)
6. WS-M3-F (governance and core_audit traceability)

Rationale:

- Do not edit report language before status taxonomy and contradiction rules are defined.

---

## 7) Decision Matrix for SK-M3 Coherence Status

| Condition | Output Status | Allowed Claim |
|---|---|---|
| Final determinations and method-status tables are aligned with canonical status index and markers | `COHERENCE_ALIGNED` | "Report status and conclusions are internally coherent and policy-compliant." |
| Minor non-blocking legacy caveats remain but are explicitly archival-labeled | `COHERENCE_QUALIFIED` | "Coherence is largely resolved with explicit archival caveats." |
| Any tracked report contains unresolved contradictory final vs pending status patterns | `COHERENCE_BLOCKED` | "Coherence claim blocked until contradictory status blocks are remediated." |
| Status evidence is incomplete to assign alignment confidently | `INCONCLUSIVE_COHERENCE_SCOPE` | "Coherence status remains provisional pending complete artifact alignment." |

---

## 8) Detailed Status Tracker

| Workstream | Status | Owner | Start | End | Notes |
|---|---|---|---|---|---|
| WS-M3-A Policy/Taxonomy | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added taxonomy policy and machine-readable config. |
| WS-M3-B Inventory/Register | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added coherence contradiction register for Phase 4 status-bearing blocks. |
| WS-M3-C Report Normalization | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Removed contradictory pending rows and aligned status language across Phase 4 docs. |
| WS-M3-D Status Index | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Added canonical `PHASE_4_STATUS_INDEX.json` and linked all tracked docs. |
| WS-M3-E Guardrails/CI | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Implemented checker/tests and integrated checks into CI and pre-release scripts. |
| WS-M3-F Governance/Audit | COMPLETE | Codex | 2026-02-10 | 2026-02-10 | Updated reproducibility docs, execution status report, and core_audit log traceability. |

Status vocabulary: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `COMPLETE`.

---

## 9) Risk Register

| Risk ID | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Removing legacy tables could lose historical context needed for provenance. | Medium | Medium | Preserve legacy content with explicit archival markers and canonical index references. |
| R2 | Coherence edits in one report may diverge from linked reports. | High | High | Use contradiction register plus canonical status index as source of truth. |
| R3 | Guardrails may flag legitimate historical notes as contradictions. | Medium | Medium | Add scoped allowlist with tests and archival marker exceptions. |
| R4 | Coherence fixes might unintentionally alter substantive conclusions. | Low | High | Limit edits to status framing and trace all changes in SK-M3 execution report. |
| R5 | Future report edits reintroduce stale status blocks. | Medium | High | Integrate SK-M3 checker in CI and pre-release gates. |

---

## 10) Deliverables

Required deliverables for execution pass:

1. SK-M3 report-coherence policy and machine-readable config.
2. SK-M3 coherence register mapping contradictions to remediation actions.
3. Remediated Phase 4 core_status/coherence language across tracked reports.
4. Canonical Phase 4 method-status index artifact.
5. SK-M3 checker and tests integrated into CI/release checks.
6. SK-M3 execution status report under `reports/core_skeptic/`.
7. Audit log entry documenting SK-M3 decisions and residual risk.
