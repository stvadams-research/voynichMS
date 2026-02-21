# Phase 18: Workbench Page Generator Completion Plan

**Date:** 2026-02-21
**Revised:** 2026-02-21 (critical assessment pass)
**Status:** EXECUTED (implementation completed 2026-02-21)
**Scope:** `tools/workbench/` page generation by folio id

---

## 1. Objective

Implement the missing `Page Generator` capability in `tools/workbench` so a user can request a folio id (for example `f42r`) and generate structurally valid output using the lattice model, with explicit controls and validation.

This document started as a planning artifact and has now been executed in the
current repository state.

## 1.1 Execution Snapshot (Completed)

1. Extended `scripts/phase14_machine/run_14x_mask_inference.py` to persist per-line schedule metadata.
2. Added `scripts/phase18_generate/build_page_generation_assets.py` and generated:
   - `results/data/phase18_generate/folio_state_schedule.json`
   - `results/data/phase18_generate/page_priors.json`
3. Extended `scripts/tools/build_workbench_bundle.py` to emit:
   - `tools/workbench/data/page_schedule_data.js`
   - `tools/workbench/data/page_priors_data.js`
4. Implemented workbench page generation:
   - `tools/workbench/js/core/page_generator.js`
   - `tools/workbench/js/views/page_generator_view.js`
   - Updated `tools/workbench/index.html`, loader/state wiring.
5. Added validation/docs:
   - `tests/integration/test_phase18_assets.py` (passing)
   - `tools/workbench/docs/page_generator.md`

---

## 2. Current Baseline (What Exists Today)

1. `tools/workbench/js/views/page_generator_view.js` is a placeholder only (7 lines, no logic).
2. `Folio Generator` exists and can route output directly to `IVTFF Validator`. It already has: seed control, line count selection, min/max word params, scribe profile (Hand 1/Hand 2), content-only and full IVTFF format output.
3. `IVTFF Validator` supports syntax, sanitized-token, and lattice-admissibility checks.
4. `tools/workbench/data/folio_data.js` includes 227 folios, 5,386 lines with IVTFF location headers (ZL source).
5. `tools/workbench/data/lattice_data.js` includes the full 50-window lattice (7,717 tokens, `window_contents` + `lattice_map`).
6. Deferred prerequisites are already stated in `tools/workbench/index.html` and `planning/tools/tools_execution_plan.md`:
   - folio→section mask/state schedule mapping,
   - stable line-count and line-entry priors by folio/quire context,
   - transliteration bridge rules for source-specific rendering.

### 2.1 Critical Data Gap Assessment

| Prerequisite | Current State | Readiness |
|---|---|---|
| **Line-level mask schedule** | `run_14x_mask_inference.py` computes per-line offsets internally but saves only aggregate summaries to `mask_inference.json`. Per-line arrays (`line_offsets`, `line_scores`) are discarded. | **Trivially fixable** — extend save logic. |
| **Mask prediction rules** | `mask_prediction.json` has global_mode (offset=17), per-section, per-hand, per-quire, per-page, prev-line-carry rules. **Best rule is global_mode at 44.2% capture (6.3pp gain).** | **Available.** But gain is modest. |
| **Section map** | 7 sections defined covering f1–f116 (116 folios). **Folios f117–f227 (111 folios, 49% of workbench set) are unmapped.** | **Partial.** Must define supported set. |
| **Quire map** | `(folio_num-1)//8+1` approximation in 2 places. No validated mapping table. | **Approximation only.** But quire-level prediction is WORSE than global mode (39.5% vs 44.2% capture), so quire precision is not the bottleneck. |
| **Hand classification** | Hard-coded: Hand 1 ≤f66, Hand 2 f75–f84+f103–f116, rest "Unknown". | **Approximation only.** f67–f74 (Astro) and f85–f102 (Cosmo/Pharma) are "Unknown". |
| **Line-count priors** | `folio_data.js` has real line counts per folio (observed values). No distributional priors. | **Observed counts available** for all 227 folios. |
| **Transliteration bridge** | No rules, profiles, or loss metrics exist anywhere in codebase. | **Not started.** |
| **Build pipeline** | `build_workbench_bundle.py` (307 lines) has clear extensible pattern (`write_js()` helper). | **Ready to extend.** |

---

## 3. Minimum Requirements (Phase 18 Hard Gates)

1. Validated mapping from folio id to section-level mask/state schedule.
2. Stable line-count capability (observed passthrough OR sampled priors).
3. Page output must remain compatible with current validation pipeline (generate → validate with IVTFF Validator).

### 3.1 Descoped from Hard Gates (Deferred)

- **Transliteration bridge rules for multi-source rendering.** Rationale: The page generator's primary value is demonstrating folio-specific structurally valid output from the lattice model. All existing generation operates in ZL-sanitized space. Multi-source rendering is a presentation feature, not a structural one. Descoped to P3 roadmap item.

---

## 4. Deliverables

| ID | Deliverable | Path | Priority |
|---|---|---|---|
| D1 | Per-line mask schedule artifact (extends `run_14x` output) | `results/data/phase14_machine/mask_inference.json` (extended) | P0 |
| D2 | Folio schedule artifact (section + line schedule with fallback chain) | `results/data/phase18_generate/folio_state_schedule.json` | P1 |
| D3 | Line-count and line-entry priors artifact | `results/data/phase18_generate/page_priors.json` | P1 |
| D4 | Workbench bundled data files for D2-D3 | `tools/workbench/data/page_schedule_data.js`, `tools/workbench/data/page_priors_data.js` | P2 |
| D5 | Page generator engine (JS) | `tools/workbench/js/core/page_generator.js` | P2 |
| D6 | Page generator UI (replace placeholder) | `tools/workbench/js/views/page_generator_view.js`, `tools/workbench/index.html` | P2 |
| D7 | Tests for artifact schema, deterministic behavior, fallback safety | `tests/tools/test_phase18_*.py` | P3 |
| D8 | Operator docs for page generator data contracts and limits | `tools/workbench/docs/page_generator.md` | P3 |

**Removed from deliverables:**
- ~~D3 (transliteration bridge artifact)~~ — Descoped. Internal generation stays in ZL-sanitized space. Optional bridge is a future enhancement.
- ~~D4 (translit_bridge_data.js)~~ — Follows from above.
- ~~D7 (build pipeline as separate deliverable)~~ — Folded into D4. Build pipeline extension is mechanical (add write_js() calls).

---

## 5. ROI-Prioritized Execution Plan

## P0: Emit Line-Level Data and Define Contracts

### P0.1 Extend `run_14x_mask_inference.py` to persist per-line schedule

The script already computes `line_offsets` and `line_scores` via `infer_mask_schedule()` (line 113-137) but discards them. Changes:
1. Accept folio metadata from `load_canonical_lines()` (folio_id per line).
2. Save extended output alongside existing summary:
   ```json
   "line_schedule": [
     {"folio_id": "f1r", "line_index": 0, "best_offset": 17, "line_score": 0.52, "section": "Herbal A", "hand": "Hand1"},
     ...
   ]
   ```
3. Preserve all existing output keys (no breaking change).

**Scope:** ~50 lines of code change in existing script. Straightforward because `infer_mask_schedule()` already returns the arrays.

**Verification:** `line_schedule` array length = 5,145 (total lines from mask_prediction.json confirms this count).

### P0.2 Define schema contracts for D2-D3

- Define required keys, types, and version fields for folio_state_schedule.json and page_priors.json.
- Include `provenance`, source paths, `generated_at`.
- Add schema checks as tests before UI work.

### P0.3 Define supported folio set and fallback policy

**Critical decision:** The SECTIONS dict covers f1–f116 only (116 folios). Workbench has 227 folios.

Options:
1. **Supported set = f1–f116 only.** Page generator rejects f117+ with clear message. Folio Generator still works for arbitrary generation.
2. **All folios supported with fallback.** f117+ get global mode offset (17) with explicit "fallback: no section data" flag.

**Recommendation:** Option 2. Global mode captures 44.2% of oracle gain. The page generator provides value for ALL folios via global offset, with section-level refinement where available. UI must clearly show when fallback is used.

---

## P1: Build the 2 Required Data Assets

### P1.1 Folio→section-level mask/state schedule (D2)

Tasks:
1. Build hierarchical schedule with deterministic fallback chain:
   - line-level inferred offset (from P0.1 artifact),
   - folio-level mode (most common offset for that folio),
   - section-level mode (from mask_prediction.json section_mode_offsets),
   - global mode (offset=17).
2. Store source level and confidence for every line decision:
   - `"source": "line_inferred"` / `"folio_mode"` / `"section_mode"` / `"global_mode"`
3. Include explicit baseline comparison:
   - `baseline_admissibility` (offset=0): 39.57%
   - `global_mode_admissibility` (offset=17): 45.91%
   - `oracle_admissibility`: 53.91%
   - `schedule_admissibility`: measured from the fallback chain

**Critical honesty note:** The best non-oracle rule (global_mode) captures only 44.2% of oracle gain (+6.3pp). The page generator's schedule adds modest structural value over the existing Folio Generator, not dramatic folio-specific customization. The diagnostics panel must make this clear.

Acceptance:
1. Every folio in workbench dataset has a resolved schedule chain.
2. Fallback usage rates are measured and reported:
   - Expected: ~116/227 folios (51%) have section data, remainder use global fallback.
3. Schedule admissibility matches global_mode baseline within ±0.5pp (since most folios share offset=17).

### P1.2 Line-count and line-entry capability (D3)

**Pragmatic approach:** Implement TWO modes, not just priors:

**Mode 1: Observed passthrough (default).** Use actual line count from `folio_data.js` for the requested folio. This is trivially available for all 227 folios. Zero priors infrastructure needed.

**Mode 2: Sampled from priors.** For generating line counts that "look like" a section:
1. Parse IVTFF line headers into normalized entry classes (`@P0`, `+P0`, `=Pt`, `@L0`, etc.).
2. Build priors conditioned by section + recto/verso.
3. Use hierarchical smoothing: section → global.
4. Run stability checks (holdout by section).

**Descoped:** Quire-level conditioning. Rationale: mask prediction showed per_quire prediction (39.5% capture) is worse than global_mode (44.2%). The quire approximation `(n-1)//8` is unreliable, and fixing it adds complexity without improving results. Section-level conditioning is sufficient.

Acceptance:
1. Mode 1 works for all 227 folios with zero failures.
2. Mode 2 produces non-degenerate line counts for all 7 sections.
3. Unknown contexts (f117+) degrade to global priors with explicit warning.

---

## P2: Workbench Integration

### P2.1 Data bundling and loader wiring

Tasks:
1. Extend `scripts/tools/build_workbench_bundle.py` to emit D4 files (2 new `write_js()` calls following existing pattern).
2. Update `tools/workbench/js/data_loader.js` to load `WORKBENCH_PAGE_SCHEDULE` and `WORKBENCH_PAGE_PRIORS` from window globals.
3. Add artifact version to metadata.js.

Acceptance:
1. `tools/workbench/index.html` still runs via `file://`.
2. Missing D4 files fail gracefully with explicit console warnings. Page generator tab shows "data not yet generated" message.

### P2.2 Page generator engine

Tasks:
1. Add `tools/workbench/js/core/page_generator.js`.
2. Implement deterministic generation pipeline:
   - resolve folio context (lookup in schedule artifact),
   - select line count (observed or sampled from priors),
   - for each line: resolve mask offset from schedule, generate tokens using lattice transitions with that offset,
   - format output as content-only or full IVTFF (reuse Folio Generator's format logic).
3. Maintain seed control and reproducibility parity with Folio Generator.

**Key difference from Folio Generator:** The Folio Generator uses offset=0 (no mask) and user-specified line count. The Page Generator uses per-line offsets from the schedule and observed/prior line counts. The lattice transition engine itself is identical.

Acceptance:
1. Same input config + seed gives byte-identical output.
2. Invalid folio id returns actionable error message with list of valid folios.
3. Generation diagnostics record: folio context, schedule source level per line, line count source.

### P2.3 Page generator UI

Tasks:
1. Replace placeholder view with controls:
   - folio id selector (dropdown of all 227 folios, searchable),
   - schedule mode (auto/global-only),
   - line-count mode (observed/sampled),
   - output format (content/full IVTFF),
   - seed and strictness toggles.
2. Add `Generate → Validate` button using existing validator route (same pattern as Folio Generator).
3. Add diagnostics panel showing:
   - resolved section name (or "Other - global fallback"),
   - schedule source level per line (inferred/folio/section/global),
   - line count source (observed/sampled),
   - expected admissibility range from Phase 14 baseline data.

Acceptance:
1. User can generate and validate without leaving workbench.
2. Diagnostics make clear WHAT schedule was used and WHY (no hidden fallbacks).

---

## P3: Verification, Tests, and Docs

### P3.1 Test suite additions

1. Artifact schema tests for D2-D3 (required keys, types, provenance).
2. Determinism tests: page generation with fixed seed + folio id → identical output.
3. Fallback behavior tests: unknown folio gets global fallback with warning flag.
4. Validator compatibility tests:
   - syntax mode pass for generated full IVTFF output,
   - lattice mode pass rate reported (expect near global_mode baseline: ~46%).

### P3.2 Documentation updates

1. Add `tools/workbench/docs/page_generator.md`:
   - data contracts for D2-D3,
   - generation pipeline description,
   - fallback semantics,
   - limitations (mask schedule is modest improvement over global mode).
2. Update `planning/tools/tools_execution_plan.md` status for Page Generator.
3. Add brief operator note in workbench UI near controls.

### P3.3 Transliteration bridge (ROADMAP — not Phase 18)

Deferred to future phase. When implemented:
1. Define source profiles (ZL/VT/IT/RF/GC/FG/CD).
2. Deterministic bridge rule tables (case, punctuation, source-specific substitutions).
3. Coverage metrics per source.
4. New D4 bundle: `translit_bridge_data.js`.

---

## 6. Acceptance Matrix

| Gate | Pass Condition |
|---|---|
| G1 Schedule completeness | 100% of 227 folios resolve to a schedule chain (section-specific or global fallback) with explicit provenance |
| G2 Line-count modes | Observed mode works for all 227 folios. Sampled mode produces non-degenerate counts for all 7 sections + global. |
| G3 Determinism | Fixed config + seed + folio_id reproduces identical output |
| G4 Validator compatibility | Generated full IVTFF passes syntax validation; lattice admissibility reported (expect ~46%) |
| G5 Offline behavior | Workbench remains fully functional from `file://` |
| G6 Fallback transparency | Any fallback path (section→global, unknown folio, etc.) yields explicit diagnostic, never silent default |
| G7 Graceful degradation | Missing D4 data files → page generator tab shows clear "not yet available" message; other tabs unaffected |

---

## 7. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| **Line-level mask data discarded in current script** | Blocks folio schedule | P0.1 is a trivial save extension (~50 LOC) |
| **Mask schedule adds only 6.3pp over baseline** | User expects dramatic folio-specific differences, gets marginal improvement | Honest diagnostics: show baseline vs schedule vs oracle. Frame as "structurally informed" not "reconstructive". |
| **49% of folios (f117–f227) have no section mapping** | Half of folios hit global fallback immediately | Accept this. Global mode is already the best prediction rule. UI clearly labels fallback. |
| **Quire mapping is approximate** | Could distort section-boundary assignments | Descoped from blocking. Section map is stable for f1–f116. Quire conditioning was removed as it underperforms global mode. |
| **JS/Python drift in generation logic** | Reproducibility risk | Artifact-first contracts. JS engine reads schedule from data, doesn't recompute offsets. |
| **Overfitting priors to sparse sections** | Unstable generation for Cosmo (2 folios) | Hierarchical smoothing. Cosmo falls back to global priors with warning. |

---

## 8. Non-Goals (Phase 18)

1. No claim that generated page equals true historical folio reconstruction.
2. No semantic decoding or content interpretation.
3. No redesign of lattice solver or replacement of Phase 14 model.
4. No deprecation of existing Folio Generator workflow during rollout.
5. No multi-source transliteration rendering (deferred to P3.3 roadmap).
6. No quire mapping validation (descoped — approximation adequate for current model fidelity).

---

## 9. Execution Order

```
P0.1 Extend run_14x (persist line-level schedule)     ← unblocks P1.1
P0.2 Schema contracts for D2-D3                        ← unblocks P1.1, P1.2
P0.3 Define supported set + fallback policy             ← unblocks P1.1
  │
  ├── P1.1 Build folio_state_schedule.json             ← depends on P0.1-P0.3
  └── P1.2 Build page_priors.json                      ← parallel with P1.1
        │
        └── P2.1 Bundle + loader wiring                ← depends on P1.1, P1.2
              │
              ├── P2.2 Page generator engine (JS)
              └── P2.3 Page generator UI
                    │
                    └── P3 Tests + docs
```

P1.1 and P1.2 can run in parallel. P2.2 and P2.3 are sequential (engine before UI).

---

## 10. Interim Operating Recommendation (Until Phase 18 Execution Completes)

Continue using current workflow:

1. Generate synthetic output with `Folio Generator` (offset=0, user-specified line count).
2. Validate with `IVTFF Validator`.
3. Treat `Page Generator` as planned-only until P0 gates pass.

---

## Appendix A: Expected Output Example (f1r)

For folio f1r (Herbal A, Hand 1, 28 lines observed):

**Schedule resolution:**
- Section: Herbal A → section_mode_offset = 17
- Line-level offsets: available from P0.1 artifact (per-line oracle varies, mode = 17)
- Fallback: none needed (fully section-mapped)

**Expected lattice admissibility:** ~46% (global_mode baseline). Oracle upper bound: ~54%.

**Diagnostics panel would show:**
```
Folio: f1r  |  Section: Herbal A  |  Hand: Hand1
Line count: 28 (observed)  |  Schedule: section_mode (offset=17)
Expected admissibility: ~46% (baseline: 40%, oracle: 54%)
Lines using inferred offset: 28/28  |  Fallback lines: 0
```

---

## Appendix B: Scope Reduction Rationale

### Why transliteration bridge was descoped

1. **Zero existing infrastructure.** No rules, profiles, or metrics exist anywhere in the codebase. Building from scratch is a multi-week effort.
2. **Orthogonal to core value.** The page generator proves folio-specific structural generation works. Source rendering is a presentation concern.
3. **All existing generation is ZL-sanitized.** The Folio Generator, validator, and all analysis scripts use sanitized tokens. Adding multi-source rendering to one tool creates an inconsistency.
4. **Cross-transcription analysis (Phase 14G Sprint 4) already measured independence.** The lattice structure holds across transcriptions; generating in different source styles doesn't add structural evidence.

### Why quire mapping validation was descoped

1. **Per-quire prediction underperforms global mode.** Mask prediction results: global_mode captures 44.2% of oracle gain, per_quire captures only 39.5%. Quire precision doesn't improve the model.
2. **No validated quire table exists.** Building one requires manuscript codicology expertise beyond what the codebase contains.
3. **The `(n-1)//8` approximation is only used in mask_prediction.py,** which is already a secondary analysis. The page generator will use section-level conditioning (which performs identically to global mode for this lattice).
