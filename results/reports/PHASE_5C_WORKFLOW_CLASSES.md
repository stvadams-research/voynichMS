# PHASE 5C WORKFLOW CLASSES: LINE-CONDITIONED PRODUCTION MODELS

**Project:** Voynich Manuscript – Workflow Reconstruction  
**Objective:** Define the minimal line-conditioned workflows to be evaluated for structural sufficiency.

---

## 1. Independent Line-Scoped Pool
- **Defining Assumptions:** Each line is an independent generation event. A unique token pool is sampled for the line, and all latent state is discarded at the line boundary.
- **Degrees of Freedom:** Pool size distribution, token selection bias.
- **What it explains:** High within-line repetition, perfect line-end resets.
- **Key Vulnerability:** May not explain subtle cross-line statistical regularities if they exist.

## 2. Weakly Coupled Line Pools
- **Defining Assumptions:** Line pools are sampled from a drifting "active reservoir." Some token overlap persists between adjacent lines, but no persistent semantic state.
- **Degrees of Freedom:** Reservoir size, drift rate (token replacement frequency).
- **What it explains:** Local clusters of repetition that span 2-3 lines (if observed).
- **Key Vulnerability:** Over-predicts cross-line transition stability.

## 3. Parameter-Coupled Lines
- **Defining Assumptions:** Lines are independent in their token pools but share "macro-parameters" (e.g., a specific entropy budget or a local grammar variant).
- **Degrees of Freedom:** Macro-parameter distributions, coupling strength.
- **What it explains:** Global consistency in statistics without requiring specific token persistence.
- **Key Vulnerability:** Harder to distinguish from purely independent lines using text alone.

## 4. Two-Stage Line Workflow
- **Defining Assumptions:** A line-local generator produces raw text, which is then processed by a secondary line-local filter (e.g., phonetic smoothing or length normalization).
- **Degrees of Freedom:** Stage 1 generator type, Stage 2 filter rules.
- **What it explains:** Complex within-line constraints that seem "too regular" for simple pools.
- **Key Vulnerability:** Risk of over-parameterization (violating minimal sufficiency).

---
**Status:** Workflow families frozen.  
**Next:** Pre-register necessary consequences and implement simulators.
