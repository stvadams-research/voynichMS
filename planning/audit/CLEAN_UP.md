# VoynichMS Audit-Ready Cleanup Plan
**Objective:** Make the codebase audit-ready for external scrutiny by tightening the engineering foundation first (code quality, determinism, tests, structure), then tightening internal docs and results capture, and only then producing a public-facing findings document.

**Guiding rule:** No new research claims while the foundation is being tightened. This is a stabilization pass, not a discovery pass.

---

## 0. Definitions and Success Criteria

### “Audit-ready” means an outsider can:
- Clone the repo and run a minimal reproducible pipeline from scratch.
- Verify that outputs are computed (not simulated) under enforcement rules.
- Trace any headline number to:
  - a specific RunID
  - a specific config
  - a specific dataset/ledger hash
  - a specific metric implementation
- See tests that fail if:
  - simulation paths are used
  - randomness leaks into computed paths
  - determinism is broken
  - schemas drift

### Deliverables of this cleanup phase
- A stable, documented folder structure and naming convention.
- A consistent results and run artifact format.
- Strong automated tests (unit, integration, determinism, enforcement).
- A clean CI run (local or GitHub Actions, whichever you use) proving green.
- A concise internal “engineering runbook” to reproduce key runs.

---

## 1. Phase 1: Freeze and Inventory (Foundation Lock)
**Goal:** Stop drift, identify what exists, and define what “clean” means.

### 1.1 Freeze rules
- No new features.
- No refactors that change behavior without a locked baseline run.
- No new metrics.
- No new datasets.
- Any necessary change must be justified as:
  - correctness fix
  - determinism enforcement
  - testability improvement
  - naming/structure stabilization

### 1.2 Baseline capture (before changes)
- Pick 1 canonical run per major stage (Phase 2, Phase 3.2, Phase 3.3).
- Record for each:
  - RunID
  - config file
  - environment snapshot (Python version, package lock)
  - dataset/ledger hash
  - outputs folder path
- Store these as “golden references” (not for truth claims, for regression control).

### 1.3 Repo inventory checklist
- Enumerate modules:
  - ledger generation
  - metrics
  - controls
  - synthesis/generation
  - admissibility logic
  - reporting
- Identify:
  - unused modules
  - duplicate utilities
  - dead scripts
  - legacy prototypes
- Inventory dependency managers:
  - requirements.txt / poetry / uv / pip-tools
  - package-lock / pnpm-lock (if JS exists)
- Identify entry points:
  - CLI commands
  - scripts
  - notebooks

**Exit criteria**
- You can point to “the” current pipeline entry point.
- You have baseline run artifacts saved and immutable.

---

## 2. Phase 2: Naming and Folder Structure Normalization
**Goal:** Make the repo navigable and boring. Remove ambiguity.

### 2.1 Naming convention decision (one-time)
Choose and enforce:
- snake_case for file and folder names
- no spaces
- no mixed case for paths
- consistent suffixes for scripts, configs, and reports

### 2.2 Folder structure target (example template)
You can adjust, but pick a stable target:

- `src/` core library code (no scripts)
- `tools/` one-off utilities (audits, migrations)
- `cli/` command entry points (thin wrappers)
- `tests/` unit and integration tests
- `configs/` canonical configs (versioned)
- `runs/` run artifacts (immutable, structured)
- `data/` raw inputs + ledgers (immutable or write-once)
- `results/` human-facing outputs generated from `runs/`
- `docs/` internal technical docs (not public report)
- `papers/` or `reports/` for public-facing writeups (later phase)

### 2.3 File relocation and compatibility
- Replace hardcoded paths with a centralized path resolver.
- Add a deprecation period if necessary:
  - stubs that redirect old paths
  - warnings for old paths
- Decide where notebooks live:
  - either `notebooks/` with clear “non-audited exploratory” label
  - or remove from audited branch entirely

**Exit criteria**
- There is one obvious place for each class of artifact.
- A new contributor can guess where to add a new metric or test.
- No “misc”, “tmp”, “old”, “final_final”, or time-stamped folders in root.

---

## 3. Phase 3: Determinism, Enforcement, and Provenance Hardening
**Goal:** Ensure the repo cannot accidentally produce untrustworthy outputs.

### 3.1 Enforcement invariants (must never regress)
- `REQUIRE_COMPUTED=1` hard-fails if anything simulated is used.
- No RNG in computed paths (already your rule).
- Seeds required and logged for synthesis/control paths.
- Every metric output includes:
  - computed/simulated/cached flag
  - input dataset hash
  - code version hash (git commit)
  - config hash
  - run timestamp

### 3.2 Provenance schema stabilization
Define a strict schema for run artifacts, at minimum:
- `run.json` (RunID, timestamps, git commit, command)
- `config.json` (fully expanded config, no references)
- `inputs.json` (ledger hashes, dataset version)
- `coverage.json` (ComputationTracker output)
- `metrics.jsonl` or `metrics/` folder (one file per metric)

Define immutability rules:
- Run folders are write-once.
- Derived reports go to `results/`, not `runs/`.

### 3.3 Caching policy
- Make caching explicit:
  - cache keys must include config and dataset hash
  - cache directory separate from results
- Under `REQUIRE_COMPUTED=1`, cached values must still be traceable to a computed origin run.

**Exit criteria**
- You can delete `results/` and regenerate it from `runs/`.
- You can delete caches and still reproduce key runs deterministically.

---

## 4. Phase 4: Code Quality Refactor Pass (Behavior-Preserving)
**Goal:** Reduce drift and fragility without changing results.

### 4.1 Refactor constraints
- Any refactor must have:
  - a pre-refactor baseline run
  - a post-refactor run with matching outputs (within declared tolerances)
- Prefer small PR-sized steps.

### 4.2 Remove duplication and clarify boundaries
- Separate:
  - pure functions (metrics)
  - IO and orchestration (pipeline runners)
  - visualization/report generation
- Enforce “no side effects in metrics” (except logging).

### 4.3 Style and static checks
Pick a minimal set and enforce:
- formatting (one formatter, automatic)
- linting (one linter)
- type checks (where feasible)
- import ordering
- docstrings policy (short, not essays)

### 4.4 Dead code policy
- Move deprecated code to `archive/` with a clear label, or delete it.
- Anything left must be either:
  - executed by pipeline
  - imported by pipeline
  - tested

**Exit criteria**
- The pipeline code path is readable top-to-bottom.
- There is no “mystery module” that isn’t used or tested.

---

## 5. Phase 5: Test Coverage and Test Design (The Big One)
**Goal:** Make your prior audit failure impossible to repeat.

### 5.1 Test categories (minimum set)
1) **Unit tests**
- metrics operate on controlled small ledgers
- adjacency rules (q->o, y->END, etc.) verified

2) **Enforcement tests**
- simulation path triggers failure under `REQUIRE_COMPUTED=1`
- RNG usage triggers failure in computed code paths

3) **Determinism tests**
- same inputs + same config => bitwise-identical outputs (or declared stable hashes)
- RunID determinism where required

4) **Integration tests**
- end-to-end pipeline on a tiny fixture dataset
- golden output hashes for key metrics

5) **Schema tests**
- run artifacts must validate against schema
- missing required metadata fails tests

### 5.2 Coverage goals
- Do not chase 100%.
- Prioritize coverage of:
  - enforcement
  - determinism
  - any code that outputs a published number
- Track coverage trends but do not let it become the project.

### 5.3 Fixtures
- Create a miniature “toy ledger” fixture:
  - small but representative
  - includes edge cases
- Create a “known-bad” fixture to test failure modes.

**Exit criteria**
- You have a test suite that would have caught the earlier simulation placeholders.
- CI is green and reproducible locally.

---

## 6. Phase 6: CI and Reproducible Environment
**Goal:** Make reproducibility mechanical.

### 6.1 Environment lock
- Choose one:
  - `uv` / `poetry` / `pip-tools` / `conda`
- Require a lockfile or pinned dependencies.
- Record platform assumptions (OS, Python version).

### 6.2 CI pipeline (minimum)
- lint/format check
- unit tests
- integration tests
- determinism check on fixture
- schema validation

**Exit criteria**
- A stranger can run the same checks locally as CI.

---

## 7. Phase 7: Internal Results and Documentation Tightening (Not Public Report Yet)
**Goal:** Make internal artifacts coherent and traceable before writing anything public.

### 7.1 Standardize result capture
- Every phase output goes through one reporting mechanism.
- No ad hoc markdown scattered across random folders.
- Reports reference RunIDs and configs explicitly.

### 7.2 Documentation targets (internal)
- `RUNBOOK.md` (how to run, how to reproduce baseline)
- `ARCHITECTURE.md` (modules, data flow)
- `DATASETS.md` (what ledgers exist, how built)
- `METRICS.md` (definitions, references to code)
- `GLOSSARY.md` (lay definitions of key terms)

### 7.3 Cleanup old artifacts
- Move provisional documents to `archive/` with a header:
  - “Provisional, pre-audit”
- Keep them, but label them clearly.

**Exit criteria**
- A reviewer can locate every claim’s underlying run.
- A new reader can understand the repo layout without tribal knowledge.

---


---

## 10. Execution Order (What You Do Next)
1) Phase 1: Freeze and Inventory
2) Phase 2: Naming and Folder Structure
3) Phase 3: Determinism and Provenance
4) Phase 5: Tests (start early, expand continuously)
5) Phase 4: Refactor (only as tests make it safe)
6) Phase 6: CI and environment lock
7) Phase 7: Internal docs and results tightening

---

## “Stop Conditions” for Cleanup
Cleanup is done when:
- CI is green
- baseline runs reproduce
- run artifacts follow schema
- enforcement tests prove no simulation fallback
- naming and structure are stable
- every published number is traceable to code + run + data hash

At that point, writing can begin without fear of retraction-by-audit.
