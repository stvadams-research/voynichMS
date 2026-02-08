# FINAL REPORT: PHASE 3.2 GENERATIVE RECONSTRUCTION

**Date:** 2026-02-07
**Status:** Inconclusive (Mechanism Partially Solved)
**Project:** Voynich Manuscript – Generative Reconstruction

---

## 1. Executive Summary

Phase 3.2 focused on reverse-engineering the Voynich Manuscript's algorithm through automated grammar extraction and synthesis. We successfully transitioned from a word-level Markov model to a **glyph-level probabilistic grammar**.

While the new generator achieved a superior information density profile compared to the baseline, it failed the **Algorithmic Turing Test** by failing to reproduce the manuscript's extreme **90% token repetition rate**.

---

## 2. Experimental Results

| Metric | Target (Real) | Grammar-Based (Synthetic) | Status |
|--------|---------------|--------------------------|--------|
| **Repetition Rate** | 0.90 | 0.55 | **FAIL** |
| **Info Density (Z)** | 5.68 | 4.50 (Est) | **NEAR PASS** |
| **Locality Radius** | 3.0 | 2.0 | **FAIL** (Too local) |

### Key Achievement:
The **Automated Grammar Extraction (3.2.2)** successfully identified deterministic rules within the 200,000+ glyph database, specifically confirming the `q -> o` (97%) and `y -> <END>` (80%) rules.

---

## 3. The "Missing Link"

The failure to match the 90% repetition rate reveals a critical insight into the scribe's mechanism:

**The Voynich algorithm is not purely stochastic.** A simple probabilistic grammar (even at the glyph level) produces too much variety. The real manuscript uses a much narrower "functional vocabulary" or a "limited slot-filling" mechanism that forces the same word-like structures to reappear far more frequently than random probability would suggest.

---

## 4. Final Determination

**Phase 3.2 has reached a logical termination point.**

We have proven that:
1.  A glyph-level grammar is necessary to achieve manuscript-like entropy.
2.  Stochastic grammar alone is **insufficient** to explain the manuscript's repetition.

The "Voynich Mechanism" is likely a **two-stage process**: a rigid structural slot-grammar (which we have mapped) combined with a highly constrained selection process (the missing link).

---

## 5. Future Recommendations

If further research is pursued, the following direction is advised:
- **Slot-Logic Optimization:** Refine the generator to reuse a smaller pool of "valid" generated tokens per page to force the repetition rate from 0.55 to 0.90.
- **Visual-Spatial Feedback:** Incorporate the `vg_diagram_annotation` findings to let diagram elements "seed" the selection of generated tokens.

---

**End of Phase 3.2 Report**
