# Methods Reference

This document summarizes the quantitative methods used across all research phases and
the key caveats needed for audit interpretation.

## 0. Transcription Standard

All token-level analysis uses the **Zandbergen-Landini (ZL)** transcription
(`ZL3b-n.txt`, IVTFF 2.0 format) in the **EVA (Extensible Voynich Alphabet)**
encoding — lowercase character set.

- **Canonical loader:** `load_canonical_lines()` in
  `src/phase1_foundation/core/data_loading.py`
  (default `source_id="zandbergen_landini"`)
- **Sanitization:** `sanitize_token()` strips IVTFF markup (`<%>`, `<!...>`,
  `[...]`, punctuation) but performs no case conversion
- **Source:** <https://www.voynich.nu/transcr/>
- **Citation:** Zandbergen, R., & Landini, G. (2024). *The Voynich Manuscript
  Transliteration Archive*.

Six other transcription sources (RF, VT, IT, GC, FG, CD) are stored in the
database for reference but are **not used** in any production analysis.
The Currier/D'Imperio source (`CD2a-n.txt`) uses an uppercase alphabet
unrelated to EVA — it is isolated from the canonical pipeline.

## 1. Foundation Metrics

### 1.1 Repetition Rate (`src/phase1_foundation/metrics/library.py`)
- Primary formula:
  `token_repetition_rate = repeated_token_occurrences / total_tokens`
- Supplementary statistic:
  `vocabulary_coverage = 1 - (unique_tokens / total_tokens)`
- Canonical output:
  `MetricResult.value` is always `token_repetition_rate`.
- Known confounds:
  Corpus length, transcription sparsity, and token normalization choices can
  shift absolute values.

### 1.2 Cluster Tightness (`src/phase1_foundation/metrics/library.py`)
- Embedding path:
  `tightness = 1 / (1 + mean_distance_from_embedding_centroid)`
- BBox fallback path:
  same formula but over 2D region centroids.
- Non-comparability note:
  embedding- and bbox-based scales are not directly interchangeable. Use
  `details["method"]` / `details["computation_path"]` for interpretation.
- Known confounds:
  Missing embeddings, sparse region extraction, and page-scale heterogeneity.

## 2. Stress Tests

### 2.1 Mapping Stability (`src/phase2_analysis/stress_tests/mapping_stability.py`)
- Tests segmentation/order/omission robustness under perturbation.
- Thresholds come from `configs/phase2_analysis/thresholds.json`.
- Known confounds:
  boundary quality, alignment completeness, and control coverage.

### 2.2 Information Preservation (`src/phase2_analysis/stress_tests/information_preservation.py`)
- Uses token entropy, redundancy, and cross-scale correlation.
- Known confounds:
  token truncation limits (`MAX_TOKENS_ANALYZED`), page sampling limits, and
  uneven anchor density.

### 2.3 Locality & Compositionality (`src/phase2_analysis/stress_tests/locality.py`)
- Uses locality ratio bands, compositional score bands, and procedural signals.
- Thresholds come from `configs/phase2_analysis/thresholds.json`.
- Known confounds:
  line ordering quality, sparse alignments, and vocabulary drift across pages.

## 3. Comparative Separation

### 3.1 Indistinguishability (`src/phase3_synthesis/indistinguishability.py`)
- Separation score:
  `S = inter_centroid_distance / (inter_centroid_distance + average_spread)`
- Success/failure thresholds come from `configs/phase2_analysis/thresholds.json`.
- Synthetic positional entropy is now computed from generated token position
  distributions, not a simulated constant.
- Known confounds:
  feature-set incompleteness and control-generation assumptions.

## 4. Inference Evaluation

### 4.1 Language ID under Flexible Transforms (`src/phase4_inference/lang_id_transforms/`)
- Evaluates the "Noise Floor" of linguistic identification.
- Success criterion: confidence score must exceed the threshold established by non-semantic shuffled controls (typically 0.70+).
- Known confounds: search space size, transform flexibility, and corpus bias.

## 5. Circularity Disclosure

Some anomaly modules intentionally take observed Phase 1-3 values as constraint
inputs. This is explicit and scoped:
- `src/phase2_analysis/anomaly/capacity_bounding.py`:
  uses observed values to test whether non-semantic systems could produce them.
- `src/phase2_analysis/anomaly/constraint_analysis.py`:
  uses observed values as fixed constraint parameters for intersection logic.
- `src/phase2_analysis/anomaly/stability_analysis.py`:
  baseline values are caller-provided references; analysis tests perturbation
  stability, not baseline independence.

## 6. Control Pipeline

Control generators (`synthetic`, `self_citation`, `table_grille`,
`mechanical_reuse`) now run under explicit **normalization symmetry** policy.

Allowed normalization modes:

- `parser`: parser-equivalent canonicalization path for control tokens.
- `pre_normalized_with_assertions`: strict lowercase-alpha assertion path for
  already-canonical token streams.

SK-H3 enforcement requirements:

- normalization mode must be explicit in control provenance,
- parser-mode canonicalization must be deterministic,
- strict mode must fail on non-canonical tokens.

Comparability caveat handling:

- if control generation cannot satisfy normalization policy, comparability status
  must be downgraded (`NON_COMPARABLE_BLOCKED` or `INCONCLUSIVE_DATA_LIMITED`),
- release-path checks must not treat such runs as conclusive.

## 7. SK-H3 Comparability Guardrails

- Matching and evaluation metrics are partitioned and audited.
- Any overlap between `matching_metrics` and `holdout_evaluation_metrics` is
  treated as target leakage.
- Data-availability constraints are tracked in
  `core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json`.
- When required source pages are unavailable, comparability must remain
  blocked for full closure with:
  - `reason_code=DATA_AVAILABILITY`
  - `evidence_scope=available_subset`
  - `full_data_closure_eligible=false`
- SK-H3.4 irrecoverability governance must be explicit:
  - `approved_lost_pages_policy_version`
  - `approved_lost_pages_source_note_path`
  - `irrecoverability.recoverable`
  - `irrecoverability.approved_lost`
  - `irrecoverability.unexpected_missing`
  - `irrecoverability.classification`
  - `full_data_feasibility`
  - `full_data_closure_terminal_reason`
  - `h3_4_closure_lane`
- SK-H3.5 closure governance must be explicit:
  - `h3_5_closure_lane`
  - `h3_5_residual_reason`
  - `h3_5_reopen_conditions`
- Available-subset transition reason codes:
  - `AVAILABLE_SUBSET_QUALIFIED` (thresholds pass)
  - `AVAILABLE_SUBSET_UNDERPOWERED` (thresholds fail)
- Available-subset comparability is explicitly non-conclusive and cannot be
  promoted to full-dataset closure claims.
- Canonical checker:

```bash
python3 scripts/core_skeptic/check_control_comparability.py --mode ci
python3 scripts/core_skeptic/check_control_comparability.py --mode release
python3 scripts/core_skeptic/check_control_data_availability.py --mode ci
python3 scripts/core_skeptic/check_control_data_availability.py --mode release
```

## 8. Phase 10 Admissibility Methods

All six Phase 10 methods are adversarial stress-tests of the Phase 4.5
"procedural-artifact" closure hypothesis. Each method has a pre-registered defeat
condition. Possible outcomes: `closure_strengthened`, `closure_weakened`,
`indeterminate`, `test_invalid`. All result files include a provenance envelope
(`run_id`, `git_commit`, `timestamp`, `seed`, `experiment_id`, `command`).

### 8.1 Method F: Reverse Mechanism (`src/phase10_admissibility/stage3_pipeline.py`)

- **Test design:** The identified generative mechanisms (table-grille, slot-logic,
  constrained-Markov) are tested as encoding devices. 10,000 random reverse
  parameterizations per family decode the Voynich token sequence. Symbol entropy
  of each decoded output is compared against a block-bootstrapped null
  distribution (1,000 permutations, block sizes 2–12).
- **Null hypothesis:** No sampled reverse parameterization yields decoded output
  with entropy significantly below what random-input encoding produces.
- **Test statistic:** Symbol entropy of decoded output vs. null 1st percentile
  (`null_q01`).
- **Significance gates:**
  - Primary: entropy < `null_q01`
  - Stability: perturbation pass rate >= 0.70 (12 perturbations per candidate)
  - Naturalness: Zipf-alpha in [0.6, 1.6], top-symbol frequency <= 0.45,
    bigram-MI >= null 95th percentile
- **Decision:**
  - `closure_weakened`: at least one stable-natural outlier in any family
  - `closure_strengthened`: no parameterization below `null_q01` in all families
  - `indeterminate`: outliers found but none survive stability + naturalness
- **Runner:** `scripts/phase10_admissibility/run_stage3_f.py`
- **Known confounds:** Symbol alphabet size (mod-64), block-bootstrap block size
  range, parameterization sample coverage relative to constrained space.

### 8.2 Method G: Text-Illustration Content Correlation (`src/phase10_admissibility/stage2_pipeline.py`)

- **Test design:** Visual feature vectors (37 features: gray/HSV stats, edge
  density, ink ratio, connected-component metrics, patch densities) and TF-IDF
  text vectors are computed per folio. A Mantel test (1,000 permutations)
  measures correlation between visual-distance and text-distance matrices.
  Section-level effects are removed via within-section permutation and text
  demeaning.
- **Null hypothesis:** No significant correlation between visual similarity and
  textual similarity across folio pairs, beyond section membership.
- **Test statistic:** Mantel r (Pearson correlation between upper triangles of
  distance matrices); `p_one_sided`.
- **Decision:**
  - `closure_weakened`: full r > 0, p < 0.01, AND residual r > 0, residual p < 0.01
  - `closure_strengthened`: full p >= 0.01
  - `indeterminate`: section-level coupling significant but residual is not
- **Runner:** `scripts/phase10_admissibility/run_stage2_gi.py`
- **Known confounds:** Scan resolution, feature extraction pipeline, section
  label granularity, TF-IDF max features.

### 8.3 Method H: Writing System Typology (`src/phase10_admissibility/stage1_pipeline.py`)

- **Test design:** Compute 4 features per corpus (glyph_count, mean_word_length,
  ttr_10000, combinatorial_productivity_log_ratio). Compute weighted Euclidean
  distance (weights: 1.4, 1.0, 1.0, 0.8) to 5 typology prototypes (alphabet,
  abjad, abugida, syllabary, logographic). Assign nearest typology. Check
  range-exclusion gates.
- **Null hypothesis:** Voynich's combinatorial structure is best explained by the
  known generators rather than a distinct writing-system type.
- **Test statistic:** Weighted Euclidean distance to each typology centroid;
  nearest-typology assignment; range-exclusion count.
- **Decision:**
  - `closure_weakened`: Voynich's nearest typology has no generators assigned AND
    Voynich is not excluded from that typology's range
  - `closure_strengthened`: at least one generator shares Voynich's nearest
    typology, OR Voynich excluded from 3+ typologies
- **Runner:** `scripts/phase10_admissibility/run_stage1_hjk.py`
- **Known confounds:** Typology centroid definitions, weight choices,
  TTR sample-size sensitivity.

### 8.4 Method I: Cross-Linguistic Positioning (`src/phase10_admissibility/stage2_pipeline.py`)

- **Test design:** Compute 11-feature Phase 4 vector (entropy, compression,
  TTR, Zipf-alpha, bigram/trigram conditional entropy, bigram MI,
  mean_word_length, line-initial/final entropy, hapax ratio) for Voynich,
  12+ typologically diverse languages (>= 4 typology classes), and generators.
  Z-score normalize. Measure Voynich distance to language centroid vs. generator
  centroid. Bootstrap (500 iterations) for confidence intervals.
- **Null hypothesis:** Voynich is not systematically closer to the generator
  cloud than to the natural-language cloud.
- **Test statistic:** `dist_to_language_centroid` and `dist_to_generator_centroid`
  (Euclidean in z-score space); `bootstrap_confidence_generator_closer`.
- **Decision:**
  - Coverage gate: >= 12 languages and >= 4 typology classes, else `test_invalid`
  - `closure_weakened`: dist_to_language < dist_to_generator AND
    bootstrap_confidence_language_closer >= 0.95
  - `closure_strengthened`: dist_to_generator < dist_to_language AND
    bootstrap_confidence_generator_closer >= 0.80
- **Runner:** `scripts/phase10_admissibility/run_stage2_gi.py`
- **Known confounds:** Language corpus availability, tokenization differences
  across scripts, z-score sensitivity to outlier corpora.

### 8.5 Method J: Steganographic Extraction (`src/phase10_admissibility/stage1_pipeline.py`)

- **Test design:** Apply 9 positional extraction rules (line-initial, line-final,
  word-initial glyphs, nth-token-2/3/5/7, slot-position-3, paragraph-initial) to
  the Voynich token stream. For each extracted subsequence, compute entropy,
  compression ratio, TTR, bigram MI. Calibrate against 100 null runs from three
  line-reset generator families. Flag anomalies at |z| >= 3.0 on entropy or
  bigram MI. Stability check: 12 bootstrap resamples and 12 line-permutations,
  requiring >= 80% pass rate each.
- **Null hypothesis:** All positional extractions are statistically
  indistinguishable from the same extractions applied to generated text.
- **Test statistic:** z_score per extraction rule × metric pair.
- **Significance gates:** |z| >= 3.0, bootstrap pass >= 0.80, line-permutation
  pass >= 0.80.
- **Decision:**
  - `closure_weakened`: at least one stable anomaly
  - `closure_strengthened`: no extraction shows |z| >= 3.0
  - `indeterminate`: anomalies found but unstable
  - Stage 1b upgrade gate: >= 1 non-edge stable anomaly survives folio-order
    permutation
- **Runner:** `scripts/phase10_admissibility/run_stage1_hjk.py`
- **Known confounds:** Edge-rule sensitivity (line-initial, paragraph-initial),
  generator family coverage, extraction rule completeness.

### 8.6 Method K: Residual Gap Anatomy (`src/phase10_admissibility/stage1_pipeline.py`)

- **Test design:** Compute 11-feature vector for Voynich and 100 samples from
  the best-fit generator family (selected by minimum normalized MAD distance).
  Flag outlier features at |z| >= 2.0. Compute mean absolute Pearson correlation
  among outlier features across synthetic runs. Check whether outliers are
  language-ward (Voynich closer to Latin than generator). Parameter sweep
  classifies modification difficulty (trivial/moderate/hard).
- **Null hypothesis:** All outlier features where Voynich deviates from the best
  generator are independent, small, and closable by minor parameter adjustments.
- **Test statistics:**
  - `mean_abs_correlation`: mean |Pearson r| among outlier features
  - `toward_language_count`: outlier features where Voynich is closer to Latin
  - `hard_count`: features classified as `hard_framework_shift`
- **Decision:**
  - `closure_weakened`: >= 2 outliers AND mean_abs_correlation >= 0.4 AND
    toward_language_count >= 2 AND hard_count >= 2
  - `closure_strengthened`: no outliers OR (corr < 0.3 AND all trivial/moderate)
  - `indeterminate`: everything else
  - Stage 5b adjudication: seed-band pass rate >= 75% across 8 seeds
- **Runner:** `scripts/phase10_admissibility/run_stage1_hjk.py`
  (adjudication: `scripts/phase10_admissibility/run_stage5b_k_adjudication.py`)
- **Known confounds:** Best-family selection sensitivity, parameter sweep
  coverage, Latin as sole language reference.

### 8.7 Phase 10 Outcome Summary

| Method | Outcome | Key evidence |
|--------|---------|-------------|
| F | `indeterminate` | Outliers found below null_q01 but zero survive stability + naturalness |
| G | `indeterminate` | Full Mantel r = 0.221, p < 0.001; residual r ≈ 0, not significant |
| H | `closure_strengthened` | Voynich excluded from 4/5 typologies; generators share remaining type |
| I | `closure_strengthened` | dist_to_generator = 3.36, dist_to_language = 5.47; bootstrap confidence = 0.95 |
| J | `closure_weakened` | Stable non-edge anomalies confirmed across seeds 42, 77, 101 |
| K | `closure_weakened` | Adjudicated: mean_abs_corr = 0.41, 5 hard language-ward features, 7/8 seeds pass |

Overall closure status: `in_tension` (mixed results; H/I strengthened, J/K weakened, F/G indeterminate).

## 9. Phase 11 Stroke Topology

Phase 11 tests whether sub-glyph stroke composition of EVA characters carries
predictive structure beyond token identity. This is the only phase operating
below the TOKEN scale. The phase terminated early via a **fast-kill gate**.

### 9.1 Feature Schema (`src/phase11_stroke/schema.py`)

21 EVA characters are assigned 6 features each:

| Feature | Type | Definition |
|---------|------|-----------|
| `gallows` | binary | Tall vertical stem; strictly {t, k, p, f} |
| `loop` | binary | Closed or near-closed curved enclosure |
| `bench` | binary | Horizontal connecting stroke at baseline; strictly {c, h} |
| `descender` | binary | Stroke extends below baseline; {y, s, g, m} |
| `minimal` | binary | Single simple stroke or dot; {i, r, l} |
| `stroke_count` | integer 1–4 | Estimated distinct pen strokes |

This is a code constant (not runtime-computed), validated on import with a
SHA-256 version hash for provenance. `stroke_count` is normalized to [0, 1]
by dividing by 4.0 for analyses requiring homogeneous scale.

Token-level representations: mean profile (6D), boundary profile (12D: first +
last character features), aggregate profile (6D sum).

### 9.2 Test A: Stroke-Feature Clustering (`src/phase11_stroke/clustering.py`)

- **Test design:** For tokens with count >= 5, compute pairwise cosine similarity
  between mean stroke profiles and pairwise co-occurrence rate (fraction of lines
  containing both types). Log-frequency product is regressed out via OLS
  residualization. Compute partial Spearman correlation. Null distribution:
  10,000 permutations of the character-to-feature mapping.
- **Null hypothesis:** Random reassignment of stroke feature vectors to characters
  produces equal or greater co-occurrence correlation.
- **Test statistic:** Partial Spearman rho (frequency-controlled).
- **Decision:**
  - `significant`: p < 0.01 AND partial_rho > 0.05
  - `indeterminate`: p < 0.01 AND partial_rho <= 0.05
  - `null`: p >= 0.01
- **Known confounds:** Feature table is hand-assigned from EVA specification (not
  image-derived), minimum occurrence threshold, line-level granularity.

### 9.3 Test B: Stroke Features Predict Token Transitions (`src/phase11_stroke/transitions.py`)

Three sub-measures on inter-token character boundaries (last char of token N,
first char of token N+1):

- **B1 (gate-relevant):** Mutual information between feature classes of outgoing
  and incoming characters. Null: 10,000 permutations of character-to-feature-class
  mapping. Decision: `significant` if p < 0.01, else `null`.
- **B2 (supplemental):** Same MI computation over intra-token consecutive
  character pairs. Reports whether intra-token MI exceeds inter-token MI.
- **B3 (diagnostic):** Information ratio = MI(stroke features) / MI(character
  identity). Measures what fraction of raw character-level transition information
  the stroke projection captures. Ratio > 0.3 classified `non_trivial`.

Production constraint evidence requires B1 AND B2 significant AND intra_MI >
boundary_MI.

### 9.4 Fast-Kill Gate

**Condition:** Test A p >= 0.01 AND Test B1 p >= 0.01.

If both primary tests return null, Stages 3–5 (positional analysis, sensitivity
sweep, synthesis integration) are terminated unconditionally. The STROKE scale
is declared formally redundant.

### 9.5 Phase 11 Results

| Test | Statistic | Value | p-value | Determination |
|------|-----------|-------|---------|---------------|
| A | Partial Spearman rho | 0.016 | 0.307 | `null` |
| B1 | Boundary MI (bits) | 0.122 | 0.711 | `null` |
| B2 | Intra-token MI (bits) | 1.088 | 0.774 | `null` |
| B3 | Information ratio | 0.717 | — | `non_trivial` |

Fast-kill gate triggered. Outcome class: **STROKE_NULL**.

Note: B3 information ratio of 0.72 shows the feature decomposition captures
~72% of character-level transition information — the features are not
informationally poor — yet MI is not higher than random reassignment produces.

- **Runners:** `scripts/phase11_stroke/run_11a_extract.py` (Stage 1 extraction),
  `scripts/phase11_stroke/run_11b_cluster.py` (Test A),
  `scripts/phase11_stroke/run_11c_transitions.py` (Test B)
- **Replication:** `python3 scripts/phase11_stroke/replicate.py`
- **Randomness:** FORBIDDEN for extraction (deterministic), SEEDED (42) for
  permutation tests. All use `numpy.random.default_rng(42)`.
- **Permutations:** 10,000 per test.

## 10. Phase 12: Mechanical Slip Detection

Phase 12 searches for vertical offset errors — words selected from adjacent
windows rather than the correct one — as evidence that a physical device with
manual indexing was used during production.

### 10.1 Vertical Offset Detection (`src/phase12_mechanical/`)

- **Test design:** For each bigram in the corpus, check whether the second
  token belongs to the expected next window (per the lattice model) or to an
  adjacent window (±1 offset). Count deviations as "vertical slips." Compare
  the observed slip count against a shuffle-control baseline (randomized corpus
  with preserved unigram frequencies).
- **Test statistic:** Observed slip count vs. shuffle-control mean.
- **Signal-to-noise ratio:** 20× above shuffle control (914 detected slips).
- **Decision:** The 914 slips are mechanically diagnostic — consistent with
  a physical reference device where the operator mis-indexes a page.
- **Runners:** `scripts/phase12_mechanical/` (6 scripts: run_12a through run_12f)
- **Key caveat:** Slip detection depends on the accuracy of the window
  assignment model. False positives can arise from rare-word window ambiguity.

## 11. Phase 13: Grand Blueprint Synthesis

Phase 13 reverse-engineers the physical layout of the production device by
analyzing transition patterns between windows and identifying "physical anchors"
(high-frequency words whose positions are mechanically constrained).

### 11.1 Context Masking (`src/phase13_closure/`)

- **Test design:** Introduce a persistent context mask — a non-semantic
  modulation parameter that varies across lines and pages — to the lattice
  model. Measure whether linguistic-ward anomalies (identified in Phase 10
  Method K) collapse under context masking.
- **Test statistic:** ANOVA F-test on residual z-scores with and without
  context mask.
- **Result:** p = 4.24 × 10⁻⁴⁷. Context masking reduces linguistic-ward
  anomalies by over 70%.
- **Runners:** `scripts/phase13_demonstration/` (3 scripts)

## 12. Phase 14: High-Fidelity Emulation

Phase 14 (15 sub-phases, A-O) constructs and calibrates a complete emulator
of the Voynich production tool. This is the core mechanical reconstruction
phase.

### 12.1 50-Window Lattice (`scripts/phase14_machine/run_14a_*.py` through `run_14o_*.py`)

- **Architecture:** Each of 7,717 word types is assigned to exactly one of 50
  windows. Each word encodes a deterministic next-window transition. Per-window
  correction offsets (range -20 to +13, 43 non-zero) account for systematic
  drift.
- **Calibration method:** Per-window offsets are computed as the mode of
  `(observed_next_window - raw_next_window)` across all transitions with ≥5
  observations per window. Cross-validated via leave-one-section-out splits
  (7/7 significant, mean z = 29.1σ).
- **Structural fit:** 93.72% of observed transitions are reproduced by the
  emulator (126σ above null).
- **Entropy comparison:** Emulator entropy = 11.49 bits; manuscript entropy =
  12.26 bits (0.77-bit gap, consistent with scribal selection variance).
- **Runners:** 15 scripts in `scripts/phase14_machine/` (run_14a through run_14o)
- **Randomness:** SEEDED (42). All use `numpy.random.default_rng(42)`.
- **Key output:** `results/data/phase14_machine/canonical_offsets.json`

### 12.2 Residual Diagnosis (`scripts/phase14_machine/run_14l_*.py`)

- **Method:** Stratify all token transitions by frequency tier (common >100,
  medium 10-100, rare <10, hapax =1). Compute per-tier failure rate.
- **Result:** Common words obey the lattice at 93.1%. Rare words fail at 84.5%.
  The residual is frequency-dominated, not structurally anomalous.
- **Key output:** `results/data/phase14_machine/failure_taxonomy.json`

### 12.3 Scribal Hand Modeling (`scripts/phase14_machine/run_14n_*.py`)

- **Method:** Gaussian drift profiles with suffix-biased selection. Hand 1
  (drift=15, suffix=-dy) and Hand 2 (drift=25, suffix=-in) are calibrated
  via per-hand admissibility maximization.
- **Window distribution test:** JSD = 0.012, cosine = 0.998 between hands —
  both traverse the same lattice.
- **Vocabulary overlap:** 15.6% shared types, 66-72% shared token coverage.

## 13. Phase 15: Rule Extraction

Phase 15 formalizes the implicit lattice into explicit, declarative production
rules.

### 13.1 Driver Analysis (`src/phase15_selection/`)

- **Method:** For each word type, record its window assignment, next-window
  transition, and the contextual factors influencing its selection. Measure
  information contribution of each driver via conditional entropy decomposition.
- **Result:** 7,717 rules extracted. Bigram context contributes 2.43 bits/word
  (dominant driver). Suffix bias contributes 1.2-1.8 bits (hand-dependent).
  Positional constraint contributes 0.5-0.8 bits.
- **Runners:** `scripts/phase15_rule_extraction/` (4 scripts)
- **Key output:** `results/data/phase15_selection/integrated_rules.json`

## 14. Phase 16: Physical Grounding

Phase 16 tests whether the abstract lattice model is consistent with
15th-century physical production constraints.

### 14.1 Ergonomic Modeling (`src/phase16_physical/`)

- **Test design:** Compute per-folio scribal effort proxy (strokes per token ×
  tokens per line × lines per folio) and page complexity proxy (vocabulary
  diversity × mean word length). Measure Spearman correlation.
- **Null hypothesis:** Scribal effort is independent of page complexity
  (consistent with mechanical process).
- **Result:** ρ = -0.0003, p = 0.9926. **Null correlation confirmed.**
- **Runners:** `scripts/phase16_physical_grounding/` (3 scripts)

### 14.2 Grid Layout Efficiency

- **Method:** Compute mean transition distance on the 10×5 physical grid
  versus random grid layouts (10,000 permutations).
- **Result:** 81.50% improvement over random layout. The window arrangement
  is geometrically optimized for short transition distances.

## 15. Phase 17: Steganographic Bandwidth

Phase 17 bounds the maximum information capacity of the lattice's choice
freedom.

### 15.1 Bandwidth Calculation (`src/phase17_finality/bandwidth.py`)

- **Method:** For each admissible choice (word selection within a window),
  compute log₂(window_size) bits. Sum over all 12,519 admissible decisions.
- **Result:** 7.53 bits/word realized bandwidth. Total capacity = 11.5 KB
  (~23,000 Latin characters).
- **Runner:** `scripts/phase17_finality/run_17b_bandwidth_audit.py`

### 15.2 Latin Encoding Test (`scripts/phase17_finality/run_17d_latin_test.py`)

- **Test design:** Encode a Latin Vulgate passage (Genesis 1:1-5, 339 chars)
  into the lattice constraint space by mapping character bits to word-selection
  choices.
- **Result:** Encoding succeeded. 342 of 12,519 choices consumed. Residual
  steganographic bandwidth = 2.21 bits/word.
- **Verdict:** Sparse encoding is feasible; high-density natural language is
  structurally unlikely.

## 16. Phase 20: State Machine Architecture

Phase 20 (12 sprints) systematically evaluates physical device candidates
for the 50-window lattice.

### 16.1 Codebook Architecture (`scripts/phase20_state_machine/run_20a_*.py`)

- **Method:** Compute vocabulary per window, estimate codebook page count
  at 60 words/page (2 columns × 30 rows), compute total pages and quires.
- **Result:** 154 pages, 10 quires. W18 alone = 396 words (~7 pages).
  Consultation rate = 100% (annotation impractical).

### 16.2 State Merging (`scripts/phase20_state_machine/run_20b_*.py`)

- **Method:** Iteratively merge smallest-vocabulary windows into nearest
  neighbor until target state count reached. Evaluate admissibility loss at
  each reduction step.
- **Result:** 15-state merge at 193mm diameter achieves 56.84% admissibility
  (viable but incoherent — Jaccard similarity = 0.000 for all merged states).

### 16.3 Angular Sector Analysis (`scripts/phase20_state_machine/run_20c_*.py`)

- **Method:** Compute minimum disc diameter for N angular sectors using
  D = N × W / π, where W = minimum sector width for readability (6mm label +
  2×3mm margins × 1/sin(π/N) for angled text).
- **Result:** 50-state volvelle requires 549mm minimum diameter. All
  configurations exceed the Apian range (350mm). **Volvelle ruled out.**

### 16.4 Non-Circular Device Ranking (`scripts/phase20_state_machine/run_20d_*.py`)

- **Method:** Score 5 device candidates on weighted criteria (physical size,
  state capacity, vocabulary access, historical plausibility, construction
  complexity).
- **Result:** Tabula + codebook scores 0.865 (rank 1). All 5 candidates are
  physically plausible (≤170mm), but tabula + codebook wins on vocabulary
  access and historical precedent.

### 16.5 Production Workflow Synthesis (`scripts/phase20_state_machine/run_20h_*.py`)

- **Method:** Integrate all findings into a complete production model with
  per-section profiles, error model, and scribal variation characterization.
- **Result:** `PRODUCTION_MODEL.md` — standalone specification sufficient for
  third-party reproduction.
- **Key output:** `results/reports/phase20_state_machine/PRODUCTION_MODEL.md`
