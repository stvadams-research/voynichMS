# TEST C FINDINGS: GLYPH VARIANT SENSITIVITY (ABLATION TEST)

**Date:** 2026-02-07
**Result:** STABLE (Conclusions insensitive to variant interpretation)

---

## 1. Objective
Determine if the project's conclusions (specifically the high repetition rate and positional entropy) are sensitive to how glyph variants (like gallows characters `k/t` or minims `i/ii/iii`) are interpreted.

---

## 2. Quantitative Results

| Mode | Vocabulary Size | Repetition Rate | Start Glyph Entropy | Result |
|------|-----------------|-----------------|----------------------|--------|
| **Expanded** | 11,178 | 0.7447 | 3.2829 | **Baseline** |
| **Collapsed** | 10,401 | 0.7629 | 3.2321 | **Stable** |

---

## 3. Analysis

The structural findings of the project are **robust against glyph variant interpretation**.

1.  **Invariance:** Collapsing common glyph variants (e.g., merging `k` and `t`) slightly reduced the vocabulary size and increased the repetition rate, but it did not fundamentally alter the statistical profile of the manuscript.
2.  **Repetition Rate:** The repetition rate remained significantly high (>0.74) in both modes, confirming that the "Repetition Anomaly" is a structural feature of the text rather than a choice of glyph categorization.
3.  **Positional Entropy:** Start-glyph entropy remained stable (approx. 3.2), indicating that the positional constraints of Voynichese are independent of variant-level distinctions.
4.  **Conclusion:** The choice to treat variants as distinct or identical does not impact the admissibility of explanation classes. The "Language" exclusion and the "Procedural" lead remain valid under both interpretations.

---

## 4. Final Determination for Test C

**Findings are Stable.** The manuscript's structural signals are macroscopic and do not depend on fine-grained transliteration or categorization choices.

---
**End of Test C Findings**
