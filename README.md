# Voynich Foundation Project

## Purpose

This repository exists to build the most rigorous, assumption-aware foundation ever constructed for the study of the Voynich Manuscript.

The explicit goal is **not translation**.

The goal is to remove foundational uncertainty about what kind of system the manuscript is, so that translation becomes possible in principle, or conclusively impossible, without speculation.

Everything in this repository must justify itself by answering:

**Does this reduce uncertainty about the structure of the system, or does it merely add structure?**

If it only adds structure, it does not belong here.

---

## Current Status: AUDIT-REMEDIATED (Phases 2-7 Implemented)

The project has executable phase runners through **Phase 7** (analysis,
synthesis, mechanism, inference, and human/codicological tracks), a 
**Visualization Layer** for automated result reporting, and a 
**Publication Framework** for research drafting.

### Key Findings
1.  **Natural-language/simple-cipher hypotheses are not supported within tested diagnostics:** Mapping stability tests (0.02) and control comparisons do not isolate the manuscript as linguistic under the current framework.
2.  **Structural anomaly persists:** High information density (z=5.68) and strong locality (2-4 units) remain stable across tested analyses.
3.  **Mechanism class identified:** The manuscript is structurally consistent with a two-stage procedural system: rigid glyph-level grammar plus bounded selection pools.
4.  **Generative reconstruction bounded:** Grammar-level reconstruction succeeded, while selection dynamics remain constrained rather than fully closed.
5.  **Inference Admissibility defined:** Established that common decipherment tools yield similar confidence scores on random noise as they do on the manuscript, establishing a statistical "noise floor" for meaning claims.

See `results/reports/FINAL_REPORT_PHASE_3.md` for the full conclusion.

## Conclusion Scope

The conclusions in this repository are **framework-bounded**:

- They apply to the tested structural/computational diagnostics over currently available manuscript data.
- They establish what is and is not supported by this evidence class.
- They do not claim universal impossibility of meaning under all conceivable future evidence.

Primary boundary references:

- `results/reports/PHASE_5_FINAL_FINDINGS_SUMMARY.md`
- `results/reports/PHASE_4_5_CLOSURE_STATEMENT.md`
- `results/reports/FINAL_PHASE_3_3_REPORT.md`

## Operational Entitlement State

Canonical operational entitlement source:

- `status/audit/release_gate_health_status.json`

Current gate-health class: `GATE_HEALTH_DEGRADED`.

When gate health is degraded, claims in this repository are operationally contingent and must remain qualified/reopenable pending restored CI, pre-release, and reproduction gate integrity.

Current degraded-state dependency is the SK-C1 release sensitivity evidence contract (`status/audit/sensitivity_sweep_release.json`).

## What This Does Not Claim

This project does not claim:

- semantic reconstruction of manuscript content,
- authorial intent or fraud determinations,
- historical/cultural final interpretation,
- impossibility of any future progress with new external evidence.

## Historical Provenance Confidence

Historical run-traceability confidence is explicitly bounded and policy-governed.

- Canonical source of truth: `status/audit/provenance_health_status.json`
- Current expected class while legacy rows remain: `PROVENANCE_QUALIFIED`
- SK-M4.5 lane key in canonical artifact: `m4_5_historical_lane`
- Current expected SK-M4.5 lane while legacy orphan rows remain in-scope: `M4_5_BOUNDED`
- Compatibility mirror key retained for legacy consumers: `m4_4_historical_lane`
- Policy and allowed-claim contract: `docs/HISTORICAL_PROVENANCE_POLICY.md`
- Operational provenance mechanics: `docs/PROVENANCE.md`

This means closure claims are framework-bounded and should not be read as
claiming complete historical manifest certainty for every legacy run row.

---

## Core Principles

These principles are non-negotiable and apply to all code, data, and experiments.

- **Determinism is Mandatory:** All runs must be reproducible from a seed and
  verified via `scripts/verify_reproduction.sh` canonical result checks.
- **Computed, Not Simulated:** No placeholders allowed in final analysis (`REQUIRE_COMPUTED=1`).
- **Image Geometry is Law:** When there is disagreement, the image wins.
- **Ambiguity is Preserved:** Do not force decisions early.
- **Failures are Data:** Anomalies are valuable signals, not bugs to be squashed.
- **Provenance is First-Class:** Runner outputs are written with provenance and
  retained under run-scoped history (`by_run`) in addition to latest pointer files.

See `planning/foundation/PRINCIPLES_AND_NONGOALS.md` for the full statement.

---

## Repository Structure

The repository follows a strict "Audit-Ready" structure:

```
voynich/
├── src/                # Core library code (Foundation, Analysis, Synthesis)
├── scripts/            # Execution entry points (Phase runners)
├── tests/              # Unit, integration, and enforcement tests
├── configs/            # Canonical configuration files
├── docs/               # Technical documentation (Runbook, Architecture)
├── results/            # Human-facing reports and data
├── runs/               # Immutable execution artifacts (gitignored)
├── data/               # Raw and derived ledgers (gitignored)
└── planning/           # Governance and roadmaps
```

---

## How to Work on This Project

1.  **Read the Runbook:** `docs/RUNBOOK.md` explains how to reproduce the baseline.
2.  **Visualization:** Use the `visualization` CLI to generate plots:
    ```bash
    visualization foundation token-frequency voynich_real
    ```
3.  **Publication:** Use the assembly script to compile research drafts:
    ```bash
    python3 scripts/preparation/assemble_draft.py
    ```
4.  **Check the Rules:** `RULES_FOR_AGENTS.md` defines the strict constraints on AI and human contributors.
5.  **Enforce Standards:** All contributions must pass the CI check (`scripts/ci_check.sh`) and adhere to the `REQUIRE_COMPUTED` standard.

---

## Success Criteria

This project is successful because it produced:

- A foundation where assumptions are explicit
- Infrastructure that survives changing hypotheses
- Evidence-based conclusions about what the manuscript is (Procedural) and is not (Linguistic).

A translation was not required for success.

---

## Final Note

This repository prioritizes **epistemic discipline** over speed, novelty, or cleverness.

If something feels exciting but is not falsifiable, it is probably out of scope.
If something feels boring but reduces uncertainty, it probably belongs here.
