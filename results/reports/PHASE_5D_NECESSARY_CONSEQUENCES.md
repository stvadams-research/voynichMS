# PHASE 5D GRAMMAR-LEVEL NECESSARY CONSEQUENCES

**Project:** Voynich Manuscript – Deterministic Line Grammar  
**Objective:** Pre-register measurable consequences that must hold for a deterministic grammar family to remain sufficient.

---

## 1. Universal Grammar Consequence: C5D.UNIV.1 (Uniqueness and Resets)
- **Statement:** Every line must exhibit a Type-Token Ratio (TTR) near 1.0, and successor rules must reset at every line boundary.
- **Observable proxy:** Line-level TTR and Reset Score (from Phase 5B).
- **Kill rule:** If any model permits token repetition within a line or carries state across lines, it is eliminated.

## 2. Family 1 & 2: Slot-Structure Consequences
### Consequence ID: C5D.SLOT.1 (Positional Class Stability)
- **Statement:** Tokens must occupy stable, non-overlapping positional roles across the manuscript.
- **Observable proxy:** Mutual Information between token identity and position-in-line.
- **Kill rule:** If token-position MI is indistinguishable from a matched shuffled control, slot-based models are eliminated.

### Consequence ID: C5D.SLOT.2 (Successor Entropy Bottlenecks)
- **Statement:** Successor entropy must drop sharply at the transition between slots.
- **Observable proxy:** Variance of successor entropy as a function of word index.
- **Kill rule:** If successor entropy is uniform across positions, rigid slot models are eliminated.

## 3. Family 3: Traversal Consequences
### Consequence ID: C5D.TRAV.1 (Path Re-entry)
- **Statement:** If lines are traversals of a static object, identical word pairs must be followed by identical successors more often than chance.
- **Observable proxy:** Conditional successor consistency for recurring bigrams.
- **Kill rule:** If bigram successor consistency is low, static-object traversal is eliminated.

---
**Status:** Consequences registered.  
**Next:** Implement slot boundary detection.
