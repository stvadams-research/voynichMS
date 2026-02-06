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

See `PRINCIPLES_AND_NONGOALS.md` for the full statement.

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

## High-Level Roadmap

The work is organized into strict levels with defined entry and exit criteria.

- Level 0: Governing principles and safety rails
- Level 1: Data and identity foundation
- Level 2A: Text ledger (geometry-first, transcription-aligned)
- Level 2B: Region ledger (visual grammar of pages)
- Level 3: Negative controls and baselines
- Level 4: Cross-ledger integration
- Level 5: Measurement and decision gates
- Level 6: Hypothesis modules (plug-in only)

Only one level should be actively implemented at a time.

See `MASTER_ROADMAP.md` for the authoritative plan.

---

## Repository Structure

```
voynich/
├── README.md
├── MASTER_ROADMAP.md
├── PRINCIPLES_AND_NONGOALS.md
├── pyproject.toml
│
├── src/
│   ├── core/
│   ├── storage/
│   ├── runs/
│   ├── qc/
│   ├── cli/
│   │
│   ├── ledger_text/
│   ├── ledger_region/
│   ├── integrate/
│   └── experiments/
│
├── configs/
├── data/
│   ├── raw/
│   ├── derived/
│   └── qc/
│
├── runs/
├── scripts/
└── tests/
```

Empty directories are intentional. They act as guardrails against premature work.

---

## Transliterations

Transliterations are treated as **external interpretive artifacts**, not as truth.

- Stored under `data/raw/transcriptions/`
- Parsed via adapters in `src/transcriptions/`
- Always associated with a `source_id`
- Multiple transliterations may coexist
- Never normalized, corrected, or merged

They exist only to support alignment and indexing.

---

## Current Status

The project is currently focused on **Level 1: Data and Identity Foundation**.

No segmentation, transcription parsing, or visual analysis should occur until Level 1 is complete and validated.

---

## How to Work on This Project

Before writing code:

1. Read `PRINCIPLES_AND_NONGOALS.md`
2. Read `MASTER_ROADMAP.md`
3. Identify the current active level
4. Confirm the task belongs to that level

If you are unsure where something belongs, it probably does not belong yet.

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
