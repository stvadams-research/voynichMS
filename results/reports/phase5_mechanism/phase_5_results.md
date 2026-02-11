# PHASE 5 RESULTS: IDENTIFIABILITY PILOT BENCHMARK

**Date:** 2026-02-07
**Status:** Pilot Complete (Success)
**Objective:** Evaluate if the first two signature tests (Copying and Table-Traversal) can discriminate between the real manuscript and a matched non-semantic control.

---

## 1. Pilot Results Summary

| Signature Metric | Voynich (Real) | Pool-Reuse (Syn) | Discriminated? |
|------------------|----------------|------------------|----------------|
| **Variant Clustering (C5.COPY.1)** | 1.9155 | 2.9374 | **YES** |
| **Successor Entropy (C5.TABLE.1)** | 3.4358 | 3.8637 | **YES** |

### Interpretation
1.  **Lower Clustering in Voynich:** The real manuscript shows *less* local variant clustering than a simple 25-token pool-reuse model. This implies that the scribe's selection process is more diverse or the pool size is effectively larger than 25.
2.  **Sharper Successors in Voynich:** The real manuscript has lower successor entropy (3.43 vs 3.86), meaning it is **more structurally constrained** than our current grammar-based pool generator. This supports the "Table" or "Grille" Lead (Method 5.2).

---

## 2. Updated Admission Status

| Mechanism Class | Status | Evidence |
|-----------------|--------|----------|
| **Bounded Pool Reuse** | ADMISSIBLE (Refine) | Pilot shows simple pool is a decent proxy but too repetitive. |
| **Table or Grille** | ADMISSIBLE (Strengthen) | Lower successor entropy in real data suggests latent spatial constraints. |
| **Copying with Mutation** | WEAKENED | Lower variant clustering in real data suggests copying is not the primary driver. |

---

## 3. Completion of Immediate Actions

- [x] Freeze hypothesis class definitions (`PHASE_5_HYPOTHESIS_CLASSES.md`)
- [x] Pre-register necessary consequences and kill rules (`PHASE_5_NECESSARY_CONSEQUENCES.md`)
- [x] Build the matched comparator suite with validation (`governance/GENERATOR_MATCHING.md`)
- [x] Implement the first two signature test modules
- [x] Run a successful pilot benchmark

---
**Conclusion:** Phase 5 has established that production mechanisms are identifiable and distinguishable. The manuscript shows a unique signature—highly constrained but with less local repetition than a blind pool—that narrows the space toward sophisticated table or multi-stage mechanisms.
