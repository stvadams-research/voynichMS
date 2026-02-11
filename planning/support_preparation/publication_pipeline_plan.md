# Publication Pipeline Redesign Plan

**Status: IMPLEMENTED (2026-02-11)**

## Problem Statement

The current publication process consists of 6+ independent Python scripts, each generating a separate `.docx` file with largely hardcoded prose and fabricated data values. There is no single source of truth, no data-driven content, and no unified entry point. The result is a proliferation of stale, inconsistent documents in `results/publication/` with no clear canonical output.

This plan replaces the current approach with a single, data-driven pipeline that separates **content** (authored markdown), **data** (computed results), and **formatting** (docx rendering).

---

## 1. What We Have to Work With

### Real Data (currently ignored by generators)
- `results/data/phase4_inference/` — 6 JSON result files (montemurro, network, topic, morph, lang_id)
- `results/data/phase5_mechanism/` — 12+ JSON result files (pilot through 5k, sectional profiles, lattice overlap, anchor coupling)
- `results/data/phase6_functional/` — 3 JSON result files (6a, 6b, 6c)
- `results/data/phase7_human/` — 3 JSON result files (7a, 7b, 7c) plus by-run provenance

### Real Reports (partially used by `generate_publication.py`, ignored by the rest)
- `results/reports/phase2_analysis/final_report_phase_2.md`
- `results/reports/phase3_synthesis/final_report_phase_3.md`
- `results/reports/phase4_inference/phase_4_conclusions.md` (+ 5 others)
- `results/reports/phase5_mechanism/` — 20+ individual sub-phase reports (5a through 5k, plus hypothesis classes, topology sets, necessary consequences)
- `results/reports/phase6_functional/` — 4 reports
- `results/reports/phase7_human/` — 4 reports
- `results/reports/phase8_comparative/` — 8 reports (proximity analysis, artifact library, scoring, etc.)

### Real Visuals
- `results/visuals/phase1_foundation/` through `phase8_comparative/` — actual computed plots from analysis runs

### Current Scripts (to be replaced)
- `generate_publication.py` — chapter-based, partially data-loaded
- `generate_scientific_publication.py` — 100% hardcoded narrative
- `generate_dual_reports.py` — hardcoded prose + hardcoded chart data
- `generate_definitive_paper.py` — verbose copy of dual_reports
- `generate_massive_academic_paper.py` — another copy
- `generate_final_treatise.py` — yet another copy
- `assemble_draft.py` — markdown assembler (references non-existent chapter dirs)

---

## 2. Triage of Revised Draft Feedback

The `Voynich_Revised_Draft.docx` contains 15 AUTHOR NOTE annotations from a prior Claude review. Below is our assessment of each — accepting what's genuinely useful, rejecting what comes from a "journal submission checklist" mentality that doesn't apply to our work.

### Accept — Genuine structural problems

| Note | Issue | Why it matters |
|------|-------|----------------|
| Para 20 | Introduction repeated ~10 times | Direct symptom of copy-paste generation approach; single source of truth fixes this |
| Para 36 | Section 2.2 repeated ~14 times | Same root cause |
| Para 49 | Section 4 repeated ~15 times | Same root cause |
| Para 55 | Phase 5 had 12 near-identical boilerplate paragraphs instead of real methodology/data | The actual Phase 5 sub-reports exist (`results/reports/phase5_mechanism/phase_5b_results.md` through `5k`); the generator just didn't use them |
| Para 58 | Phase 5A needs specific methodology and numerical results | Real data exists in `results/data/phase5_mechanism/pilot_results.json` — should be sourced |
| Para 75 | Phases 5H, 5I, 5J described as "missing" | Reports actually DO exist: `phase_5h_results.md`, `phase_5i_results.md`, `phase_5j_results.md`. Generator simply didn't include them |
| Para 93 | "Several orders of magnitude" claim lacks numerical backing | Claims must be traceable to computed values or be softened |
| Para 116 | Appendix shows identical values for all 26 quires | Placeholder data baked into Python code; must pull from real DB or omit |
| Para 120 | Appendix B is one sentence with no data | Either source from `results/reports/phase8_comparative/artifact_library.md` or omit |
| Para 101 | Pop culture references (*Matrix*) | Tone issue; easy fix in authored content |

### Accept with reservation — Useful but reframe for our context

| Note | Issue | Our position |
|------|-------|--------------|
| Para 103 | "Limitations section mandatory" | A limitations section IS genuinely valuable — not because a journal checklist says so, but because the ARF methodology is built on explicit boundary-setting. We should articulate what our framework *cannot* diagnose (e.g., authorial intent, meaning embedded in non-textual elements). This is a strength, not a concession. |

### Reject — Checklist mentality that misunderstands our methodology

| Note | Issue | Why we reject it |
|------|-------|-----------------|
| Para 23 | "Literature review section needed for journal submission" | The Assumption-Resistant Framework *deliberately* avoids starting from others' claims. We identify structure first, then compare to existing work in Phase 8 (Comparative Analysis). A literature review at the front would undermine the epistemic discipline that IS the methodology. If we engage prior work, it belongs in Discussion/Comparative, not as a prerequisite. |
| Para 112 | "Zero citations would result in immediate desk rejection" | Same reasoning. We reference prior work where our results *intersect* it (Phase 8), not where tradition says we should. Any citations added should serve the argument, not a convention. |
| Para 5 | Missing author names, ORCIDs | Boilerplate. Not a pipeline issue. |
| Para 12 | Missing keywords | Formatting detail. Not a pipeline issue. |

---

## 3. New Architecture

### Design Principles
1. **Content is markdown, not Python strings** — Authored prose lives in `.md` files, versioned and editable without touching code
2. **Data is sourced, not fabricated** — Every number in the document is pulled from a JSON result file or the database, with the source path recorded
3. **One generator, multiple profiles** — A single script with a config that controls which sections to include and how verbose to be
4. **Visuals are referenced, not regenerated** — Use existing plots from `results/visuals/`; generate new ones only from real data when needed
5. **Provenance trail** — The generated document includes metadata about which data files and report files were sourced

### Directory Structure

```
planning/support_preparation/
  publication_pipeline_plan.md    ← this file
  publication_master_plan.md      ← existing (historical reference)

planning/support_preparation/content/
  00_front_matter.md              ← title, abstract, scope statement
  01_epistemic_crisis.md          ← introduction / why prior approaches fail
  02_methodology.md               ← ARF description, perturbation, admissibility
  03_foundational_ledger.md       ← Phase 1 narrative wrapper
  04_structural_exclusion.md      ← Phase 2 narrative wrapper
  05_generative_reconstruction.md ← Phase 3 narrative wrapper
  06_inference_evaluation.md      ← Phase 4 narrative wrapper
  07_mechanism_identification.md  ← Phase 5 narrative wrapper (5A-5K)
  08_functional_characterization.md ← Phase 6 narrative wrapper
  09_scribal_hand_analysis.md     ← Phase 7 narrative wrapper
  10_comparative_classification.md ← Phase 8 narrative wrapper
  11_discussion.md                ← interpretive context, limitations, boundaries
  12_conclusion.md                ← final synthesis
  appendix_a_sectional_data.md    ← template for data-sourced appendix
  appendix_b_artifact_library.md  ← template for comparative data

scripts/support_preparation/
  generate_publication.py         ← REWRITTEN: single unified generator
  publication_config.yaml         ← profiles (full, summary, technical)
```

### Content Files: What Goes In Them

Each chapter `.md` file contains:
- **Authored prose** — the narrative, written by us, explaining the methodology and significance
- **Data placeholders** — markers like `{{phase5.pilot.successor_entropy}}` that the generator resolves from JSON
- **Report inclusions** — markers like `{{include:results/reports/phase5_mechanism/phase_5b_results.md}}` to pull in computed report sections
- **Visual references** — markers like `{{figure:results/visuals/phase5_mechanism/...png|Caption text}}` that the generator embeds

Example snippet from `07_mechanism_identification.md`:
```markdown
## Phase 5A: Identifiability Pilot

The initial pilot differentiated real manuscript data from stochastic controls.
Real successor entropy ({{phase5.pilot.successor_entropy}}) was significantly
lower than pool-reuse controls ({{phase5.pilot.control_entropy}}), identifying
a higher-order constraint operating beyond simple token reuse.

{{include:results/reports/phase5_mechanism/phase_5_results.md}}

{{figure:results/visuals/phase5_mechanism/...|Successor entropy comparison}}
```

### Generator Script Design

The rewritten `generate_publication.py` does three things:

1. **Resolve** — Walk through each content `.md` file, resolve `{{...}}` placeholders against JSON data files and report markdown
2. **Assemble** — Concatenate resolved content into a single master markdown document
3. **Render** — Convert the assembled markdown to `.docx` using `python-docx`, applying consistent styles

```
Content .md files  ──┐
                     ├──→ [Resolver] ──→ [Assembler] ──→ [Renderer] ──→ .docx
Data .json files   ──┘
Report .md files   ──┘
Visual .png files  ──┘
```

The config file controls profiles:
```yaml
profiles:
  full:
    chapters: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    appendices: [a, b]
    include_figures: true
    output: "Voynich_Structural_Identification_Full.docx"

  summary:
    chapters: [0, 1, 2, 7, 10, 12]
    appendices: []
    include_figures: true
    output: "Voynich_Research_Summary.docx"

  technical:
    chapters: [0, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    appendices: [a, b]
    include_figures: true
    output: "Voynich_Technical_Report.docx"
```

Usage: `python scripts/support_preparation/generate_publication.py --profile full`

### Data Resolution

A `DataResolver` class maps placeholder keys to JSON paths:
```yaml
data_sources:
  phase5.pilot.successor_entropy: results/data/phase5_mechanism/pilot_results.json -> results.successor_entropy
  phase5.pilot.control_entropy: results/data/phase5_mechanism/pilot_results.json -> results.control_entropy
  phase5.5b.reset_score: results/data/phase5_mechanism/constraint_geometry/pilot_5b_results.json -> results.reset_score
  # ... etc for all referenced values
```

Any placeholder that can't be resolved produces a visible `[MISSING: key]` marker in the output and a warning in the build log — no silent defaults, no fabricated numbers.

---

## 4. Execution Phases

### Phase A: Content Extraction (do first)
1. Audit every JSON file in `results/data/` to build the data source map — know what keys exist and what values they hold
2. Audit every report `.md` in `results/reports/` to identify which sections are substantial vs. stubs
3. Create the `planning/support_preparation/content/` directory
4. Write the initial content `.md` files by extracting and deduplicating the best prose from the existing generators (primarily `generate_scientific_publication.py` for readability, `generate_publication.py` for chapter structure)
5. Replace hardcoded numbers with `{{placeholder}}` markers

### Phase B: Generator Rewrite
1. Implement the `DataResolver` — reads JSON files, resolves `{{key}}` placeholders
2. Implement the `ReportIncluder` — resolves `{{include:path}}` markers by reading the referenced `.md` file
3. Implement the `FigureResolver` — resolves `{{figure:path|caption}}` markers, verifies file existence
4. Implement the `DocxRenderer` — converts resolved markdown to Word using `python-docx` (port the best style setup from `generate_dual_reports.py`)
5. Implement the `PublicationBuilder` — orchestrates resolve → assemble → render
6. Write the config YAML with initial profiles
7. Write the data source mapping

### Phase C: Validation
1. Generate all profiles and verify no `[MISSING: ...]` markers remain
2. Diff key numerical claims against source JSON to confirm accuracy
3. Confirm all figure references resolve to existing files
4. Review the full output document for flow and coherence
5. Spot-check that no hardcoded/fabricated numbers survived from old generators

### Phase D: Cleanup
1. Remove or archive the 6 legacy generator scripts (move to `scripts/support_preparation/archive/`)
2. Remove stale `.docx` files from `results/publication/` (or move to archive)
3. Update `publication_master_plan.md` to reference this new plan

---

## 5. What This Does NOT Address (and shouldn't)

- **Authorial voice** — The content `.md` files need human authorship for the narrative prose. The pipeline provides the scaffolding; the words still need to be written/edited by us.
- **Journal submission formatting** — We are not formatting for a specific journal. If that becomes relevant later, the profile system can accommodate it.
- **Literature review / citations** — Per our methodology, external work is engaged in the comparative phase, not as a prerequisite. The pipeline doesn't enforce a citation section; the content files will reference prior work where our results warrant it.
- **Peer review process** — This plan covers document generation, not the review/revision cycle.

---

## 6. Success Criteria

- [x] Single command (`generate_publication.py --profile full`) produces the complete document
- [x] Every numerical claim in the output is traceable to a specific JSON file and key path
- [x] No hardcoded data values exist in the generator script
- [x] Adding a new research result requires only: (a) adding the JSON file, (b) adding a placeholder in the content `.md`, (c) adding a mapping in the data sources config
- [x] The content `.md` files are readable and editable standalone, without needing to understand the Python code
- [x] Build log reports exactly which data files, reports, and visuals were included

---

## 7. Implementation Record (2026-02-11)

### What was built
- **15 content markdown files** in `planning/support_preparation/content/`
- **1 unified generator** at `scripts/support_preparation/generate_publication.py` (560 lines, 5 classes)
- **1 config file** at `scripts/support_preparation/publication_config.yaml` with 3 profiles and 60+ data source mappings
- **3 output documents** generated successfully (full, summary, technical)
- **3 build logs** with full provenance

### What was removed
- **7 legacy scripts**: assemble_draft.py, generate_academic_paper.py, generate_definitive_paper.py, generate_dual_reports.py, generate_final_treatise.py, generate_massive_academic_paper.py, generate_scientific_publication.py
- **9 stale output files**: all prior .docx files except Voynich_Revised_Draft.docx (kept as feedback reference)

### Validation
- `--list-missing` shows 0 unresolved placeholders across all profiles
- 6 critical numerical values spot-checked against source JSON — all match
- 24 data values resolved, 21 reports included, 4 figures embedded in full profile
