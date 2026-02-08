# Corpus Construction for Phase 4

This document defines the methodology for constructing the matched corpora used in Phase 4 Inference Admissibility Evaluation.

## 1. Target Scale
All corpora are matched to the scale of the primary Voynich dataset (`voynich_real`):
- **Token Count:** ~233,000 tokens.
- **Sectioning:** Default 20 bins of equal length, or natural manuscript sections where applicable.

## 2. Semantic Baselines
We require natural language texts to establish "diagnostic" success.
- **Latin (latin_classic):** Selected for its morphological richness and historical relevance.
- **English (english_mid):** Selected as a modern comparative baseline.

*Method:* Texts will be sourced from Project Gutenberg or similar public domain repositories, tokenized by whitespace, and truncated to match Voynich length.

## 3. Non-Semantic Structured Controls
These are the most critical datasets for falsifying inference claims.

### 3.1 Self-Citation Model (Timm/Schinner)
- **Logic:** Randomly select a "kernel" from a small pool, then mutate it or append suffixes based on local similarity.
- **Goal:** Reproduce the Zipf-like distributions and local repetitions without meaning.

### 3.2 Table and Grille Model (Rugg)
- **Logic:** Use a 2D table of prefixes, infixes, and suffixes. Use a "grille" (mask) to select components.
- **Goal:** Reproduce rigid positional constraints and vocabulary properties.

### 3.3 Phase 3.2/3.3 Generators
- **voynich_synthetic_grammar:** Probabilistic glyph-level grammar.
- **mechanical_reuse:** Grammar-based with bounded token pools (size 20-30).

## 4. Negative Controls
- **shuffled_global:** All tokens in `voynich_real` are pooled and randomly redistributed. Destroys all section-level and local structure.
- **shuffled_section:** Tokens are shuffled only within their natural sections. Preserves section-level frequency distributions but destroys local adjacency.

## 5. Metadata and Hash Verification
Every corpus must be registered in the database with a unique ID and a SHA256 checksum of its token sequence to ensure provenance.
