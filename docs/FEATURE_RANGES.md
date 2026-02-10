# Discriminative Feature Ranges

This document provides the reference ranges for features used to discriminate between real Voynich pharmaceutical pages and synthetic/scrambled controls.

## 1. Spatial Features

| Feature ID | Real (Default) | Scrambled Range | Description |
|---|---|---|---|
| `spatial_jar_variance` | 0.20 | [0.3, 0.5] | Variance in jar positions across the page. |
| `spatial_text_density_gradient` | 0.02 | [-0.1, 0.1] | Top-to-bottom text density gradient. |
| `spatial_jar_alignment` | 0.70 | [0.2, 0.6] | Degree of horizontal/vertical alignment of visual elements. |

## 2. Textual Features

| Feature ID | Real (Default) | Scrambled Range | Description |
|---|---|---|---|
| `text_inter_jar_similarity` | 0.35 | [0.05, 0.15] | Jaccard similarity of tokens between distinct jars. |
| `text_vocabulary_overlap` | 0.42 | [0.06, 0.18] | Fraction of vocabulary shared across the page. |
| `text_bigram_consistency` | 0.70 | [0.2, 0.4] | Consistency of local bigram patterns. |

## 3. Positional and Variance Features

| Feature ID | Real (Default) | Scrambled Range | Description |
|---|---|---|---|
| `pos_left_right_asymmetry` | 0.08 | [0.0, 0.2] | Difference in text properties between page halves. |
| `pos_first_last_line_diff` | 0.15 | [0.1, 0.5] | Statistical difference between start and end of blocks. |
| `var_locality_variance` | 0.10 | [0.3, 0.5] | Variance of locality metrics across regions. |
| `var_word_length_variance` | 0.12 | [0.3, 0.6] | Variance of mean word length across regions. |

## 4. Temporal and Gradient Features

| Feature ID | Real (Default) | Scrambled Range | Description |
|---|---|---|---|
| `temp_repetition_spacing` | 4.5 | [1.0, 10.0] | Average token distance between repeated occurrences. |
| `temp_token_burst_rate` | 0.05 | [0.02, 0.15] | Rate of consecutive token repetitions (bursts). |
| `grad_entropy_slope` | -0.02 | [-0.1, 0.1] | Change in Shannon entropy across the page. |
| `grad_density_slope` | -0.016 | [-0.08, 0.08] | Change in information density across the page. |
