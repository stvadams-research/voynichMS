# CODE AUDIT REPORT
## Voynich Manuscript Project – Phase 1 & Phase 2 Independent Review

**Audit Date:** 2026-02-07
**Auditor:** Claude Opus 4.5 (Independent Technical Review)
**Scope:** Code correctness, methodological integrity, reproducibility, output validity

---

## EXECUTIVE SUMMARY

This core_audit examined the Phase 1 (Foundation) and Phase 2 (Analysis) codebases for alignment between documentation claims and actual implementation. The review reveals a **critical architectural gap**: while the framework design is methodologically sound with proper abstractions and explicit falsification requirements, the **implementations are predominantly simulations that do not perform the documented analyses**.

**Overall Assessment:** The codebase is **not defensible as a methodological contribution** in its current form. The documented findings are derived from hardcoded values and predetermined logic paths, not from actual data phase2_analysis or perturbation experiments.

---

## 1. CODE CORRECTNESS AUDIT

### 1.1 Implementations Match Documentation?

| Module | Claimed Function | Actual Implementation | Match? |
|--------|------------------|----------------------|--------|
| `metrics/library.py` | Compute token repetition rate | Returns hardcoded 0.15 (real) or 0.02 (scrambled) | **NO** |
| `metrics/library.py` | Compute cluster tightness | Returns `random.uniform(0.5, 0.8)` | **NO** |
| `hypotheses/library.py` | Calculate glyph position entropy | Returns hardcoded 0.40 (real) or 0.95 (scrambled) | **NO** |
| `hypotheses/destructive.py` | Perturb word boundaries, measure stability | Returns formula `0.15 + (p * 4.0) + (p² * 10)` | **NO** |
| `stress_tests/mapping_stability.py` | Test segmentation stability | Returns constant 0.625 | **NO** |
| `stress_tests/locality.py` | Calculate local/global similarity | Returns constants 0.65/0.35 | **NO** |
| `stress_tests/information_preservation.py` | Measure information density | Returns 0.7 or 0.3 based on dataset_id string | **NO** |
| `models/disconfirmation.py` | Run perturbation battery | Uses hardcoded degradation formulas | **NO** |
| `admissibility/manager.py` | Evaluate constraints against evidence | Actually queries database and evaluates | **YES** |

**Finding:** 8 of 9 core analytical modules are simulations, not computations.

### 1.2 Bugs and Logical Errors

| Location | Issue | Severity |
|----------|-------|----------|
| `core/ids.py:36` | `infer_folio_id` returns `FolioID` but declares `Optional[str]` | LOW |
| `core/ids.py:48` | `RunID` uses random UUID, breaks reproducibility | HIGH |
| `core/queries.py:54` | `find_similar_regions` returns `random.random()` scores | CRITICAL |
| `runs/manager.py:6` | `_current_run` is class-level mutable state, not thread-safe | HIGH |
| `storage/filesystem.py:28` | File writes are not atomic | MEDIUM |

### 1.3 Misleading Naming

| Code Element | Name Suggests | Actual Behavior |
|--------------|---------------|-----------------|
| `_test_segmentation_stability()` | Tests stability under segmentation perturbation | Returns constant 0.625 |
| `_calculate_local_similarity()` | Computes similarity from data | Returns constant 0.65 |
| `apply_perturbation()` | Applies perturbation to data | Computes formula with no data access |
| `test_prediction()` | Tests prediction against evidence | Cites Phase 1 summaries, declares pass/fail |

---

## 2. METHODOLOGICAL INTEGRITY AUDIT

### 2.1 Explicit Assumptions

The codebase documents several assumptions explicitly:
- Word boundaries as meaningful units (stated in hypotheses)
- Segmentation produces fixed glyph classes (stated in destructive tests)
- Information density is measurable (stated in interface)

**Assessment:** Explicit assumptions are appropriately documented at the interface level.

### 2.2 Implicit/Hidden Assumptions

| Assumption | Location | Impact |
|-----------|----------|--------|
| Dataset identification by name pattern ("scrambled", "synthetic") | Throughout | Tautological test results |
| Phase 1 findings are valid numerical constants | All stress tests | Circular reasoning |
| Vocabulary size = 8000 | capacity_bounding.py | Unvalidated constraint |
| "Non-semantic" systems don't use meaning | semantic_necessity.py | Semantic judgment hidden as definition |
| Perturbation formula coefficients (4.0, 10.0) | destructive.py | Unjustified assumptions |

### 2.3 Semantic Leakage Detection

**Critical Finding:** The Phase 2.4 semantic necessity test is circular.

1. The anomaly definition (`interface.py:42`) includes `all_nonsemantic_models_failed: bool = True`
2. The semantic necessity test (`semantic_necessity.py`) then tests whether non-semantic models fail
3. The anomaly is **defined** by what the test is supposed to **discover**

**Additional semantic leakage:**
- `constraint_analysis.py:108-113`: "Natural language ruled inadmissible" is a semantic category, not a structural measurement
- `visual_grammar.py:141-145`: "Diagram dependency" test passes based on "spatial locality," not actual diagram phase2_analysis

### 2.4 Stopping Conditions

| Module | Documented Stopping Condition | Actually Enforced? |
|--------|------------------------------|-------------------|
| Stress tests | "terminate when constraints become unreasonably complex" | NO - no iteration limits |
| Disconfirmation | "stop testing if model fails" | YES - but masks failure characterization |
| Semantic necessity | "terminate if all non-semantic systems fail" | CIRCULAR - assumes conclusion |

### 2.5 Negative Result Symmetry

**Issue:** Failed predictions do not propagate to model status.

- `constructed_system.py:126-132`: `proc_p3` explicitly fails (`prediction.passed = False`)
- `interface.py:139-143`: Status only updates from `disconfirmation_log`, not failed predictions
- Result: Model "survives" despite failed predictions

---

## 3. REPRODUCIBILITY AUDIT

### 3.1 Seeds and Parameters

| Component | Seed Tracked? | Parameters Stored? |
|-----------|--------------|-------------------|
| Control dataset generation | YES | YES |
| Sensitivity phase2_analysis | NO | YES |
| Stability phase2_analysis | NO | N/A |
| Perturbation tests | N/A (hardcoded) | N/A (hardcoded) |
| RunID | NO (random UUID) | YES |

**Critical Gap:** `RunID` uses `uuid.uuid4()` making runs impossible to reproduce deterministically.

### 3.2 Provenance Tracking

| Element | Tracked? |
|---------|---------|
| Git commit hash | YES |
| Git working directory status | YES (boolean only) |
| Command-line arguments | YES |
| Config parameters | YES |
| Intermediate results | NO |
| NumPy/TensorFlow seeds | NO |

### 3.3 Can Phases Be Reproduced?

| Phase | Reproducible? | Blocker |
|-------|--------------|---------|
| Phase 1 | PARTIAL | RunID random, no ML seed management |
| Phase 2.1 | YES | Admissibility manager is deterministic |
| Phase 2.2 | NO | Stress tests return hardcoded constants |
| Phase 2.3 | NO | Disconfirmation uses hardcoded formulas |
| Phase 2.4 | NO | Stability phase2_analysis uses invented values |

---

## 4. OUTPUT VALIDITY AUDIT

### 4.1 Documented Findings vs. Code Output

**Phase 2.3 Execution Plan claims (Section 12.2):**
> "Adjacency Grammar: 0.84 degradation at strength 0.10"

**Actual code (`visual_grammar.py:170-180`):**
```python
base_degradation = {
    "anchor_disruption": 0.70,
}.get(perturbation_type, 0.30)
degradation = min(1.0, base_degradation * (1 + strength * 2))
# At strength 0.10: degradation = 0.70 * 1.20 = 0.84
```

**Assessment:** The documented value matches the code output—but both are derived from a hardcoded formula, not measurement. The finding is **internally consistent but empirically meaningless**.

### 4.2 Tables and Summaries

| Reported Finding | Source | Issue |
|-----------------|--------|-------|
| "z=4.00 information density" | information_preservation.py | Hardcoded (not measured) |
| "Locality radius 2-4" | locality.py | Hardcoded ratio → always radius=4 |
| "35% glyph collapse at 5% perturbation" | destructive.py | Formula output, not experiment |
| "5/6 models falsified" | run_phase_2_3.py | Based on hardcoded thresholds |

### 4.3 Conclusions Bounded by Data?

**Finding:** Conclusions are bounded by **hardcoded constants**, not actual data.

The manuscript is never analyzed. Instead:
1. Phase 1 findings are embedded as constants
2. Simulations produce predetermined values
3. Thresholds are set to trigger expected conclusions
4. Implications are written as if they arose from testing

---

## 5. CRITICAL ISSUES

### 5.1 Critical (Must Fix)

1. **Metrics are simulated, not computed** (`metrics/library.py`)
   - RepetitionRate returns hardcoded values
   - ClusterTightness returns random noise
   - No actual data phase2_analysis occurs

2. **Perturbation tests are formulas, not experiments** (`hypotheses/destructive.py`)
   - No boundary shifting occurs
   - No re-segmentation performed
   - No glyph identity comparison
   - Results from mathematical formula

3. **Stress tests return constants** (`stress_tests/*.py`)
   - mapping_stability: 0.625, 0.70, 0.65, 0.30
   - locality: 0.65, 0.35, 0.55
   - information_preservation: 0.7 or 0.3 by string matching

4. **Model disconfirmation is performative** (`models/disconfirmation.py`)
   - Degradation values from hardcoded base_degradation
   - No actual perturbation of manuscript data
   - Models test their own predictions

5. **Semantic necessity test is circular** (`anomaly/semantic_necessity.py`)
   - Anomaly definition assumes non-semantic failure
   - Test then "discovers" non-semantic failure
   - Conclusion embedded in premise

### 5.2 High Severity

1. RunID non-deterministic (breaks reproducibility)
2. RunManager not thread-safe
3. No iteration limits in stress tests
4. Failed predictions don't update model status
5. Evidence schema inconsistent (no validation)

### 5.3 Medium Severity

1. Type annotation mismatches in ids.py
2. Non-atomic file writes
3. Nullable foreign keys may cause silent data loss
4. Arbitrary thresholds without justification
5. Early stopping in perturbation battery

---

## 6. NON-CRITICAL SUGGESTIONS

1. Add `calculation_method` field to `MetricResult` ("computed" vs "simulated")
2. Use TypedDict for query return structures
3. Implement proper confidence intervals for findings
4. Add `decision_sequence_number` for temporal tracking
5. Capture environment details (Python version, package versions)
6. Separate simulation utilities from production code
7. Add feature flags for real vs simulated mode
8. Document all threshold justifications

---

## 7. FINAL DETERMINATION

### Is this codebase and phase2_analysis defensible as a methodological contribution?

**NO.**

The framework design is excellent:
- Clean abstractions with explicit interfaces
- Proper falsification requirements in model definitions
- Sound provenance tracking architecture
- Appropriate separation of concerns

However, the implementations systematically replace measurement with simulation:
- Metrics return hardcoded values, not computations
- Perturbation tests use formulas, not experiments
- Stress tests return constants, not data-driven results
- Model disconfirmation is performative, not genuine

**The documented findings cannot be trusted** because they derive from predetermined logic paths, not actual data phase2_analysis.

### What Would Make It Defensible?

1. Replace all hardcoded metric implementations with actual computations
2. Implement genuine perturbation (shift boundaries, re-segment, measure)
3. Compute stress test values from actual data, not constants
4. Make model disconfirmation use real manuscript data
5. Separate semantic necessity definition from semantic necessity testing
6. Add validation that distinguishes "computed" from "simulated" results

### Positive Elements

Despite the critical issues, these elements are sound:
- `admissibility/manager.py` - Actually evaluates constraints against evidence
- `decisions/registry.py` - Proper decision logging with justification
- `storage/metadata.py` - Comprehensive provenance schema
- Interface designs throughout - Clear contracts and abstractions

---

## 8. EVIDENCE SUMMARY

| Audit Criterion | Assessment |
|-----------------|-----------|
| Code does what documentation claims | **FAIL** (8/9 modules simulated) |
| Analytical process internally consistent | **PARTIAL** (framework good, implementations fake) |
| Outputs follow from inputs and methods | **FAIL** (outputs are predetermined) |
| No hidden semantic assumptions | **FAIL** (multiple semantic leakage points) |
| Negative results properly justified | **FAIL** (asymmetric handling) |

---

**End of Audit Report**
