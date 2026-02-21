# Where We Stand — Updated Claim Statement (2026-02-21 1pm)

## 1. The text is constructively generable — but the capture rate is lower than previously claimed

You have a deterministic 50-window lattice that maps 7,717 tokens (94.93% of the ZL corpus vocabulary) into a sequential constraint system where word(n) determines window(n+1).

**What "generable" actually means:**
- **43.44%** of token transitions are admissible under strict ±1 drift
- **57.73%** under extended ±3 drift
- **53.91%** with oracle per-line mask inference (upper bound for mask-based models)
- **45.91%** with a single global mask offset (=17), the best predictive rule

The earlier claim of "97.6% of the full corpus" was overstated. The model captures **roughly half** of sequential transitions under its best configuration, not nearly all of them. What makes this significant is not the raw percentage but the **statistical certainty**: holdout generalization at z = 16.2σ, cross-transcription independence at z > 86, and 202 verified mechanical slips at z = 9.47σ. No null model produces these signals.

This is still constructive generation under constraint — but the constraint system explains the **structure** of the corpus, not the **majority of individual transitions**.

## 2. The system is layered — confirmed by ablation

Multiple interacting constraint families are required. The path through incremental constraint addition:

| Layer | Admissibility | What it adds |
|:---|---:|:---|
| Random baseline (50 windows) | ~2% | Chance adjacency |
| Lexicon clamp (full vocab) | ~20% | Pre-reordering lattice structure |
| Spectral reordering | 43.44% | +23pp — sequential access optimization |
| Global mask offset | 45.91% | +2.5pp — single-parameter rotation |
| Oracle per-line mask | 53.91% | +8pp ceiling — line-level variation |

The jump from 20% to 43% via spectral reordering alone suggests real structural invariants — the vocabulary has genuine sequential organization that a physical ordering can recover.

## 3. The traversal is nondeterministic — confirmed

The constraint space is deterministic but the path through it branches freely. Evidence:
- **0% word-level overgeneration** (lexicon clamp: only real words are generable)
- **100% trigram overgeneration** (499,364 lattice-admissible trigrams vs 25,040 observed — the model permits ~20x more sequences than appear)
- **Within-window selection entropy** is 7.17 bits per choice (12,519 recorded choices). Bigram context reduces this to 4.74 bits, but substantial freedom remains.

The manuscript is one valid traversal. The constraint space admits many others.

## 4. The remaining gap is large and partially diagnosed

**~46% of tokens are not admissibly reached** even under oracle mask inference. The failure taxonomy from current artifacts:

| Category | Rate | Status |
|:---|---:|:---|
| Admissible (dist 0-1) | 43.44% | Explained by lattice |
| Extended drift (dist 2-3) | 14.29% | Consistent with wider physical tolerance |
| Mechanical slip (dist 4-10) | 30.42% | Consistent with tool misalignment or mask rotation |
| Extreme jump (>10) | 11.85% | Residual — possible missing constraint class |
| Not in palette | 5.07% | Hapax/near-hapax tokens outside vocabulary clamp |

The "wrong window" category (dist 2-10, about 42% of tokens) is the key frontier. Some fraction is likely mask rotation not yet captured by predictive rules; some may require an additional constraint family. The extreme jumps (11.85%, down from 47.25% pre-reordering) remain the hardest to explain.

**What we do NOT yet know:** whether the residual is noise, transcription artifacts, missing constraint classes, or a fundamental model limitation. The failure taxonomy exists but the **causal diagnosis** is incomplete.

## 5. Meaning is structurally bounded — not eliminated

The lattice constrains but does not saturate the available entropy:
- **Real corpus entropy:** 10.88 bits/token
- **Synthetic corpus entropy:** 12.23 bits/token
- **Mirror entropy fit:** 87.60% (synthetic is 12% more entropic than real)

Steganographic bandwidth analysis: **7.53 bits/word** of choice freedom within the lattice, yielding total capacity of **~11.5 KB (~23K Latin characters)** across the full corpus. This bounds but does not eliminate cipher capacity.

What you can say:
- High-density linguistic meaning (natural language) is structurally unlikely — the entropy profile is wrong
- Efficient cipher is structurally unlikely — the per-word bandwidth is low
- Rich semantic content is structurally unlikely — most "choice" is consumed by structural constraints

What you cannot say:
- Absolute absence of meaning — 7.53 bits/word is enough for a sparse code
- That the remaining ~46% unexplained transitions don't carry information

## 6. A physical machine is not required — unchanged

The "lattice" is an abstract constraint system. It could be implemented as:
- Overlays or rotating tables
- A sliding grille or tabula recta
- Rule tables (paper-based lookup)
- Purely cognitive procedural discipline
- Any combination

The physical grounding analysis found **81.50% grid layout efficiency** (transitions favor adjacent windows) but **null ergonomic correlation** (rho = -0.0003, p = 0.99). The layout is geometrically optimized for sequential access, but scribes did not select easier tokens preferentially. This is consistent with a physical tool but does not require one.

## 7. Multiple scribes do not break the model — strengthened

Three new lines of evidence:

- **Section-specific routing: null result.** Section-specific spectral reordering hurts global admissibility (-8.0pp). The scribe uses the same traversal pattern across all 7 sections. The 25.5pp section gap (Biological 53.2% vs Astro 27.7%) is driven by vocabulary distribution, not different tool configurations.
- **Hand mode offsets identical.** All three hand classifications (Hand 1, Hand 2, Unknown) share mode offset = 17.
- **Cross-transcription independence confirmed.** The ZL-trained lattice generalizes to 3 independent EVA transcriptions (VT, IT, RF) with admissibility ratios 1.09–1.15 and z-scores > 86. The lattice structure is transcription-independent.

## 8. What is not yet proven — updated with measurements

| Open question | Current state | What would close it |
|:---|:---|:---|
| **Minimality of 50 windows** | Minimality sweep exists (2→500 windows). MDL-optimal point not yet identified. At 50 windows: 5.64 BPT ablation. | Formal MDL elbow analysis |
| **Overgeneration rate** | 0% word-level (trivial: lexicon clamp). 100% trigram level (20x overgeneration). | Bounded trigram/n-gram overgeneration at higher orders |
| **Branching factor** | Within-window selection: 7.17 bits (unrestricted), 4.74 bits (bigram-conditioned). | Formal branching factor per position |
| **Description length efficiency** | Corrected Lattice BPT: 12.37. Copy-Reset: 10.90. Gap: 1.47 BPT. | Lattice BPT at or below Copy-Reset, or formal argument for why model cost is justified by explanatory power |
| **Full failure taxonomy** | 4 categories measured (Section 4 above). Causal attribution incomplete. | Distinguish mask rotation, transcription error, missing constraint, and true noise within the 46% residual |
| **Holdout robustness** | Single split tested (Herbal→Biological, z=16.2σ). | Multiple holdout splits, cross-validation |

These determine whether you have **a** strong generative model or **the** strong generative model.

## 9. What this does not tell you — unchanged but sharpened

- **Author intent:** The model is agnostic. A medical reference, a philosophical exercise, a hoax, and a devotional artifact could all produce this structure.
- **Hoax vs. intellectual artifact:** The constraint system is equally consistent with deliberate deception and with a sincere production ritual.
- **Physical implementation:** The lattice abstraction does not specify hardware.
- **Absolute absence of meaning:** 7.53 bits/word is enough for sparse encoding. The model bounds capacity but cannot prove emptiness.
- **Whether the residual matters:** 46% of transitions are unexplained. If the residual is structured, it could contain information the model doesn't capture.

## 10. Where you stand

You are past descriptive statistics and firmly in constructive modeling territory.

**What has changed since this morning:**
- The "97.6%" claim has been corrected to ~43-54% depending on configuration. The significance comes from statistical certainty (z > 16σ holdout), not from high raw coverage.
- Cross-transcription independence is now proven (3 sources, z > 86).
- Within-window selection is diagnosed: bigram context is the dominant driver (2.43 bits), not physical effort.
- Section-specific variation is explained by vocabulary distribution, not tool reconfiguration.
- MDL gap with Copy-Reset has narrowed from 4.83 to 1.47 BPT after correcting double-counting.

**What has NOT changed:**
- You have not proven necessity or minimality.
- The failure residual (~46%) is measured but not causally diagnosed.
- Copy-Reset still wins on MDL parsimony (10.90 vs 12.37 BPT), though it fails on holdout generalization (3.71% vs 10.81%).

**The honest framing:** You have a constraint system that captures statistically significant, cross-transcription-independent, section-invariant sequential structure in the Voynich Manuscript. It explains roughly half of token transitions and bounds the remaining semantic capacity. It does not explain the other half, and it is not yet the most parsimonious model on description length.
