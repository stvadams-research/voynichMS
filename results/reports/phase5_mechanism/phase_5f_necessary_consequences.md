# PHASE 5F ENTRY-LEVEL NECESSARY CONSEQUENCES

**Project:** Voynich Manuscript – Entry-Point Identifiability  
**Objective:** Define the measurable signatures required for an entry selection phase5_mechanism to be admissible.

---

## 1. Consequence: C5F.UNIV.1 (Boundary Independence)
- **Statement:** Entry points must show no predictive carryover across line boundaries beyond what is expected by chance or anchoring.
- **Observable proxy:** Mutual Information between the first word of adjacent lines.
- **Kill rule:** If inter-line first-word MI significantly exceeds the 95th percentile of a matched-anchor control, purely independent models are eliminated.

## 2. Consequence: C5F.IND.1 (Vocabulary Diffusion)
- **Statement:** If selection is independent and uniform, every node in the large object should have an equal probability of being an entry point over a sufficiently large corpus.
- **Observable proxy:** Uniformity of "Start-Word" distribution compared to the global word distribution.
- **Kill rule:** Significant non-uniformity in the starting-word set (beyond frequency matching) eliminates the Uniform Independent class.

## 3. Consequence: C5F.ANCH.1 (Block Shift Signature)
- **Statement:** If entry is anchored, the statistical profile of starting words must shift abruptly at known structural boundaries (e.g., page turns).
- **Observable proxy:** Change-point detection score on the first-word vector per page.
- **Kill rule:** Absence of detectable shifts at structural boundaries eliminates the Section-Anchored class.

## 4. Consequence: C5F.PARM.1 (Parameter Parsimony)
- **Statement:** The number of unique entry parameters must be much smaller than the number of distinct lines generated.
- **Kill rule:** Any model requiring > 1 distinct parameter per line is eliminated as non-explanatory (overfitting).

---
**Status:** Consequences registered.  
**Next:** Implement entry simulators and run prefix phase2_analysis.
