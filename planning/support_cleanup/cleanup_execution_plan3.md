# Final Audit Pass

**Created:** 2026-02-20
**Purpose:** Post-cleanup sweep to identify any remaining high-ROI items.
**Methodology:** Parallel audits of test gaps, code quality, and documentation
completeness, cross-referenced against all work done in cleanup plans 1 and 2.

---

## Audit Results

### Code Quality: CLEAN

Full scan of all 163 source files found:

- **Bare `except:` clauses:** None (all use typed exceptions)
- **Unseeded randomness:** None (all use `random.Random(seed)` + `require_seed_if_strict`)
- **Mutable default arguments:** None
- **Unguarded division:** None (all division operations have zero-checks)
- **TODO/FIXME/HACK comments:** Zero in src/
- **Known dual-formula issue (RepetitionRate):** Documented, both paths compute same metric
- **Known dual-path issue (ClusterTightness):** Documented, result includes `"method"` indicator

No action needed.

### Documentation: COMPLETE

All governance documents exist with substantive content:

| Document | Status | Lines |
|---|---|---|
| governance/glossary.md | 50+ domain terms | 221 |
| ARCHITECTURE.md | System overview, DB schema, design decisions | 301 |
| PHASE_DEPENDENCIES.md | DAG, I/O table, time estimates | 120 |
| governance/THRESHOLDS_RATIONALE.md | 50+ thresholds justified | 169 |
| governance/PAPER_CODE_CONCORDANCE.md | All 15 chapters mapped | Real content |
| governance/DEVELOPER_GUIDE.md | 3 walkthroughs + conventions | Real content |
| CHANGELOG.md | Version history through current sprint | Real content |
| README.md | Quick-start in 4 steps | Real content |

Config files lack inline comments but are documented externally in
THRESHOLDS_RATIONALE.md. Sufficient for reproducibility.

No action needed.

### Test Coverage: Two Remaining High-ROI Gaps

The exploration agent flagged ~11 untested modules, but cross-referencing against
tests written in cleanup plan 2 shows most are already covered. After filtering:

**Actually untested modules that matter:**

| Module | LOC | Used By | Why It Matters |
|---|---|---|---|
| `phase1_foundation/metrics/library.py` | 331 | 5 Phase 3 scripts | RepetitionRate and ClusterTightness produce publication metrics. A calculation bug here silently corrupts results. |
| `phase1_foundation/core/id_factory.py` | 144 | 8+ scripts | DeterministicIDFactory is foundational for reproducible ID generation across populate_database, Phase 3, and Phase 4. |

**Modules flagged but already tested (no action needed):**

- `anomaly/capacity_bounding.py` — TestCapacityBoundingAnalyzer (12 tests)
- `anomaly/constraint_analysis.py` — TestConstraintIntersectionAnalyzer (9 tests)
- `anomaly/stability_analysis.py` — TestAnomalyStabilityAnalyzer (12 tests)
- `models/evaluation.py` — TestCrossModelEvaluator (7 tests)
- `models/perturbation.py` — TestPerturbationCalculator (8 tests)
- `adversarial/metrics.py` — TestAdversarialAnalyzer* (multiple classes)
- `projection_diagnostics/ncd.py` — TestNCDAnalyzer
- `projection_diagnostics/kolmogorov_proxy.py` — TestKolmogorovProxyAnalyzer
- `projection_diagnostics/line_reset_*.py` — TestLineReset* generators

**Lower-priority untested modules (not worth dedicated effort):**

| Module | LOC | Assessment |
|---|---|---|
| `models/disconfirmation.py` | 206 | Orchestrator over already-tested components |
| `hypotheses/library.py` | 214 | Data definitions, low bug risk |
| `phase7_human/ergonomics.py` | 157 | Single analyzer, not on critical path |
| `projection_diagnostics/discrimination.py` | 273 | Niche metric, tested indirectly via integration |

---

## Recommendations

### Worth doing (2 items)

**R1. Test `metrics/library.py` (RepetitionRate + ClusterTightness)**

331 LOC, imported by 5 scripts that produce publication tables. Tests should cover:
- RepetitionRate: compute() with known token lists, verify formula matches docs
- ClusterTightness: both computation paths (embeddings vs bboxes), fallback behavior
- Edge cases: empty input, single-token input, all-identical tokens

Estimated scope: ~15-20 tests.

**R2. Test `core/id_factory.py` (DeterministicIDFactory)**

144 LOC, imported by 8+ scripts including populate_database (the data pipeline entry
point). Tests should cover:
- Same seed produces same IDs
- Different seeds produce different IDs
- Sequential ID generation is deterministic
- ID format/uniqueness guarantees

Estimated scope: ~8-10 tests.

### Not worth doing

Everything else. The codebase is clean, well-documented, and has comprehensive test
coverage across all critical paths. The 13 remaining open findings from cleanup plan 2
are all lower-priority items (Phase 1/3/7 module coverage, minor code quality) with
diminishing returns.

---

## Execution

### R1. RESOLVED — `metrics/library.py` tests

**File:** `tests/phase1_foundation/metrics/test_library.py` (22 tests)

Tests written:
- RepetitionRate: no-pages NaN, no-tokens NaN, known rate (5/6), no repetitions (0.0),
  all-identical (1.0), single token, vocabulary_coverage, top_5_tokens, multi-page
  aggregation, word-alignment fallback, result metadata
- ClusterTightness: no-pages NaN, identical embeddings (1.0), known embedding distance
  (1/3), insufficient embeddings NaN, bbox fallback, bbox insufficient regions NaN,
  bbox ignores non-mid scale, identical bboxes (1.0), embedding stats (std/min/max),
  tightness range (0,1], result metadata

**Bug found and fixed:** SQLAlchemy `Row` objects were not unpacked by
`isinstance(t, tuple)` check at `library.py:81`, causing `top_5_tokens` dict to have
tuple keys like `{('a',): 3}` instead of `{'a': 3}`. Fixed to use
`hasattr(t, '__getitem__') and not isinstance(t, str)`.

### R2. RESOLVED — `core/id_factory.py` tests

**File:** `tests/phase1_foundation/core/test_id_factory.py` (20 tests)

Tests written:
- DeterministicIDFactory: same-seed reproducibility, different-seed divergence,
  different-prefix divergence, sequential uniqueness (100 IDs), 32-hex format,
  empty prefix, counter increment
- next_uuid: UUID format (8-4-4-4-12), deterministic, shared counter
- reset: sequence reproduction, counter zeroing
- fork: different IDs from parent, deterministic across instances, different
  namespaces diverge, no parent counter side-effect
- Global functions: singleton behaviour, reinit with seed, deterministic_id format,
  deterministic_uuid format

---

## Final Test Suite Status

```
605 passed, 23 failed (all pre-existing core_skeptic/core_audit), 1 collection error (pre-existing CLI import)
```

42 new tests added (22 metrics/library + 20 id_factory). All 23 failures are
pre-existing integration tests in core_skeptic/ and core_audit/ that depend on
repo state artifacts. Zero regressions from cleanup work.

## Status: COMPLETE

All recommendations executed. Both high-ROI test gaps closed. One production bug
found and fixed during testing.
