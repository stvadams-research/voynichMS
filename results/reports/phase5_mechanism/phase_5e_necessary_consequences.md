# PHASE 5E NECESSARY CONSEQUENCES AND KILL RULES

**Project:** Voynich Manuscript – Large-Object Traversal  
**Objective:** Define the measurable signatures required for a topology-traversal pair to be admissible.

---

## 1. Consequence: C5E.COLL.1 (Path Collision Signature)
- **Statement:** If lines are paths through a static object, identical word-pairs appearing in different lines must have identical successors significantly more often than random chance.
- **Observable proxy:** Successor consistency for recurring bigrams across the manuscript.
- **Kill rule:** If successor consistency is indistinguishable from a matched shuffled-control, any "static object" model is eliminated.

## 2. Consequence: C5E.ENTR.1 (Global-Local Entropy Gap)
- **Statement:** The mechanism must simultaneously support high global entropy (many valid tokens) and low local entropy (fixed path).
- **Observable proxy:** Ratio of global slot entropy to mean within-line conditional entropy.
- **Kill rule:** If the ratio is < 4.0, simple low-dimensional models are eliminated as insufficient.

## 3. Consequence: C5E.FREQ.1 (Natural Frequency Emergence)
- **Statement:** The global Zipf-like distribution must emerge as a consequence of the traversal frequency of nodes, not be hard-coded.
- **Kill rule:** If the model requires an explicit "frequency table" to match Voynich's Zipf curve, the topology is eliminated as non-explanatory.

---
**Status:** Consequences registered.  
**Next:** Implement path determinism and collision tests.
