# Phase 10 Methods Summary

Six adversarial stress-tests of the Phase 5 mechanism identification (Implicit
Constraint Lattice). Each method targets a specific gap in Phases 1-9 with a
pre-registered defeat condition.

**Aggregate Status:** `in_tension` — 2 strengthened, 2 weakened, 2 indeterminate.

---

## Method Overview

| Method | Name | Target Gap | Outcome |
|---|---|---|---|
| **F** | Reverse Mechanism | Could the lattice also be a cipher? | indeterminate |
| **G** | Text-Illustration Correlation | Does text relate to adjacent images? | indeterminate |
| **H** | Writing System Typology | Does Voynich match a known script type? | **strengthened** |
| **I** | Cross-Linguistic Positioning | Is Voynich closer to languages or generators? | **strengthened** |
| **J** | Steganographic Extraction | Do positional subsequences hide structure? | **weakened** |
| **K** | Residual Gap Anatomy | Are generator gaps random or systematic? | **weakened** |

---

## Method F: Reverse Mechanism

**Question:** Can any of the identified generative mechanisms (table-grille,
slot-logic, constrained-Markov) also function as a decoder that extracts
structured plaintext from the Voynich token sequence?

**Design:** Sample 10,000 reverse parameterizations per generator family. Decode
the Voynich sequence through each. Measure decoded entropy against a null
distribution (1,000 block-bootstrap permutations). Flag candidates with entropy
below the null 1st percentile, test stability (≥70% perturbation pass rate), and
check naturalness (Zipf-alpha, bigram MI).

**Defeat condition:** Any stable-natural decoder exists.

**Result:** 294 low-entropy outliers found across 3 families, but **zero** passed
both stability and naturalness gates. Top candidates failed perturbation tests
(pass rate 0.0) and lacked language-like frequency distributions.

**Scripts:** `run_stage3_f.py` → `stage3_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_f_reverse_mechanism.json`

---

## Method G: Text-Illustration Correlation

**Question:** Does text on each folio correlate with that folio's specific
illustrations beyond what section-level frequency shifts would predict?

**Design:** Extract 37 visual features per folio (grayscale/HSV statistics, edge
density, ink ratio, component metrics). Compute TF-IDF text vectors. Run Mantel
test (1,000 permutations) on visual vs. text distance matrices. Remove section
effects by demeaning within sections and recomputing residual correlation.

**Defeat condition:** Full Mantel r > 0, p < 0.01 AND residual r > 0, p < 0.01.

**Result:** Full dataset Mantel r = 0.221 (p < 0.001) — expected from section-level
clustering. Residual correlation after section demeaning: r ≈ −0.0003 (p = 1.0).
**No folio-level text-image coupling detected.**

**Scripts:** `run_stage2_gi.py` → `stage2_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_g_text_illustration.json`

---

## Method H: Writing System Typology

**Question:** Does the Voynich glyph inventory and word-length distribution match
a known writing system type (alphabet, syllabary, abugida, abjad, logographic)?

**Design:** Compute 4 features (glyph count, mean word length, TTR, combinatorial
productivity). Measure weighted Euclidean distance to 5 typology prototypes.
Check whether any generator family shares Voynich's nearest typology.

**Defeat condition:** Voynich's nearest typology has no generators assigned AND
Voynich is not excluded from that typology's property range.

**Result:** Voynich nearest to alphabet type (distance 0.665). Excluded from 4 of
5 typologies. **Six generator families share the alphabet typology** (Latin classic,
mechanical reuse, shuffled global, line-reset variants). The typological signal
is fully explained by the generative framework.

**Scripts:** `run_stage1_hjk.py` → `stage1_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_h_typology.json`

---

## Method I: Cross-Linguistic Positioning

**Question:** Is Voynich statistically closer to a diverse set of natural
languages or to the generator cloud?

**Design:** Compute 11-feature vectors for Voynich, 13 languages (5+ typology
classes), and 4 generator families. Z-score normalize. Measure Euclidean distance
from Voynich to language centroid vs. generator centroid. Bootstrap 500 iterations
for confidence intervals.

**Defeat condition:** dist_to_language < dist_to_generator AND bootstrap
confidence ≥ 0.95.

**Result:** Distance to language centroid: 5.47. Distance to generator centroid:
3.36. Margin: −2.11 (Voynich is 63% closer to generators). Bootstrap confidence
that generator is closer: 0.95. **Voynich's statistical profile is better
explained by generative mechanics than by any natural language.**

**Scripts:** `run_stage2_gi.py` → `stage2_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_i_cross_linguistic.json`

---

## Method J: Steganographic Extraction

**Question:** Do extractable positional subsequences (line-initial, nth-token,
paragraph-initial) contain anomalous structure not present in generated
equivalents?

**Design:** Define 9 extraction rules. Compute entropy, compression, TTR, and
bigram MI for each. Calibrate against 100 null runs from line-reset generators.
Flag anomalies at |z| ≥ 3.0. Test stability via 12 bootstrap resamples and 12
line-permutations (≥80% pass rate). Distinguish edge rules (line/paragraph
initial) from non-edge rules (nth-token, slot-position).

**Defeat condition:** At least one non-edge stable anomaly survives
folio-order permutation.

**Result:** Multiple stable non-edge anomalies detected. Paragraph-initial
entropy z = 43.25 (bootstrap/permutation pass = 100%). nth-token-5 entropy
z = 36.3 (stable). Consistent across seeds 42, 77, 101. **Positional
subsequences contain structure beyond what generators produce.**

**Scripts:** `run_stage1_hjk.py`, `run_stage1b_jk_replication.py` → `stage1_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_j_steganographic.json`

---

## Method K: Residual Gap Anatomy

**Question:** Are the features where Voynich deviates from the best generator
random noise, or are they correlated, language-ward, and hard to close?

**Design:** Generate 100 samples from the best-fit generator (line_reset_markov).
Compute 11-feature vectors. Flag outlier features (|z| ≥ 2.0). Measure
inter-outlier correlation. For each outlier, test direction (closer to Latin?)
and modification difficulty (trivial/moderate/hard).

**Defeat condition:** ≥2 outliers AND mean |correlation| ≥ 0.4 AND ≥2 toward
language AND ≥2 hard-to-close, across ≥75% of seeds.

**Result:** All 11 features flagged as outliers. Mean inter-correlation: 0.460
(above 0.4 threshold). 5 features trend toward language. All 11 classified as
hard-framework-shift. Seed-band adjudication: 7/8 seeds pass (87.5% > 75%).
**The generator gap is systematic, language-ward, and structurally resistant
to parameter adjustment.**

**Scripts:** `run_stage1_hjk.py`, `run_stage5b_k_adjudication.py` → `stage1_pipeline.py`
**Output:** `results/data/phase10_admissibility/method_k_residual_gap.json`,
`stage5b_k_adjudication_summary.json`

---

## Implications

Methods H and I confirm that Voynich's macro-statistical profile is well-explained
by the generative lattice. Methods J and K identify micro-structural anomalies
that the lattice does not yet account for — specifically, positional subsequence
structure and systematic feature deviations toward natural language.

The overall status is `in_tension`: the mechanism identification holds at the
macro level but faces unresolved challenges at the feature level.
