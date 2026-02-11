Phase 4.5 Execution Plan: Semantic Admissibility Boundary Formalization

Project: Voynich Manuscript, Structural Admissibility Program
Phase: 4.5
Goal Type: Epistemic boundary setting and necessary-condition formalization
Primary Goal: Explicitly define what would count as statistical or computational evidence for semantics, and demonstrate that Phase 4 methods do not and cannot meet that standard, even in principle.

1. Phase 4.5 Purpose and Core Question
1.1 Core question

What necessary conditions must a statistical or computational signal satisfy to be admissible as evidence of semantics, and do any Phase 4 methods even target those conditions?

1.2 Why Phase 4.5 exists

Phase 4 established that existing methods are not diagnostic.

Phase 4.5 closes the remaining interpretive gap by:

formalizing the semantic target

distinguishing semantic evidence from structural proxies

preventing post hoc redefinition of “meaning”

1.3 What Phase 4.5 is not

Not a new battery of methods

Not an attempt to “find meaning another way”

Not an extension of Phase 3 generators

Not a philosophical argument about intention

Phase 4.5 is an admissibility clarification phase, not a discovery phase.

1.4 Success criteria

Phase 4.5 is successful if it produces:

A clear necessary-condition definition for semantic evidence

A mapping showing that Phase 4 methods fail those conditions by construction

A formal statement of what future claims must demonstrate to reopen the question

2. Phase 4.5 Design Principles
2.1 Necessary, not sufficient, conditions only

Phase 4.5 defines what must be true for semantics to be possible to infer.

It does not attempt to define:

sufficient conditions

a full theory of meaning

how meaning would be encoded historically

2.2 No new empirical signals without new assumptions

All phase2_analysis must be grounded in:

Phase 4 results

already computed metrics

already frozen corpora

Any new signal requires an explicit new assumption and is therefore out of scope.

2.3 Inference, not ontology

Phase 4.5 addresses:

what can be inferred from text statistics

It does not address:

whether the author intended meaning

whether meaning exists in some private or external sense

3. Semantic Admissibility Framework
3.1 Definition: semantics for this project

For the purposes of phase4_inference, semantics is defined as:

A stable mapping between symbolic variation and latent states that are not reducible to local mechanical constraints, reuse rules, or bounded generative procedures.

This definition is intentionally minimal and operational.

3.2 Necessary conditions for semantic evidence

A statistical signal is admissible as semantic evidence only if all of the following hold:

Non-mechanical irreducibility
The signal cannot be reproduced by any non-semantic generator with comparable structural constraints.

Cross-context stability
The signal persists under sectioning changes, resampling, and local perturbation in a way that mechanical reuse signals do not.

Latent-state dependence
The signal reflects dependencies that cannot be explained solely by token frequency, reuse locality, or production rules.

Control separability
The signal cleanly separates semantic corpora from all tested non-semantic structured corpora, not just from noise.

Failure of any one condition renders the signal non-diagnostic.

4. Phase 4 Method Mapping to Semantic Conditions

Phase 4.5 explicitly maps each Phase 4 method to the necessary conditions above.

4.1 Method A: Information clustering

Targets frequency variation across partitions

Fails condition 1: fully reproducible by bounded reuse

Fails condition 3: no latent-state dependence

Conclusion: structurally descriptive only

4.2 Method B: Network and language-likeness features

Targets adjacency and distributional regularity

Fails condition 1: exceeded by mechanical models

Fails condition 4: cannot separate structured non-semantic from language

Conclusion: compatibility test, not evidence test

4.3 Method C: Topic modeling and alignment

Targets local frequency concentration

Fails condition 2: highly sensitive to arbitrary partitions

Fails condition 3: topics correspond to reuse patterns, not latent states

Conclusion: section-sensitive structure detector

4.4 Method D: Language ID under flexible transforms

Targets best-match similarity under search

Fails condition 4: null corpora yield equivalent matches

Fails condition 2: unstable under preprocessing

Conclusion: multiple-comparisons artifact

4.5 Method E: Morphology and grammar induction

Targets regularity in word formation

Fails condition 1: trivially produced by tables

Fails condition 3: reflects vocabulary construction, not meaning

Conclusion: generator fingerprinting, not semantics

5. Explicit Non-Equivalence Statement

Phase 4.5 must include a formal statement that:

Structural complexity is not semantic evidence

Topic-like clustering is not semantic evidence

Language-likeness is not semantic evidence

Stability under reuse is not semantic evidence

These are necessary but not sufficient properties of language, and therefore inadmissible as proof.

6. What Would Reopen Semantic Admissibility

Phase 4.5 explicitly documents the only paths forward.

A future claim must provide at least one of the following:

A signal that survives comparison against all known non-semantic structured generators and cannot be reproduced without latent-state coupling.

Independent external grounding, such as bilingual anchors or non-textual alignment, that bypasses pure text statistics.

A formally specified new assumption, clearly acknowledged as such, changing the admissibility framework.

Absent this, further statistical phase2_analysis is not justified.

7. Primary Outputs

reports/PHASE_4_5_SEMANTIC_ADMISSIBILITY.md

reports/PHASE_4_5_METHOD_CONDITION_MAP.md

reports/PHASE_4_5_CLOSURE_STATEMENT.md

No new code directories are required unless strictly necessary for exposition.

8. Execution Order and Bounded Scope
Stage 0: Write admissibility definitions and necessary conditions

Deliverable:

Semantic admissibility framework document

Stage 1: Map Phase 4 methods to conditions

Deliverable:

Method-to-condition matrix with explicit failures

Stage 2: Draft closure and reopening criteria

Deliverable:

Formal closure statement and future-work gate

Stop immediately after Stage 2.

9. Phase 4.5 Termination Statement, pre-written

Phase 4.5 formalizes the admissibility boundary for inferring semantics from the Voynich Manuscript using statistical and computational methods. By defining necessary conditions for semantic evidence and demonstrating that Phase 4 methods fail these conditions by construction, Phase 4.5 establishes that existing signals cannot justify claims of language or meaning. Further progress requires new assumptions, new evidence, or a fundamentally different question.

10. Immediate Next Actions

Write the semantic admissibility definition and necessary conditions

Produce the method-to-condition mapping table

Draft the closure and reopening criteria

Freeze Phase 4 and Phase 4.5 together as a single inferential boundary