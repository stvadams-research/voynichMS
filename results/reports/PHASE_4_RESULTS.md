# PHASE 4 RESULTS: INFERENCE ADMISSIBILITY

**Date:** 2026-02-07
**Status:** Method A Evaluation Complete

---

## 1. Method A: Information Clustering (Montemurro & Zanette)

### Objective
Evaluate if non-uniform token distributions across sections are diagnostic of semantic topicality.

### Quantitative Benchmark

| Dataset | Tokens | Avg Info (bits) | Max Info (bits) | Keywords (>1bit) |
|---------|--------|-----------------|-----------------|------------------|
| **Voynich (Real)** | 230,337 | 2.2025 | 4.3220 | 4,288 |
| **Latin (Semantic)** | 230,000 | 1.1620 | 2.3219 | 3,231 |
| **Self-Citation** | 230,000 | 3.5870 | 4.3219 | 8,761 |
| **Mechanical Reuse** | 230,000 | 3.6222 | 4.3219 | 7,247 |
| **Table-Grille** | 230,000 | 0.0103 | 0.0206 | 0 |
| **Shuffled (Global)**| 230,000 | 1.2608 | 3.3510 | 3,028 |

### Key Findings
1.  **False Positive Confirmation:** The `Self-Citation` and `Mechanical Reuse` models produced higher average information scores (3.58 - 3.62) than the real Voynich manuscript (2.20).
2.  **Semantic Baseline:** The Latin baseline showed significantly *lower* average information (1.16) than the structured non-semantic models, suggesting that mechanical reuse is a more powerful driver of section-clustering than actual natural language semantics in this scale.
3.  **Sensitivity:** Shuffling the global corpus reduced the info score to 1.26, which is still higher than the Table-Grille model but significantly lower than the real/self-citation models.

### Method Classification
**NOT DIAGNOSTIC.** 
Information clustering fails to separate semantic corpora from non-semantic structured corpora. In fact, simple mechanical reuse patterns (Self-Citation and bounded pools) produce stronger "topical" signals than natural language.

---

## 2. Method B: Network Features (Amancio et al.)

### Objective
Evaluate if Word Adjacency Network (WAN) metrics distinguish semantic text from structured non-semantic text.

### Quantitative Benchmark

| Dataset | Clustering | Assortativity | Zipf Alpha | TTR |
|---------|------------|---------------|------------|-----|
| **Voynich (Real)** | 0.1173 | -0.0735 | 0.7738 | 0.1684 |
| **Latin (Semantic)** | 0.1008 | -0.1215 | 0.7869 | 0.0516 |
| **Mechanical Reuse** | 0.3393 | -0.1423 | 1.0777 | 0.1304 |
| **Self-Citation** | 0.0437 | 0.0087 | 0.2493 | 0.0883 |
| **Table-Grille** | 0.0060 | 0.2927 | 0.1989 | 0.0004 |
| **Shuffled (Global)**| 0.0393 | -0.0338 | 0.7738 | 0.1685 |

### Key Findings
1.  **Similarity to Language:** Voynich metrics for clustering and assortativity are indeed compatible with the Latin semantic baseline.
2.  **False Positive (The "Super-Structure" Problem):** The `Mechanical Reuse` model (bounded token pools) produced a clustering coefficient (0.3393) nearly **3x higher** than natural language. 
3.  **Independence of Frequencies:** Zipf Alpha remained invariant under shuffling, as expected, proving it is a property of the vocabulary distribution, not its linear structure.

### Method Classification
**NOT DIAGNOSTIC.**
While Voynich's network metrics are "language-like," they are also "mechanical-like." The fact that a simple pool-reuse model exceeds the clustering of natural language proves that high clustering is not a reliable indicator of semantic adjacency.

---

## 3. Method C: Topic-Section Alignment

### Objective
Determine if latent topics identified by LDA align with manuscript sections in a way that is unique to semantic text.

### Quantitative Benchmark

| Dataset | Unique Dominant Topics | Avg KL (Topicality) |
|---------|------------------------|---------------------|
| **Voynich (Real)** | 5 | 3.0732 |
| **Latin (Semantic)** | 2 | 2.9115 |
| **Self-Citation** | 9 | 3.0621 |
| **Mechanical Reuse** | 2 | 3.0832 |
| **Table-Grille** | 8 | 0.0667 |
| **Shuffled (Global)**| 1 | 3.3200 |

### Key Findings
1.  **False Positive Confirmation:** The `Self-Citation` model produced 9 unique dominant topics across 20 sections, compared to only 5 for the real Voynich manuscript.
2.  **Topic Concentration:** Both `Voynich` and `Self-Citation` showed nearly identical "topicality" scores (Avg KL from uniform ~3.06-3.07), proving that non-semantic generators can produce latent topics just as concentrated as those found in the manuscript.
3.  **Low Semantic Discrimination:** The Latin baseline performed *worse* on unique topic count (2) than the structured non-semantic models, suggesting that topic models are more sensitive to mechanical repetition than to semantic flow at this scale.

### Method Classification
**NOT DIAGNOSTIC.**
The alignment of topic models with sections is not evidence of semantics. It is a highly sensitive detector of local frequency variation, which is a feature of many mechanical production models (especially Self-Citation).

---

## 4. Method D: Language ID under Flexible Transforms

### Objective
Quantify the risk of false positive language matches when applying flexible transformations to non-semantic data.

### Quantitative Benchmark (Best Match Confidence)

| Dataset | Target: Latin | Target: English |
|---------|---------------|-----------------|
| **Voynich (Real)** | 0.1369 | 0.1651 |
| **Shuffled (Global)**| 0.1363 | 0.1692 |
| **Mechanical Reuse** | 0.1214 | 0.1734 |

### Key Findings
1.  **Noise Indistinguishability:** The "best match" scores for the real Voynich manuscript were indistinguishable from those obtained for globally shuffled tokens. 
2.  **False Positive Lead:** The `Mechanical Reuse` model (non-semantic) actually produced a *higher* English similarity score (0.1734) than the real manuscript (0.1651).
3.  **Search Flexibility Risk:** Even with a small set of 14 dummy transforms, we achieved "matches" for random noise that were statistically equal to the real data. 

### Method Classification
**NOT DIAGNOSTIC.**
Language identification under flexible transforms is highly susceptible to the "multiple comparisons" problem. High-confidence matches do not imply underlying semantics, as they can be replicated (and even exceeded) by non-semantic and shuffled corpora.

---

## 5. Method E: Unsupervised Morphology Induction

### Objective
Measure if morphological units (prefixes/suffixes) identify semantic structure differently than mechanical structure.

### Quantitative Benchmark (Consistency Score)

| Dataset | Unique Words | Consistency Score | Top Suffixes |
|---------|--------------|-------------------|--------------|
| **Voynich (Real)** | 38,800 | 0.0711 | y, 9, G |
| **Latin (Semantic)** | 11,868 | 0.0846 | s, t, e |
| **Self-Citation** | 20,309 | 0.0957 | y, h, x |
| **Mechanical Reuse** | 29,982 | 0.0403 | y, n, in |
| **Table-Grille** | 91 | 0.1758 | y, m, dy |
| **Shuffled (Global)**| 38,764 | 0.0711 | y, 9, G |

### Key Findings
1.  **Vocabulary Invariance:** The consistency score for `Shuffled (Global)` was identical to the real manuscript, proving that morphology induction measures vocabulary properties, not linear syntax or meaning.
2.  **False Positive Confirmation:** The `Self-Citation` model produced a *higher* morphological consistency (0.0957) than the natural language Latin baseline (0.0846). 
3.  **Mechanical Sufficiency:** Purely mechanical table-grille models (Rugg style) produce the highest consistency scores (0.1758), as they explicitly reuse suffixes.

### Method Classification
**NOT DIAGNOSTIC.**
Morphology induction identifies regularities in the word-formation process, which are present in both natural language and mechanical generation models. It cannot be used to infer the presence of semantics.

---

## 6. Phase 4 Final Conclusion

Phase 4 has systematically evaluated five common inference methods used to claim the presence of language or meaning in the Voynich Manuscript. In every case, the methods failed to separate semantic text from non-semantic, structurally constrained controls.

### Summary of Admissibility Boundary

| Method | Status | Primary Vulnerability |
|--------|--------|-----------------------|
| **A: Info Clustering** | **NOT DIAGNOSTIC** | Triggered by bounded-pool mechanical reuse. |
| **B: Network Features**| **NOT DIAGNOSTIC** | Mechanical models exceed language in clustering. |
| **C: Topic Alignment** | **NOT DIAGNOSTIC** | Measures local frequency shift, not coherence. |
| **D: AI Lang-ID** | **NOT DIAGNOSTIC** | Search flexibility yields false positives on noise. |
| **E: Morph Induction** | **NOT DIAGNOSTIC** | Property of vocabulary, easily simulated by tables. |

**DETERMINATION:**
None of the widely cited statistical or computational "proofs" of language in the Voynich Manuscript are diagnostic of semantics. They all identify features that are equally (or more) prevalent in purely mechanical production models. The manuscript remains structurally admissible as a non-semantic procedural artifact.

| Method | Status | Outcome |
|--------|--------|---------|
| **A: Info Clustering** | **COMPLETE** | **NOT DIAGNOSTIC** (False Positives confirmed) |
| **B: Network Features**| PENDING | |
| **C: Topic Alignment** | PENDING | |
| **D: AI Decipherment** | PENDING | |
| **E: Morph Induction** | PENDING | |

**Conclusion:** The claim that Voynich keyword clustering implies "topical meaning" is structurally unjustified. The signal is entirely consistent with (and even weaker than) simple mechanical production models.
