# Contributing

This repository is a foundational infrastructure project. It is not a translation effort.

Contributions are expected to improve rigor, reproducibility, and falsifiability. If a change introduces hidden assumptions or collapses ambiguity prematurely, it should not be merged.

Before contributing, read:

- README.md
- planning/foundation/PRINCIPLES_AND_NONGOALS.md
- planning/foundation/MASTER_ROADMAP.md
- RULES_FOR_AGENTS.md

---

## Guiding Commitments

All contributions must:

- Respect the current active level in the roadmap
- Preserve ambiguity unless the change is explicitly reversible and justified
- Treat transliterations as third-party indexes, not truth
- Log failures and anomalies as first-class data
- Enforce scale boundaries in code and data
- Include negative controls for any claim of “structure”

---

## Active Level Policy

Work proceeds level by level.

Only the current active level may be modified. Do not implement future-level work “because it will be useful later”. That is how this project becomes unmaintainable.

Current active level:
- Level 1, Data and Identity Foundation

Allowed directories for Level 1 (Foundation):
- src/foundation/
- tests/foundation/
- scripts/foundation/
- configs/

Forbidden (until their levels are active):
- src/analysis/ (except for scaffolding)
- tests/analysis/

---

## Branch and PR Workflow

- Create a feature branch per change.
- Keep PRs small. One conceptual change per PR.
- Include a clear PR description:
  - What problem does this solve?
  - What assumptions does it make?
  - What does it explicitly not assume?
  - How can it fail?
  - How is it tested?

---

## Coding Standards

- Prefer explicit data models (Pydantic) over ad hoc dicts.
- Prefer deterministic IDs over random IDs for core objects.
- No “magic numbers”. All thresholds and costs belong in config.
- Use the shared geometry primitives and coordinate conventions.
- No silent error suppression.
- If you add a warning, also add a way to query it later.

---

## Testing Requirements

All non-trivial changes must include tests.

Minimum expectations:
- Unit tests for logic and invariants
- Golden tests for determinism (IDs, hashes, schemas)

Do not merge changes that reduce test coverage unless the reduction is justified and temporary.

---

## Provenance and Reproducibility Requirements

Any new artifact or derived data output must record:
- run_id
- config hash
- method identifier
- parameter snapshot
- checksums for files

If a change makes outputs non-reproducible, it must not be merged.

---

## Failure and Anomaly Handling

Failures are data.

If you encounter cases where the pipeline cannot proceed cleanly:
- Record an anomaly with severity and category
- Attach diagnostic data and IDs
- Do not “fix” by forcing alignment or collapsing categories

A system that never fails is likely hiding failure modes.

---

## Negative Controls and “Structure” Claims

If a contribution introduces an analysis that discovers structure, it must include at least one of:

- Synthetic null data baseline
- Scrambled Voynich baseline

A result that does not survive controls is likely an artifact of the pipeline.

---

## Review Checklist

Reviewers should verify:

- The change belongs to the active level
- The change respects PRINCIPLES_AND_NONGOALS.md
- Assumptions are stated explicitly
- No irreversible normalization was introduced
- Failures are logged, not suppressed
- Tests exist and pass
- Outputs are reproducible

If any of these fail, request changes.

---

## Versioning and Backward Compatibility

- Avoid breaking schema changes unless necessary.
- If schema changes are required:
  - include migrations
  - bump internal schema version
  - update docs

---

## Security and Data Policy

- Do not commit raw images, transliterations, databases, or run artifacts.
- Keep data in data/raw, data/derived, and runs (all gitignored).
- Do not redistribute copyrighted material improperly.

---

## Contact and Coordination

If you are unsure whether a change belongs in the current level or violates a principle, stop and ask before proceeding.

Overreach is worse than delay.
