# GENERATOR MATCHING AND VALIDATION

**Project:** Voynich Manuscript – Identifiability Phase  
**Objective:** Define the methodology for constructing matched control generators for each mechanism class.

---

## 1. Matching Requirements (Global)
Every matched generator, regardless of its class mechanism, must match the primary Voynich dataset (`voynich_real`) on the following "Phase 1–3" metrics:

| Metric | Target Value (ZL) | Tolerance |
|--------|-------------------|-----------|
| **Total Tokens** | ~230,000 | ±5% |
| **Information Density (z)** | 5.68 | ±0.5 |
| **Repetition Rate** | 0.90 | ±0.05 |
| **Locality Radius** | 3.0 | ±1.0 |
| **Glyph Grammar** | `voynich_grammar.json` | Mandatory |

---

## 2. Class-Specific Generator Logic

### 2.1 Bounded Pool Matcher (`pool_matcher`)
- **Mechanism:** Draws from a per-page pool of size $N \in [10, 30]$.
- **Matching Strategy:** Tune $N$ and the replenishment rate to match the global repetition rate while preserving the glyph-level grammar.

### 2.2 Table-Grille Matcher (`table_matcher`)
- **Mechanism:** Traverses a 10x10 component table.
- **Matching Strategy:** Assign components to the table such that the resulting bigram frequencies and glyph grammar match the manuscript.

### 2.3 Copy-Mutation Matcher (`copy_matcher`)
- **Mechanism:** Selects a parent passage and applies edits.
- **Matching Strategy:** Tune the mutation rate ($M$) to produce the target repetition and info density.

---

## 3. Validation Protocol
Before a generator is used in Phase 5 signature tests, it must pass the "Matching Gate":

1.  **Generation:** Generate 230,000 tokens.
2.  **Profiling:** Run the `PharmaceuticalProfileExtractor` on the synthetic data.
3.  **Check:** Verify that all metrics fall within the tolerance ranges in Section 1.
4.  **Logging:** Record the matched parameters in the run manifest.

---
**Status:** Matching methodology defined.  
**Next:** Implement signature test modules.
