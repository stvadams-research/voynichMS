# PHASE 4.5: METHOD-TO-CONDITION MAPPING

**Objective:** Document the specific failures of Phase 4 inference methods to satisfy the necessary conditions for semantic evidence.

---

## 1. Admissibility Matrix

| Method | C1: Irreducible | C2: Stable | C3: Latent-State | C4: Separable | Status |
|--------|:---:|:---:|:---:|:---:|--------|
| **A: Info Clustering** | FAIL | FAIL | FAIL | FAIL | **NOT DIAGNOSTIC** |
| **B: Network Metrics** | FAIL | PASS | FAIL | FAIL | **NOT DIAGNOSTIC** |
| **C: Topic Alignment** | FAIL | FAIL | FAIL | FAIL | **NOT DIAGNOSTIC** |
| **D: AI Lang-ID** | PASS | FAIL | FAIL | FAIL | **NOT DIAGNOSTIC** |
| **E: Morph Induction** | FAIL | PASS | FAIL | PASS | **NOT DIAGNOSTIC** |

---

## 2. Detailed Failure Analysis

### 4.1 Method A: Information Clustering
- **Failure:** Fully reproduced by `Self-Citation` and `Mechanical Reuse` (C1).
- **Insight:** Clustering measures token reuse frequency, not topical coherence. Bounded pools produce stronger "keywords" than natural language.

### 4.2 Method B: Network Features (Clustering/Assortativity)
- **Failure:** Exceeded by `Mechanical Reuse` model (C1).
- **Insight:** High network clustering is a trivial result of frequent local token reuse. It does not imply semantic adjacency.

### 4.3 Method C: Topic Modeling
- **Failure:** Highly sensitive to arbitrary partitioning (C2). Topics align with non-semantic frequency shifts in gibberish (C3).
- **Insight:** LDA identifies "distributional consistency," which is a hallmark of the Voynich generator but not unique to language.

### 4.4 Method D: Flexible AI Decipherment
- **Failure:** Null corpora yield equivalent matches under search flexibility (C4).
- **Insight:** "High-confidence" language matches are artifacts of the large search space (multiple comparisons), not evidence of underlying plaintext.

### 4.5 Method E: Unsupervised Morphology Induction
- **Failure:** Trivially produced by suffix tables (C1). Reflects the rules of the generator, not the intent of a scribe (C3).
- **Insight:** Morphology induction identifies the "Slot-Logic" of the algorithm, confirming it is structured, but not that it is meaningful.

---

## 3. Conclusion

All Phase 4 methods fail the **Latent-State Dependence (C3)** condition. They measure structural regularities that are purely mechanical in origin. Therefore, none of these methods can be used to support an inference of language or meaning in the Voynich Manuscript.

---
**Status:** Mapping Complete.  
**Next:** Formal Closure Statement.
