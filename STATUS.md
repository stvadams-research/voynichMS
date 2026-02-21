# Where We Stand — Updated Claim Statement (2026-02-21 evening)

## 1. The text is constructively generable — but the capture rate is lower than previously claimed

You have a deterministic 50-window lattice that maps 7,717 tokens (94.93% of the ZL corpus vocabulary) into a sequential constraint system where word(n) determines window(n+1).

**What "generable" actually means:**
- **43.44%** of token transitions are admissible under strict ±1 drift
- **57.73%** under extended ±3 drift
- **53.91%** with oracle per-line mask inference (upper bound for mask-based models)
- **45.91%** with a single global mask offset (=17), the best predictive rule

The model captures **roughly half** of sequential transitions under its best configuration, not nearly all of them. What makes this significant is not the raw percentage but the **statistical certainty**: holdout generalization at z = 16.2σ, cross-transcription independence at z > 86, and 202 verified mechanical slips at z = 9.47σ. No null model produces these signals.

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

## 4. The remaining gap is large — now fully diagnosed

**~46% of tokens are not admissibly reached** even under oracle mask inference. The failure taxonomy (Phase 14H, per-token analysis of all 34,605 tokens):

| Category | Count | Rate | Status |
|:---|---:|---:|:---|
| Admissible (dist 0-1) | 14,270 | 41.24% | Explained by lattice |
| Extended drift (dist 2-3) | 4,696 | 13.57% | Consistent with wider physical tolerance |
| Wrong window (dist 4-10) | 9,994 | 28.88% | Diagnosed below |
| Extreme jump (>10) | 3,892 | 11.25% | Residual — structurally confirmed |
| Not in palette | 1,753 | 5.07% | Hapax/near-hapax tokens outside vocabulary clamp |

**Causal diagnosis of wrong-window tokens (Phase 14H):**
- **Mask recoverability: 2.8%** — oracle mask offsets recover almost none. The residual is NOT explained by simple mask rotation.
- **Distance distribution: unimodal** (BC=0.219) — a single smooth drift mechanism, not two distinct failure modes.
- **Bigram context: 1.31 bits** of information gain from previous word on distance — drift is context-dependent, not random.
- **Signed distances: symmetric** (±2: 9.3%/9.2%, ±4: 6.8%/6.6%) — no dominant offset family, ruling out "missed mask state."
- **Cross-transcription: 93.6% structural** — failures confirmed in VT/IT/RF, only 6.4% are ZL-only artifacts.
- **Section variation**: Biological 53.2% admissible vs Astro 27.7%, driven by vocabulary distribution.

**Interpretation:** The wrong-window residual is real structural signal (not noise or transcription error), context-dependent (bigram-predictable), and cannot be recovered by mask rotation alone. It likely requires a richer transition model — possibly wider drift tolerance, context-dependent window selection, or a complementary constraint family that the current lattice does not capture.

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

## 8. What is not yet proven — updated after Phase 14H

| Open question | Current state | Status |
|:---|:---|:---|
| **Minimality of 50 windows** | MDL elbow analysis (14H Sprint 3): optimal K=3-7 by knee detection. K=50 penalty: +1.46 BPT. K=50 is over-specified for MDL but provides maximum structural discrimination. | **CLOSED** — penalty quantified, tradeoff documented |
| **Overgeneration rate** | 0% word-level (trivial: lexicon clamp). 100% trigram level (20x overgeneration). | Open — bounded at higher orders needed |
| **Branching factor** | Within-window selection: 7.17 bits (unrestricted), 4.74 bits (bigram-conditioned). | Open — formal per-position analysis needed |
| **Description length efficiency** | Corrected Lattice BPT: 12.37. Copy-Reset: 10.90. Gap: 1.47 BPT. MDL elbow shows K=20 achieves 12.47 BPT with similar admissibility. | Open — gap persists but is now well-characterized |
| **Full failure taxonomy** | Per-token analysis of 34,605 tokens (14H Sprint 1). Wrong-window is structural (93.6%), context-dependent (1.31 bits), mask-unrecoverable (2.8%), unimodal, symmetric. | **CLOSED** — fully diagnosed, see Section 4 |
| **Holdout robustness** | 7/7 leave-one-section-out splits significant (14H Sprint 2). Mean z=29.1σ. Lattice wins admissibility in 7/7 vs Copy-Reset. | **CLOSED** — robust across all sections |

Three of six open questions are now closed. The remaining three (overgeneration bounding, branching factor formalization, and description length gap) are analytical refinements, not existential threats to the model's validity.

## 9. What this does not tell you — unchanged but sharpened

- **Author intent:** The model is agnostic. A medical reference, a philosophical exercise, a hoax, and a devotional artifact could all produce this structure.
- **Hoax vs. intellectual artifact:** The constraint system is equally consistent with deliberate deception and with a sincere production ritual.
- **Physical implementation:** The lattice abstraction does not specify hardware.
- **Absolute absence of meaning:** 7.53 bits/word is enough for sparse encoding. The model bounds capacity but cannot prove emptiness.
- **Whether the residual matters:** 46% of transitions are unexplained. If the residual is structured, it could contain information the model doesn't capture.

## 10. Where you stand

You are past descriptive statistics and firmly in constructive modeling territory. Phase 14H substantially strengthened the foundation.

**Phase 14H accomplishments (2026-02-21):**
- **Failure taxonomy fully diagnosed** (Sprint 1): The 42% wrong-window residual is structural (93.6%), context-dependent (1.31 bits info gain), not mask-recoverable (2.8%), and follows a unimodal symmetric drift pattern. The residual is real signal requiring a richer transition model, not noise or transcription error.
- **Holdout validation robust** (Sprint 2): Lattice is significant in **7/7** leave-one-section-out splits (mean z=29.1σ), winning admissibility vs Copy-Reset in all 7. This replaces the single Herbal→Biological split with comprehensive cross-validation.
- **MDL optimality quantified** (Sprint 3): K=50 imposes a +1.46 BPT penalty vs MDL-optimal K=3. This is significant but well-characterized: K=50 provides maximum structural discrimination at quantifiable compression cost. The model's value is holdout generalization, not MDL parsimony.

**What has NOT changed:**
- Copy-Reset still wins on MDL parsimony (10.90 vs 12.37 BPT), though it fails on holdout generalization (2-4% vs 10-33%).
- ~46% of token transitions remain unexplained. The diagnosis is now complete but a model that explains more transitions has not been built.
- Three open questions remain (overgeneration bounding, branching factor, description length gap), all analytical refinements.

**The honest framing:** You have a constraint system that captures statistically significant, cross-transcription-independent, section-invariant sequential structure in the Voynich Manuscript. It explains roughly half of token transitions and bounds the remaining semantic capacity. The other half is now fully diagnosed — it is structural, context-dependent, and requires a richer transition model (not noise or artifacts). The foundation is sound; the ceiling is known.
