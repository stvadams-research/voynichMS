# Publication Workflow

## Quick Reference

To generate or refine the Voynich research publication, follow this process.

---

## Architecture

The publication pipeline separates **content** (authored prose), **data** (computed results), and **rendering** (docx generation).

```
planning/support_preparation/content/*.md   ← authored prose with {{placeholders}}
scripts/support_preparation/publication_config.yaml  ← profiles + data source mappings
scripts/support_preparation/generate_publication.py  ← unified generator
results/publication/                         ← output documents + build logs
```

### Content Files (the editorial surface)

All prose lives in `planning/support_preparation/content/`:

| File | Content |
|------|---------|
| `00_front_matter.md` | Title, abstract, scope statement |
| `01_epistemic_crisis.md` | Introduction — why prior approaches fail |
| `02_methodology.md` | ARF description, perturbation, admissibility gates |
| `03_foundational_ledger.md` | Phase 1 — corpus statistics, repetition rate |
| `04_structural_exclusion.md` | Phase 2 — linguistic model exclusion |
| `05_generative_reconstruction.md` | Phase 3 — non-semantic sufficiency test |
| `06_inference_evaluation.md` | Phase 4 — noise floor, false positive analysis |
| `07_mechanism_identification.md` | Phase 5 (5A-5K) — lattice identification |
| `08_functional_characterization.md` | Phase 6 — efficiency and ergonomic profile |
| `09_scribal_hand_analysis.md` | Phase 7 — cross-scribe stability |
| `10_comparative_classification.md` | Phase 8 — artifact morphospace |
| `11_discussion.md` | Interpretive context, limitations, boundaries |
| `12_conclusion.md` | Final synthesis |
| `appendix_a_sectional_data.md` | Sectional metrics (data-sourced) |
| `appendix_b_artifact_library.md` | Comparative artifact reference |

### Placeholder Syntax

- `{{phase5.5e.successor_consistency}}` — resolved from JSON data files
- `{{include:results/reports/phase5_mechanism/phase_5k_results.md}}` — inserts report content
- `{{figure:results/visuals/phase1_foundation/...png|Caption text}}` — embeds image

### Profiles

| Profile | Scope | Output |
|---------|-------|--------|
| `full` | All 15 files (chapters + appendices) | `Voynich_Structural_Identification_Full.docx` |
| `summary` | Front matter, intro, methodology, mechanism, comparative, conclusion | `Voynich_Research_Summary.docx` |
| `technical` | All chapters minus intro/discussion/conclusion, plus appendices | `Voynich_Technical_Report.docx` |

---

## The Process

### Step 1: Generate

Ask Claude to generate the publication, specifying which profile:

> "Generate the full publication"

Claude runs:
```
python scripts/support_preparation/generate_publication.py --profile full
```

This resolves all data from JSON, includes all reports, embeds figures, and produces the `.docx` plus a `.build_log.txt` with full provenance.

### Step 2: Review

Open the generated `.docx` and review. Common feedback:
- Narrative flow or transitions between chapters
- Sections that are too dense or too thin
- Tone adjustments (too assertive, too hedged, etc.)
- Specific claims that need rewording
- Reports that were bulk-included but should be trimmed or summarized

### Step 3: Refine

Tell Claude what to change. Claude edits the relevant content `.md` files. Examples:

> "The mechanism chapter is too long — summarize the Phase 5 sub-reports instead of including them in full"

> "The introduction needs a stronger opening — rewrite the first two paragraphs"

> "Add a transition between the inference evaluation and mechanism identification chapters"

### Step 4: Regenerate

Claude regenerates the document. Edits to content files flow through automatically; data values stay sourced from JSON.

### Step 5: Repeat

Iterate steps 2-4 until the document meets the standard.

---

## Useful Commands

Check for unresolved placeholders without generating:
```
python scripts/support_preparation/generate_publication.py --list-missing
```

Generate a specific profile:
```
python scripts/support_preparation/generate_publication.py --profile summary
```

Build log (provenance) is written alongside each output:
```
results/publication/Voynich_Structural_Identification_Full.build_log.txt
```

---

## Key Properties

- **Every number** in the output traces to a JSON file (see `publication_config.yaml` data_sources)
- **No hardcoded data** in the generator script — all values are sourced or produce `[MISSING]` markers
- **Content is editable markdown** — no need to touch Python to change prose
- **Adding new data**: (1) add JSON file, (2) add `{{placeholder}}` in content .md, (3) add mapping in config YAML
