# PHASE 5F ENTRY MECHANISM CLASSES: PATH INSTANTIATION MODELS

**Project:** Voynich Manuscript – Entry-Point Identifiability  
**Objective:** Define the phase5_mechanism families for selecting per-line starting points in a large deterministic structure.

---

## 1. Uniform Independent Entry
- **Definition:** Entry points (start nodes) are sampled uniformly at random from the set of all nodes in the large object.
- **Selection Rule:** $P(Start_i) = 1/N_{nodes}$.
- **What it explains:** Global coverage, lack of obvious long-range sequence persistence.
- **Key Vulnerability:** Fails if the manuscript shows local clustering of vocabulary or path types.

## 2. Locally Coupled Entry
- **Definition:** The entry point for line $N+1$ is biased by the entry point of line $N$.
- **Selection Rule:** $P(Start_{i+1} | Start_i) \propto K(dist(Start_{i+1}, Start_i))$.
- **What it explains:** "Scribal drift" or local topicality without explicit sections.
- **Key Vulnerability:** Risks violating the near-perfect line reset signatures established in Phase 5B.

## 3. Section-Anchored Entry
- **Definition:** Entry points are drawn from a specific sub-region or "layer" of the object for an entire page or section.
- **Selection Rule:** $P(Start_i | Section_k) = 1/N_{nodes \in Region_k}$.
- **What it explains:** Stable statistical differences between sections (e.g., Herbal vs. Pharma) within a single global grammar.
- **Key Vulnerability:** Requires evidence of block-level parameter shifts.

## 4. Parameter-Driven Entry (Systematic)
- **Definition:** Entry points are not chosen as nodes, but derived from a small set of parameters (e.g., Page Number, Line Index, a "Key" word).
- **Selection Rule:** $Start_i = f(	heta_{page}, 	heta_{line})$.
- **What it explains:** High diversity from minimal "seed" data.
- **Key Vulnerability:** Over-predicts regularity if the mapping $f$ is too simple.

---
**Status:** Entry phase5_mechanism classes frozen.  
**Next:** Pre-register necessary consequences and kill rules.
