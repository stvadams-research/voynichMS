# CODE_AUDIT_AND_CLEANUP_PLAYBOOK.md
## Voynich Project, Pre-Publication Code Audit and Cleanup

---

## Objective

Prepare the project codebase for public release by ensuring:

- No results depend on hidden assumptions, placeholders, or hardcoded behavior.
- All methods are explicit, parameterized, and reproducible.
- The codebase is internally consistent in structure, naming, and execution.
- The analysis pipeline can be understood and rerun by an external reader.
- Documentation clearly separates method, configuration, and interpretation.

The goal is to remove anything that could cause a reader to question:
- whether results were implicitly “baked in”
- whether methods drifted during experimentation
- whether conclusions depend on undocumented choices

---

## Scope and Philosophy

### What this audit covers
- Correctness and clarity of analytical methods
- Explicitness of assumptions and parameters
- Reproducibility of numerical results
- Structural consistency across the codebase
- Documentation sufficient for independent replication

### What this audit does not cover
- Performance tuning unless it affects correctness
- Aesthetic refactoring unrelated to clarity
- Feature expansion or methodological changes

---

## Expected Outputs

By the end of this process, you should have:

1. `AUDIT_LOG.md`  
   A running list of issues found, decisions made, and fixes applied.

2. `METHODS_REFERENCE.md`  
   A plain-language description of every metric, method, and analysis step.

3. `CONFIG_REFERENCE.md`  
   A complete inventory of parameters, defaults, and their effects.

4. `REPRODUCIBILITY.md`  
   Step-by-step instructions to rerun the entire analysis deterministically.

5. Clean, readable code with no silent behavior.

---

## Phase 0, Inventory and Orientation

### Task 0.1 Identify All Executable Paths

List every way results are produced:
- scripts
- notebooks
- command-line entry points
- functions called manually

Outcome:
- one clearly identified “primary execution path”
- secondary paths either removed or documented as exploratory

### Task 0.2 File and Module Inventory

Create a list of:
- analysis modules
- helper utilities
- data loading and preprocessing code
- visualization code
- configuration files
- data assets (fixtures vs full corpora)

This prevents “orphan logic” from influencing results unnoticed.

---

## Phase 1, Results Integrity Audit (Assumption and Hardcoding Hunt)

### Goal
Ensure no conclusions depend on unexamined or hidden decisions.

### Task 1.1 Placeholder and Temporary Code Search

Search the entire codebase for:
- TODO, FIXME, HACK, TEMP, DEBUG
- commented-out logic
- placeholder values
- partially implemented branches

Action:
- remove
- fully implement
- or explicitly document as non-contributing

Record each in `AUDIT_LOG.md`.

---

### Task 1.2 Hardcoded Values and Magic Numbers

Identify:
- numeric thresholds
- window sizes
- entropy cutoffs
- distance weights
- section boundaries
- token lists or filters

For each:
- move into a named parameter
- give it a default
- document why that default exists
- state whether changing it affects published results

---

### Task 1.3 Silent Defaults and Implicit Behavior

Look for:
- library defaults not explicitly set
- implicit sorting or ordering
- dictionary or set iteration used as if ordered
- conditional behavior triggered by `None` or missing values

Action:
- make defaults explicit
- add comments explaining why they are acceptable
- document them in `CONFIG_REFERENCE.md`

---

### Task 1.4 Randomness and Non-Determinism

Identify any source of randomness:
- random sampling
- shuffling
- stochastic algorithms
- probabilistic initializations

Requirements:
- all randomness must be controllable
- deterministic mode must exist
- random behavior must be documented and justified

If stochastic output is retained:
- document expected variance
- show that conclusions are stable

---

### Task 1.5 Circularity and Data Leakage Checks

Audit for:
- parameters chosen because they “match Voynich”
- tuning based on target outputs
- reuse of results to justify method choices

Rule:
- methods must be defined independently of results
- any fitting to Voynich must be labeled as illustrative, not evidentiary

---

### Task 1.6 Control and Baseline Symmetry

For every analysis:
- confirm identical preprocessing for:
  - Voynich
  - controls
  - synthetic generators
- ensure identical tokenization, segmentation, and normalization

Add a simple validation:
- identical corpora must produce identical outputs regardless of label

---

### Task 1.7 Output Provenance Metadata

Every generated result should include:
- date/time of run
- parameter configuration used
- corpus identifier
- script or function name

This can be a header, sidecar file, or embedded metadata.

---

## Phase 2, Method Correctness and Internal Consistency

### Goal
Ensure each method means exactly one thing everywhere it appears.

### Task 2.1 Metric Registry

Create a central registry listing:
- metric name
- conceptual definition
- inputs and outputs
- parameters
- implementation location

Ensure:
- no duplicate metrics with subtle differences
- no “versioned” metrics without documentation

---

### Task 2.2 Input and Output Contracts

For core functions:
- validate inputs (types, shapes)
- define output structure clearly
- avoid implicit coercion or mutation
- ensure stable ordering where order matters

---

### Task 2.3 Canonical Preprocessing Pipeline

Ensure a single shared implementation exists for:
- text normalization
- tokenization
- segmentation (lines, pages, sections)
- filtering rules

All analysis must use this pipeline.

---

### Task 2.4 Unit-Level Validation

For each metric:
- test on small, known inputs
- test boundary cases (empty, minimal, degenerate)
- test invariances (renaming tokens, reordering where appropriate)

These do not need a framework, simple assert-based scripts are sufficient.

---

### Task 2.5 End-to-End Sanity Checks

Create a minimal fixture set:
- small Voynich excerpt
- small natural-language excerpt
- small synthetic corpus

Lock expected outputs numerically (within tolerance).
This prevents accidental drift later.

---

## Phase 3, Structural and Naming Consistency

### Goal
Make the code readable and predictable to outsiders.

### Task 3.1 Directory and File Structure

Ensure a clear separation between:
- analysis logic
- execution scripts
- data assets
- documentation

Avoid:
- logic embedded in notebooks only
- duplicated scripts with minor variations

---

### Task 3.2 Terminology Discipline

Enforce consistent vocabulary:
- token vs glyph vs state
- line vs page vs section
- generator vs corpus vs artifact

Avoid semantic terms unless explicitly discussing semantics.

---

### Task 3.3 Logging and Error Clarity

Replace ad hoc prints with:
- consistent status messages
- clear error descriptions
- actionable failure explanations

---

## Phase 4, Documentation for External Readers

### Goal
Allow someone else to understand and rerun the work without guidance.

### Task 4.1 README (Minimal Publishing Standard)

README should include:
- project purpose
- scope and limitations
- high-level pipeline overview
- how to run the analysis
- expected outputs
- runtime expectations

---

### Task 4.2 Methods Documentation

`METHODS_REFERENCE.md` should explain:
- each metric conceptually
- how it is computed
- why it exists
- what it does and does not measure
- known confounds

---

### Task 4.3 Configuration Documentation

`CONFIG_REFERENCE.md` should list:
- all parameters
- defaults
- rationale
- sensitivity notes

---

### Task 4.4 Reproducibility Instructions

`REPRODUCIBILITY.md` should contain:
- exact commands or steps to rerun analyses
- deterministic mode instructions
- how to run a minimal demo
- common failure modes

---

## Phase 5, External-Critique Simulation

### Goal
Anticipate reviewer skepticism.

### Task 5.1 Skeptical Reader Checklist

Answer explicitly:
- Where are assumptions stated?
- Which parameters matter most?
- What happens if they change?
- How do we know this is not tuned?
- What evidence is negative or null?

Each answer should point to code or documentation.

---

### Task 5.2 Clean-Room Re-Execution

From a fresh environment:
- follow `REPRODUCIBILITY.md`
- confirm outputs match expected values
- log discrepancies and resolve them

---

## Severity Levels for Audit Log

Use the following categories:

- **Critical**: could change conclusions
- **High**: could materially alter numbers
- **Medium**: correctness or clarity risk
- **Low**: style or maintainability

---

## Known High-Risk Areas for This Project

Pay special attention to:
- tokenization and segmentation
- reset definitions
- history window logic
- generator parameterization
- distance normalization
- visualization smoothing or binning

---

## Definition of “Done”

This audit is complete when:

- Every parameter is explicit
- Every method is documented
- All outputs are reproducible
- No silent assumptions remain
- A skeptical reader can rerun and audit the work

At that point, the codebase is ready to be released as a methodological artifact.
