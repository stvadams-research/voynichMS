# Voynich Foundation Project

## Purpose

This repository exists to build the most rigorous, assumption-aware foundation ever constructed for the study of the Voynich Manuscript.

The explicit goal is **not translation**.

The goal is to remove foundational uncertainty about what kind of system the manuscript is, so that translation becomes possible in principle, or conclusively impossible, without speculation.

Everything in this repository must justify itself by answering:

**Does this reduce uncertainty about the structure of the system, or does it merely add structure?**

If it only adds structure, it does not belong here.

---

## Current Status: AUDIT-READY (Phase 3 Completed)

The project has successfully completed **Phase 2 (Analysis)** and **Phase 3 (Synthesis)**.

### Key Findings
1.  **Language Hypothesis Falsified:** Mapping stability tests (0.02) confirm the manuscript is not a natural language or simple cipher.
2.  **Structural Anomaly:** High information density (z=5.68) and strong locality (2-4 units) persist.
3.  **Mechanism Identified:** The manuscript is mechanically explainable as a two-stage procedural system: a rigid glyph-level grammar combined with a bounded selection pool.
4.  **Generative Reconstruction:** We have successfully reverse-engineered the grammar but identified that the selection process is not purely stochastic.

See `results/reports/FINAL_REPORT_PHASE_3.md` for the full conclusion.

---

## Core Principles

These principles are non-negotiable and apply to all code, data, and experiments.

- **Determinism is Mandatory:** All runs must be reproducible from a seed.
- **Computed, Not Simulated:** No placeholders allowed in final analysis (`REQUIRE_COMPUTED=1`).
- **Image Geometry is Law:** When there is disagreement, the image wins.
- **Ambiguity is Preserved:** Do not force decisions early.
- **Failures are Data:** Anomalies are valuable signals, not bugs to be squashed.

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
2.  **Check the Rules:** `RULES_FOR_AGENTS.md` defines the strict constraints on AI and human contributors.
3.  **Enforce Standards:** All contributions must pass the CI check (`scripts/ci_check.sh`) and adhere to the `REQUIRE_COMPUTED` standard.

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