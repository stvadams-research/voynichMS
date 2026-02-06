# MIGRATION_PLAN_FOUNDATION_TO_INFERENCE.md
## Voynich Project – Phase 1 Freeze and Phase 2 Enablement

This document provides explicit, executable instructions for migrating the current monolithic
voynich package into a frozen Foundation substrate and a clean, extensible Phase 2 layer,
without breaking existing behavior or contaminating the epistemic guarantees of Phase 1.

This is not a refactor for elegance.
This is a contractual migration.

---

## 1. Purpose of This Migration

The project has completed its foundational mandate (Levels 0–6).
The next work requires interpretive risk, which must not pollute the foundation.

This migration exists to:

- Freeze Phase 1 as a stable, immutable substrate
- Enable Phase 2 work under strict dependency rules
- Preserve all existing outputs, tests, and provenance
- Allow growth without architectural drift

---

## 2. Naming Philosophy

Phases are planning concepts, not architectural concepts.

Folder and package names must encode purpose and mutability, not timeline.

Therefore:

- Phase 1 becomes voynich_foundation
- Phase 2 becomes voynich_analysis

Phase labels remain roadmap-only.

---

## 3. Current State

All implementation currently lives under src/voynich and mixes substrate and interpretation.

---

## 4. Target State

Two sibling Python packages under src:

src/
- voynich_foundation/
- voynich_analysis/
- voynich/ (compatibility shim)

voynich_foundation contains all current implementation.
voynich_analysis contains all Phase 2 work.

---

## 5. Foundation Public API

Public API means the only surface Phase 2 may depend on.

Required actions:

- Create voynich_foundation/api.py
- Export stable constructs only
- Re-export in voynich_foundation/__init__.py
- Phase 2 may import only from voynich_foundation or voynich_foundation.api

---

## 6. Migration Steps

1. Create new packages
2. Move existing code to voynich_foundation
3. Add voynich compatibility shim
4. Update imports
5. Update pyproject.toml
6. Freeze schema contract

---

## 7. Data Rules

Foundation outputs are immutable.
Analysis outputs must be separate.

---

## 8. CLI Rules

Keep existing CLI behavior.
Add analysis subcommands later.

---

## 9. Tests and Fixtures

Existing tests validate foundation.
Phase 2 tests are separate.

---

## 10. Project-Level Documents

Roadmaps, status files, and principles remain project-level and immutable.

---

## 11. Guardrails

- Approval required for foundation changes
- CI blocks deep imports
- Phase 2 must declare dependencies

---

## 12. Acceptance Criteria

Migration is complete when all tests pass and Phase 1 outputs are identical.

---

## 13. Final Statement

This migration separates evidence from interpretation.
