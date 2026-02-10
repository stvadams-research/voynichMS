# Methods Reference

This document summarizes the quantitative methods used in analysis/synthesis and
the key caveats needed for audit interpretation.

## 1. Foundation Metrics

### 1.1 Repetition Rate (`src/foundation/metrics/library.py`)
- Primary formula:
  `token_repetition_rate = repeated_token_occurrences / total_tokens`
- Supplementary statistic:
  `vocabulary_coverage = 1 - (unique_tokens / total_tokens)`
- Canonical output:
  `MetricResult.value` is always `token_repetition_rate`.
- Known confounds:
  Corpus length, transcription sparsity, and token normalization choices can
  shift absolute values.

### 1.2 Cluster Tightness (`src/foundation/metrics/library.py`)
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

### 2.1 Mapping Stability (`src/analysis/stress_tests/mapping_stability.py`)
- Tests segmentation/order/omission robustness under perturbation.
- Thresholds come from `configs/analysis/thresholds.json`.
- Known confounds:
  boundary quality, alignment completeness, and control coverage.

### 2.2 Information Preservation (`src/analysis/stress_tests/information_preservation.py`)
- Uses token entropy, redundancy, and cross-scale correlation.
- Known confounds:
  token truncation limits (`MAX_TOKENS_ANALYZED`), page sampling limits, and
  uneven anchor density.

### 2.3 Locality & Compositionality (`src/analysis/stress_tests/locality.py`)
- Uses locality ratio bands, compositional score bands, and procedural signals.
- Thresholds come from `configs/analysis/thresholds.json`.
- Known confounds:
  line ordering quality, sparse alignments, and vocabulary drift across pages.

## 3. Comparative Separation

### 3.1 Indistinguishability (`src/synthesis/indistinguishability.py`)
- Separation score:
  `S = inter_centroid_distance / (inter_centroid_distance + average_spread)`
- Success/failure thresholds come from `configs/analysis/thresholds.json`.
- Synthetic positional entropy is now computed from generated token position
  distributions, not a simulated constant.
- Known confounds:
  feature-set incompleteness and control-generation assumptions.

## 4. Circularity Disclosure

Some anomaly modules intentionally take observed Phase 1-3 values as constraint
inputs. This is explicit and scoped:
- `src/analysis/anomaly/capacity_bounding.py`:
  uses observed values to test whether non-semantic systems could produce them.
- `src/analysis/anomaly/constraint_analysis.py`:
  uses observed values as fixed constraint parameters for intersection logic.
- `src/analysis/anomaly/stability_analysis.py`:
  baseline values are caller-provided references; analysis tests perturbation
  stability, not baseline independence.

## 5. Control Pipeline

Control generators (`synthetic`, `self_citation`, `table_grille`,
`mechanical_reuse`) generate token streams programmatically and intentionally
bypass EVAParser normalization. Rationale:
- control tokens are emitted from already-normalized vocabularies;
- objective is structural contrast testing, not manuscript transcription.

Known confound:
- if future control vocabularies include non-normalized glyph variants, they
  should be routed through EVAParser to maintain symmetry.
