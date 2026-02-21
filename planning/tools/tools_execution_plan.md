# Tooling Execution Plan: Slip Explorer -> Multi-Tool Workbench

**Created:** 2026-02-21  
**Scope:** `tools/workbench/`  
**Target artifact:** `tools/workbench/index.html` opens directly via `file://` (drag into browser), with navigation across existing and new tools.

---

## 1. Objective

Evolve the current single-page Slip/Lattice demo into a small offline tool suite with:

1. Existing capabilities preserved:
   - Slip Explorer
   - Lattice Sandbox
2. New capability #1 (now): IVTFF text validation
3. New capability #2 (now): synthetic folio generation that can be validated by #1
4. New capability #3 (later): page generation by folio id (e.g., `f42r1`)

---

## 2. Current State Snapshot

1. `tools/workbench/index.html` is monolithic (~38k lines, ~710 KB) and embeds large JSON objects (`EMBEDDED_SLIPS`, `EMBEDDED_GRID`) inline.
2. Current UI has two tabs only: `SLIPS` and `LATTICE`.
3. The model/generation logic already exists in Python (`src/phase14_machine/high_fidelity_emulator.py`) but not in browser JS.
4. Existing parser utilities:
   - IVTFF line parsing: `src/phase1_foundation/transcription/parsers.py`
   - token sanitization: `src/phase1_foundation/core/data_loading.py`
5. Important compatibility gap:
   - Current lattice assets are ZL-based lowercase vocabulary.
   - Example input from `CD2a-n.txt` is Currier/D’Imperio-style uppercase tokens.
   - Therefore we need separate validation layers: syntax validity vs lattice-admissibility validity.

---

## 3. Architecture Decisions

## 3.1 Offline-first (drag-and-drop HTML)

1. No runtime server dependency.
2. Avoid runtime `fetch()` to local JSON (unreliable under `file://`).
3. Use local `<script src>` files with prebuilt JS data blobs.
4. Keep all files in `tools/workbench/` and subdirectories for permission simplicity.

## 3.2 Modularize without breaking local file loading

1. Keep `index.html` as parent shell.
2. Split CSS and JS into multiple files (non-module script loading order to avoid `file://` module restrictions).
3. Keep data in generated JS files (`window.TOOL_DATA = ...`) instead of inline HTML constants.

## 3.3 Two-tier validation model

1. **Tier A: IVTFF Syntax Validation**
   - Accept content-only pasted lines (your sample).
   - Accept full IVTFF lines with location prefix (`<f29r.1,@P0> ...`).
2. **Tier B: Machine Validation (optional)**
   - Token sanitization parity with `sanitize_token`.
   - Lattice coverage and admissibility (strict and drift).
   - Clear messaging when source/transliteration mismatch causes low coverage.

---

## 4. Proposed File Layout

```
tools/workbench/
  index.html
  css/
    app.css
  js/
    app.js
    state.js
    router.js
    ui_console.js
    data_loader.js
    views/
      slips_view.js
      lattice_view.js
      validator_view.js
      folio_generator_view.js
      page_generator_view.js        # placeholder in this cycle
    core/
      ivtff_parser.js
      ivtff_validator.js
      sanitize.js
      lattice_engine.js
      folio_generator.js
  data/
    slips_data.js                   # generated
    lattice_data.js                 # generated
    metadata.js                     # generated (source/version hashes)
```

Build/export helper (new):

```
scripts/tools/build_workbench_bundle.py
```

This script will read:
- `results/data/phase13_demonstration/slip_viz_data.json`
- `results/data/phase14_machine/full_palette_grid.json`

and emit `tools/workbench/data/*.js`.

---

## 5. Execution Plan

## Phase 0 - Baseline + Guardrails

1. Snapshot current behavior:
   - Open current `tools/workbench/index.html` and record Slip + Lattice behavior.
2. Add rollback safety:
   - Keep current `index.html` as `index_legacy.html` during migration.
3. Define canonical sample fixtures:
   - Include your 9-line sample as `validator_sample_currier.txt` fixture in docs/tests.

Deliverable:
- migration safety and baseline notes.

## Phase 1 - Shell + Navigation Refactor

1. Create parent shell `index.html` with left nav / top nav:
   - `Slips`
   - `Lattice`
   - `IVTFF Validator`
   - `Folio Generator`
   - `Page Generator` (disabled badge: `Planned`)
2. Move inline CSS into `css/app.css`.
3. Move inline JS into `js/*` modules (script-order loaded).
4. Preserve existing Slip/Lattice behavior exactly.

Deliverable:
- same current capabilities, but modular structure and app-level navigation.

## Phase 2 - Data Packaging Pipeline

1. Implement `scripts/tools/build_workbench_bundle.py`.
2. Generate:
   - `tools/workbench/data/slips_data.js`
   - `tools/workbench/data/lattice_data.js`
   - `tools/workbench/data/metadata.js`
3. Remove giant inline JSON from `index.html`.
4. Add quick sanity checks in build script:
   - expected key presence (`slips`, `lattice_map`, `window_contents`)
   - non-empty counts
   - source timestamp metadata.

Deliverable:
- small `index.html`, external static data blobs, still fully offline.

## Phase 3 - IVTFF Validator (New Capability #1)

1. Implement parser/validator core in JS:
   - line classification: full-line vs content-only
   - token splitting parity with Python behavior (`.` / whitespace)
   - structural checks (empty tokens, malformed tags, unsupported chars)
   - detailed per-line errors.
2. Implement validation modes:
   - `Syntax Only` (default)
   - `Syntax + Sanitized Token Report`
   - `Syntax + Lattice Admissibility`
3. Add UI:
   - multiline input
   - mode selector
   - validation report panel
   - copyable normalized output.
4. Acceptance fixture:
   - Your provided sample must return `Syntax Valid`.

Deliverable:
- robust IVTFF validator with explicit source mismatch warnings when applicable.

## Phase 4 - Folio Generator (New Capability #2)

1. Port core behavior from `HighFidelityVolvelle` into `js/core/folio_generator.js`:
   - seeded RNG
   - window traversal via `lattice_map`
   - selectable scribe profile and mask behavior.
2. Generator UI controls:
   - `Seed`
   - `Line count`
   - `Words per line min/max`
   - `Start window` (auto/manual)
   - `Output format`: content-only vs full-IVTFF-style.
3. Add pipeline button:
   - `Generate -> Send to Validator`.
4. Validation expectation:
   - generated output passes Tier A syntax validation.
   - generated output passes Tier B lattice validation when evaluated against same loaded lattice.

Deliverable:
- deterministic, reproducible folio generation directly in browser.

## Phase 5 - Page Generator Discovery (New Capability #3, Deferred)

Status: not implemented in this cycle; ship as explicit roadmap tab.

Why deferred:
1. No validated mapping from folio id (e.g., `f42r1`) to required generator state:
   - line/paragraph structure
   - section-specific mask schedule
   - hand/style schedule
   - start-window priors per line.
2. Existing Phase 3 page generators are for pharmaceutical gap synthesis, not direct folio-id recreation from Phase 14 lattice.
3. Transliteration incompatibility is unresolved for cross-source rendering expectations.

Deliverable this cycle:
- `Page Generator` view with explicit prerequisites checklist and tracked blockers.

---

## 6. Gaps and Mitigation

1. **Transliteration mismatch (critical)**
   - Gap: Currier uppercase sample vs ZL lattice vocabulary.
   - Mitigation: keep syntax validation source-agnostic; machine validation explicitly tied to selected model source.
2. **Local-file browser restrictions**
   - Gap: `fetch()` from `file://` may fail.
   - Mitigation: precompiled JS data bundles + plain script tags.
3. **Python/JS parity drift**
   - Gap: generator behavior may diverge.
   - Mitigation: add parity fixtures with fixed seeds and expected first-N tokens/line lengths.
4. **Performance with large lattice data**
   - Gap: rendering 7k+ token map can stall.
   - Mitigation: virtualized list rendering and lazy panel updates.

---

## 7. Acceptance Criteria (Definition of Done)

1. `tools/workbench/index.html` opens directly from Finder/File Explorer into browser, no server required.
2. User can navigate between:
   - Slips
   - Lattice
   - IVTFF Validator
   - Folio Generator
   - Page Generator (planned/disabled)
3. Your sample block validates as `Syntax Valid` in Validator.
4. A folio generated by Folio Generator can be sent to Validator and passes syntax validation.
5. Same generated folio passes lattice admissibility check under the same loaded lattice dataset.
6. Existing Slip/Lattice functionality remains operational.
7. Codebase is modular (no giant inline JSON in `index.html`).

---

## 8. Execution Order

1. Phase 0: Baseline + fixture capture
2. Phase 1: Shell/navigation refactor
3. Phase 2: Data bundling script + data externalization
4. Phase 3: IVTFF validator
5. Phase 4: Folio generator + validator handoff
6. Phase 5: page-generator roadmap tab + blockers

---

## 9. Immediate Next Step

Start with Phases 1-2 together (modular shell + data bundle script), because this creates the stable foundation needed for both validator and generator without rework.
