# Contributing

This repository is a foundational infrastructure project. It is not a translation effort.

Contributions are expected to improve rigor, reproducibility, and falsifiability. If a change introduces hidden assumptions or collapses ambiguity prematurely, it should not be merged.

Before contributing, read:

- README.md
- planning/phase1_foundation/PRINCIPLES_AND_NONGOALS.md
- planning/phase1_foundation/ROADMAP.md
- RULES_FOR_AGENTS.md
- governance/RUNBOOK.md

---

## 1. Audit-Ready Standards (Non-Negotiable)

This codebase is maintained in an **Audit-Ready** state. Any contribution that breaks these invariants will be rejected.

### Determinism
- **No `uuid.uuid4()`:** You must use `phase1_foundation.core.id_factory.DeterministicIDFactory`.
- **No `random.` or `np.random`:** You must use seeded generators passed from the config.
- **Seeded Runs:** Every CLI command or script must accept a `--seed` argument.

### Enforcement
- **REQUIRE_COMPUTED=1:** All pipeline code must run successfully with this environment variable set.
- **No Simulations:** Do not add "placeholder" values for metrics. If you cannot compute it, fail.

### Provenance
- **Artifact Schema:** All runs must produce `run.json`, `config.json`, `inputs.json`, and `outputs.json`.
- **Traceability:** Every metric output must be traceable to a specific RunID and dataset hash.

---

## 2. Active Level Policy

Work proceeds level by level. Do not implement future-level work “because it will be useful later”.

**Current Phase:** Phase 8 (Visualization and Publication) - Active.

Allowed directories:
- `src/`
- `tests/`
- `scripts/`
- `configs/`
- `planning/support_preparation/`

---

## 3. Branch and PR Workflow

- Create a feature branch per change.
- Keep PRs small. One conceptual change per PR.
- Include a clear PR description:
  - What problem does this solve?
  - What assumptions does it make?
  - How is it tested?
  - Does it preserve determinism?

---

## 4. Coding Standards

- **Explicit Data Models:** Use Pydantic schemas for all internal data structures.
- **No Magic Numbers:** All thresholds and costs belong in `configs/`.
- **Shared Primitives:** Use `phase1_foundation.core.geometry` for all spatial logic.
- **Error Handling:** No silent error suppression. Fail fast or log an anomaly.

---

## 5. Testing Requirements

All changes must include tests.

**Minimum expectations:**
- **Unit tests:** For logic and invariants.
- **Enforcement tests:** Prove that your code respects `REQUIRE_COMPUTED`.
- **Determinism tests:** Prove that running twice with the same seed yields identical output.

Run `scripts/ci_check.sh` locally before pushing.

---

## 6. Review Checklist

Reviewers should verify:

- The change respects `PRINCIPLES_AND_NONGOALS.md`.
- No `uuid.uuid4()` or unseeded randomness exists.
- `REQUIRE_COMPUTED` is respected.
- Artifacts are generated correctly.
- Tests pass and cover the new logic.

---

## 7. Security and Data Policy

- Do not commit raw images, transliterations, databases, or run artifacts.
- Keep data in `data/raw`, `data/derived`, and `runs` (all gitignored).
- Do not redistribute copyrighted material improperly.

---

## Contact and Coordination

If you are unsure whether a change belongs in the current level or violates a principle, stop and ask before proceeding.

Overreach is worse than delay.