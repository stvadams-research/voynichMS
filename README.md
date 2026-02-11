# Voynich Foundation Project

## Purpose

This repository exists to build the most rigorous, assumption-aware foundation ever constructed for the study of the Voynich Manuscript.

The explicit goal is **not translation**.

The goal is to remove foundational uncertainty about what kind of system the manuscript is, so that translation becomes possible in principle, or conclusively impossible, without speculation.

Everything in this repository must justify itself by answering:

**Does this reduce uncertainty about the structure of the system, or does it merely add structure?**

If it only adds structure, it does not belong here.

---

## Current Status: AUDIT-REMEDIATED

The project has executable phase runners through **Phase 9**, an automated **Visualization Layer**, and a **Publication Framework** for academic-grade reporting.

### Research Phases
1.  **Phase 1 (Foundation)**: Digital ledgering and data integrity.
2.  **Phase 2 (Analysis)**: Admissibility and formal model exclusion.
3.  **Phase 3 (Synthesis)**: Structural sufficiency and generative reconstruction.
4.  **Phase 4 (Inference)**: Method evaluation and false-positive "noise floor" mapping.
5.  **Phase 5 (Mechanism)**: Identification of the Implicit Constraint Lattice.
6.  **Phase 6 (Functional)**: Algorithmic efficiency and ergonomic optimization.
7.  **Phase 7 (Human)**: Physical scribe constraints and codicology.
8.  **Phase 8 (Comparative)**: Proximity to historical mechanical artifacts.
9.  **Phase 9 (Conjecture)**: Speculative synthesis and Algorithmic Glossolalia.

### Key Findings
1.  **Natural-language/simple-cipher hypotheses are not supported:** Mapping stability tests (0.02) and control comparisons do not isolate the manuscript as linguistic.
2.  **Mechanism class identified:** The manuscript is identified as a Globally Stable, Deterministic Rule-Evaluated Constraint Lattice.
3.  **Inference Admissibility defined:** Established a statistical "noise floor" proving that standard decipherment tools find "meaning" in random noise as easily as in the manuscript.

---

## Master Replication & Publication

This project is built for total transparency. You can recreate the entire research lifecycle—from raw scans to a 30-page research summary—using a single command:

```bash
python3 scripts/support_preparation/replicate_all.py
```

### Manual Generation
*   **Definitive Research Paper (30-40+ Pages)**: `.venv/bin/python3 scripts/support_preparation/generate_definitive_paper.py`
*   **Full Publication (Word)**: `python3 scripts/support_preparation/generate_publication.py`
*   **Individual Phase Report**: `python3 scripts/support_preparation/generate_publication.py --phase [1-9]`
*   **Markdown Master**: `python3 scripts/support_preparation/assemble_draft.py`

Outputs are saved to `results/publication/`.

---

## How to Work on This Project

1.  **Read the Runbook:** `governance/runbook.md` explains how to reproduce the baseline.
2.  **Visualization:** Use the `visualization` CLI to generate plots:
    ```bash
    visualization foundation token-frequency voynich_real
    ```
3.  **Enforce Standards:** All contributions must pass the CI check (`scripts/ci_check.sh`) and adhere to the `REQUIRE_COMPUTED` standard.
4.  **Check the Rules:** `RULES_FOR_AGENTS.md` defines the strict constraints on AI and human contributors.

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
