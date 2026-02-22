[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18651595.svg)](https://doi.org/10.5281/zenodo.18651595)

# Voynich Foundation Project

## Purpose

This repository exists to build the most rigorous, assumption-aware foundation ever constructed for the study of the Voynich Manuscript.

The explicit goal is **not translation**.

The goal is to remove foundational uncertainty about what kind of system the manuscript is, so that translation becomes possible in principle, or conclusively impossible, without speculation.

Everything in this repository must justify itself by answering:

**Does this reduce uncertainty about the structure of the system, or does it merely add structure?**

If it only adds structure, it does not belong here.

---

## Current Status: 18 Release-Canonical Phases Complete

The project has executable phase runners through **Phase 20**, an automated
**Visualization Layer**, and a **Publication Framework** for academic-grade reporting.

Release-canonical replication currently includes **Phases 1-17 and Phase 20**.
Exploratory extensions (Phases 18-19) are implemented but remain outside the
default release-canonical replication contract. See
[governance/RELEASE_SCOPE.md](governance/RELEASE_SCOPE.md).

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
10. **Phase 10 (Admissibility Retest)**: Adversarial re-testing of closure via
    Methods F/G/H/I/J/K, including external grounding and reverse-mechanism search.
11. **Phase 11 (Stroke Topology)**: Fast-kill glyph-stroke extraction, clustering,
    and transition analysis testing whether stroke patterns break the lattice model.
12. **Phase 12 (Mechanical Reconstruction)**: Large-scale detection of vertical eye-slips and physical columnar reconstruction.
13. **Phase 13 (Interactive Demonstration)**: Interactive "Mechanical Sandbox" and Evidence Gallery generation.
14. **Phase 14 (Voynich Engine)**: Reconstructing the full physical device (grille/volvelle) achieving 43.44% drift admissibility and 87.60% mirror corpus entropy fit.
15. **Phase 15 (Rule Formalization)**: Extraction of the declarative rule table and choice stream instrumentation.
16. **Phase 16 (Physical Grounding)**: Ergonomic and geometric verification of the 10x5 sliding grille.
17. **Phase 17 (Finality)**: Physical synthesis (blueprints) and steganographic bandwidth boundary mapping.
18. **Phase 18 (Comparative Signature Program)**: Cross-corpus structural signature definition and discrimination.
19. **Phase 19 (Alignment Evaluation)**: Line-conditioned and retrieval-edit baselines against held-out folios.
20. **Phase 20 (State Machine Architecture)**: Tabula+codebook production model synthesis and physical plausibility ranking.

### Key Findings
1.  **Natural-language/simple-cipher hypotheses are not supported:** Mapping stability tests (0.02) and control comparisons do not isolate the manuscript as linguistic.
2.  **Mechanism class identified:** The manuscript is identified as a Globally Stable, Deterministic Rule-Evaluated Constraint Lattice.
3.  **Inference Admissibility defined:** Established a statistical "noise floor" proving that standard decipherment tools find "meaning" in random noise as easily as in the manuscript.
4.  **The "Voynich Engine" Reconstructed:** Rebuilt the physical tool (LMWS) that generates the manuscript. Achieved 43.44% drift admissibility (±1 window) with MDL: Lattice 12.37 BPT vs Copy-Reset 10.90 BPT.
5.  **Selection Rules Extracted (Phase 15):** Bigram context is the top driver of token selection at 2.43 bits, explaining 21.49% selection skew within the lattice windows.
6.  **Physical Grounding Tested (Phase 16):** Ergonomic coupling is null (rho approx. 0), ruling out motor-habit explanations; geometric layout efficiency is 81.50%.
7.  **Finality Achieved:** The manuscript is documented as a non-semantic mechanical artifact, with a formal specification for its reproduction.

---

## Master Replication & Publication

This project is built for total transparency. You can recreate the entire research lifecycle—from raw scans to a 100-page research summary—using a single command:

```bash
python3 scripts/support_preparation/replicate_all.py
```

The runner is manifest-driven (`configs/project/phase_manifest.json`) and
defaults to release-canonical phases (1-17, 20). To include exploratory phases
(18-19), run:

```bash
python3 scripts/support_preparation/replicate_all.py --include-exploratory
```

### Manual Generation
*   **Full Publication (Word)**: `python3 scripts/support_preparation/generate_publication.py --profile full`
*   **Research Summary (Word)**: `python3 scripts/support_preparation/generate_publication.py --profile summary`
*   **Technical Publication (Word)**: `python3 scripts/support_preparation/generate_publication.py --profile technical`

Outputs are saved to `results/publication/`.

---

## Quick Start

```bash
# 1. Clone and set up environment
git clone <repo-url> && cd voynichMS
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt

# 2. Download external data (~50 MB transliterations + ~5 MB corpora)
python3 scripts/phase0_data/download_external_data.py

# 3. Populate the database (~5-15 min)
python3 scripts/phase1_foundation/populate_database.py

# 4. Run full replication (18 release-canonical phases, ~4-8 hours)
python3 scripts/support_preparation/replicate_all.py

# 5. Verify determinism (optional, re-runs key phases twice and compares)
bash scripts/verify_reproduction.sh
```

Results appear in `results/data/` (JSON artifacts) and `results/reports/` (Markdown).
See [replicateResults.md](replicateResults.md) for detailed reproduction instructions.

> **Transcription standard:** All analysis uses the Zandbergen-Landini (ZL)
> transcription in EVA lowercase encoding. See [DATA_SOURCES.md](DATA_SOURCES.md)
> for details.

---

## Data Sources

The raw manuscript scans, transliteration files, and external corpora are too large
to commit. The automated downloader (`scripts/phase0_data/download_external_data.py`)
fetches transliterations and corpora. Yale manuscript scans (7+ GB) require manual
download — see [DATA_SOURCES.md](DATA_SOURCES.md) for full instructions and expected
directory layout.

---

## Project Documentation

| Document | Purpose |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System overview, data flow, DB schema, core components |
| [PHASE_DEPENDENCIES.md](PHASE_DEPENDENCIES.md) | Phase dependency graph, minimum subsets, execution times |
| [replicateResults.md](replicateResults.md) | Step-by-step external reproduction instructions |
| [DATA_SOURCES.md](DATA_SOURCES.md) | External data sources, download instructions, checksums |
| [governance/glossary.md](governance/glossary.md) | 50+ domain terms (manuscript, analysis, infrastructure) |
| [governance/methods_reference.md](governance/methods_reference.md) | Statistical methods and formal test designs |
| [governance/runbook.md](governance/runbook.md) | Operational procedures for running the pipeline |
| [governance/claim_artifact_map.md](governance/claim_artifact_map.md) | Maps 154 tracked claims (154 fully verifiable) to artifact paths |
| [governance/RELEASE_SCOPE.md](governance/RELEASE_SCOPE.md) | Defines release-canonical (Phases 1-17 and 20) vs exploratory scope |
| [governance/THRESHOLDS_RATIONALE.md](governance/THRESHOLDS_RATIONALE.md) | Why each threshold/parameter has its value |
| [governance/PAPER_CODE_CONCORDANCE.md](governance/PAPER_CODE_CONCORDANCE.md) | Paper sections mapped to code and scripts |
| [governance/PHASE_10_METHODS_SUMMARY.md](governance/PHASE_10_METHODS_SUMMARY.md) | Phase 10 adversarial methods: designs, outcomes |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines and standards |
| [RULES_FOR_AGENTS.md](RULES_FOR_AGENTS.md) | Constraints on AI and human contributors |

---

## How to Work on This Project

1.  **Understand the architecture:** Read [ARCHITECTURE.md](ARCHITECTURE.md) for system design and [governance/glossary.md](governance/glossary.md) for domain terminology.
2.  **Read the Runbook:** [governance/runbook.md](governance/runbook.md) explains how to reproduce the baseline.
3.  **Visualization:** Use the visualization CLI to generate plots:
    ```bash
    python3 -m support_visualization.cli.main foundation token-frequency voynich_real
    ```
4.  **Enforce Standards:** All contributions must pass the CI check (`scripts/ci_check.sh`) and adhere to the `REQUIRE_COMPUTED` standard.
5.  **Check the Rules:** [RULES_FOR_AGENTS.md](RULES_FOR_AGENTS.md) defines the strict constraints on AI and human contributors.

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


## Associated Paper

**Structural Identification of the Voynich Manuscript: An Assumption-Resistant Framework for Non-Semantic Analysis**

Preprint DOI: https://zenodo.org/records/18651937

Citation:

Adams, Steven A. (2026). *Structural Identification of the Voynich Manuscript: An Assumption-Resistant Framework for Non-Semantic Analysis*. Zenodo. https://zenodo.org/records/18651937


## Archived Software Release

This repository is permanently archived at:

https://doi.org/10.5281/zenodo.18651596

The Zenodo archive corresponds to software release `v1.0.1` and supports full reproducibility of the associated paper.
