# ROADMAP
## Voynich Foundation Project

This document defines the authoritative, program-level roadmap for the Voynich Foundation Project.

It is designed to be stable over time. Details may evolve, but the structure, ordering, and intent of the levels below should not change without explicit justification.

This roadmap exists to prevent:
- premature interpretation
- scope creep
- mixing of abstraction levels
- accumulation of unfalsifiable structure

Translation is the *eventual* end goal, but it is never a task within this roadmap. Every level exists to make translation possible *in principle*, not to perform it.

---

## Program Mission

To construct the most rigorous, assumption-aware, and falsifiable foundation ever built for the study of the Voynich Manuscript, such that:

- translation becomes possible in principle, or
- the impossibility of translation becomes unavoidable and demonstrable

This project prioritizes **epistemic discipline** over speed, novelty, or cleverness.

---

## Execution Model

- Work proceeds **level by level**, in strict order.
- Only one level is considered “active” at any time.
- Each level has:
  - a goal
  - a defined scope
  - explicit dependencies
  - exit criteria
  - a logic stop before advancing
- Levels may be revisited only to fix defects, not to add new scope.

---

## LEVEL 0 – Governing Principles and Safety Rails

### Goal
Establish immutable constraints that prevent conceptual drift and premature interpretation.

### Scope
- Core principles
- Explicit non-goals
- Decision discipline
- Safety rails for humans and LLMs

### Key Artifacts
- PRINCIPLES_AND_NONGOALS.md
- Decision gate checklist

### Dependencies
- None

### Exit Criteria
- Principles are documented and committed.
- All subsequent plans explicitly reference Level 0.

---

## LEVEL 1 – Data and Identity Foundation

### Goal
Create a stable, reproducible substrate on which all later work depends.

### Scope
- Canonical IDs
- Coordinate and geometry conventions
- Storage and provenance
- Scale registry
- Run and experiment management
- Logging and QC scaffolding

### Explicit Exclusions
- No segmentation
- No transcription parsing
- No region proposals
- No embeddings
- No normalization

### Dependencies
- Level 0 complete

### Exit Criteria
- Deterministic IDs exist for pages and objects.
- Runs are reproducible with full provenance.
- Scale boundaries are enforced in code.
- Data products are queryable and auditable.

---

## LEVEL 2A – Text Ledger (Geometry-First)

### Goal
Make text-like content queryable without assuming glyph identity or linguistic structure.

### Scope
- Line segmentation
- Word segmentation
- Word-to-transcription alignment
- Glyph candidate extraction
- Soft glyph-to-symbol alignment

### Assumptions
- Glyph boundaries are uncertain.
- Transcriptions are indexes, not truth.
- Split/merge/null alignments are expected.

### Dependencies
- Level 1 complete

### Exit Criteria
- Query: transcription token → image instances.
- Query: word → glyph candidate instances.
- Alignment uncertainty is explicit and measurable.

---

## LEVEL 2B – Region Ledger (Visual Grammar)

### Goal
Treat each page as a visual system independent of text assumptions.

### Scope
- Exhaustive multi-scale region proposals
- Region graphs (containment, adjacency, connection)
- Region embeddings and geometric descriptors

### Assumptions
- Regions may overlap.
- Multiple competing segmentations may coexist.
- No region is semantic yet.

### Dependencies
- Level 1 complete

### Exit Criteria
- Query: region → similar regions across pages.
- Query: region → spatial relationships.
- Graph consistency checks pass.

---

## LEVEL 3 – Negative Controls and Baselines

### Goal
Determine which observed structures are meaningful and which are artifacts.

### Scope
- Synthetic null manuscripts
- Scrambled Voynich variants
- Metric evaluation under control conditions

### Dependencies
- Level 2A and/or Level 2B complete

### Exit Criteria
- Signals surviving controls are identified.
- Artifact-driven metrics are documented and rejected.

---

## LEVEL 4 – Cross-Ledger Integration

### Goal
Relate text objects and visual objects without mixing assumptions.

### Scope
- Anchors between text-ledger and region-ledger objects
- Proximity and overlap relations only

### Explicit Exclusions
- No semantic labeling
- No interpretation

### Dependencies
- Level 2A complete
- Level 2B complete

### Exit Criteria
- Query: label-like text → nearby diagram regions.
- Anchors degrade appropriately under negative controls.

---

## LEVEL 5 – Measurement and Decision Gates

### Goal
Ensure progress reduces uncertainty rather than accumulating structure.

### Scope
- Stability metrics
- Sensitivity analyses
- Formal decision gates

### Dependencies
- Levels 2–4 complete

### Exit Criteria
- Hypotheses are explicitly accepted or rejected.
- Decision records are written and versioned.

---

## LEVEL 6 – Hypothesis Modules (Plug-in Only)

### Goal
Test specific structural hypotheses in a controlled, removable way.

### Scope
- Equivalence class proposals
- Core-plus-modifier models
- Generative systems
- Constraint grammars

### Constraints
- Must consume ledgers, not raw images.
- Must emit new ledgers or metrics.
- Must be removable without refactoring.

### Dependencies
- Levels 1–5 complete

### Exit Criteria
- Hypotheses improve explanatory power beyond controls, or
- Hypotheses are explicitly falsified and retired.

---

## Program Completion Criteria

The program is complete when one of the following is achieved:

- A stable foundation exists that enables serious translation attempts without foundational ambiguity, or
- It is demonstrated that translation is not a coherent objective given the system’s structure

Both outcomes are considered success.

---

## Final Note

This roadmap is designed to make incorrect conclusions difficult and correct conclusions unavoidable.

If a step feels slow or overly cautious, that is intentional.

Rigor is the product.
