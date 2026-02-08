# NEXT STEPS: Phase 1 & Phase 2 Reassessment

**Date:** 2026-02-07
**Context:** Remediation complete, database populated, ready for full analysis re-run

---

## EXECUTIVE SUMMARY

The codebase has been remediated and the database populated with 233K transcription tokens. The stress tests now compute real values. The next step is to systematically re-run Phase 1 and Phase 2 analyses to establish genuine baseline results.

---

## PHASE 1: FOUNDATION (Prerequisites Check)

### Current State
- Metrics have real computation paths
- Hypotheses have real computation paths
- Controls can be generated with deterministic seeds
- Database has full transcription data

### Required Actions

#### 1.1 Verify Real Dataset Registration
```bash
# Check dataset registration
python -c "
from foundation.storage.metadata import MetadataStore, DatasetRecord
store = MetadataStore('sqlite:///data/voynich.db')
session = store.Session()
for d in session.query(DatasetRecord).all():
    print(f'{d.id}: {d.path}')
session.close()
"
```

**Expected:** `voynich_real` dataset registered

#### 1.2 Generate Fresh Control Datasets
```bash
# Generate scrambled control (deterministic seed)
REQUIRE_COMPUTED=1 python -c "
from foundation.storage.metadata import MetadataStore
from foundation.controls.scramblers import ScrambledControlGenerator

store = MetadataStore('sqlite:///data/voynich.db')
generator = ScrambledControlGenerator(store)
generator.generate('voynich_real', 'voynich_scrambled', seed=42)
print('Scrambled control generated')
"

# Generate synthetic control (deterministic seed)
REQUIRE_COMPUTED=1 python -c "
from foundation.storage.metadata import MetadataStore
from foundation.controls.synthetic import SyntheticNullGenerator

store = MetadataStore('sqlite:///data/voynich.db')
generator = SyntheticNullGenerator(store)
generator.generate('voynich_real', 'voynich_synthetic', seed=42, params={'num_pages': 50})
print('Synthetic control generated')
"
```

#### 1.3 Run Foundation Metrics
```bash
# Run metrics on real and control datasets
REQUIRE_COMPUTED=1 python -m foundation metrics run --dataset voynich_real --metric RepetitionRate
REQUIRE_COMPUTED=1 python -m foundation metrics run --dataset voynich_scrambled --metric RepetitionRate
REQUIRE_COMPUTED=1 python -m foundation metrics run --dataset voynich_real --metric ClusterTightness
REQUIRE_COMPUTED=1 python -m foundation metrics run --dataset voynich_scrambled --metric ClusterTightness
```

#### 1.4 Run Foundation Hypotheses
```bash
# Run glyph position entropy hypothesis
REQUIRE_COMPUTED=1 python -m foundation hypotheses run \
    --id glyph_position_entropy \
    --real voynich_real \
    --controls voynich_scrambled,voynich_synthetic
```

#### 1.5 Expected Outputs
- Metric results stored in database with `calculation_method="computed"`
- Hypothesis results with real entropy values (not 0.40/0.95)
- Coverage report showing 100% computed

---

## PHASE 2: ANALYSIS (Full Re-run)

### Phase 2.1: Admissibility Mapping

**Already verified working with full data.**

```bash
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_1.py
```

**Expected Output:**
- Natural language: INADMISSIBLE (glyph identity issues)
- Enciphered language: INADMISSIBLE (same)
- Constructed system: ADMISSIBLE
- Visual grammar: ADMISSIBLE
- Hybrid system: UNDERCONSTRAINED

### Phase 2.2: Stress Tests

**Already verified with new results.**

```bash
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_2.py
```

**New Results (from full data):**
| Track | Score | Status |
|-------|-------|--------|
| B1: Mapping Stability | 0.02 | COLLAPSED |
| B2: Information Preservation | z=5.68 | STABLE |
| B3: Locality | 0.40 | procedural |

### Phase 2.3: Model Instantiation

```bash
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_3.py
```

**Expected:**
- 6 models tested
- ~5 falsified, 1 surviving
- cs_procedural_generation likely leads

### Phase 2.4: Anomaly Characterization

```bash
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_4.py
```

**Expected:**
- Anomaly CONFIRMED
- Semantic necessity: NOT_NECESSARY (if Phase 2.2/2.3 results hold)
- Phase 3 decision: NOT JUSTIFIED (if non-semantic models pass)

---

## RECOMMENDED EXECUTION ORDER

### Step 1: Phase 1 Controls (10 min)
```bash
# Create script: scripts/foundation/phase_1_baseline.py
python scripts/foundation/phase_1_baseline.py
```

Creates:
- Fresh control datasets
- Baseline metric measurements
- Foundation hypothesis results

### Step 2: Phase 2 Full Run (20 min)
```bash
# Run all Phase 2 analyses in sequence
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_1.py
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_2.py
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_3.py
REQUIRE_COMPUTED=1 python scripts/analysis/run_phase_2_4.py
```

### Step 3: Generate Coverage Report
```bash
python -c "
from foundation.config import get_tracker
tracker = get_tracker()
report = tracker.generate_report('full_analysis')
print(f'Computed: {report.summary[\"total_computed\"]}')
print(f'Simulated: {report.summary[\"total_simulated\"]}')
print(f'Is Clean: {report.summary[\"is_clean\"]}')
"
```

### Step 4: Compare to Original Results
Document differences between:
- Original Phase 2 results (sparse data, placeholder values)
- New Phase 2 results (full data, computed values)

---

## VALIDATION CHECKLIST

Before proceeding to Phase 3 (Synthesis), verify:

- [ ] Phase 1 metrics computed (not simulated)
- [ ] Control datasets generated with deterministic seeds
- [ ] Phase 2.1 admissibility matrix generated
- [ ] Phase 2.2 stress tests run with real values
- [ ] Phase 2.3 models tested and scored
- [ ] Phase 2.4 anomaly characterized
- [ ] Coverage report shows 100% computed
- [ ] No SimulationViolationError raised

---

## POTENTIAL ISSUES

### 1. Missing Anchor Data
The anchor-based perturbation tests require anchors in the database. Check:
```bash
sqlite3 data/voynich.db "SELECT COUNT(*) FROM anchors;"
```

If zero, run anchor generation first:
```bash
REQUIRE_COMPUTED=1 python -m foundation anchors generate \
    --dataset voynich_real \
    --method geometric_v1
```

### 2. Missing Region Embeddings
ClusterTightness metric needs region embeddings. Check:
```bash
sqlite3 data/voynich.db "SELECT COUNT(*) FROM region_embeddings;"
```

If zero, the metric will fall back to bbox-based calculation (acceptable).

### 3. Insufficient Glyph Data
GlyphPositionHypothesis needs glyph candidates. Check:
```bash
sqlite3 data/voynich.db "SELECT COUNT(*) FROM glyph_candidates;"
```

If zero, run segmentation first or use token-based calculation.

---

## SUCCESS CRITERIA

**Phase 1 Complete When:**
1. Metrics computed and differ from hardcoded values
2. Hypotheses evaluated with real entropy calculations
3. Control datasets generated deterministically

**Phase 2 Complete When:**
1. All 4 phases run with REQUIRE_COMPUTED=1
2. No SimulationViolationError raised
3. Results differ from placeholder values
4. Phase 3 decision documented

---

---

## EXECUTION COMPLETE (2026-02-07)

All steps executed successfully:

### Phase 1 Baseline
- [x] voynich_scrambled control generated (seed=42)
- [x] voynich_synthetic control generated (seed=42, 50 pages)
- [x] RepetitionRate computed: 0.9003 (real) vs 0.0000 (controls)
- [x] ClusterTightness computed: 0.5000 (all datasets)
- [x] GlyphPositionHypothesis: FALSIFIED (no glyph data for voynich_real)

### Phase 2 Full Run
- [x] Phase 2.1: Admissibility Mapping - 2 inadmissible, 2 admissible
- [x] Phase 2.2: Stress Tests - B1: 0.02, B2: z=5.68, B3: procedural
- [x] Phase 2.3: Model Instantiation - 1 surviving, 5 falsified
- [x] Phase 2.4: Anomaly Characterization - CONFIRMED, Phase 3 NOT JUSTIFIED

### Documentation Created
- `status/analysis/PHASE_2_RESULTS.md` - Complete results documentation

## PHASE 1 GAP - RESOLVED (2026-02-07)

**Original Issue:** GlyphPositionHypothesis returned FALSIFIED due to missing glyph data.

**Resolution Applied:**
```bash
# Populated glyphs from transcription tokens
python scripts/foundation/populate_glyphs.py
```

**Results:**
- Created 208,907 glyph candidates with EVA character alignments
- GlyphAlignmentRecord links each glyph to its EVA symbol

**Official Framework Results:**
| Dataset | Entropy | Interpretation |
|---------|---------|----------------|
| voynich_real | 0.7841 | Constrained |
| voynich_scrambled | 1.0000 | Random (control) |
| voynich_synthetic | 1.0000 | Random (control) |

**Margin:** 0.2159 (21.6% more constrained than random)

**Key Findings (by EVA character):**
| Symbol | Position Preference | Entropy |
|--------|---------------------|---------|
| q | 97% word-initial | 0.12 |
| n | 92% word-final | 0.27 |
| y | 80% word-final | 0.57 |
| i, h, e | 99%+ mid-word | 0.01-0.05 |

**Hypothesis Outcome:** SUPPORTED (entropy 0.78 < 1.0, margin 0.22)

**Phase 1 Status:** ✅ COMPLETE
