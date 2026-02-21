# Architecture

How the VoynichMS codebase is organized, how data flows through it, and how
the major components interact.

For terminology, see [governance/glossary.md](governance/glossary.md).
For reproduction instructions, see [replicateResults.md](replicateResults.md).

---

## System Overview

```
  External Data               Foundation Layer              Analysis Phases
  ============               ================              ===============

  IVTFF files ──►  EVAParser ──► MetadataStore ──► Phase 2  (Admissibility)
  (ZL3b-n.txt)        │              │  (SQLite)      Phase 3  (Synthesis)
                       │              │                Phase 4  (Inference)
  Yale scans ───► Segmentation ──►   │                Phase 5  (Mechanism)
  (JPEG/TIFF)     (pages/lines/      │                Phase 6  (Functional)
                   words/glyphs)     │                Phase 7  (Human Factors)
                       │              │                Phase 8  (Comparative)
  Gutenberg ────► External ─────►    │                Phase 10 (Admissibility Retest)
  corpora          Corpora           │                Phase 11 (Stroke Topology)
                                     │                    │
                                     │                    ▼
                               results/data/         results/reports/
                               (JSON artifacts)      (Markdown reports)
                                     │
                                     ▼
                              results/publication/
                              (Word documents)
```

**Data enters** from three sources: IVTFF transliteration files, Yale
manuscript scans, and Project Gutenberg comparison corpora.

**Phase 1 (Foundation)** populates a SQLite database with parsed
transcriptions, image segmentation, and structural metadata.

**Phases 2-11** consume the database and prior phase outputs. Each phase
produces JSON result artifacts (in `results/data/`) and Markdown reports
(in `results/reports/`).

**Phase 9** is narrative synthesis only — no computation.

---

## Directory Layout

```
src/
├── phase1_foundation/       Core infrastructure (all other phases depend on this)
│   ├── core/                Models, queries, provenance, randomness, IDs, logging
│   ├── transcription/       EVAParser — IVTFF → tokens
│   ├── storage/             MetadataStore (SQLAlchemy ORM, 33 tables)
│   ├── runs/                RunManager, RunContext (experiment lifecycle)
│   ├── metrics/             RepetitionRate, ClusterTightness, etc.
│   ├── controls/            Scrambled, synthetic, self-citation, table grille
│   ├── alignment/           Word ↔ token alignment engine
│   ├── anchors/             Text ↔ region spatial linking
│   ├── regions/             Spatial region detection (grid, connected components)
│   ├── segmentation/        Page → line → word → glyph extraction
│   ├── hypotheses/          Hypothesis definitions and falsification
│   ├── decisions/           Accept/reject/hold criteria
│   └── analysis/            Sensitivity, stability, comparison
├── phase2_analysis/         Admissibility evaluation and stress tests
├── phase3_synthesis/        Generative reconstruction and indistinguishability
├── phase4_inference/        Information clustering, network analysis, NLP diagnostics
├── phase5_mechanism/        Constraint lattice identification (8 substages)
├── phase6_functional/       Formal system classification, efficiency, adversarial
├── phase7_human/            Scribe coupling, quire analysis, codicology
├── phase8_comparative/      Proximity to historical mechanical artifacts
├── phase10_admissibility/   Adversarial retest via Methods F/G/H/I/J/K
├── phase11_stroke/          Sub-glyph stroke extraction and transition analysis
└── support_visualization/   Publication-quality figure generation

scripts/
├── phase0_data/             External data download
├── phase1_foundation/       Database population, acceptance tests
├── phase2_analysis/         Admissibility stress tests
├── phase3_synthesis/        Generative reconstruction tests
├── phase4_inference/        Statistical inference analyses
├── phase5_mechanism/        Mechanism identification pilots
├── phase6_functional/       Functional characterization
├── phase7_human/            Human factors analysis
├── phase8_comparative/      Comparative classification
├── phase9_conjecture/       Publication generation (narrative only)
├── phase10_admissibility/   Adversarial retest stages
├── phase11_stroke/          Stroke topology analysis
├── support_preparation/     replicate_all.py, publication generation
├── core_audit/              Verification, golden outputs, provenance checks
└── core_skeptic/            Adversarial policy enforcement

governance/                  Policies, methods reference, glossary, runbook
configs/                     JSON threshold/parameter files
tests/                       Pytest test suite (mirrors src/ structure)
data/                        Raw data, database, external corpora (gitignored)
results/                     Output artifacts (data/, reports/, publication/)
core_status/                 Transient execution status files (gitignored)
```

---

## Core Components

### EVAParser (`phase1_foundation/transcription/parsers.py`)

The single canonical tokenization path. Parses IVTFF-format transliteration
files into structured `ParsedLine` and `ParsedToken` objects. Extracts folio
ID, line index, section, and ordered token sequences from location headers.

All downstream analysis consumes tokens produced by EVAParser — there is no
alternative tokenization path.

### MetadataStore (`phase1_foundation/storage/metadata.py`)

SQLAlchemy ORM access layer to the SQLite database (`data/voynich.db`, ~400 MB).
Provides session management and helper methods (`add_page()`, `add_dataset()`,
etc.) for all 33 tables. Uses `merge()` for upsert on deterministic IDs.

The database is regenerated from raw data — not distributed. Run
`scripts/phase1_foundation/populate_database.py` to create it.

### ProvenanceWriter (`phase1_foundation/core/provenance.py`)

Standard mechanism for writing JSON result files. Every analysis output is
wrapped in a provenance envelope:

```json
{
  "provenance": {
    "run_id": "...",
    "git_commit": "...",
    "timestamp": "...",
    "seed": 42,
    "command": "..."
  },
  "results": { ... }
}
```

### RunManager (`phase1_foundation/runs/manager.py`)

Thread-safe experiment lifecycle manager. Creates run directories under `runs/`,
captures environment (Python version, packages, git state), enforces seed
requirements under `REQUIRE_COMPUTED=1`, and records completion status.

### RandomnessController (`phase1_foundation/core/randomness.py`)

Enforces reproducibility constraints via three modes:

| Mode | Purpose | Behavior |
|---|---|---|
| FORBIDDEN | Analytical/computed paths | Any RNG call raises error |
| SEEDED | Control generation (synthesis, scrambling) | RNG allowed with explicit seed |
| UNRESTRICTED | Legacy compatibility | No enforcement |

Can patch/unpatch Python's `random` module to guard against accidental
unseeded RNG usage in analytical code.

### ComputationTracker (`phase1_foundation/config.py`)

Records whether each component's output was COMPUTED (from real data),
SIMULATED (from fallback logic), or CACHED. When `REQUIRE_COMPUTED=1`,
simulation fallbacks raise `SimulationViolationError`. Generates coverage
reports proving what was actually computed vs simulated.

---

## Database Schema

The SQLite database has 33 tables organized in 6 levels:

### Level 1: Infrastructure
| Table | Purpose | Key Columns |
|---|---|---|
| `runs` | Experiment execution records | id, timestamp, git_commit, config (JSON), status |
| `datasets` | Named page collections | id (e.g., "voynich_real"), path, checksum |
| `artifacts` | Output file records | run_id, path, type, checksum |
| `anomalies` | Flagged issues | run_id, severity, category, message |

### Level 2A: Segmentation & Transcription
| Table | Purpose | Key Columns |
|---|---|---|
| `pages` | Manuscript sides (folios) | id (e.g., "f1r"), dataset_id, width, height |
| `lines` | Horizontal text lines | page_id, line_index, bbox (JSON) |
| `words` | Space-delimited tokens | line_id, word_index, bbox, features (JSON) |
| `glyph_candidates` | Individual characters | word_id, glyph_index, bbox |
| `objects` | Detected page objects | page_id, scale (enum), geometry (JSON) |
| `transcription_sources` | Transcriber identity | id (e.g., "eva_v1"), name, citation |
| `transcription_lines` | Raw transcription text | source_id, page_id, line_index, content |
| `transcription_tokens` | Individual parsed tokens | line_id, token_index, content |

### Level 2B: Spatial Analysis
| Table | Purpose | Key Columns |
|---|---|---|
| `regions` | Spatial zones on pages | page_id, scale, method, bbox, features |
| `region_edges` | Region adjacency graph | source_id, target_id, type, weight |
| `region_embeddings` | Vector representations | region_id, model_name, vector (blob) |

### Level 3: Alignment & Metrics
| Table | Purpose | Key Columns |
|---|---|---|
| `word_alignments` | Word ↔ token links | word_id, token_id, type (1:1/1:N/N:1) |
| `glyph_alignments` | Glyph ↔ symbol links | glyph_id, symbol, score |
| `control_datasets` | Synthetic baselines | source_dataset_id, type, params, seed |
| `metric_results` | Computed measurements | run_id, dataset_id, metric_name, value |
| `metric_comparisons` | Real vs control | metric_name, real_id, control_id, significance |

### Level 4: Anchors (Text ↔ Image)
| Table | Purpose | Key Columns |
|---|---|---|
| `anchor_methods` | Linking algorithms | id, name, parameters (JSON) |
| `anchors` | Text-region scored links | page_id, source_type/id, target_type/id, score |
| `anchor_metrics` | Anchor quality measures | run_id, dataset_id, metric_name, value |

### Level 5: Structures & Decisions
| Table | Purpose | Key Columns |
|---|---|---|
| `structures` | Detected patterns | name, origin_level, status (accepted/rejected) |
| `decisions` | Recorded judgments | structure_id, decision, reasoning, evidence |
| `sensitivity_results` | Parameter sensitivity | structure_id, parameter, metric_value |

### Level 6: Hypotheses & Admissibility
| Table | Purpose | Key Columns |
|---|---|---|
| `hypotheses` | Falsifiable claims | description, status (active/falsified) |
| `hypothesis_structures` | Hypothesis ↔ structure links | (join table) |
| `hypothesis_runs` | Test outcomes | hypothesis_id, outcome (SUPPORTED/FALSIFIED) |
| `hypothesis_metrics` | Supporting measurements | hypothesis_id, metric_name, value |
| `explanation_classes` | Mechanism categories | name, status (admissible/inadmissible) |
| `admissibility_constraints` | Required/forbidden properties | class_id, constraint_type |
| `admissibility_evidence` | Evidence links | class_id, constraint_id, support_level |

---

## Execution & Reproducibility Infrastructure

### Execution Chain

```
replicate_all.py
  └── phase1/replicate.py    (populate database, acceptance tests)
  └── phase2/replicate.py    (admissibility stress tests)
  └── phase3/replicate.py    (synthesis + indistinguishability)
  └── phase4/replicate.py    (inference analyses)
  └── phase5/replicate.py    (mechanism identification)
  └── phase6/replicate.py    (functional characterization)
  └── phase7/replicate.py    (human factors)
  └── phase8/replicate.py    (comparative classification)
  └── phase9/replicate.py    (publication generation only)
  └── phase10/replicate.py   (adversarial retest, 7 stages)
  └── phase11/replicate.py   (stroke topology)
```

### Verification Chain

```
ci_check.sh                  (lint, tests, policy checks, determinism)
verify_reproduction.sh       (dual-run determinism, output comparison)
check_golden_outputs.py      (regression against known-good values)
```

### Provenance Flow

1. `RunManager.start_run()` creates a run directory and captures environment
2. `RandomnessController` enforces seeding constraints
3. `ComputationTracker` records computed vs simulated status
4. Analysis code writes results via `ProvenanceWriter.save_results()`
5. `RunContext` writes manifest (run.json, config.json, inputs.json, outputs.json)
6. `verify_reproduction.sh` strips provenance metadata and compares result payloads

---

## Key Design Decisions

1. **Single tokenization path:** All text analysis flows through EVAParser
   using the `ZL3b-n.txt` transliteration. No alternative parsers exist.

2. **Database as shared state:** All phases read from and write to the same
   SQLite database. This ensures consistency but means Phase 1 must complete
   before any other phase can run.

3. **Provenance-wrapped outputs:** Every JSON result file includes provenance
   metadata (run ID, git commit, seed). The `verify_reproduction.sh` script
   strips this metadata for comparison.

4. **REQUIRE_COMPUTED enforcement:** When set, prevents any component from
   falling back to simulated/placeholder values. This ensures all results
   come from actual computation on real data.

5. **Phase 9 is narrative only:** Phase 9 (Conjecture) produces no
   computational artifacts. It synthesizes findings from Phases 1-8 into
   the publication.

6. **Controls are first-class:** Scrambled, synthetic, and mechanical-reuse
   controls are generated in Phase 1 and stored as `ControlDatasetRecord`
   entries, enabling all subsequent phases to compare real vs control.
