# PHASE 4 METHOD MAP: INFERENCE ADMISSIBILITY

This document pre-registers the phase4_inference methods to be evaluated in Phase 4. Each method includes its core claim, implementation goal, and the "Decision Rule" for determining if it is semantics-diagnostic.

---

## 4.1 Method A: Information Clustering (Montemurro & Zanette)
**Claim:** Topical/semantic structure is revealed by the non-uniform distribution of "keyword" tokens across sections.
**Metric:** Kullback-Leibler (KL) divergence or Information per token about section identity.

### Test Plan
- **Baseline:** Run on `voynich_real`. Replicate the "keyword" list and information curves.
- **Specificity:** Run on `latin_classic`. Should show strong clustering.
- **False Positive:** Run on `self_citation` and `mechanical_reuse`.
- **Outcome Rule:**
  - **NOT DIAGNOSTIC:** If non-semantic structured corpora produce similar info-peaks and stable "keywords".
  - **POTENTIALLY DIAGNOSTIC:** If `voynich_real` and `latin_classic` are significantly clustered while `mechanical_reuse` is not.

---

## 4.2 Method B: Network Language-Likeness (Amancio et al.)
**Claim:** Natural language possesses unique network topology (clustering, assortativity, degree distribution) distinct from random text.
**Metric:** Word Adjacency Network (WAN) metrics.

### Test Plan
- **Baseline:** Compute WAN features for `voynich_real`.
- **False Positive:** Compare feature vectors of `voynich_real` against `voynich_synthetic_grammar`.
- **Outcome Rule:**
  - **NOT DIAGNOSTIC:** If non-semantic structured models fall within the "Natural Language" cluster in feature space.
  - **ADMISSIBLE:** If `voynich_real` is closer to non-semantic generators than to semantic baselines.

---

## 4.3 Method C: Topic-Section Alignment
**Claim:** LDA Topic models align with illustrated manuscript sections, implying semantic coherence.
**Metric:** Jaccard similarity or Topic Coherence scores.

### Test Plan
- **Baseline:** Run LDA on `voynich_real`.
- **False Positive:** Run LDA on `mechanical_reuse` with *artificial* sections (arbitrarily assigned).
- **Outcome Rule:**
  - **NOT DIAGNOSTIC:** If topic models align with any stable frequency shift, even if non-semantic.

---

## 4.4 Method D: Flexible AI Decipherment
**Claim:** Under flexible transformations (e.g. anagramming, vowel deletion), Voynich matches a specific known language.
**Metric:** Language identification confidence scores.

### Test Plan
- **False Positive:** Run the same "best match" pipeline on `shuffled_global`.
- **Outcome Rule:**
  - **NOT DIAGNOSTIC:** If "high-confidence" matches are frequently found for nonsense data under flexible transforms.

---

## 4.5 Method E: Unsupervised Morphology Induction
**Claim:** Identification of stable affixes (prefixes/suffixes) proves morphological syntax.
**Metric:** Morphological consistency score.

### Test Plan
- **False Positive:** Run induction on a generator that uses a random prefix-suffix table (e.g. `table_grille`).
- **Outcome Rule:**
  - **NOT DIAGNOSTIC:** If induction identifies "convincing" affixes in purely mechanical generators.

---

This document is a pre-registration/planning artifact. Canonical post-evaluation method status is tracked in:

- `results/reports/phase4_inference/PHASE_4_STATUS_INDEX.json`
