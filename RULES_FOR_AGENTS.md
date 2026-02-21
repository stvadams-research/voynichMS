# RULES FOR AGENTS
## Voynich Foundation Project

This document defines mandatory rules for any human or AI agent contributing code, analysis, or artifacts to this repository.

These rules exist to prevent conceptual drift, premature interpretation, and accumulation of unfalsifiable structure.

They are not suggestions.

---

## 1. Read Before Acting

Before writing any code or proposing any change, an agent must read:

1. README.md  
2. planning/phase1_foundation/PRINCIPLES_AND_NONGOALS.md  
3. CONTRIBUTING.md

If a proposal contradicts any of these documents, it must not be implemented.

---

## 2. Determinism Is Absolute

Agents must NEVER introduce non-deterministic behavior.

- **Forbidden:** `uuid.uuid4()`, `random.random()`, `np.random.rand()` (without seed).
- **Mandatory:** Use `foundation.core.id_factory.DeterministicIDFactory` for all IDs.
- **Mandatory:** Use seeded `random.Random(seed)` or `np.random.RandomState(seed)` for stochastic logic.
- **Mandatory:** Expose a `seed` parameter in all entry points (CLI, scripts).

---

## 3. Computation, Not Simulation

Agents must respect the `REQUIRE_COMPUTED=1` standard.

- Do not write code that returns hardcoded "placeholder" values for metrics.
- Do not use "simulated" fallbacks in production paths.
- If a metric cannot be computed from data, raise an error or log an anomaly.

---

## 4. No Interpretation, No Meaning

Agents must not:

- speculate about meaning
- assume language
- identify symbols (beyond visual similarity)
- normalize glyphs (without explicit justification)
- infer semantics

This project is about **structure**, not meaning.

---

## 5. Image Geometry Is Law

When there is disagreement between:

- image geometry, and
- transliterations or assumptions

The image always wins.

Agents must never adjust geometry to fit transcription.

---

## 6. Transliterations Are Indexes Only

Transliterations are third-party artifacts, not truth.

Agents must not:
- Treat them as ground truth.
- "Fix" them to match expectations.
- Depend on a single source without verifying invariance (Test B).

---

## 7. Failures Are Data

Errors and anomalies are valuable.

Agents must:
- Log failures explicitly.
- Store anomalies in the database.
- Never "fix" failures silently.

---

## 8. Scale Boundaries

Every object belongs to a scale (Page, Line, Word, Glyph, Region).

Agents must not:
- Mix scales implicitly.
- Apply word-level logic to glyphs without explicit adaptation.

---

## 9. Negative Controls Are Mandatory

If an agent proposes an analysis that finds "structure", they must also propose:
- A synthetic null control.
- A scrambled baseline.

A result that does not survive controls is an artifact.

---

## 10. No Irreversible Decisions

Agents must not introduce:
- Fixed alphabets.
- Canonical symbol sets.
- Irreversible normalization.

Reversibility is a hard requirement.

---

## 11. Maintenance of Status

Agents must ensure `results/reports/` and `governance/` are kept up to date.

- Upon completing a phase, generate a `FINAL_REPORT_PHASE_X.md`.
- Ensure `governance/RUNBOOK.md` reflects the current execution commands.

---

## 12. Engineering Rigor (CI Compliance)

Agents must ensure all code is compliant with the repository's engineering standards BEFORE declaring a task complete.

- **Mandatory Linting:** All Python code must pass `ruff check .`.
- **Mandative Provenance:** All new runner scripts (`run_*.py`) MUST include a `ProvenanceWriter.save_results()` call to satisfy the SK-M4 contract.
- **Mandatory Preflight:** Agents must execute `./scripts/core_audit/preflight_check.sh` and verify it passes before finishing a turn.
- **Robustness:** Scripts must handle missing environment artifacts (like the database) gracefully to prevent CI crashes.

---

## Final Statement

This project values:

- **Rigor** over speed.
- **Clarity** over novelty.
- **Falsifiability** over excitement.

If you find yourself trying to be clever, you are probably doing the wrong thing.