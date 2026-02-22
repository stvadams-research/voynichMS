# Phase 17: Physical Synthesis & The "Meaning" Boundary

**Objective:** To achieve absolute closure by producing the physical blueprints for the tabula + codebook production tool, bounding the steganographic capacity, documenting the operator protocol, and consolidating all phases into a research monograph.

**Status:** COMPLETE (all 4 tasks finished 2026-02-22)
**Updated:** 2026-02-22

---

## 1. Task 1: Physical Blueprint Generation
**Goal:** Translate the digital lattice into 15th-century "Hardware."

- [x] **1.1: Tabula Card SVG** — 10x5 state tracker with 50 windows + per-window correction offsets (170x160mm).
    - **Artifact:** `results/visuals/phase17_finality/tabula_card.svg`
- [x] **1.2: Palette Plate SVG** — 10x5 vocabulary grid with word labels, counts, and correction offsets.
    - **Artifact:** `results/visuals/phase17_finality/palette_plate.svg`
- [x] **1.3: Codebook Index SVG** — W0-W49 section index with word counts, page spans, and offsets.
    - **Artifact:** `results/visuals/phase17_finality/codebook_index.svg`
- [x] **1.4: Correction Offsets Reference** — Per-window offset table (43 non-zero, range -20 to +13).
    - **Artifact:** `results/visuals/phase17_finality/correction_offsets.txt`
- [x] **1.5: Historical Volvelle Rings** — Preserved in `historical/` subdirectory (deprecated by Phase 20).
    - **Note:** Phase 20 proved volvelle IMPLAUSIBLE; tabula + codebook (score 0.865) is canonical model.

## 2. Task 2: Steganographic Bandwidth Audit
**Goal:** Conclusively bound the "Head" (Meaning) vs. the "Hand" (Ergonomics).

- [x] **2.1: Information Capacity Calculation**
    - **Result:** 7.53 bits/word realized bandwidth; total capacity 11.5 KB (~23K Latin chars).
    - **Artifact:** `results/data/phase17_finality/bandwidth_audit.json`
- [x] **2.2: The "Latin Test"**
    - **Result:** Genesis 1:1-5 (339 chars) encoded in 342 of 12,519 admissible choices. RSB = 2.21 bpw.
    - **Artifact:** `results/data/phase17_finality/latin_test.json`
- [x] **2.3: Verdict:** Steganographic feasibility confirmed but not proven. 7.53 bpw exceeds 3.0 bpw stego threshold — the model does NOT rule out hidden content.

## 3. Task 3: The 15th-Century Operator Protocol
**Goal:** Document the "Manual" for the Voynich Engine.

- [x] **3.1: Protocol Definition** — Complete 8-step production protocol (tabula + codebook model).
    - **Artifact:** `results/reports/phase17_finality/OPERATOR_MANUAL.md`
- [x] **3.2: Error Handling** — Mechanical slip classification and recovery procedures documented.
    - Codebook indexing errors (92.6% at W18), offset miscalculations, self-correction mechanism.
- [x] **3.3: Scribal Variation** — Hand 1 vs Hand 2 fluency profiles documented.
- [x] **3.4: Production Capacity** — Estimated ~200-400 hours total scribal labor for full manuscript.

## 4. Task 4: Final Research Monograph
**Goal:** Consolidate 20 phases of research into a single academic-grade synthesis.

- [x] **4.1: New Content Chapters**
    - `10a_lattice_constraint.md` — Phases 9-11 (admissibility lattice, Method K, stroke topology)
    - `10b_mechanical_reconstruction.md` — Phases 12-14 (slips, blueprint, high-fidelity emulation)
    - `10c_production_model.md` — Phases 15-20 (rules, grounding, bandwidth, state machine)
- [x] **4.2: Updated Chapters**
    - `11_discussion.md` — Integrated Phase 14-20 findings (volvelle question, meaning boundary)
    - `12_conclusion.md` — Updated to 20-phase scope with quantitative summary table
- [x] **4.3: Publication Pipeline** — Updated `publication_config.yaml` with 3 new chapters across all profiles.
- [x] **4.4: Document Generation** — All three profiles generated with zero missing references:
    - `results/publication/Voynich_Structural_Identification_Full.docx` (19 chapters)
    - `results/publication/Voynich_Research_Summary.docx` (8 chapters)
    - `results/publication/Voynich_Technical_Report.docx` (16 chapters)

---

## Success Criteria for Phase 17

1. **Physicality:** Printable SVG blueprints allow any researcher to physically reproduce the Voynich production tool using 15th-century technology. **MET** — tabula card, palette plate, and codebook index all generated.
2. **Bandwidth Bound:** The meaning boundary is quantified. **MET** — 7.53 bpw realized, Latin test confirms sparse encoding feasibility.
3. **Operator Protocol:** Step-by-step production manual documented. **MET** — OPERATOR_MANUAL.md with 8-step protocol, error handling, scribal variation.
4. **Monograph:** All 20 phases consolidated into academic-grade document. **MET** — 3 publication profiles generated with zero unresolved references.
