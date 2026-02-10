# Execution Plan: Audit 3 Full Remediation

**Source:** `reports/audit/COMPREHENSIVE_AUDIT_REPORT_3.md`
**Findings:** 11 Critical, 22 High, 38 Medium, 16 Low
**Approach:** Grouped into 12 workstreams ordered by dependency and severity.

## Execution Status (2026-02-10)

| Workstream | Status | Notes |
|------------|--------|-------|
| A: Randomness and Reproducibility | COMPLETE | Seed threading and local RNG isolation completed across targeted controls/generators/fallbacks. |
| B: Threshold Externalization | COMPLETE | `configs/analysis/thresholds.json` added and wired into consuming modules. |
| C: Circularity Remediation | COMPLETE | Baseline/circularity dependencies documented and made explicit. |
| D: Placeholder and Simulated Values | COMPLETE | Simulated/default hotspots converted to computed, logged fallback, or documented behavior. |
| E: Silent Defaults and Exception Handling | COMPLETE | Bare exception handlers removed from `src/`; logging added; non-CLI `print` removed. |
| F: Metric Correctness | COMPLETE | RepetitionRate canonical value and ClusterTightness computation-path disclosure aligned. |
| G: Control Symmetry | COMPLETE | Synthetic control token generation fixed; EVAParser bypass rationale documented. |
| H: Output Provenance | COMPLETE | Stress test outputs now include run metadata fields; provenance path in scripts retained. |
| I: Script Structure | COMPLETE | Shared query helpers extracted and mechanism pilots refactored. |
| J: Terminology Standardization | COMPLETE | Token/Word and Page/Folio terminology updates applied to code/docs. |
| K: Documentation | COMPLETE | REPRODUCIBILITY, RUNBOOK, GLOSSARY, README, SENSITIVITY docs updated. |
| L: Test Coverage | COMPLETE | New synthesis/mechanism/human/control tests added; boundary tests expanded. |
| M: I/O Contracts and Type Safety | COMPLETE | Provenance serialization guard + mutation/type-hint docs implemented. |

---

## Workstream A: Randomness and Reproducibility

**Addresses:** C1, C2, C3, C4, H5, H6, R5-R9, CS1
**Priority:** CRITICAL — blocks reproducibility of Phase 3-5 results
**Estimated scope:** 8 files, ~40 call sites

### A1: Convert global `random.seed()` + bare calls to `random.Random(seed)` instances

**Files:**
- `src/foundation/controls/self_citation.py:19-48` (C3) — Replace `random.seed(seed)` + 8 bare `random.*()` calls with `rng = random.Random(seed)` instance. Thread `rng` through all internal calls.
- `src/foundation/controls/synthetic.py:13` (C4, CS1) — Same pattern: replace `random.seed(seed)` with local `rng` instance.
- `src/foundation/controls/table_grille.py:18-56` — Same pattern (discovered in agent scan, not separately numbered). Replace `random.seed(seed)` + `random.choice/randint` with `rng` instance.
- `src/foundation/controls/mechanical_reuse.py:20,44` — Same pattern. Replace global seed with local instance.

### A2: Add seed parameter to unseeded generators

**Files:**
- `src/mechanism/generators/pool_generator.py:27-31` (C1) — Add `seed` parameter to `__init__`, create `self.rng = random.Random(seed)`. Replace `random.choice()`, `random.random()`, `random.randint()` with `self.rng.*()`. Update all callers (mechanism pilot scripts).
- `src/mechanism/generators/constraint_geometry/table_variants.py:47-48` (H6) — Add `seed` parameter, create local `rng`, replace `random.randint(-1, 1)`.

### A3: Seed fallback paths in synthesis

**Files:**
- `src/synthesis/refinement/feature_discovery.py:111,156,203,270,620,677,726` (C2) — The 7 `random.uniform()` fallback calls need a seeded `rng`. Options:
  1. Accept `seed` in constructor, create `self.fallback_rng = random.Random(seed)`.
  2. Or raise an error instead of returning random fallback values (preferred if REQUIRE_COMPUTED is active).
  - Decision: Add `seed` parameter AND log when fallback path is taken.

### A4: Adopt RandomnessController where feasible

**Files (medium priority):**
- `src/synthesis/text_generator.py:308` (H5) — Currently uses `random.Random(seed)` directly. Wire through `RandomnessController.seeded_context()` or at minimum document why controller is bypassed.
- `src/foundation/regions/dummy.py:59` (R8) — Uses `random.Random(self.seed)` correctly; add comment noting controller bypass is intentional for dummy data.
- 8+ files in `src/mechanism/*/simulators.py` (R7) — All correctly seeded with `random.Random(seed)`. Low priority to convert to controller, but add comment explaining pattern.

### A5: Remove `uuid.uuid4()` non-determinism

- `src/foundation/controls/synthetic.py:2` (R9) — If UUID is used for record IDs, replace with `DeterministicIDFactory`. If used for non-critical labels, document why non-determinism is acceptable.

### Verification
- Run `grep -rn "random\." src/ | grep -v "random.Random(" | grep -v "import random" | grep -v "#"` to confirm no bare module-level random calls remain.
- Run `python -m pytest tests/audit/test_determinism.py` to verify seeded reproducibility.

---

## Workstream B: Threshold Externalization

**Addresses:** C8, C9, C10, H8, H9, H11, H12, H13, H19, H20, H21, H22, H12-H18 (operational)
**Priority:** CRITICAL/HIGH — undocumented thresholds determine analysis conclusions
**Estimated scope:** 6 files, 30+ threshold values

### B1: Create centralized threshold config file

Create `configs/analysis/thresholds.json` with sections:
```
{
  "mapping_stability": {
    "perturbation_strength": 0.05,
    "constructed_system": { "ordering_collapse": 0.5, "min_stable": 0.6 },
    "visual_grammar": { "segmentation_collapse": 0.4 },
    "hybrid_system": { "variance_limit": 0.3 },
    "standard_high_confidence": 0.7
  },
  "locality": {
    "radius_thresholds": [2.0, 1.5, 1.0],
    "compositional_scores": [0.7, 0.5, 0.3],
    "procedural_signature": { "repetition": 0.15, "regularity": 0.7, "combined": 0.6 },
    "pattern_type": { "min_radius": 4, "max_radius": 8, "score_threshold": 0.5 },
    "outcome": { "stable": 0.6, "collapsed": 0.4 }
  },
  "indistinguishability": {
    "separation_success": 0.7,
    "separation_failure": 0.3
  },
  "comparator": {
    "significant_difference": 0.05,
    "negligible_difference": 0.02
  },
  "stability_analysis": {
    "representation_sensitivity": { "high": 1.0, "moderate": 0.5, "low": 0.3 }
  },
  "constraint_formalization": {
    "feature_importance_threshold": 0.2,
    "separation_threshold": 0.3
  }
}
```

### B2: Add config loader for analysis thresholds

In `src/foundation/config.py`, add:
```python
def get_analysis_thresholds() -> dict:
    """Load analysis thresholds from configs/analysis/thresholds.json."""
```
Pattern: same as existing `get_model_params()`.

### B3: Wire thresholds into consuming files

**Files to update:**
1. `src/analysis/stress_tests/mapping_stability.py:169,343-393` (C8, H7) — Load from config; replace 8+ hardcoded values.
2. `src/analysis/stress_tests/locality.py:176-183,315-322,389-399,579-584,655-657` (C9, C10, H19, H20, H21) — Load from config; replace 12+ hardcoded values.
3. `src/synthesis/indistinguishability.py:79-80` (H8) — Load separation thresholds.
4. `src/foundation/analysis/comparator.py:33-36` (H9) — Load comparison thresholds.
5. `src/analysis/anomaly/stability_analysis.py:228-247` (H13) — Load sensitivity thresholds.
6. `src/synthesis/refinement/constraint_formalization.py:51,58` (H22) — Load feature thresholds.

### B4: Document rationale for each threshold

Add a `"_rationale"` key or companion section in `docs/CALIBRATION_NOTES.md` for every new config value. At minimum, state whether each value is:
- Empirically derived (from which phase/dataset)
- Theoretically motivated (cite reasoning)
- Arbitrary/conventional (flag for sensitivity analysis)

### Verification
- `grep -rn "0\.\(05\|5\|6\|4\|7\|3\)" src/analysis/stress_tests/` should show config references, not literals.
- All tests pass after refactor.

---

## Workstream C: Circularity Remediation

**Addresses:** C5, C6, C7, CL4, CL5
**Priority:** CRITICAL — circular reasoning undermines core analysis
**Estimated scope:** 2 files, requires design decision

### C1: Decouple BASELINE_* constants from analysis logic

**File:** `src/analysis/anomaly/stability_analysis.py:39-48`

**Options (choose one):**

**(a) Parameterize from caller:** Remove `BASELINE_*` constants. Require callers to pass baseline values explicitly:
```python
def __init__(self, store, baseline_info_density, baseline_locality, baseline_robustness):
```
This makes the data dependency visible and prevents circular embedding.

**(b) Load from database:** Replace constants with a DB query that loads Phase 2.2 results dynamically:
```python
baseline = self.store.get_metric("information_density", dataset_id="voynich_real")
```
Still uses Voynich data, but the dependency is explicit and traceable.

**(c) Document as intentional:** If the analysis deliberately uses observed values as reference points (not as independent validation), add prominent docstring:
```
NOTE: BASELINE values are derived from Voynich Phase 2.2 measurements.
This analysis tests STABILITY of the anomaly under perturbation, not independence from Voynich data.
```

**Recommendation:** Option (a) for clean separation + option (c) for documentation. The stability analysis inherently needs a reference point; the problem is that it's hidden, not that it exists.

### C2: Document circularity in capacity_bounding.py

**File:** `src/analysis/anomaly/capacity_bounding.py:39-44`

The `OBSERVED_*` constants serve a legitimate purpose (establishing what capacity bounds must accommodate), but the circularity risk must be documented. Add docstring explaining:
- These values are Phase 2.2 outputs used as INPUTS to Phase 2.4
- The capacity bounding analysis asks "could a non-semantic system produce these numbers?" not "are these numbers anomalous?"
- Cross-reference `docs/METHODS_REFERENCE.md` for full methodology

### C3: Document circularity in constraint_analysis.py

**File:** `src/analysis/anomaly/constraint_analysis.py:79-207`

Similar treatment: `observed_value` fields are legitimate constraint definitions. Add module-level docstring explaining the data flow and why observed values are used as constraint parameters rather than validation targets.

### C4: Audit feature_discovery fallback values

**File:** `src/synthesis/refinement/feature_discovery.py` (CL5)

The fallback values (0.7, 0.35, etc.) may be tuned to Voynich data. For each fallback:
1. Document where the value came from
2. If derived from Voynich, flag as potentially circular
3. If arbitrary, flag for sensitivity analysis

### Verification
- No `BASELINE_*` constant used without accompanying docstring explaining provenance.
- `docs/METHODS_REFERENCE.md` updated with circularity disclosure section.

---

## Workstream D: Placeholder and Simulated Values

**Addresses:** C11, P1-P6, H9, H10
**Priority:** HIGH — simulated values masquerade as computed results
**Estimated scope:** 3 files, ~15 values

### D1: Replace `positional_entropy=0.40 # Simulated`

**File:** `src/synthesis/indistinguishability.py:120` (C11)

Options:
1. Compute positional entropy from actual token position distributions in the dataset.
2. If computation is infeasible, raise `NotImplementedError` when `REQUIRE_COMPUTED=1`.
3. If kept as estimate, rename to `estimated_positional_entropy` and add warning log.

**Recommendation:** Option 1 if data is available; option 2 otherwise.

### D2: Replace hardcoded defaults in profile_extractor.py

**File:** `src/synthesis/profile_extractor.py:223,236,248` (H10)

- `return 5.2 # Default word length` → compute from actual glyph data or raise if unavailable
- `return 0.20 # Default repetition rate` (2x) → compute from actual token frequencies or raise

For each: add `logger.warning("Using default value for %s: no data available", metric_name)` if defaults are retained.

### D3: Replace feature_discovery fallback values

**File:** `src/synthesis/refinement/feature_discovery.py:111,156,203,270,620,677,726` (H9)

These 7 `random.uniform()` fallbacks are doubly problematic (unseeded AND placeholder). After Workstream A seeds them:
1. Add `logger.warning()` each time a fallback is used.
2. Consider returning `float("nan")` instead of random values, with downstream NaN handling.
3. Document each fallback value's expected range.

### D4: Replace simulated metric base values

**File:** `src/synthesis/text_generator.py:325,330` (P6)

`3.0 + metric_rng.uniform(-0.5, 0.5)` and `3.5 + vocab_ratio * 1.5` are simulated metrics. Either:
1. Compute from actual generated text properties.
2. Add `calculation_method="simulated"` tag to results.
3. Log when simulated path is taken.

### D5: Audit `return {}` stubs in inference analyzers

**Files:** `human/comparative.py:26`, `inference/*/analyzer.py` (P5)

These early-return guards are acceptable for empty input but should:
1. Log a warning when returning empty results.
2. Return a typed empty result (not bare `{}`), e.g., `AnalysisResult(metrics={}, status="no_data")`.

### Verification
- `grep -rn "# Simulated\|# Default\|# Hardcoded" src/` should return zero hits.
- All simulated/default values either computed, logged, or documented.

---

## Workstream E: Silent Defaults and Exception Handling

**Addresses:** S1-S10, H16, LG1-LG3, P7
**Priority:** HIGH — silent failures mask bugs and corrupt results
**Estimated scope:** 12+ files, ~20 handler sites

### E1: Replace high-impact silent defaults

| Finding | File | Current | Remediation |
|---------|------|---------|-------------|
| S1 | `metrics/library.py:148` | Returns `0.5` when no pages | Log warning; return `value=None` or `value=float("nan")` with `details={"status": "no_data"}` |
| S2 | `mapping_stability.py:301` | Returns `0.3` when no controls | Log warning; return `None` and let caller handle |
| S3 | `indistinguishability.py:122` | `info_density` defaults to `4.0` | Log warning; use `REQUIRE_COMPUTED` gate |
| S4 | `perturbation.py:348` | `.get(..., 0)` for coordinates | Replace with explicit `None` check + log |

### E2: Add logging to bare exception handlers

For each of the 8+ silent handlers (H16, LG1):

| File | Line | Current | Remediation |
|------|------|---------|-------------|
| `filesystem.py:68` | `except Exception:` | Add `logger.warning("Atomic write cleanup failed for %s", path, exc_info=True)` |
| `runs/context.py:16` | `except Exception: return "unknown"` | Add `logger.debug("Git revision unavailable", exc_info=True)` |
| `runs/context.py:22` | `except Exception: return "unknown"` | Add `logger.debug("Git status unavailable", exc_info=True)` |
| `quire_analysis.py:31` | `except Exception: return 0` | Narrow to `except (ValueError, IndexError):`; add `logger.warning()` |
| `scribe_coupling.py:34` | `except Exception: return "Unknown"` | Narrow to `except (ValueError, IndexError):`; add `logger.warning()` |
| `network_features/analyzer.py:53` | `except Exception: assortativity = 0.0` | Narrow to specific networkx exception; add `logger.warning()` |
| `runs/manager.py:34,42` | `except Exception:` | Add `logger.debug()` for environment capture failures |
| `qc/checks.py:20` | `except ValueError:` | Add `logger.warning()` with context |

### E3: Replace `print()` with `logger`

| File | Line | Current | Remediation |
|------|------|---------|-------------|
| `qc/anomalies.py:27` (P7) | `print(f"WARNING: ...")` | `logger.warning("Anomaly outside active run: %s", message)` |
| `analysis/sensitivity.py:36` (P7) | `print(f"Error in ...")` | `logger.error("Sensitivity sweep error for %s=%s: %s", param_name, val, e)` |

### E4: Handle `float("nan")` propagation

**File:** `src/synthesis/refinement/feature_discovery.py` (S5)

13 methods return `float("nan")` without caller awareness. Add:
1. Module-level docstring: "Feature computation methods may return `float('nan')` when data is unavailable."
2. In the caller (`DiscriminativeFeatureComputer.compute()`), filter NaN values before aggregation.
3. Add `isnan()` guard in any downstream comparison or sorting logic.

### Verification
- `grep -rn "except Exception:" src/ | grep -v "logger\|logging"` should return zero hits (all handlers now log).
- `grep -rn "^[^#]*print(" src/ | grep -v "cli/"` should return zero hits.

---

## Workstream F: Metric Correctness

**Addresses:** H1/MR1, MR2, H2, H3, H4, TD3
**Priority:** HIGH — ambiguous metrics undermine analysis conclusions
**Estimated scope:** 2 files

### F1: Resolve RepetitionRate dual formula

**File:** `src/foundation/metrics/library.py:88-103` (H1, MR1, TD3)

**Decision needed:** Which formula is canonical?
- `token_repetition_rate` = sum(count for tokens appearing >1) / total_tokens
- `vocabulary_entropy_rate` = 1 - (unique_tokens / total_tokens)

**Recommendation:**
1. Keep `token_repetition_rate` as the primary `value` field.
2. Rename `vocabulary_entropy_rate` to `vocabulary_coverage` (what it actually measures: 1 - type/token ratio).
3. Move `vocabulary_coverage` to a separate metric class or clearly label it as a supplementary statistic.
4. Update `docs/METHODS_REFERENCE.md` to specify which formula is used in all downstream analysis.

### F2: Document ClusterTightness computation path

**File:** `src/foundation/metrics/library.py:156-289` (MR2)

1. Add `computation_path` field to `MetricResult.details` (already has `method` key - verify it's always set).
2. In `docs/METHODS_REFERENCE.md`, document that embedding-based and bbox-based paths produce different scales and are NOT directly comparable.
3. Add a warning log when falling back from embeddings to bboxes: `logger.warning("ClusterTightness falling back to bbox computation for dataset %s", dataset_id)`.

### Verification
- RepetitionRate returns exactly ONE formula as primary `value`.
- ClusterTightness always indicates which method was used in `details["method"]`.

---

## Workstream G: Control Symmetry

**Addresses:** H7, H8, CS2, CS3, CS4, CS5
**Priority:** HIGH — asymmetric controls invalidate comparisons
**Estimated scope:** 3 files

### G1: Fix SyntheticNullGenerator (generates no tokens)

**File:** `src/foundation/controls/synthetic.py:38-43` (H7, CS2)

The generator creates pages and lines but NO tokens. This renders it useless as a null control.

1. After creating line records, generate random tokens (drawn from a flat distribution over the Voynich vocabulary).
2. Store tokens via `add_transcription_line()` so downstream metrics can compute on them.
3. Use a seeded `random.Random(seed)` instance (from Workstream A).

### G2: Document EVAParser bypass in controls

**Files:** `controls/synthetic.py`, `controls/self_citation.py`, `controls/table_grille.py`, `controls/mechanical_reuse.py` (H8, CS3, CS4)

Controls generate tokens programmatically and bypass EVAParser. This is potentially intentional (controls don't need manuscript-specific normalization) but must be documented:

1. Add docstring to each control generator: "Generated tokens bypass EVAParser normalization. This is intentional: control tokens are drawn from the EVA vocabulary directly and do not require manuscript-specific tokenization."
2. In `docs/METHODS_REFERENCE.md`, add a "Control Pipeline" section documenting the asymmetry and its justification.
3. If EVAParser normalization would change control tokens (e.g., glyph clustering), either:
   - Route controls through EVAParser for symmetric treatment, OR
   - Document that EVAParser is a no-op for already-normalized EVA tokens

### Verification
- `SyntheticNullGenerator.generate()` produces datasets with non-zero token counts.
- Each control generator has a docstring explaining its relationship to EVAParser.

---

## Workstream H: Output Provenance

**Addresses:** OV1-OV5
**Priority:** MEDIUM — results lack traceability
**Estimated scope:** 2 files

### H1: Add provenance fields to StressTestResult

**File:** `src/analysis/stress_tests/interface.py:25-47` (OV1)

Add fields:
```python
run_id: Optional[str] = None
timestamp: Optional[str] = None
dataset_id: Optional[str] = None
parameters: Dict[str, Any] = field(default_factory=dict)
```

### H2: Persist stress test results to database

**Files:** `stress_tests/mapping_stability.py`, `locality.py`, `information_preservation.py` (OV2)

Currently, `run()` returns a `StressTestResult` dataclass that is never stored. Options:
1. Add a `store_result()` method that writes to a `stress_test_results` table.
2. Or have the calling scripts store results via `ProvenanceWriter.save_results()`.

**Recommendation:** Option 2 (less invasive). Update calling scripts to wrap results in provenance.

### Verification
- `StressTestResult` objects have `run_id` and `timestamp` populated.
- At least one calling script demonstrates result persistence.

---

## Workstream I: Script Structure

**Addresses:** H14, DS1, DS2
**Priority:** HIGH — duplicated logic causes maintenance drift
**Estimated scope:** 12+ script files, 1 new module

### I1: Extract shared helpers to importable module

Create `src/foundation/core/queries.py` additions (or new `src/foundation/script_helpers.py`):

```python
def get_lines_from_store(store: MetadataStore, dataset_id: str) -> List[List[str]]:
    """Extract tokenized lines from the database. Used by mechanism pilots."""

def get_tokens_and_boundaries(store: MetadataStore, dataset_id: str) -> Tuple[List[str], List[int]]:
    """Extract flat token list and line boundary indices."""
```

### I2: Refactor mechanism pilot scripts

**Files:** `scripts/mechanism/run_5b_pilot.py` through `run_5k_pilot.py` (12 files)

Replace duplicated `get_lines()` / `get_tokens_and_boundaries()` helper functions with imports from the shared module.

### I3: Consider parametric pilot runner

If all 12 pilots follow the same template (load data → instantiate simulator → run → save results), create a generic runner:
```python
def run_mechanism_pilot(simulator_class, config_path, seed, output_dir):
```

**Note:** Only pursue if template is truly uniform. Don't force abstraction if pilots diverge significantly.

### Verification
- `grep -rn "def get_lines" scripts/` returns zero hits (all moved to `src/`).
- All pilot scripts import from shared module.

---

## Workstream J: Terminology Standardization

**Addresses:** H15, TD1, TD2, TD4
**Priority:** MEDIUM — causes confusion, not incorrect results
**Estimated scope:** 6+ files (documentation + code comments)

### J1: Standardize "Word" vs "Token" in alignment code

**File:** `src/foundation/alignment/engine.py:46-73` (H15, TD1)

1. Rename internal variables and parameters for clarity:
   - `word` → keep for `WordRecord` references (visual segments)
   - `token` → keep for transcription text units
2. Update docstrings to use the standard distinction: "Token = transcript text unit, Word = visual image segment."
3. Add module-level docstring clarifying the alignment maps Tokens → Words.

### J2: Document Page vs Folio convention

**Files:** `core/ids.py`, `human/quire_analysis.py`, `synthesis/interface.py` (TD2)

1. Add to `docs/GLOSSARY.md`: "Page: abstract database record. Folio: physical manuscript leaf (e.g., f1r, f2v). In this codebase, PageRecord.id stores folio identifiers."
2. Add docstring to `PageRecord` clarifying the naming convention.
3. No code rename needed — the convention is established, just undocumented.

### J3: Clarify score/metric/value/result terminology

**Scope:** Documentation only (TD4). Add to `docs/GLOSSARY.md`:
- **Value:** A single numeric measurement (e.g., `MetricResult.value`).
- **Metric:** A named measurement type (e.g., RepetitionRate).
- **Score:** An aggregate or derived assessment (e.g., stability_score).
- **Result:** A container holding one or more values with metadata.

### Verification
- `docs/GLOSSARY.md` covers all four terms.
- `alignment/engine.py` docstrings clearly distinguish Word from Token.

---

## Workstream K: Documentation

**Addresses:** H17, H18, Phase 4 findings
**Priority:** HIGH — documentation lag undermines external credibility
**Estimated scope:** 4 docs files

### K1: Execute sensitivity analysis OR retract document

**File:** `docs/SENSITIVITY_ANALYSIS.md` (H17)

The document describes a plan to sweep thresholds and model weights but was never executed.

**Option A (preferred):** Create `scripts/analysis/run_sensitivity_sweep.py` implementing the documented plan:
1. Sweep perturbation thresholds [0.4, 0.8] in 0.05 steps.
2. Sweep model sensitivities ±20%.
3. Sweep evaluation weights with permutations.
4. Stability criterion: >90% of iterations maintain top-ranked model.
5. Store results in `reports/audit/SENSITIVITY_RESULTS.md`.

**Option B (minimum):** Add a prominent "STATUS: NOT YET EXECUTED" banner to `docs/SENSITIVITY_ANALYSIS.md` so readers know results are unavailable.

### K2: Update REPRODUCIBILITY.md for Phase 4-5

**File:** `docs/REPRODUCIBILITY.md` (H18)

Add sections:
1. **Phase 4 (Mechanism Simulation):** List all `scripts/mechanism/run_5*_pilot.py` commands with `--seed` flags.
2. **Phase 5 (Generator Matching):** Document the matching workflow and seed management.
3. **Phase 6-7 (Inference, Human):** List inference and human factor scripts.
4. **Automated Verification:** Reference `scripts/ci_check.sh` and `scripts/verify_reproduction.sh`.

### K3: Update README.md phase status

**File:** `README.md`

Change "Phase 3 Completed" to reflect actual status (through Phase 7).

### K4: Update METHODS_REFERENCE.md

**File:** `docs/METHODS_REFERENCE.md`

1. Add "Known Confounds" subsection for each metric.
2. Document RepetitionRate canonical formula choice (after Workstream F).
3. Document ClusterTightness dual computation paths.
4. Add "Circularity Disclosure" section (after Workstream C).
5. Add "Control Pipeline" section (after Workstream G).

### K5: Update RUNBOOK.md

**File:** `docs/RUNBOOK.md`

1. Complete the Phase 2 section (currently has placeholder content).
2. Add Phase 4-7 execution instructions.

### Verification
- All docs files updated.
- `SENSITIVITY_ANALYSIS.md` either has results or a clear "not executed" notice.

---

## Workstream L: Test Coverage

**Addresses:** Phase 2.4 findings
**Priority:** MEDIUM — current coverage ~15%
**Estimated scope:** 6-8 new test files

### L1: Critical module tests (synthesis)

Create `tests/synthesis/test_text_generator.py`:
- Test `ConstrainedMarkovGenerator.train()` with known input.
- Test `generate_line()` determinism with fixed seed.
- Test boundary cases (empty input, single token).

Create `tests/synthesis/test_grammar_based.py`:
- Test `GrammarBasedGenerator.generate_word()` determinism.
- Test with various seed values.

### L2: Critical module tests (mechanism)

Create `tests/mechanism/test_pool_generator.py`:
- Test `PoolGenerator.generate()` determinism after Workstream A seeds it.
- Test pool replenishment behavior.

### L3: Control generator tests

Create `tests/foundation/test_controls.py`:
- Test each control generator produces non-empty output.
- Test determinism: same seed → same output.
- Test `SyntheticNullGenerator` produces tokens (after Workstream G fix).

### L4: Metric boundary tests (extend existing)

Extend `tests/foundation/test_boundary_cases.py`:
- Test RepetitionRate with 0 tokens, 1 token, all-same tokens.
- Test ClusterTightness fallback from embeddings to bboxes.
- Test NaN handling in downstream consumers.

### L5: Human module tests

Create `tests/human/test_quire_analysis.py`:
- Test `get_quire()` with valid folios.
- Test with malformed folio IDs (after Workstream E narrows exceptions).

### Verification
- `python -m pytest tests/ -v` passes.
- Coverage for synthesis/, mechanism/, and human/ modules > 0%.

---

## Workstream M: I/O Contracts and Type Safety

**Addresses:** IO1-IO4
**Priority:** LOW — correctness risk is minor
**Estimated scope:** 4 files

### M1: Add type validation to ProvenanceWriter

**File:** `src/foundation/core/provenance.py:13` (IO1)

Add a check that `results` is JSON-serializable before writing:
```python
try:
    json.dumps(results)
except TypeError as e:
    raise ValueError(f"Results must be JSON-serializable: {e}")
```

### M2: Document mutation in guarded_shuffle

**File:** `src/foundation/core/randomness.py:130` (IO2)

Add docstring: "Warning: mutates input list in-place (matches stdlib random.shuffle behavior)."

### M3: Add return type hints to public methods

**Files:** `synthesis/text_generator.py`, `alignment/engine.py`, `refinement/feature_discovery.py` (IO3)

Add `-> List[str]`, `-> None`, `-> Dict[str, float]` etc. to the 8+ methods identified.

### Verification
- `mypy src/foundation/core/provenance.py` passes.
- All updated methods have return type annotations.

---

## Execution Order and Dependencies

```
Phase 1 (Parallel):
  ├── Workstream A (Randomness)         ← no dependencies
  ├── Workstream B (Thresholds)         ← no dependencies
  └── Workstream C (Circularity)        ← no dependencies

Phase 2 (Depends on Phase 1):
  ├── Workstream D (Placeholders)       ← depends on A (seeded fallbacks)
  ├── Workstream E (Silent Defaults)    ← no hard dependency, but cleaner after A
  ├── Workstream F (Metrics)            ← no dependencies
  └── Workstream G (Controls)           ← depends on A (seeded generators)

Phase 3 (Depends on Phase 2):
  ├── Workstream H (Provenance)         ← no hard dependency
  ├── Workstream I (Script Structure)   ← no hard dependency
  └── Workstream J (Terminology)        ← no hard dependency

Phase 4 (Depends on Phase 1-3):
  ├── Workstream K (Documentation)      ← depends on B, C, F, G (needs decisions made)
  ├── Workstream L (Test Coverage)      ← depends on A, G (tests against fixed code)
  └── Workstream M (I/O Contracts)      ← no hard dependency
```

## Summary

| Workstream | Priority | Files | Findings Addressed |
|------------|----------|-------|-------------------|
| A: Randomness | Critical | 8 | C1-C4, H5, H6, R5-R9, CS1 |
| B: Thresholds | Critical | 6 | C8-C10, H8-H9, H11-H13, H19-H22 |
| C: Circularity | Critical | 2 | C5-C7, CL4-CL5 |
| D: Placeholders | High | 3 | C11, P1-P6, H9-H10 |
| E: Silent Defaults | High | 12 | S1-S10, H16, LG1-LG3, P7 |
| F: Metrics | High | 2 | H1, H2-H4, MR1-MR2, TD3 |
| G: Controls | High | 3 | H7-H8, CS2-CS5 |
| H: Provenance | Medium | 2 | OV1-OV5 |
| I: Script Structure | Medium | 13 | H14, DS1-DS2 |
| J: Terminology | Medium | 6 | H15, TD1-TD2, TD4 |
| K: Documentation | High | 5 | H17-H18, Phase 4 |
| L: Test Coverage | Medium | 8 new | Phase 2.4 |
| M: I/O Contracts | Low | 4 | IO1-IO4 |
| **Total** | | **~55 files** | **87 findings** |
