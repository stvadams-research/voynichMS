# RULES FOR AGENTS
## Voynich Foundation Project

This document defines mandatory rules for any human or AI agent contributing code, analysis, or artifacts to this repository.

These rules exist to prevent conceptual drift, premature interpretation, and accumulation of unfalsifiable structure.

They are not suggestions.

---

## 1. Read Before Acting

Before writing any code or proposing any change, an agent must read:

1. README.md  
2. planning/foundation/PRINCIPLES_AND_NONGOALS.md  
3. planning/foundation/MASTER_ROADMAP.md  

If a proposal contradicts any of these documents, it must not be implemented.

---

## 2. Respect the Active Level

Work is organized into strict levels.

- Only the **current active level** may be modified.
- Code or artifacts belonging to future levels are forbidden.

Current active level:
- **Level 1: Data and Identity Foundation**

This means:

Allowed:
- src/foundation/
- configs/
- tests/foundation/
- scripts/foundation/

Forbidden:
- src/analysis/ (except scaffolding)
- experiments/

If code “feels useful later”, it belongs later.

---

## 3. No Interpretation, No Meaning

Agents must not:

- speculate about meaning
- assume language
- identify symbols
- normalize glyphs
- infer semantics
- “clean up” variation

This project is not about being clever.
It is about being correct.

---

## 4. Image Geometry Is Law

When there is disagreement between:

- image geometry, and
- transliterations or assumptions

The image always wins.

Agents must never adjust geometry to fit transcription.

---

## 5. Transliterations Are Indexes Only

Transliterations:

- are third-party artifacts
- encode assumptions we do not accept
- may be wrong or inconsistent

Agents must not:

- treat them as truth
- normalize them
- “fix” them
- prefer one source silently

Multiple transliterations must be allowed to coexist.

---

## 6. Preserve Ambiguity

Agents must not force decisions early.

Forbidden behaviors include:
- collapsing categories prematurely
- choosing “best” segmentation
- enforcing 1:1 mappings
- deleting uncertainty

If something is ambiguous, it must remain ambiguous.

---

## 7. Failures Are Data

Errors and anomalies are valuable.

Agents must:

- log failures explicitly
- store anomalies in the database
- avoid suppressing warnings
- never “fix” failures silently

A system that never fails is lying.

---

## 8. Enforce Scale Boundaries

Every object belongs to a scale.

Examples:
- page
- line
- word
- glyph_candidate
- region

Agents must not:
- mix scales implicitly
- apply word-level logic to glyphs
- apply region-level logic to words

Cross-scale operations must be explicit and validated.

---

## 9. Negative Controls Are Mandatory

If an agent proposes an analysis that finds “structure”, they must also propose:

- a synthetic null control, or
- a scrambling test

If a result survives controls, it matters.
If it does not, it is an artifact.

---

## 10. No Irreversible Decisions

Agents must not introduce:

- fixed alphabets
- canonical symbol sets
- irreversible normalization
- semantic labels

Reversibility is a hard requirement.

---

## 11. Prefer Ledgers Over Models

This project prefers:

- explicit data tables
- queryable artifacts
- clear provenance

Over:
- opaque end-to-end models
- black-box inference
- hidden assumptions

Models may come later. Ledgers come first.

---

## 12. Document Assumptions Explicitly

Every non-trivial function, module, or script must declare:

- what it assumes
- what it does not assume
- what would falsify its usefulness

If assumptions cannot be stated, the code is not ready.

---

## 13. Stop Conditions Are Required

Agents must define:

- success criteria
- failure criteria
- stop conditions

“Looks promising” is not a criterion.

---

## 14. When in Doubt, Stop

If an agent is unsure whether something belongs:

- in the current level
- in this project at all
- or violates a principle

The correct action is to stop and ask.

Overreach is worse than delay.

---

## 15. Maintain Status Documentation

Agents must ensure the `status/foundation/` folder is kept up to date. This is a critical default behavior.

- **IMMEDIATELY** upon completing a level or significant phase, update the corresponding `LEVEL_XX.md` file to **COMPLETED**.
- Ensure all deliverables and verification steps are checked off in the status file.
- Create the next level's status file as **PENDING** if it does not exist.
- This ensures the project state is always instantly queryable and prevents "lost" progress.

---

## Final Statement

This project values:

- rigor over speed
- clarity over novelty
- falsifiability over excitement

Agents are expected to act accordingly.

If you find yourself trying to be clever, you are probably doing the wrong thing.
