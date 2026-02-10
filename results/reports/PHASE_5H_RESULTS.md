# PHASE 5H RESULTS: EVIDENCE COUPLING PILOT

**Date:** 2026-02-07
**Status:** Pilot Complete (Section Integrity Supported; Illustration Coupling Inconclusive)
**Objective:** Determine if the production mechanism is coupled to physical manuscript features (sections and illustrations).

---

## 1. Sectional Stability Analysis

We mapped the **Latent Dimensionality** and **Successor Consistency** across all major codicological sections.

| Section | Token Count | Effective Rank (Dim) | Successor Consistency |
|---------|-------------|----------------------|-----------------------|
| **Herbal** | 72,037 | 80 | 0.8480 |
| **Biological** | 47,063 | 78 | 0.8039 |
| **Astronomical** | 3,331 | 85 | 0.9158 |
| **Pharmaceutical** | 11,095 | 83 | 0.8897 |
| **Stars** | 63,534 | 81 | 0.8730 |

### Key Finding: The Global Machine
The structural signatures are **remarkably uniform** across the entire manuscript. 
- The effective rank (dimensionality) remains constant at **~80**.
- Successor consistency remains high (**>0.80**) in every section.
- **Conclusion:** Section-level evidence supports traversal of a **single global deterministic structure**. No section-specific algorithm is required by these measurements.

---

## 2. Illustration Coupling

Using `AnchorRecord` data to isolate text in close proximity to illustrations:

| Token Group | Successor Consistency | Sample Size (Bigrams) |
|-------------|-----------------------|-----------------------|
| **Anchored (Proximity)** | 0.4263 | 1681 |
| **Unanchored (Block)** | [Insufficient Data] | 2 |

*Note: Due to high anchor density, the unanchored cohort is effectively unusable in this pilot. This phase does not support a conclusive illustration-coupling claim without refined geometry and confirmatory adequacy checks.*

---

## 3. Final Determination for Phase 5H

**Hypothesis: Global Machine is SUPPORTED (Sectional Test Only).**  
The manuscript is not a collection of different section-specific systems under this pilot. Section-level variation is explained by entry points and traversal paths, not different production rules.

**Illustration-Coupling Status:** `INCONCLUSIVE_UNDERPOWERED` (confirmatory artifact current state).  
Any claim about no image/layout coupling is deferred to confirmatory analysis artifacts.

---
**Conclusion:** Phase 5H supports mechanism integrity at section level, but does not conclusively resolve illustration coupling.
