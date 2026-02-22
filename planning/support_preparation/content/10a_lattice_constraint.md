# 10a. The Admissibility Lattice

## 10a.1 From Exclusion to Construction

Phases 1-8 established what the Voynich Manuscript is *not*: not natural language, not a simple substitution cipher, not a random artifact. Phase 9 (the Opportunities program, 27 sprints) systematically explored every residual anomaly and confirmed that no excluded hypothesis could be revived. With the diagnostic landscape cleared, the analysis entered its constructive phase: identifying the specific constraint system that generated the text.

## 10a.2 The 50-Window Lattice (Phase 10)

The breakthrough of Phase 10 was the discovery that the entire Voynich vocabulary (7,717 word types) can be partitioned into exactly 50 disjoint sets — called *windows* — such that word-to-word transitions in the manuscript correspond to transitions between windows. This is not a statistical correlation; it is a deterministic constraint: each word belongs to exactly one window, and each word encodes a specific next-window transition.

The lattice was identified through the Method K admissibility framework:

| Metric | Value |
|:---|:---|
| Windows | 50 |
| Vocabulary | 7,717 types |
| Window size range | 18-396 words |
| Canonical admissibility (raw) | 58.27% |
| With suffix recovery | 64.94% |
| Overgeneration | ~20x at all n-gram orders |
| Branching factor | 761.7 candidates per position (9.57 effective bits) |

The admissibility rate — the fraction of observed transitions that are *reachable* under the lattice model — stabilized at 64.94% after incorporating suffix-biased drift recovery. This means roughly two-thirds of all token transitions in the manuscript follow the lattice exactly, while the remaining third represents the combined effect of rare-word sparsity, scribal variation, and mechanical error.

### Residual Diagnosis

The ~35% non-admissible residual is not uniformly distributed. It is dominated by rare words:

| Frequency Tier | Failure Rate | Share of All Failures |
|:---|---:|---:|
| Common (>100 occurrences) | 6.9% | 6.8% |
| Medium (10-100) | 35.1% | 25.9% |
| Rare (<10) | 84.5% | 55.8% |
| Hapax (1 occurrence) | 97.8% | 11.5% |

Words appearing more than 100 times obey the lattice with 93.1% fidelity. The residual is a frequency effect, not a structural one — the lattice accounts for virtually all common transitions.

## 10a.3 Method K: Adversarial Testing

The lattice hypothesis was subjected to adversarial testing via "Method K" — a battery of probes designed to find linguistic-ward anomalies that might indicate hidden natural language structure. Initial results showed systematic residuals: paragraph-initial entropy anomalies, section-boundary effects, and features that trended toward natural language profiles.

However, these residuals were fully resolved by introducing a **context mask** — a persistent, non-semantic modulation parameter that varies across lines and pages. With context masking, the z-scores of linguistic-ward anomalies collapsed by over 70% (ANOVA p = 4.24 x 10^-47). The residuals were not evidence of hidden language; they were the signature of a multi-parameter constraint system where rules are modulated by position and persistent state.

This moved the identification status from "in tension" to "refined closure": the text is the output of a constrained generative process, not a natural language with disguised structure.

## 10a.4 Stroke-Level Independence (Phase 11)

A critical test of the lattice hypothesis was whether it operated at a single scale or was fractal — present at both word-level and sub-glyph stroke-level. Phase 11 measured the similarity between word-scale transition topology and stroke-scale transition topology.

The result was unambiguous: average cross-scale similarity was below 30%. The constraint lattice operates **exclusively at the word level**. It is not an emergent property of handwriting or a recursive pattern that appears at all scales. This confirms a *deliberative* system — the scribe was consciously selecting tokens from a rule-governed set, not composing characters in a way that would naturally produce lattice structure.

The scale independence result has a strong practical implication: the physical production device operates on whole words (tokens), not on individual glyphs. The scribe was not "spelling" — they were selecting pre-formed word units from a reference.
