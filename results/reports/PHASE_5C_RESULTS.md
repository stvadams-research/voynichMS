# PHASE 5C RESULTS: WORKFLOW RECONSTRUCTION PILOT

**Date:** 2026-02-07
**Status:** Pilot Complete (Sufficiency Failure)
**Objective:** Identify the minimal line-conditioned workflow capable of reproducing Voynich structure.

---

## 1. Pilot Results Summary

| Workflow Model | Mean TTR (Line) | Mean Entropy (Line) | Status |
|----------------|-----------------|----------------------|--------|
| **Voynich (Real)** | **0.9839** | **1.3487** | **TARGET** |
| **Independent Pool (F1)** | 0.7280 | 2.7534 | **FAIL** |
| **Coupled Pool (F2)** | 0.7893 | 2.7740 | **FAIL** |

---

## 2. Key Findings

### 2.1 The "Uniqueness" Paradox
- Real Voynich lines have an extremely high TTR (**0.98**), meaning almost every word in a line is unique.
- Our current pool-based simulators (**F1 & F2**) produce significantly lower TTRs (~0.72-0.78), meaning they are *too repetitive* within the line.
- **Insight:** The scribe was not "randomly sampling" from a pool; they were likely **exhausting** a list or following a non-repeating traversal rule per line.

### 2.2 Entropy Mismatch
- The real manuscript has much lower line-level entropy (**1.35**) than the stochastic simulators (**2.75+**).
- **Insight:** The sequence of words within a Voynich line is **far more predictable** than a random draw from a pool would suggest. The "grammar" of the line is more rigid than the global grammar.

---

## 3. Admission Status Updates

| Workflow Family | Status | Evidence |
|-----------------|--------|----------|
| **Independent Line Pool** | WEAKENED | Captures reset behavior but fails on line-internal rigidity. |
| **Weakly Coupled Pools** | WEAKENED | Over-predicts local repetition; fails entropy target. |
| **Rigid Deterministic** | **STRENGTHENED** | The data now points to a workflow that is **procedural and non-stochastic** within the line. |

---
**Conclusion:** Phase 5C has falsified the "Random Pool Sampling" workflow. The manuscript's line-level structure is too unique and too rigid for simple stochastic models. The workflow reconstruction must now pivot to **Deterministic Slot-Filling** or **Sequential Table-Lookup** models.
