# Thresholds Rationale

Why each major threshold, cutoff, and configurable parameter has the value it
does. Organized by config file and source location.

For **where** each config lives, see [config_reference.md](config_reference.md).
This document covers the **why**.

---

## Guiding Principles

1. **Convention over invention:** Where a well-established statistical convention
   exists (z=2.0 for outliers, z=3.0 for high-significance, p<0.01 for
   hypothesis tests), we adopt it directly.

2. **Sensitivity-informed:** Where no convention exists, we derive thresholds from
   the data's own sensitivity profile — typically using Phase 2 perturbation
   analysis to identify stability boundaries.

3. **Conservative by default:** Thresholds are set to minimize false positives
   (Type I errors) rather than maximize detection power. This reflects the
   project's epistemic-discipline priority.

4. **Symmetric controls:** Where possible, thresholds are validated by running the
   same tests on scrambled/synthetic controls to verify discrimination power.

---

## Phase 2: Analysis Thresholds

**Config:** `configs/phase2_analysis/thresholds.json`

### Mapping Stability

| Parameter | Value | Rationale |
|---|---|---|
| `perturbation_strength` | 0.05 | 5% of word width — the smallest boundary shift that reliably changes glyph identity. Derived from Phase 2.1 analysis showing that 5% shifts cause 37.5% glyph identity collapse. Smaller values (1-2%) produce negligible collapse; larger values (10%+) are unrealistically harsh. |
| `ordering_collapse` | 0.5 | A constructed system where half the token orderings collapse under perturbation is not robust. Set at 50% because scrambled controls average 0.45 collapse, so the threshold separates real from random. |
| `min_stable` | 0.6 | Minimum stability score to classify a system as "stable." Positioned above the scrambled control mean (0.45) with margin. |
| `standard_high_confidence` | 0.7 | Conservative threshold for high-confidence stability claims. Used in publication for qualifying statements. |

### Indistinguishability

| Parameter | Value | Rationale |
|---|---|---|
| `separation_success` | 0.7 | If a classifier can separate real from synthetic >70% of the time, the synthesis has failed to capture something real. 0.7 is the conventional AUC threshold for "better than weak" classification (0.5 = chance). |
| `separation_failure` | 0.3 | Below 30% separation, the classifier performs worse than chance (inverted labels). Not meaningful as a failure signal — used only as a lower bound check. |

### Comparator

| Parameter | Value | Rationale |
|---|---|---|
| `significant_difference` | 0.05 | 5% relative difference between real and control metrics is the minimum to classify a comparison as SURVIVES. Derived from variance analysis: typical metric noise is 2-3%, so 5% provides a 2x margin above noise. |
| `negligible_difference` | 0.02 | Below 2% relative difference, the comparison is classified as NEGLIGIBLE. Matches the typical measurement noise floor. |

---

## Phase 6: Functional Thresholds

**Config:** `configs/phase6_functional/synthesis_params.json`

### Continuation Generation

| Parameter | Value | Rationale |
|---|---|---|
| `locality_window` | [2, 4] | Token predecessor context window. 2 captures bigram constraints, 4 captures the widest dependency measured in Phase 5 (~3.5 token average). |
| `information_density_tolerance` | 0.5 | ±0.5 bits from observed information density (4.0). Allows natural variation while catching degenerate generators that produce near-zero or maximal entropy. |
| `min_perturbation_robustness` | 0.50 | A continuation that collapses under 50% of perturbation tests is too fragile to be a valid extension. Set at the median of observed robustness scores for real manuscript pages. |
| `max_novel_tokens` | 0.10 | A valid continuation should not introduce more than 10% previously unseen tokens. Derived from Phase 5 vocabulary analysis: real manuscript pages have <5% novel tokens vs. prior pages. 10% provides 2x margin. |

### Equivalence

| Parameter | Value | Rationale |
|---|---|---|
| `equivalence_threshold` | 0.30 | Two systems are "equivalent" if their feature distance is <30% of the full feature range. Derived from Phase 8 comparative analysis: the closest historical artifacts (Lullian wheels) score ~0.35 distance. |

---

## Phase 10: Admissibility Thresholds

**Config:** `configs/phase10_admissibility/`

### Method J (Steganographic Extraction)

| Parameter | Value | Rationale |
|---|---|---|
| `z_threshold` | 3.0 | Standard "high-significance" z-score. At 3σ, the probability of a false positive under Gaussian null is 0.13%. |
| `min_stable_non_edge_anomalies` | 1 (Stage 1), 2 (Stage 5) | At least one (Stage 1) or two (Stage 5, stricter) non-edge extraction rules must produce stable anomalies. Edge rules (line-initial, paragraph-initial) are excluded because their anomalous structure is expected from line-boundary resets identified in Phase 5. |
| `bootstrap_pass_rate` | 0.80 | An anomaly must survive 80% of bootstrap resamples to qualify as "stable." Standard resampling stability threshold. |

### Method K (Residual Gap Anatomy)

| Parameter | Value | Rationale |
|---|---|---|
| `correlation_threshold` | 0.4 | Outlier features must show mean absolute inter-correlation ≥0.4 to qualify as "systematic" rather than independent noise. Cohen's convention: r=0.3 is medium, r=0.5 is large. 0.4 is midway, balancing sensitivity with false-positive risk. |
| `min_consistent_outliers` | 2 (Stage 1), 3 (Stage 5) | Minimum count of correlated outlier features. Two is the minimum for measuring correlation; three (Stage 5) is stricter for high-stakes retest. |
| `min_seed_pass_rate_for_weakened` | 0.75 | At least 75% of seeds in the seed band must independently reproduce the weakened outcome. Ensures the result is not an artifact of one lucky seed. |

### Method F (Reverse Mechanism)

| Parameter | Value | Rationale |
|---|---|---|
| `param_samples_per_family` | 10,000 | Sufficient coverage of the parameterization space to detect low-entropy decoders. Power analysis: at 10K samples, a decoder existing in 0.01% of parameter space has 63% probability of being sampled at least once. |
| `null_sequences` | 1,000 | Block-bootstrap permutations for building the null entropy distribution. 1,000 provides stable quantile estimates (SE of 1st percentile < 0.01). |
| `stability_threshold` | 0.70 | A candidate decoder must survive 70% of perturbation tests. Stricter than 50% (coin flip) but less strict than 90% (which would miss real but noisy signals). |

### Multi-Seed Replication

| Parameter | Value | Rationale |
|---|---|---|
| `seeds` | [42, 77, 101] | Three primes spanning the seed space. 42 is the project default. 77 and 101 provide independent verification. Three seeds are the minimum for majority-vote consensus. |
| `require_same_direction` | true | All seeds must agree on the outcome direction (strengthened/weakened/indeterminate). Prevents averaging over contradictory results. |

---

## Core Audit & Skeptic Thresholds

**Config:** `configs/core_audit/`, `configs/core_skeptic/`

### Release Evidence Policy

| Parameter | Value | Rationale |
|---|---|---|
| `min_pages` | 200 | The Voynich manuscript has ~230 pages. 200 ensures near-complete coverage without requiring every page (some are damaged/fragmentary). |
| `min_tokens` | 200,000 | The canonical transliteration contains ~197,000 tokens. 200K ensures complete tokenization plus minimal overhead. |
| `max_total_warning_count` | 400 | Empirically calibrated: a clean full run produces ~250-300 warnings (mostly "sparse data" for small sections). 400 allows headroom without masking real problems. |

### Comparative Uncertainty Policy

| Parameter | Value | Rationale |
|---|---|---|
| `min_nearest_neighbor_stability_for_confirmed` | 0.75 | Standard "good stability" threshold from jackknife literature. Below 75%, the nearest-neighbor assignment is too sensitive to leave-one-out perturbations. |
| `min_rank_stability_for_confirmed` | 0.65 | Rank ordering is inherently noisier than distance metrics. 65% accounts for this while still requiring majority stability. |
| `min_rank_entropy_for_high` | 1.5 | At entropy 1.5 bits (among ~10 comparison artifacts), rank uncertainty spans ~3 effective positions. Below this, the ranking is sufficiently concentrated. |

---

## Source-Code Hardcoded Constants

These values are embedded in source rather than config files. Each has a
rationale but should ideally be migrated to configs in a future sprint.

| Value | Location | Rationale |
|---|---|---|
| `500` (Zipf rank limit) | `network_features/analyzer.py:84` | Standard Zipf-law fitting practice: ranks beyond ~500 are dominated by hapax legomena and distort the power-law fit. Empirically, the Voynich vocabulary plateaus at ~450 ranked types. |
| `8` (folios per quire) | `quire_analysis.py:30` | The most common Voynich quire size is 8 folios (quaternion). A simplifying approximation; actual quire sizes vary (6-10). Documented in code comment. |
| `66, 75-84, 103-116` (Currier hand boundaries) | `scribe_coupling.py:30-33` | Approximate folio boundaries for Currier's Hand 1 / Hand 2 classification, derived from Currier (1976) and D'Imperio (1978). These are paleographic consensus values, not computed. |
| `0.3` (fallback probability) | `text_generator.py:187` | Probability of using position-biased token selection in synthetic text generation. Set to produce text with similar positional entropy to the real manuscript (~0.80). Calibrated empirically during Phase 3 development. |
| `0.05` (alpha smoothing) | `anchor_coupling.py:53` | Laplace smoothing parameter for coupling score computation. Standard small-sample smoothing value to prevent zero-probability estimates. |
| `0.01` / `0.95` (null percentiles) | `stage3_pipeline.py:541-542` | 1st percentile for entropy outliers, 95th for bigram MI. Conservative quantile thresholds for identifying extreme values in null distributions. |
| `0.80` (bootstrap confidence) | `stage2_pipeline.py:1061` | Minimum bootstrap confidence for language-closer classification in Method I. Standard 80% confidence level for exploratory analysis. |

---

## Statistical Convention Reference

For convenience, here are the standard statistical conventions used throughout:

| Convention | Value | Usage |
|---|---|---|
| Outlier z-score | ≥ 2.0 | Feature flagging, Method K |
| High-significance z-score | ≥ 3.0 | Anomaly detection, Method J |
| Statistical significance | p < 0.01 | Hypothesis testing, Mantel tests |
| Bootstrap stability | ≥ 80% | Resampling pass rate |
| AUC "better than weak" | > 0.7 | Classification performance |
| Effect size: medium | r ≥ 0.3 | Correlation thresholds |
| Effect size: large | r ≥ 0.5 | Strong correlation thresholds |
