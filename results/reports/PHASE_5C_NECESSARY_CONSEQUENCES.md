# PHASE 5C WORKFLOW-LEVEL NECESSARY CONSEQUENCES

**Project:** Voynich Manuscript – Workflow Reconstruction  
**Objective:** Pre-register measurable consequences that must hold for a workflow family to remain sufficient.

---

## 1. Universal Workflow Consequence: C5C.UNIV.1 (Inter-Line Independence)
- **Statement:** The transition rules from line N cannot predict line N+1 successors significantly better than the global bigram frequency.
- **Observable proxy:** Mutual Information between successor sets of adjacent lines.
- **Kill rule:** If mutual information exceeds the 95th percentile of a matched shuffled control, purely independent models (Family 1 & 3) are eliminated.

## 2. Family 1: Independent Line-Scoped Pool
### Consequence ID: C5C.POOL.1 (Novelty Bursts)
- **Statement:** The introduction of "new" tokens must occur in bursts at line beginnings.
- **Observable proxy:** Position-of-first-occurrence for tokens within a line.
- **Kill rule:** If novelty is distributed uniformly across word positions in a line, the line-scoped pool model is eliminated.

## 3. Family 2: Weakly Coupled Line Pools
### Consequence ID: C5C.COUP.1 (Persistence Decay)
- **Statement:** The probability of token reuse must decay exponentially across line boundaries.
- **Observable proxy:** Token repetition frequency as a function of line distance.
- **Kill rule:** If reuse probability does not decay significantly across 1-3 lines, the coupling model is eliminated.

## 4. Family 4: Two-Stage Line Workflow
### Consequence ID: C5C.PIPE.1 (Residual Regularity)
- **Statement:** After accounting for the primary line-generator, the residuals must exhibit the "fingerprint" of the second stage.
- **Observable proxy:** Significance of secondary constraints (e.g., phonetic filters).
- **Kill rule:** If a single-stage model accounts for >95% of transition variance, the two-stage model is eliminated as unnecessary.

---
**Status:** Consequences registered.  
**Next:** Implement simulators and run parameter inference.
