# Unreferenced Module Triage

**Date:** 2026-02-22  
**Status:** Active  
**Source audit:** `planning/support_cleanup/cleanup_execution_plan3.md`

This register tracks modules previously identified as unreferenced/low-coverage
and classifies them by publication risk.

Canonical machine-readable source:
- `configs/project/unreferenced_module_tiers.json`

Validation command:

```bash
python3 scripts/core_audit/check_unreferenced_module_tiers.py
```

---

## Current Counts

- Critical-path modules tracked: **2**
- Critical-path modules still open: **0**
- Non-critical deferred modules: **4**

---

## Critical Path (Closed)

| Module | Status | Evidence |
|---|---|---|
| `src/phase1_foundation/metrics/library.py` | Covered | `tests/phase1_foundation/metrics/test_library.py` |
| `src/phase1_foundation/core/id_factory.py` | Covered | `tests/phase1_foundation/core/test_id_factory.py` |

These two modules were prioritized because they affect publication-facing
metrics and deterministic reproducibility behavior.

---

## Non-Critical Deferred

| Module | Status | Rationale |
|---|---|---|
| `src/phase2_analysis/models/disconfirmation.py` | Deferred | Coordinator over already-tested components |
| `src/phase1_foundation/hypotheses/library.py` | Deferred | Data-definition heavy, lower bug-impact surface |
| `src/phase7_human/ergonomics.py` | Deferred | Not on release-critical claim path |
| `src/phase4_inference/projection_diagnostics/discrimination.py` | Deferred | Niche metric, indirectly exercised |

Deferred modules remain in the register for future opportunistic coverage
expansion, but they are not release blockers.
