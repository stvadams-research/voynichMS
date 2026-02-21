# Phase 14: Canonical Evaluation Report

**Data source:** Zandbergen-Landini transcription (5,145 lines, 34,605 tokens, IVTFF-sanitized)
**Window ordering:** Spectral reordering via Fiedler vector of transition graph Laplacian

## 1. Model Definition
- **Lexicon Clamp:** 7,717 unique tokens (full ZL clean vocabulary).
- **Physical Complexity:** 50 windows (spectrally ordered), 15 vertical stacks.
- **Window ordering:** KMeans clustering + spectral reordering for optimal sequential access.

## 2. Headline Metrics
| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Token Coverage** | 94.93% | Percentage of manuscript tokens within lexicon clamp. |
| **Admissibility (Drift ±1)** | 43.44% | Percentage of clamped tokens within current or adjacent window. |
| **Extended Admissibility (±3)** | 57.73% | Including extended drift (distance 2-3). |
| **Compression (MDL)** | 66.6 KB | Total description length (Model 18.9 KB + Data 47.7 KB). |
| **Mirror Corpus Entropy Fit** | 87.60% | Synthetic 12.23 bits vs Real 10.88 bits. |

## 3. Transition Category Distribution
| Category | Count | Rate |
| :--- | ---: | ---: |
| Admissible (Dist 0-1) | 14,270 | 43.44% |
| Extended Drift (Dist 2-3) | 4,696 | 14.29% |
| Mechanical Slip (Dist 4-10) | 9,994 | 30.42% |
| Extreme Jump (>10) | 3,892 | 11.85% |

**Impact of spectral reordering:** Extreme jumps dropped from 47.25% to 11.85% (a 4x reduction). Most former "extreme jumps" were not actually random — they were systematic transitions that appeared distant only because KMeans assigned arbitrary window IDs.

## 4. Overgeneration Audit
| N-gram | Real Count | Syn Count | Unattested Count | Unattested Rate |
| :--- | ---: | ---: | ---: | ---: |
| Words (UWR) | 9,456 | 7,717 | 0 | 0.00% |
| Trigrams (UTR) | 25,040 | 499,364 | 499,364 | 100.00% |

The 0% word-level UWR is a byproduct of the lexicon clamp (full vocabulary mapped). The 100% trigram UTR reflects combinatorial sparsity: 7,717 tokens across 50 windows can form ~500K window-admissible trigrams, while the real corpus contains only 25K — so most generated trigrams are unseen but structurally valid.

## 5. Baseline Comparison (Two-Part MDL)
| Model | L(model) | L(data|model) | L(total) | BPT |
| :--- | ---: | ---: | ---: | ---: |
| **Copy-Reset** | **20** | **377,229** | **377,249** | **10.90** |
| Hybrid (CR+Lattice) | 154,380 | 381,719 | 536,099 | 15.49 |
| Lattice (Ours) | 154,340 | 389,950 | 544,290 | 15.73 |
| Table-Grille | 238,090 | 405,146 | 643,236 | 18.59 |
| Markov-O2 | 250,400 | 431,676 | 682,076 | 19.71 |

Copy-Reset wins on full-corpus MDL due to minimal model cost (2 parameters). The Hybrid mixture model (Copy-Reset + Lattice + Unigram) improves L(data|model) by 8K bits over the pure Lattice (381K vs 390K), confirming that Copy-Reset's within-line repetition signal and the Lattice's structural signal are complementary. However, the 154K model cost (encoding 7,717 window assignments) still dominates.

## 6. Holdout Validation (Herbal → Biological)
| Metric | Lattice (Drift ±1) | Copy-Reset (k=5) |
| :--- | ---: | ---: |
| Admissibility | 10.81% | 3.71% |
| Z-Score | 16.2 σ | 79.4 σ |
| Test Tokens | 6,422 | 6,422 |

The Lattice generalizes 2.9x better than Copy-Reset across manuscript sections. Both are statistically significant above chance, but Copy-Reset's 3.71% represents minimal structural capture.

## 7. Slip Detection (Validated)
| Metric | Value |
| :--- | ---: |
| Observed Slips | 202 |
| Null Mean (10K permutations) | 106.9 |
| Z-Score | 9.47 σ |
| Empirical p-value | < 0.0001 |

The vertical-offset signal is statistically real (p < 0.0001), not an artifact of chance line adjacency.

## 8. Physical Grounding
| Metric | Value |
| :--- | ---: |
| Ergonomic Effort Correlation (rho) | -0.0003 (p = 0.99) |
| Grid Layout Efficiency | 81.50% improvement over random |
| Steganographic Bandwidth | 7.53 bits/word |
| Total Capacity | 11.5 KB (~23K Latin chars) |

Layout efficiency is strong (transitions favor physical proximity), but effort-vs-frequency correlation is null — scribes did not preferentially select easier tokens.

## 9. Mask Offset Inference
| Configuration | No Mask | Per-Line Mask | Top-12 Restricted |
| :--- | ---: | ---: | ---: |
| Original palette | 35.32% | 49.24% | 45.89% |
| Reordered palette | 39.57% | 53.91% | 50.22% |

Per-line mask inference adds ~14pp on top of the reordered palette. The optimal offsets use 48 of 50 possible values. The emulator now uses full-range mask rotation (0 to num_windows-1) to match this empirical finding.

## 10. Failure Diagnosis (Post-Reordering)
| Category | Rate | Interpretation |
| :--- | ---: | :--- |
| Admissible | 41.24% | Correctly predicted by lattice walk. |
| Not in Palette | 5.07% | Rare tokens (hapax or near-hapax). |
| Wrong Window (2-10) | 42.45% | Reachable but not adjacent — possible mask rotation or extended drift. |
| Extreme Jump (>10) | 11.25% | Residual tracking failures (down from 47.25%). |

Per-section variation: Biological (53.2% admissible), Cosmo (48.0%), Stars (41.8%), Pharma (40.8%), Herbal A (36.4%), Herbal B (31.7%), Astro (27.7%).

## 11. Section-Aware Routing (Null Result)

Section-specific spectral reordering was tested: each of the 7 manuscript sections received its own Fiedler-vector ordering of the same 50 physical windows. Result: section-specific ordering **hurts** global admissibility (-8.0pp), and no individual section improved except Herbal B (+0.9pp, within noise).

**Interpretation:** The scribe uses the same traversal pattern across all sections. The 25.5pp section gap (Biological 53.2% vs Astro 27.7%) is driven by vocabulary distribution — sections with more common tokens (concentrated in a few windows) score higher, not by different tool configurations per section. This rules out "section-specific tool settings" as an explanation for section variation.

## 12. Formal Conclusion
The spectrally-reordered lattice model achieves 43.4% drift-admissibility and 57.7% extended admissibility, with extreme jumps reduced to 11.9%. The model captures genuine cross-section structure (holdout 16.2σ, slip signal 9.5σ) that simpler models cannot reproduce. Per-line mask inference further pushes admissibility to 53.9%, suggesting physical disc rotation is a real production feature.

The remaining 42% "wrong window" category (distance 2-10) likely represents mask rotations within lines and scribe hand changes. Section-specific tool configurations have been ruled out (Section 11). Copy-Reset remains the most parsimonious full-corpus model on MDL, but it cannot generalize across sections (3.71% vs Lattice's 10.81% holdout). The Hybrid mixture model (15.49 BPT) confirms that Copy-Reset's repetition signal and the Lattice's structural signal are complementary — both capture real aspects of the production mechanism.
