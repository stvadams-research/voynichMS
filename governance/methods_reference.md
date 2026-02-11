# Methods Reference

This document summarizes the quantitative methods used in phase2_analysis/phase3_synthesis and
the key caveats needed for audit interpretation.

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
