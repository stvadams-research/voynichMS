Step 0: Freeze and retract, internally

Before writing more code:

Mark every findings file that depended on those components as SIMULATED / INVALIDATED BY AUDIT.

Keep them, do not delete, but move them to an /archive_legacy/simulated_findings/ folder with a README explaining the core_audit.

Add a top-level AUDIT_BREAK.md stating:

which modules were stubs

which findings are invalidated

what remains valid (provenance, decision logging, admissibility manager behavior)

This prevents self-deception and prevents future readers from getting misled.

Step 1: Build an “anti-stub” enforcement layer

This is the single most important technical addition.

Introduce a ComputationMode (or ResultKind) field on every metric/test output:

COMPUTED

SIMULATED

PLACEHOLDER

Add a CI rule: any pipeline run that produces findings must fail unless all required outputs are COMPUTED.

Add a code-level guard: functions in metrics/ and stress_tests/ must raise if they are in placeholder mode and the caller requests computed results.

You want a hard crash, not a warning.

Step 2: Re-implement metrics from first principles using only ledgers

Start with metrics that are simplest and most load-bearing:

information density (define precisely: per token? per glyph candidate? per line? entropy-based? pick one and version it)

locality radius (define it as a measured dependency window, not a heuristic)

positional entropy bounds (start/mid/end distributions)

repetition spacing (you already found this discriminates, make it real)

Rules:

Every metric gets:

a definition docstring

unit tests with small hand-constructed ledger fixtures

at least one property-based test (monotonicity or invariance under known transformations)

a “sanity dataset” run (tiny sample that produces stable known output)

Step 3: Implement genuine perturbation experiments

This is where your framework’s philosophy becomes real.

Perturbations must:

operate on ledger objects, not transcriptions directly

be parameterized and recorded in provenance

produce a distribution of outcomes, not a single value

Examples:

segmentation boundary jitter (real bounding box perturbation)

token merge/split perturbation (explicitly defined operations)

reorder within a small window (for locality stress)

deletion/noise injection at controlled rates

Then compute actual collapse rates and robustness curves.

Step 4: Re-run Phase 2 and Phase 3 as a new “Computed Run Series”

Do not pretend this is continuing the previous results.

Create a new run namespace like:

RUN_SERIES_2026Q1_COMPUTED_BASELINE

Outputs:

computed Phase 2 summary

computed Phase 3 phase3_synthesis attempt

computed Phase 3.1 attempt

You may find your earlier conclusions still hold, or not. Either is fine. This is now real.

Step 5: Fix the semantic necessity circularity

Your core_audit flagged a real methodological bug: circular definition.

Fix pattern:

define anomaly without reference to “semantic” vs “non-semantic”

define semantic necessity as: “no non-semantic model family in admissible set can reproduce metric ensemble within tolerance without overfitting”

treat it as a model comparison problem with penalties (complexity, degrees of freedom)

If you keep “semantic necessity,” it must be a conclusion from model inadequacy, not baked into definitions.

What remains valid right now

Be strict:

Valid:

data/provenance plumbing

decision registry

admissibility manager logic (as software)

Not valid:

any numerical findings produced by stubbed modules

any “falsified” claims that came from hardcoded perturbations

any reported z-scores, separations, or degradation thresholds that were computed from constants

How to answer “did you try?” once this is fixed

Once you implement Step 1 (anti-stub enforcement), you can honestly say:

It is impossible for this repo to generate findings unless they are computed from data.

Every reported value is traceable to a stored run with provenance and parameters.

The full pipeline is reproducible.



Plan to implement                                                                              │
│                                                                                                │
│ Remediation Plan: Replace Simulated Implementations with Real Computations                     │
│                                                                                                │
│ Executive Summary                                                                              │
│                                                                                                │
│ The core_audit found 50+ simulated implementations across 10 files that return hardcoded values     │
│ instead of computing from actual data. This plan provides a phased approach to replace all     │
│ simulations with genuine computations using the existing database schema and query             │
│ infrastructure.                                                                                │
│                                                                                                │
│ Estimated Total Effort: 60-80 hours across 5 phases                                            │
│                                                                                                │
│ ---                                                                                            │
│ Scope of Problem                                                                               │
│ ┌───────────────────┬───────┬──────────────────────────────┐                                   │
│ │     Category      │ Count │           Examples           │                                   │
│ ├───────────────────┼───────┼──────────────────────────────┤                                   │
│ │ Hardcoded returns │ 15+   │ return 0.65, return 0.375    │                                   │
│ ├───────────────────┼───────┼──────────────────────────────┤                                   │
│ │ Random generation │ 20+   │ random.uniform(0.5, 0.8)     │                                   │
│ ├───────────────────┼───────┼──────────────────────────────┤                                   │
│ │ String matching   │ 5+    │ if "scrambled" in dataset_id │                                   │
│ ├───────────────────┼───────┼──────────────────────────────┤                                   │
│ │ Formula-based     │ 10+   │ 0.15 + (p * 4.0) + (p² * 10) │                                   │
│ └───────────────────┴───────┴──────────────────────────────┘                                   │
│ ---                                                                                            │
│ Phase 1: Foundation Metrics (4-6 hours)                                                        │
│                                                                                                │
│ File: src/phase1_foundation/metrics/library.py                                                        │
│                                                                                                │
│ 1.1 RepetitionRate.calculate()                                                                 │
│                                                                                                │
│ - Current: Returns 0.15 + random.uniform(-0.02, 0.02) based on dataset name                    │
│ - Fix: Query actual token frequencies from TranscriptionTokenRecord                            │
│ - Formula: repeated_tokens / total_tokens                                                      │
│ - Query path: PageRecord → LineRecord → WordRecord → WordAlignmentRecord →                     │
│ TranscriptionTokenRecord                                                                       │
│                                                                                                │
│ 1.2 ClusterTightness.calculate()                                                               │
│                                                                                                │
│ - Current: Returns random.uniform(0.5, 0.8)                                                    │
│ - Fix: Compute from RegionEmbeddingRecord vectors                                              │
│ - Formula: 1 / (1 + mean_distance_from_centroid)                                               │
│ - Reuse: indistinguishability.py centroid computation pattern                                  │
│                                                                                                │
│ Verification                                                                                   │
│                                                                                                │
│ - Metrics differ between real and scrambled datasets                                           │
│ - Values are deterministic (same input → same output)                                          │
│                                                                                                │
│ ---                                                                                            │
│ Phase 2: Foundation Hypotheses (14-20 hours)                                                   │
│                                                                                                │
│ 2.1 src/phase1_foundation/hypotheses/library.py                                                       │
│                                                                                                │
│ GlyphPositionHypothesis.calculate_entropy()                                                    │
│ - Current: Returns 0.40 (real) or 0.95 (scrambled) by string match                             │
│ - Fix: Compute Shannon entropy from GlyphCandidateRecord positions                             │
│ - Formula: -sum(p * log2(p)) for glyph distribution at start/mid/end                           │
│                                                                                                │
│ 2.2 src/phase1_foundation/hypotheses/destructive.py                                                   │
│ Hypothesis: FixedGlyphIdentity                                                                 │
│ Current: Formula 0.15 + p*4 + p²*10                                                            │
│ Fix: Simulate boundary shift, count affected glyphs                                            │
│ ────────────────────────────────────────                                                       │
│ Hypothesis: WordBoundaryStability                                                              │
│ Current: Hardcoded {"eva","currier": 0.72}                                                     │
│ Fix: Compare actual TranscriptionSourceRecord counts                                           │
│ ────────────────────────────────────────                                                       │
│ Hypothesis: DiagramTextAlignment                                                               │
│ Current: Hardcoded 0.45                                                                        │
│ Fix: Count real AnchorRecord links, compute z-score                                            │
│ ────────────────────────────────────────                                                       │
│ Hypothesis: AnchorDisruption                                                                   │
│ Current: Hardcoded base_degradation                                                            │
│ Fix: Measure anchor survival after region shift                                                │
│ Implementation Pattern (FixedGlyphIdentity)                                                    │
│                                                                                                │
│ for word in words:                                                                             │
│     bbox = word.bbox                                                                           │
│     shift = perturbation_strength * (bbox['x_max'] - bbox['x_min'])                            │
│     for glyph in word.glyphs:                                                                  │
│         glyph_center = (glyph.bbox['x_min'] + glyph.bbox['x_max']) / 2                         │
│         if abs(glyph_center - bbox['x_min']) < shift:                                          │
│             collapsed_count += 1                                                               │
│ collapse_rate = collapsed_count / total_glyphs                                                 │
│                                                                                                │
│ Verification                                                                                   │
│                                                                                                │
│ - Collapse rate increases with perturbation strength                                           │
│ - Different datasets produce different results                                                 │
│                                                                                                │
│ ---                                                                                            │
│ Phase 3: Analysis Stress Tests (18-24 hours)                                                   │
│                                                                                                │
│ 3.1 src/phase2_analysis/stress_tests/locality.py                                                      │
│ ┌──────────────────────────────┬───────────┬───────────────────────────────────────────┐       │
│ │            Method            │ Hardcoded │             Real Computation              │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _calculate_local_similarity  │ 0.65      │ Bigram transition probability from tokens │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _calculate_global_similarity │ 0.35      │ Long-range token co-occurrence            │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _analyze_glyph_composition   │ 0.55      │ Glyph n-gram statistics                   │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _analyze_repetition_patterns │ 0.20      │ Actual token repetition from DB           │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _analyze_sequence_regularity │ 0.55      │ N-gram entropy                            │       │
│ ├──────────────────────────────┼───────────┼───────────────────────────────────────────┤       │
│ │ _analyze_state_patterns      │ 0.50      │ Transition matrix sparsity                │       │
│ └──────────────────────────────┴───────────┴───────────────────────────────────────────┘       │
│ 3.2 src/phase2_analysis/stress_tests/mapping_stability.py                                             │
│ ┌──────────────────────────────┬───────────┬────────────────────────────────────────────┐      │
│ │            Method            │ Hardcoded │              Real Computation              │      │
│ ├──────────────────────────────┼───────────┼────────────────────────────────────────────┤      │
│ │ _test_segmentation_stability │ 0.625     │ Glyph identity after boundary perturbation │      │
│ ├──────────────────────────────┼───────────┼────────────────────────────────────────────┤      │
│ │ _test_ordering_stability     │ 0.70      │ Metric correlation under word reordering   │      │
│ ├──────────────────────────────┼───────────┼────────────────────────────────────────────┤      │
│ │ _test_omission_stability     │ 0.65      │ Reconstruction accuracy with removed words │      │
│ ├──────────────────────────────┼───────────┼────────────────────────────────────────────┤      │
│ │ _test_controls               │ 0.30      │ Run actual tests on ControlDatasetRecord   │      │
│ └──────────────────────────────┴───────────┴────────────────────────────────────────────┘      │
│ 3.3 src/phase2_analysis/stress_tests/information_preservation.py                                      │
│                                                                                                │
│ _calculate_information_metrics()                                                               │
│ - Current: information_density = 0.7 if "scrambled" not in dataset_id else 0.3                 │
│ - Fix: Compute Shannon entropy from actual token distribution                                  │
│ - Formula: entropy = -sum(p * log2(p)) normalized by log2(vocabulary_size)                     │
│                                                                                                │
│ Verification                                                                                   │
│                                                                                                │
│ - Real datasets produce higher information density than scrambled                              │
│ - Results differ meaningfully between test cases                                               │
│                                                                                                │
│ ---                                                                                            │
│ Phase 4: Analysis Models (8-12 hours)                                                          │
│                                                                                                │
│ 4.1 src/phase2_analysis/models/visual_grammar.py                                                      │
│                                                                                                │
│ apply_perturbation()                                                                           │
│ - Current: Uses hardcoded base_degradation = {"segmentation": 0.35, ...}                       │
│ - Fix: Query AnchorRecord, simulate region shift, count broken anchors                         │
│ - Pattern:                                                                                     │
│   a. Get baseline anchor count                                                                 │
│   b. Simulate geometric perturbation                                                           │
│   c. Count anchors that would break (overlap < shift distance)                                 │
│   d. degradation = broken / baseline                                                           │
│                                                                                                │
│ 4.2 src/phase2_analysis/models/constructed_system.py                                                  │
│                                                                                                │
│ Same pattern as visual_grammar.py - replace all 3 model classes' apply_perturbation methods.   │
│                                                                                                │
│ Verification                                                                                   │
│                                                                                                │
│ - Degradation is measurable and varies with strength                                           │
│ - anchor_disruption produces highest degradation (as expected)                                 │
│                                                                                                │
│ ---                                                                                            │
│ Phase 5: Synthesis Layer (14-18 hours)                                                         │
│                                                                                                │
│ 5.1 src/phase3_synthesis/profile_extractor.py                                                         │
│                                                                                                │
│ SIMULATED_PAGE_DATA dict (lines 41-62)                                                         │
│ - Current: 18 hardcoded page profiles with jar/block/line/word counts                          │
│ - Fix: Query actual data from PageRecord, RegionRecord, LineRecord, WordRecord                 │
│ - Pattern:                                                                                     │
│ def extract_page_profile(self, page_id: str) -> PageProfile:                                   │
│     page = session.query(PageRecord).filter_by(id=page_id).first()                             │
│     regions = session.query(RegionRecord).filter_by(page_id=page_id, scale="mid").all()        │
│     lines = session.query(LineRecord).filter_by(page_id=page_id).all()                         │
│     # ... compute actual counts and metrics                                                    │
│                                                                                                │
│ 5.2 src/phase3_synthesis/refinement/feature_discovery.py                                              │
│                                                                                                │
│ compute_feature() switch statement (lines 150-234)                                             │
│ - Current: Returns different hardcoded values per feature type                                 │
│ - Fix: Create FeatureComputer registry with real computation functions                         │
│ ┌───────────────────────────┬───────────────┬───────────────────────────────────────────────┐  │
│ │          Feature          │    Current    │               Real Computation                │  │
│ ├───────────────────────────┼───────────────┼───────────────────────────────────────────────┤  │
│ │ spatial_jar_variance      │ 0.15 + random │ statistics.variance(jar_x_positions)          │  │
│ ├───────────────────────────┼───────────────┼───────────────────────────────────────────────┤  │
│ │ text_inter_jar_similarity │ 0.35 + random │ Jaccard similarity of tokens via AnchorRecord │  │
│ ├───────────────────────────┼───────────────┼───────────────────────────────────────────────┤  │
│ │ text_bigram_consistency   │ 0.70 + random │ Bigram type/token ratio                       │  │
│ └───────────────────────────┴───────────────┴───────────────────────────────────────────────┘  │
│ Verification                                                                                   │
│                                                                                                │
│ - Profile extractor produces different results per page                                        │
│ - Feature discovery discriminates real vs synthetic                                            │
│                                                                                                │
│ ---                                                                                            │
│ Implementation Strategy                                                                        │
│                                                                                                │
│ Backward Compatibility                                                                         │
│                                                                                                │
│ Add feature flags to enable incremental rollout:                                               │
│ # src/phase1_foundation/config.py                                                                     │
│ USE_REAL_COMPUTATIONS = {                                                                      │
│     "metrics": True,      # Phase 1                                                            │
│     "hypotheses": False,  # Phase 2 (enable after testing)                                     │
│     "stress_tests": False,                                                                     │
│     "models": False,                                                                           │
│     "phase3_synthesis": False,                                                                        │
│ }                                                                                              │
│                                                                                                │
│ Migration Pattern                                                                              │
│                                                                                                │
│ 1. Keep simulated code as _calculate_simulated()                                               │
│ 2. Add real code as _calculate_real()                                                          │
│ 3. Switch based on feature flag                                                                │
│ 4. Run both in parallel, compare outputs                                                       │
│ 5. Enable real by default after validation                                                     │
│ 6. Mark simulated as deprecated                                                                │
│                                                                                                │
│ ---                                                                                            │
│ Critical Files to Modify                                                                       │
│ Priority: 1                                                                                    │
│ File: src/phase1_foundation/metrics/library.py                                                        │
│ Changes: 2 methods                                                                             │
│ ────────────────────────────────────────                                                       │
│ Priority: 2                                                                                    │
│ File: src/phase1_foundation/hypotheses/library.py                                                     │
│ Changes: 1 method                                                                              │
│ ────────────────────────────────────────                                                       │
│ Priority: 3                                                                                    │
│ File: src/phase1_foundation/hypotheses/destructive.py                                                 │
│ Changes: 4 hypothesis classes                                                                  │
│ ────────────────────────────────────────                                                       │
│ Priority: 4                                                                                    │
│ File: src/phase2_analysis/stress_tests/information_preservation.py                                    │
│ Changes: 1 method (string matching)                                                            │
│ ────────────────────────────────────────                                                       │
│ Priority: 5                                                                                    │
│ File: src/phase2_analysis/stress_tests/locality.py                                                    │
│ Changes: 6 methods                                                                             │
│ ────────────────────────────────────────                                                       │
│ Priority: 6                                                                                    │
│ File: src/phase2_analysis/stress_tests/mapping_stability.py                                           │
│ Changes: 4 methods                                                                             │
│ ────────────────────────────────────────                                                       │
│ Priority: 7                                                                                    │
│ File: src/phase2_analysis/models/visual_grammar.py                                                    │
│ Changes: 3 apply_perturbation methods                                                          │
│ ────────────────────────────────────────                                                       │
│ Priority: 8                                                                                    │
│ File: src/phase2_analysis/models/constructed_system.py                                                │
│ Changes: 3 apply_perturbation methods                                                          │
│ ────────────────────────────────────────                                                       │
│ Priority: 9                                                                                    │
│ File: src/phase3_synthesis/profile_extractor.py                                                       │
│ Changes: Remove SIMULATED_PAGE_DATA                                                            │
│ ────────────────────────────────────────                                                       │
│ Priority: 10                                                                                   │
│ File: src/phase3_synthesis/refinement/feature_discovery.py                                            │
│ Changes: compute_feature registry                                                              │
│ ---                                                                                            │
│ Reusable Patterns                                                                              │
│                                                                                                │
│ Follow these existing real implementations:                                                    │
│ - src/phase1_foundation/core/geometry.py - IoU, distance, containment (tested, proven)                │
│ - src/phase3_synthesis/indistinguishability.py - Vector distance, centroid, separation scoring        │
│ - src/phase1_foundation/controls/scramblers.py - Database manipulation with seed control              │
│ - src/phase1_foundation/phase2_analysis/stability.py - Anchor degradation calculation                        │
│ - src/phase1_foundation/core/queries.py - QueryEngine patterns for DB access                          │
│                                                                                                │
│ ---                                                                                            │
│ Testing Requirements                                                                           │
│                                                                                                │
│ Test Fixtures Needed                                                                           │
│                                                                                                │
│ 1. Minimal test database with known token distributions                                        │
│ 2. Scrambled control dataset with predictable degradation                                      │
│ 3. Golden file outputs for regression testing                                                  │
│                                                                                                │
│ Per-Phase Verification                                                                         │
│                                                                                                │
│ - Phase 1: Metrics differ between real/scrambled, are deterministic                            │
│ - Phase 2: Hypothesis results change with perturbation strength                                │
│ - Phase 3: Stress tests produce measurable differences                                         │
│ - Phase 4: Model degradation correlates with anchor counts                                     │
│ - Phase 5: Profiles match actual database counts                                               │
│                                                                                                │
│ ---                                                                                            │
│ Success Criteria                                                                               │
│                                                                                                │
│ The remediation is complete when:                                                              │
│ 1. No methods return hardcoded constants                                                       │
│ 2. No methods use random.uniform() for analytical values                                       │
│ 3. No methods use string matching on dataset_id for behavior                                   │
│ 4. All tests pass with real computations enabled                                               │
│ 5. Results differ meaningfully between real and control datasets                               │
│ 6. The core_audit can be re-run with PASS results                                                   │
│                                                                                                │
│ ---                                                                                            │
│ Execution Order                                                                                │
│                                                                                                │
│ 1. Week 1: Phase 1 (Metrics) + Phase 2.1 (GlyphPositionHypothesis)                             │
│ 2. Week 2: Phase 2.2 (Destructive Hypotheses)                                                  │
│ 3. Week 3: Phase 3 (Stress Tests)                                                              │
│ 4. Week 4: Phase 4 (Models) + Phase 5 (Synthesis)                                              │
│ 5. Week 5: Integration testing, deprecate simulated code                                       │
│                                                                                                │
│ ---                                                                                            │
│ Risk Mitigation                                                                                │
│ ┌─────────────────────────────┬──────────────────────────────────────────────────────┐         │
│ │            Risk             │                      Mitigation                      │         │
│ ├─────────────────────────────┼──────────────────────────────────────────────────────┤         │
│ │ Missing test data           │ Create synthetic test fixtures with known properties │         │
│ ├─────────────────────────────┼──────────────────────────────────────────────────────┤         │
│ │ Breaking existing workflows │ Feature flags enable gradual rollout                 │         │
│ ├─────────────────────────────┼──────────────────────────────────────────────────────┤         │
│ │ Performance regression      │ Profile before/after, add caching if needed          │         │
│ ├─────────────────────────────┼──────────────────────────────────────────────────────┤         │
│ │ Subtle bugs in formulas     │ Compare to hand-calculated examples                  │         │
│ └─────────────────────────────┴────────────────