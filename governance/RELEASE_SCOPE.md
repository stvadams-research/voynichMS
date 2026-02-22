# Release Scope Policy

**Date:** 2026-02-21  
**Status:** Active

This document defines what is considered release-canonical versus exploratory
work so external researchers can reproduce claims without ambiguity.

---

## 1. Release-Canonical Scope

The current release-canonical replication surface is **Phases 1-17 and 20**
(18 phases total).

Primary entrypoint:

```bash
python3 scripts/support_preparation/replicate_all.py
```

Default orchestration runs release-canonical phases only (1-17, 20).

Canonical phase definitions are sourced from:

- `configs/project/phase_manifest.json`

This path is the authoritative basis for release claims in top-level project
surfaces (`README.md`, `STATUS.md`, publication outputs).

---

## 2. Exploratory Scope

**Phases 18-19** are currently exploratory/post-publication extensions.

These phases may produce valid artifacts, tests, and planning outputs, but they
are not part of the default release-canonical replication contract unless
explicitly promoted.

Exploratory orchestration is opt-in:

```bash
python3 scripts/support_preparation/replicate_all.py --include-exploratory
```

---

## 3. Claim Surface Rules

1. Claims in release-facing documents must be reproducible from the
   release-canonical scope.
2. Claims from exploratory phases may appear in:
   - planning artifacts
   - phase-local reports
   - governance claim tracking
3. Promotion from exploratory to release-canonical requires:
   - stable replication entrypoint
   - artifact and provenance coherence checks
   - documentation updates across release-facing docs
   - explicit update of this policy document

---

## 4. Path Convention

Release evidence artifacts and reports are canonical under:

- `results/data/`
- `results/reports/`

The legacy root `reports/` path is not canonical for release evidence.

---

## 5. Phase Alias Normalization

Alias resolution is canonicalized in `configs/project/phase_manifest.json`.

| Phase | Canonical Slug | Aliases |
|---|---|---|
| 15 | `phase15_rule_extraction` | `phase15_selection` |
| 16 | `phase16_physical_grounding` | `phase16_physical` |
| 18 | `phase18_comparative` | `phase18_generate` |

Rule: release-facing docs and orchestration must use canonical slugs; aliases
may appear only when referring to historical output directories or legacy paths.

---

## 6. Script Interface Tiers

CLI guarantees are tiered to separate external researcher entrypoints from
internal helpers.

Canonical policy and script inventory:

- `governance/SCRIPT_INTERFACE_TIERS.md`
- `configs/project/script_interface_tiers.json`

Validation command:

```bash
python3 scripts/core_audit/check_script_interface_contract.py
```
