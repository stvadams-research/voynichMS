# Project Packaging Gaps

**Created:** 2026-02-20
**Context:** Post-cleanup audit looking beyond code quality at project-level
consistency — documentation, CI, test infrastructure, and cross-references.
**Note:** Research outputs and results are solid. These are all "packaging" issues.

---

## High Priority

### 1. RESOLVED — pyproject.toml missing packages and test paths

Added `phase10_admissibility` and `phase11_stroke` to `packages.include`.
Added `tests/phase4_inference`, `tests/phase6_functional`, and
`tests/phase10_admissibility` to `testpaths`.

### 2. RESOLVED — README quick-start references non-existent scripts

Removed references to `generate_definitive_paper.py` and `assemble_draft.py`
(never existed). Fixed `scripts/core_audit/verify_reproduction.sh` →
`scripts/verify_reproduction.sh`.

### 3. RESOLVED — Broken cross-reference across 28 files (case mismatch)

Replaced `results/reports/FINAL_PHASE_3_3_REPORT.md` with
`results/reports/phase3_synthesis/final_phase_3_3_report.md` across 28 files
in `results/reports/core_skeptic/`, `results/reports/core_audit/`, and
`planning/core_skeptic/`.

### 4. RESOLVED (prior CI fix) — CLI import bug blocks test collection

Fixed 3 wrong imports in `src/phase1_foundation/cli/main.py`:
`phase1_foundation.phase2_analysis.*` → `phase1_foundation.analysis.*`.

---

## Medium Priority

### 5. RESOLVED (prior CI fix) — The 23 "pre-existing" test failures

All 23 failures resolved across prior CI fix session:
- 12 synthetic test failures: missing `mkdir(parents=True)` in 5 test files
- 9 repo-state failures: wrong file paths in 8 policy JSON configs
- 1 path assertion: `results/phase5_mechanism/` → `results/data/phase5_mechanism/`
- 1 timestamp freshness: hardcoded dates → dynamic `_now_utc()`

Test suite: 770 passed, 0 failed.

### 6. NON-ISSUE — ARCHITECTURE.md lists phantom `src/phase9_conjecture/`

ARCHITECTURE.md already correctly states "Phase 9 is narrative synthesis only —
no computation" (line 46) and does not list `src/phase9_conjecture/` in the
directory layout. No action needed.

### 7. RESOLVED — CHANGELOG references non-existent files

Fixed `governance/GLOSSARY.md` → `governance/glossary.md`. Removed reference to
`governance/REPLICATION_GUIDE.md` (never created; replication instructions live
in root `replicateResults.md`).

---

## Low Priority

### 8. RESOLVED — Duplicate governance documentation

Replaced `governance/architecture.md` (57-line outdated subset) with a redirect
to the authoritative root `ARCHITECTURE.md`.

### 9. RESOLVED — Governance subdirectories missing for later phases

Created `governance/phase10_admissibility/` and `governance/phase11_stroke/`
with `.gitkeep` files. Phase 9 directory already existed.

---

## Results Coherence (no issues found)

- 398 data files, 72 reports, complete provenance tracking
- All run IDs cross-reference correctly between stage summaries and by_run/
- Phase 4: 5 methods claimed (A-E), exactly 5 result files
- Phase 10: 6 methods claimed (F-K), exactly 6 result files
- Publication outputs (PDF, DOCX) present and intact
- Artifact provenance (run_id, git_commit, timestamp, seed) consistent throughout

---

## Status: ALL RESOLVED

| Item | Status |
|---|---|
| Fix pyproject.toml (packages + testpaths) | RESOLVED |
| Fix README quick-start paths | RESOLVED |
| Fix 28-file case-mismatch reference | RESOLVED |
| Fix CLI import bug | RESOLVED (prior CI fix) |
| Fix 23 pre-existing test failures | RESOLVED (prior CI fix) |
| Clarify Phase 9 in ARCHITECTURE.md | NON-ISSUE |
| Fix CHANGELOG references | RESOLVED |
| Consolidate duplicate governance docs | RESOLVED |
| Add missing governance subdirectories | RESOLVED |
