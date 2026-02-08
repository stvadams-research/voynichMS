# Metrics Reference

## 1. Repetition Rate
- **Definition:** The proportion of tokens in a text that appear more than once.
- **Formula:** `1 - (Unique Tokens / Total Tokens)` (Simplified variant used in some contexts) or `Repeated Token Count / Total Count`.
- **Target:** ~0.90 for Voynich Manuscript (Pharmaceutical Section).
- **Implementation:** `src/foundation/metrics/library.py` (RepetitionRate).

## 2. Information Density (Z-Score)
- **Definition:** The deviation of the text's entropy from a scrambled control version, measured in standard deviations.
- **Formula:** `(Real Entropy - Mean Scrambled Entropy) / Std Dev Scrambled Entropy`.
- **Target:** ~5.68 (High density, non-random).
- **Implementation:** `src/analysis/stress_tests/information_preservation.py`.

## 3. Locality Radius
- **Definition:** The effective window size (in tokens) within which structural dependencies (e.g., bigram correlations) are strongest.
- **Target:** 2-4 units (Very local).
- **Implementation:** `src/analysis/stress_tests/locality.py`.

## 4. Mapping Stability
- **Definition:** The resilience of glyph/word identity under geometric perturbation (shifting bounding boxes).
- **Target:** < 0.10 (Collapsed/Fragile).
- **Implementation:** `src/analysis/stress_tests/mapping_stability.py`.
