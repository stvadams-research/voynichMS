# Cleanup Execution Plan 8: Path Drift, Manifest, CI Governance

**Created:** 2026-02-22
**Status:** COMPLETE
**Trigger:** Team assessment identifying 7 issues; 6 confirmed actionable, 1 already resolved.

---

## Assessment Summary

| # | Finding | Severity | Status |
|:--|:--------|:---------|:-------|
| F1 | Phase 18/19 path drift (`phase18_generate` vs `phase18_comparative`) | **HIGH** | Confirmed — 7+ consumers reference non-existent path |
| F2 | Phase 20 missing from `phase_manifest.json` | MEDIUM | Confirmed — manifest ends at phase_id 19 |
| F3 | Claim map legacy paths (`phase15_selection`, `phase16_physical`) | **HIGH** | Confirmed — 8 claims reference non-existent directories |
| F4 | Bracket parsing bug in claim validator | MEDIUM | Confirmed — `_split_key_path()` can't parse `per_window[18]` |
| F5 | `pyproject.toml` testpaths reference non-existent directories | MEDIUM | Confirmed — 2 stale entries |
| F6 | CI workflow missing governance checks | LOW | Confirmed — `ci.yml` runs lint+tests only; `ci_check.sh` exists but isn't integrated |
| F7 | `STATUS.md` opportunities path reference wrong | LOW | Confirmed — missing `opportunities/` subdirectory |

**Finding 5 (Phase 17 execution plan staleness)** from the original assessment was already resolved in the prior session.

---

## Sprint 1: Path Unification (F1, F3, F5, F7) — HIGH PRIORITY

These are all path-alias inconsistencies that cause silent failures or broken validation.

### Task 1.1: Phase 18 consumer path migration

**Problem:** `build_assets.py` writes to `results/data/phase18_comparative/` (canonical slug). Seven consumers reference `results/data/phase18_generate/` which does not exist.

**Affected files (7):**

| File | Lines | Reference |
|:-----|:------|:----------|
| `src/phase19_alignment/data.py` | 46, 51 | `results/data/phase18_generate/folio_state_schedule.json`, `page_priors.json` |
| `scripts/phase19_alignment/build_folio_match_benchmark.py` | 171 | `results/data/phase18_generate/folio_state_schedule.json` |
| `scripts/phase19_alignment/run_19a_line_conditioned_decoder.py` | 65 | `results/data/phase18_generate/folio_state_schedule.json` |
| `scripts/phase19_alignment/run_19b_retrieval_edit.py` | 65 | `results/data/phase18_generate/folio_state_schedule.json` |
| `scripts/tools/build_workbench_bundle.py` | 20-24, 286-299 | `results/data/phase18_generate/` (2 paths + 2 error messages) |
| `tests/integration/test_phase18_assets.py` | 7-8 | `results/data/phase18_generate/` (2 paths) |

**Also affected (non-code, documentation only):**

| File | Lines | Reference |
|:-----|:------|:----------|
| `tools/workbench/docs/page_generator.md` | 24, 30, 54 | Documentation references |
| `planning/tools/tools_execution_plan.md` | 270, 274-275 | Planning references |
| `planning/phase18_generate/phase_18_execution_plan.md` | 20-22, 80-81 | Execution plan |

**Fix:** Replace all `phase18_generate` path references with `phase18_comparative` in the 7 code files. Update documentation files. The `phase18_generate` alias in `phase_manifest.json` remains valid (it documents the historical name) but data paths must use the canonical slug.

**Verification:** `grep -r "phase18_generate" src/ scripts/ tests/` returns zero code matches.

### Task 1.2: Claim artifact map path correction

**Problem:** 8 claims in `governance/claim_artifact_map.md` reference non-existent directories:
- `results/data/phase15_selection/` (actual: `results/data/phase15_rule_extraction/`)
- `results/data/phase16_physical/` (actual: `results/data/phase16_physical_grounding/`)

**Affected claims:**

| Claim | Current Path | Corrected Path |
|:------|:-------------|:---------------|
| 63 | `results/data/phase15_selection/choice_stream_trace.json` | `results/data/phase15_rule_extraction/choice_stream_trace.json` |
| 64 | `results/data/phase15_selection/bias_modeling.json` | `results/data/phase15_rule_extraction/bias_modeling.json` |
| 65 | `results/data/phase15_selection/bias_modeling.json` | `results/data/phase15_rule_extraction/bias_modeling.json` |
| 66 | `results/data/phase16_physical/effort_correlation.json` | `results/data/phase16_physical_grounding/effort_correlation.json` |
| 67 | `results/data/phase16_physical/layout_projection.json` | `results/data/phase16_physical_grounding/layout_projection.json` |
| 77 | `results/data/phase15_selection/selection_drivers.json` | `results/data/phase15_rule_extraction/selection_drivers.json` |
| 78 | `results/data/phase15_selection/selection_drivers.json` | `results/data/phase15_rule_extraction/selection_drivers.json` |
| 79 | `results/data/phase15_selection/selection_drivers.json` | `results/data/phase15_rule_extraction/selection_drivers.json` |

**Fix:** Find-and-replace in `governance/claim_artifact_map.md`:
- `phase15_selection/` → `phase15_rule_extraction/`
- `phase16_physical/` → `phase16_physical_grounding/`

**Verification:** Run `python scripts/core_audit/check_claim_artifact_map.py` — all 8 claims should resolve.

### Task 1.3: pyproject.toml testpaths correction

**Problem:** Two entries in `pyproject.toml` `testpaths` (lines 121-122) reference non-existent directories:
- `tests/phase15_selection` (actual: `tests/phase15_rule_extraction`)
- `tests/phase16_physical` (actual: `tests/phase16_physical_grounding`)

**Fix:** Update testpaths to canonical directory names.

**Verification:** `python -m pytest --collect-only` shows tests from the corrected directories.

### Task 1.4: STATUS.md path fix

**Problem:** Line 228 references `planning/opportunities_execution_plan.md` — actual path is `planning/opportunities/opportunities_execution_plan.md`.

**Fix:** Update the path in STATUS.md.

**Verification:** Visual inspection.

---

## Sprint 2: Manifest & Validator Fixes (F2, F4) — MEDIUM PRIORITY

### Task 2.1: Add Phase 20 to phase manifest

**Problem:** `configs/project/phase_manifest.json` ends at phase_id 19. Phase 20 (state machine codebook architecture) is complete but not registered.

**Fix:** Add Phase 20 entry:
```json
{
  "phase_id": 20,
  "canonical_slug": "phase20_state_machine",
  "aliases": [],
  "release_scope": "release",
  "replicate_entry": "scripts/phase20_state_machine/replicate.py"
}
```

**Pre-check:** Verify `scripts/phase20_state_machine/replicate.py` exists. If not, create a minimal replicate stub consistent with other phases.

**Verification:** Run `python scripts/core_audit/check_phase_manifest.py` — should pass with 20 phases.

### Task 2.2: Fix bracket index parsing in claim validator

**Problem:** `scripts/core_audit/check_claim_artifact_map.py` function `_split_key_path()` (line 105-106) splits on `.` only:

```python
def _split_key_path(path: str) -> list[str]:
    return [segment for segment in path.split(".") if segment]
```

This cannot parse bracket indices like `per_window[18]` (claim 192: `results.codebook_estimation.per_window[18].words`). The split produces `["results", "codebook_estimation", "per_window[18]", "words"]` and `per_window[18]` won't match any dict key.

**Fix:** Update `_split_key_path()` to decompose bracket indices into separate segments:

```python
def _split_key_path(path: str) -> list[str]:
    segments: list[str] = []
    for raw in path.split("."):
        if not raw:
            continue
        # Decompose bracket indices: "per_window[18]" → ["per_window", "18"]
        while "[" in raw:
            bracket_start = raw.index("[")
            bracket_end = raw.index("]", bracket_start)
            prefix = raw[:bracket_start]
            index = raw[bracket_start + 1 : bracket_end]
            if prefix:
                segments.append(prefix)
            segments.append(index)
            raw = raw[bracket_end + 1 :]
        if raw:
            segments.append(raw)
    return segments
```

The existing `_json_key_exists()` already handles numeric list indexing (lines 128-131), so once `_split_key_path()` produces `["per_window", "18"]`, the lookup will work correctly for both dict keys and list indices.

**Verification:** Run `python scripts/core_audit/check_claim_artifact_map.py` — claim 192 should resolve without error.

---

## Sprint 3: CI Governance Integration (F6) — LOW PRIORITY

### Task 3.1: Add governance checks to GitHub Actions

**Problem:** `.github/workflows/ci.yml` runs only:
1. Lint (ruff)
2. Unit tests (pytest, ignoring integration)
3. Import smoke test

The comprehensive `scripts/ci_check.sh` includes 15+ governance checks (claim map, phase manifest, sensitivity contracts, skeptic policies, provenance, closure conditionality, etc.) but is not invoked from GitHub Actions.

**Context:** The governance checks require the full data pipeline artifacts (JSON result files, core_status files). These are not available in a fresh CI checkout — they're generated by `reproduce.yml`. Running the full `ci_check.sh` in CI would require either:
- (a) A two-stage pipeline where `reproduce.yml` runs first and caches artifacts, or
- (b) A subset of governance checks that only validate structural properties (file existence, JSON schema, markdown table parsing) without requiring pipeline outputs.

**Recommended approach (b):** Add a lightweight governance step to `ci.yml` that runs only the structural validators:

```yaml
- name: Governance structural checks
  run: |
    python scripts/core_audit/check_phase_manifest.py
    python scripts/core_audit/check_claim_artifact_map.py || echo "::warning::Claim artifact map has unresolved paths (data artifacts may not be present in CI)"
```

These two scripts validate:
- Phase manifest schema and completeness (no data dependency)
- Claim map path existence and JSON key resolution (requires data artifacts — run as warning-only in CI, blocking in `ci_check.sh`)

**Full governance remains in `ci_check.sh`** for local and post-reproduce validation. The CI workflow is intentionally lightweight for fast PR feedback.

**Verification:** Push a test branch and confirm the governance step runs in GitHub Actions.

---

## Execution Order

| Order | Task | Sprint | Estimated Scope |
|:------|:-----|:-------|:----------------|
| 1 | 1.1 — Phase 18 path migration | Sprint 1 | 7 code files, 3 doc files |
| 2 | 1.2 — Claim map path correction | Sprint 1 | 1 file, 8 claims |
| 3 | 1.3 — pyproject.toml testpaths | Sprint 1 | 1 file, 2 lines |
| 4 | 1.4 — STATUS.md path fix | Sprint 1 | 1 file, 1 line |
| 5 | 2.1 — Phase 20 manifest entry | Sprint 2 | 1-2 files |
| 6 | 2.2 — Bracket parsing fix | Sprint 2 | 1 file, 1 function |
| 7 | 3.1 — CI governance step | Sprint 3 | 1 file |

## Verification Protocol

After all fixes:
1. `grep -r "phase18_generate" src/ scripts/ tests/` — zero code matches
2. `grep -r "phase15_selection" governance/` — zero matches
3. `grep -r "phase16_physical[^_]" governance/` — zero matches
4. `python scripts/core_audit/check_phase_manifest.py` — PASS (20 phases)
5. `python scripts/core_audit/check_claim_artifact_map.py` — PASS (all 251 claims)
6. `python -m pytest tests/ --ignore=tests/integration -q --tb=short -x` — PASS
7. `ruff check .` — PASS
