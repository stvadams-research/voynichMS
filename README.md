# Voynich Foundation Project

## Purpose

This repository exists to build the most rigorous, assumption-aware foundation ever constructed for the study of the Voynich Manuscript.

The explicit goal is **not translation**.

The goal is to remove foundational uncertainty about what kind of system the manuscript is, so that translation becomes possible in principle, or conclusively impossible, without speculation.

Everything in this repository must justify itself by answering:

Does this reduce uncertainty about the structure of the system, or does it merely add structure?

If it only adds structure, it does not belong here.

---

## Core Principles

These principles are non-negotiable and apply to all code, data, and experiments.

- Image geometry is the highest authority.
- Transliterations are third-party indices, never ground truth.
- Ambiguity is preserved, not resolved.
- Failures and anomalies are first-class data.
- Scale boundaries are enforced by design.
- Negative controls are mandatory.
- No irreversible decisions are made early.

See `planning/foundation/PRINCIPLES_AND_NONGOALS.md` for the full statement.

---

## What This Project Is Not

This repository does **not** attempt:

- Translation
- Language identification
- Phonetic interpretation
- Entropy comparison to known languages
- Symbol inventories
- Alphabet discovery
- Semantic labeling

Those activities may be enabled later, but they are explicitly out of scope here.

---

## Project Architecture

The project is divided into two distinct phases to maintain epistemic discipline:

### Phase 1: Foundation (`foundation/`)
Constructs a rigorous, assumption-aware substrate. This phase is governed by a strict 7-level roadmap (Levels 0–6) designed to create a verifiable ledger of the manuscript's physical and geometric reality without interpretive bias.
- **Goal**: Deterministic, queryable evidence.
- **Status**: Infrastructure established; Level 1 (Data & Identity) active.

### Phase 2: Analysis (`analysis/`)
Enables interpretive research, hypothesis testing, and inference. This layer consumes the Foundation substrate to test specific structural and linguistic hypotheses.
- **Goal**: Falsifiable interpretation and inference.
- **Status**: Planning and Enablement.

See `planning/foundation/MASTER_ROADMAP.md` for the detailed Level 0–6 progression.

---

## Repository Structure

```
voynich/
├── planning/
│   ├── foundation/         # Phase 1 Governance & Roadmaps
│   └── analysis/           # Phase 2 Research Plans (Pending)
├── status/
│   ├── foundation/         # Phase 1 Completion Status
│   └── analysis/           # Phase 2 Progression (Pending)
├── src/
│   ├── foundation/         # Phase 1: Immutable Substrate
│   ├── analysis/           # Phase 2: Interpretive Layer
│   └── voynich/            # Deprecated Compatibility Shim
├── tests/
│   ├── foundation/         # Foundation Unit & Logic Tests
│   │   ├── dataset/        # Canonical Foundation Test Substrate
│   │   └── dataset_2b/     # Multi-ledger test data
│   └── analysis/           # Analysis & Hypothesis Tests
├── configs/                # Shared Environment Configuration
├── data/                   # Shared Data (Gitignored)
├── runs/                   # Execution Provenance (Gitignored)
└── scripts/                # Shared Utilities & Maintenance
```

---

## Current Focus

The project has transitioned into **Phase 2 Enablement**. 

While work continues to solidify **Phase 1: Level 1 (Data and Identity Foundation)**, the architectural split now allows for the parallel planning of **Phase 2: Analysis** modules without risking the integrity of the foundational evidence.

---

## How to Work on This Project

1. **Understand the Boundary**: Determine if your task belongs in the **Foundation** (infrastructure/evidence) or **Analysis** (interpretation/hypothesis).
2. **Consult the Phase Docs**:
   - For Foundation work: Read `planning/foundation/PRINCIPLES_AND_NONGOALS.md`.
   - For Analysis work: Consult the upcoming Analysis charter.
3. **Respect the Shim**: New code should import directly from `foundation` or `analysis`. Do not use the `voynich` shim for new development.

---

## Success Criteria

This project is successful if it produces:

- A foundation where assumptions are explicit
- Infrastructure that survives changing hypotheses
- Data products that enable translation without forcing it
- Evidence-based conclusions about what the manuscript is, or is not

A translation is not required for success.

---

## Final Note

This repository prioritizes **epistemic discipline** over speed, novelty, or cleverness.

If something feels exciting but is not falsifiable, it is probably out of scope.

If something feels boring but reduces uncertainty, it probably belongs here.
