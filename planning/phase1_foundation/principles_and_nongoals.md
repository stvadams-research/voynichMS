# Principles and Non-Goals

This document defines the governing principles, constraints, and explicit non-goals of the Voynich Foundation Project.

These are not guidelines. They are guardrails.

Every design decision, code change, and experiment must be compatible with this document. If a proposed action violates any principle or non-goal below, it must not be implemented.

---

## Mission Statement

The mission of this project is to construct a rigorous, assumption-aware phase1_foundation for the study of the Voynich Manuscript such that:

- Translation becomes possible in principle, or
- The impossibility of translation becomes unavoidable and demonstrable

This project does **not** attempt translation.

It exists to remove foundational uncertainty about what kind of system the manuscript is.

---

## Core Principles

### 1. Image Geometry Is the Highest Authority

All phase2_analysis ultimately derives from the manuscript images.

- Pixel geometry outranks transcription.
- Bounding boxes outrank tokens.
- Spatial relationships outrank assumed symbol identity.

If image geometry and a transcription disagree, the image wins.

---

### 2. Transliterations Are Third-Party Indices

All transliterations are treated as external, interpretive artifacts.

- They are never ground truth.
- They encode assumptions we do not accept a priori.
- Multiple transliterations may coexist simultaneously.

They are used only for indexing, alignment, and retrieval.

---

### 3. Ambiguity Is Preserved

Ambiguity is not a flaw to be eliminated. It is data.

- Uncertain alignments must remain uncertain.
- Competing segmentations may coexist.
- Multiple hypotheses may be stored in parallel.

Early forced decisions are a form of data loss.

---

### 4. Failures and Anomalies Are First-Class Data

Errors, mismatches, and edge cases are not noise.

- Alignment failures
- Segmentation breakdowns
- Outliers
- Instabilities

These must be stored, queryable, and inspectable.

They often contain more information than successes.

---

### 5. Scale Boundaries Are Enforced

Every object belongs to an explicit scale.

Examples:
- stroke
- component
- glyph candidate
- word
- line
- region
- page

Cross-scale operations must be explicit and validated.

Silent scale mixing is forbidden.

---

### 6. Negative Controls Are Mandatory

No structure is accepted without controls.

All major analyses must be tested against:
- synthetic null data
- scrambled manuscript variants

If a signal survives controls, it is meaningful.
If it does not, it is an artifact.

---

### 7. No Irreversible Early Decisions

Early stages must not commit to assumptions that cannot be undone.

Forbidden early commitments include:
- fixed alphabets
- normalized glyph sets
- assumed word boundaries
- semantic labels

Reversibility is a design requirement.

---

## Explicit Non-Goals

The following are explicitly out of scope for this project.

### Linguistic Non-Goals

- Translation
- Language identification
- Phonetic interpretation
- Mapping to known languages
- Grammar reconstruction
- Semantic labeling

These may be enabled later, but are not attempted here.

---

### Statistical Non-Goals

- Entropy comparison to known languages
- Zipf law fitting as evidence of language
- Frequency-based decoding

Statistics may be used descriptively, not inferentially toward meaning.

---

### Symbolic Non-Goals

- Alphabet discovery
- Fixed symbol inventories
- Character frequency tables treated as semantic
- One-to-one glyph-to-letter assumptions

Symbol identity is a hypothesis, not a premise.

---

### Methodological Non-Goals

- End-to-end models that obscure assumptions
- Black-box translation systems
- Optimizing for aesthetically pleasing structure
- Forcing convergence

If a method cannot explain *why* it produces a result, it does not belong here.

---

## Design Obligations

Any contribution must satisfy the following obligations.

- Be falsifiable or removable
- Declare its assumptions explicitly
- Respect scale boundaries
- Preserve ambiguity unless justified
- Produce artifacts that can be audited
- Log failures as data

Convenience is not a justification.

---

## Decision Discipline

Progress is defined by reduction of uncertainty, not accumulation of structure.

At every major step, the following questions must be answered:

- What assumption does this test?
- What would falsify it?
- What breaks if it is wrong?
- Does this survive negative controls?

If these questions cannot be answered, the work must stop.

---

## Final Statement

This project values epistemic discipline over speed, novelty, or cleverness.

It is acceptable to conclude:
- that translation is not currently possible, or
- that the manuscript is not linguistic in nature

It is not acceptable to conclude anything without structural evidence.

Everything here exists to make that distinction unavoidable.

---
