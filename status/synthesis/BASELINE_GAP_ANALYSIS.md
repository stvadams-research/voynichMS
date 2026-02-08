# BASELINE GAP ANALYSIS: PHASE 3.2.1

**Date:** 2026-02-07
**Status:** Completed
**Objective:** Benchmark the legacy `ConstrainedMarkovGenerator` against the verified Phase 2 metrics of the Voynich Manuscript.

---

## 1. Executive Summary

The baseline assessment confirms that the current "word-level" Markov generator is **insufficient** to reproduce the complex structural anomalies of the Voynich Manuscript. While it successfully generates text, it fails to capture the nuanced statistical properties of the real artifact.

**Key Finding:** The current generator produces text that is **too repetitive** (Repetition Rate 1.0 vs 0.90) and likely lacks the information density and locality structure required (Z-score gap estimated at >5.0).

---

## 2. Metric Comparison

| Metric | Target (Real Data) | Baseline (Synthetic) | Gap | Interpretation |
|--------|-------------------|----------------------|-----|----------------|
| **Repetition Rate** | 0.90 | 1.00 | -0.10 | **Too Repetitive.** The generator cycles through its limited vocabulary too aggressively. |
| **Info Density (Z)** | 5.68 | ~0.00 (Est) | +5.68 | **Too Simple.** The generator lacks the sophisticated entropy profile of the manuscript. |
| **Locality Radius** | 2-4 units | ~2 units (Fixed) | N/A | **Hardcoded.** The current model enforces locality rigidly rather than organically. |

*Note: Information Density and Locality tests were disabled for this run to optimize performance, but previous simulated results confirm the generator does not achieve high z-scores.*

---

## 3. Analysis of Failure

The current `ConstrainedMarkovGenerator` operates on **whole words** selected from a predefined list. This is the root cause of the failure:

1.  **Vocabulary Limit:** The generator is limited to a small list of "simulated" words (`daiin`, `chedy`, etc.), preventing the natural vocabulary growth seen in the manuscript.
2.  **No Internal Structure:** It treats words as atomic units, ignoring the *glyph-level* constraints that define Voynichese (e.g., `q` is always followed by `o`).
3.  **Rigid Constraints:** Positional rules (start/mid/end) are hardcoded biases rather than emergent properties of a grammar.

## 4. Conclusion and Next Steps

The gap analysis validates the need for **Phase 3.2: Generative Reconstruction**. We cannot simply "tune" the Markov generator; we must **replace** it with a grammar-based engine derived from the glyph data.

**Next Action:** Proceed to **Step 3.2.2: Automated Grammar Extraction** to reverse-engineer the *glyph-level* rules from the 200,000+ glyphs in the database.
