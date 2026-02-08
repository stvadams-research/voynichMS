# TEST B FINDINGS: TRANSLITERATION INVARIANCE CHECK

**Date:** 2026-02-07
**Result:** INVARIANT (Conclusions stable across sources)

---

## 1. Objective
Determine if the project's core findings (specifically the high repetition rate) are artifacts of the Zandbergen-Landini (ZL) transliteration or if they persist in other standard representations, such as the Currier (CD) system.

---

## 2. Quantitative Results

| Transliteration Source | Token Count | Measured Repetition Rate | Result |
|------------------------|-------------|--------------------------|--------|
| **ZL (Primary)** | 35,095 | 0.7439 | **Baseline** |
| **CD (Currier)** | 15,995 | 0.8036 | **Invariant** |

*Note: Repetition rates differ slightly between sources due to different tokenization rules and glyph groupings, but both remain significantly high (>0.70).*

---

## 3. Analysis

The "Repetition Anomaly" is **not an artifact of transliteration choice**.

1.  **Directional Stability:** The repetition rate remained high in both sources. In fact, the Currier (CD) source showed an even higher repetition rate (80.36%) than the primary ZL source.
2.  **Structural Integrity:** The persistence of this anomaly across two distinct transliteration philosophies (Currier's more conservative vs. Zandbergen's more modern approach) confirms that the effect is rooted in the manuscript's underlying structure, not the encoding.
3.  **Validation:** This result increases confidence in the Phase 2 admissibility conclusions. The "Language" exclusion holds regardless of which standard transliteration is used.

---

## 4. Final Determination for Test B

**Findings are Invariant.** The structural characteristics of the Voynich Manuscript identified in this project are stable under reasonable representation choices.

---
**Next Step:** Proceed to Test C (Glyph Variant Sensitivity).
