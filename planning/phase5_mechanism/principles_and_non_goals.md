# Principles and Non-Goals: Phase 5 (Mechanism Identification)

This document defines the governing principles, constraints, and explicit non-goals for Phase 5 of the Voynich Manuscript research program. Phase 5 focuses on the identification of the internal production mechanism class.

---

## Mission Statement: Phase 5

The objective of Phase 5 is to move from **Admissibility** (what *could* it be) to **Identifiability** (what *must* it be). By testing the manuscript against falsifiable mechanism families, we aim to collapse the hypothesis space until only the structurally necessary production class remains.

Phase 5 does **not** interpret content; it identifies the engine.

---

## Core Principles

### 1. Identifiability via Exclusion (Falsification)
We do not seek to "prove" a model is correct. We seek to "kill" every model that is incompatible with the observed data. A mechanism class is only identified when all other parsimonious classes have been formally eliminated.

---

### 2. Mechanistic Invariance
Until proven otherwise, the production mechanism is assumed to be a globally stable, project-wide invariant. Sectional differences (Herbal vs. Stars) are treated as variations in component selection or scribal weight, not as changes in the underlying algorithm.

---

### 3. Parsimony as a Hard Constraint
Structural explanations must be parsimonious. If a model (e.g., an explicit graph) requires a state-space or edge-count that exceeds the information density of the corpus by orders of magnitude, it is deemed non-explanatory and structurally inadmissible.

---

### 4. Necessary Consequences and Kill Rules
No experiment shall be conducted without the prior registration of:
- **Necessary Consequences**: What *must* be true if this mechanism class is correct.
- **Kill Rules**: What observation would immediately disqualify this mechanism class.

---

### 5. Priority of Structural Boundaries
Structural boundaries—specifically line endings—are treated as the primary reset points for the mechanism state. Any mechanism that ignores line-level reset dynamics is structurally inadmissible.

---

### 6. Determinism Before Stochasticity
We prioritize testing for deterministic, rule-evaluated forcing before assuming stochastic (probabilistic) freedom. If a rule can explain an observation, we do not invoke "probability."

---

## Explicit Non-Goals

### Interpretive Non-Goals
- **Semantic Decoding**: No attempt to assign meaning, phonetics, or labels to tokens.
- **Symbolic Interpretation**: No mapping of glyphs to "letters" or "alphabets."
- **Intent Analysis**: We do not speculate on *why* the author wrote it; only *how* the text was produced.

---

### Historical Non-Goals
- **Provenance Identification**: We do not seek to identify the specific author, location, or date.
- **Artifact Reconstruction**: While we compare to historical artifacts (wheels, grilles), we do not attempt to reconstruct the physical device used.

---

### Generative Non-Goals
- **Aesthetic Synthesis**: We are not trying to produce "convincing" Voynich-like text for human eyes.
- **Creative Extension**: No attempt to "finish" or "extend" the manuscript using identified rules.
- **Optimization**: We do not "improve" the system for efficiency.

---

### Methodological Non-Goals
- **Black-Box AI Models**: No use of neural networks or LLMs to "generate" text without explicit, auditable rule-tracing.
- **Forced Convergence**: We do not ignore anomalies to make a model "fit" better.

---

## Design Obligations for Phase 5
1. **Traceability**: Every metric must be traceable to a specific RunID and a deterministic code path.
2. **Comparator Matching**: Synthetic comparators must be matched to Voynich scale (token count, TTR, vocabulary size) to ensure valid discrimination.
3. **Negative Controls**: Every "Success" in identification must be tested against a scrambled or randomized null version of the same data.

---

## Final Statement
Phase 5 terminates when the internal structural evidence ceases to be diagnostic. Success is defined by the rigorous identification of the production class, not by the discovery of a "solution." If the data remains ambiguous between two parsimonious classes, the phase must conclude as **Inconclusive** rather than forcing a choice.
