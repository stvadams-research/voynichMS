# PRINCIPLES_AND_NON_GOALS.md
## Phase 4 – Inference Admissibility Evaluation

This document defines the binding principles and explicit non-goals governing Phase 4 of the Voynich project.

Phase 4 exists because Phases 1–3 established a structural framework and built an integrity-first engine capable of producing and testing controlled corpora.

This document is normative, not descriptive.
If work conflicts with this document, the work is wrong.

---

## 1. Phase 4 Mission Statement

Phase 4 exists to:

- evaluate whether widely cited phase4_inference methods used to claim meaning or language in the Voynich Manuscript are actually diagnostic
- measure false positive rates by applying those methods to non-semantic but structurally Voynich-like corpora with known ground truth
- clarify what can and cannot be inferred from structure alone
- narrow feasible interpretation space by closing phase4_inference loopholes, not by proposing new theories

Phase 4 does not exist to:
- prove the manuscript is meaningless
- refute specific authors
- win debates
- produce a translation or a decoded plaintext

---

## 2. Relationship to Earlier Phases

### Relationship to Phase 1 (Foundation)
Phase 1 is frozen.
Phase 4 may only read Phase 1 artifacts.

Phase 4 must not:
- alter ledgers
- revise schemas
- reinterpret provenance
- retroactively change segmentation rules to improve outcomes

### Relationship to Phase 2 (Admissibility)
Phase 2 asked:
What explanation classes are structurally allowed?

Phase 4 asks:
Which phase4_inference methods are valid evidence for those classes?

### Relationship to Phase 3 (Generative Reconstruction)
Phase 3 established that non-semantic mechanisms can reproduce many headline anomalies.
Phase 4 uses that fact to test whether popular methods mistakenly treat those anomalies as evidence of meaning.

Phase 4 does not exist to improve generators.
Generators are tools for controls, not goals.

---

## 3. Core Principles

### Principle 1: Methods, Not People
Phase 4 evaluates phase4_inference methods, not authors.

The goal is not to show that someone was wrong.
The goal is to determine whether a method can or cannot support the claims it is commonly used to support.

Any language that frames results as personal defeat, reputational attack, or ideological conflict is a violation.

---

### Principle 2: Diagnostic Power Requires Strong Controls
A method is not “validated” because it separates Voynich from random noise.

A method is only evidence for semantics if it reliably separates:
- semantic corpora
from
- non-semantic corpora that are structurally similar to Voynich

If a method cannot make that separation, it is not semantics-diagnostic.

---

### Principle 3: Pre-Registered Claims and Decision Rules
For each tested method, Phase 4 must define before running:

- the method’s claimed phase4_inference
- the minimal implementation required to fairly represent it
- the evaluation dataset(s)
- the false positive definition
- the pass, fail, and indeterminate criteria

Post hoc threshold changes are violations.

---

### Principle 4: Multiple Comparisons Are First-Class
Many Voynich claims arise from:
- trying many transformations
- trying many languages
- trying many models
- picking the best-looking output

Phase 4 must model this explicitly and quantify it.
If a method’s “best match” is reported, Phase 4 must also report:
- how often a similar best match arises under null conditions
- how sensitive the best match is to small preprocessing changes

A method that cannot control for multiple comparisons cannot claim discovery.

---

### Principle 5: Representation Invariance Is Required
Claims must be robust to reasonable representational choices, including:

- transliteration variants
- glyph variant collapsing versus expansion
- tokenization and sectioning schemes (within declared bounds)

If a method’s result flips under reasonable representation choices, it is fragile and must be downgraded.

---

### Principle 6: Separation of Sufficiency and Identification
Phase 4 may demonstrate that:
- a method produces semantic-looking signals on non-semantic corpora (false positives)
- a method fails to produce signals on non-semantic corpora (increased credibility)

Phase 4 may not conclude that:
- any specific historical phase5_mechanism produced the manuscript
- any particular semantic interpretation is true or false

Sufficiency is not identification.
Diagnostic success is not proof of meaning.

---

### Principle 7: Reproducibility and Auditability Are Mandatory
Every Phase 4 result must be traceable to:

- a specific RunID
- corpus hashes
- method configuration
- code version and environment

Phase 4 results without full provenance are invalid, regardless of how compelling they look.

---

### Principle 8: Minimal Faithful Implementations
Phase 4 must avoid straw-manning.
When evaluating a method:

- implement the method as described in its source, as faithfully as feasible
- if deviations are necessary, document them
- ensure the method is given its best fair chance to succeed

A method that fails under unfair conditions proves nothing.

---

### Principle 9: Null Results Are Valuable
Phase 4 treats null outcomes as progress.

Examples:
- a method yields high “semantic” scores on known non-semantic corpora
- topic models align with artificial section labels
- language identification outputs confident matches on random or structured gibberish

These are not disappointments.
They are boundary-setting evidence.

---

### Principle 10: Stop When the Methods Are Exhausted
Phase 4 terminates when:

- the chosen method list is fully tested against the frozen corpus suite
- robustness checks are complete
- each method is assigned a stable outcome class:
  - not diagnostic
  - partially diagnostic
  - conditionally diagnostic
  - potentially diagnostic

Continuing beyond that point requires a new question, not “one more test.”

---

## 4. What Counts as Progress in Phase 4

Progress is defined as:

- quantifying false positive rates of phase4_inference methods
- identifying which signals arise from structure alone
- documenting which methods remain credible under strong controls
- producing reusable evaluation harnesses for future claims

Progress is not defined as:
- producing persuasive narratives about meaning
- generating compelling translations
- winning social arguments
- aesthetic similarity or “it feels like” judgments

---

## 5. Explicit Non-Goals

Phase 4 explicitly does NOT aim to:

- translate the manuscript
- identify the underlying language
- assign semantics to glyphs, tokens, or diagrams
- “prove” hoax or “prove” authenticity
- publish a definitive historical account of authorship or purpose
- optimize models until they pass by brute force
- cherry-pick sections or preprocessings that strengthen a preferred conclusion

If any of the above occurs, it is accidental and must be treated skeptically.

---

## 6. Handling Ambiguity

Ambiguity is expected and acceptable.

Phase 4 must:
- preserve uncertainty where evidence is insufficient
- prefer underclaiming to overclaiming
- report indeterminate outcomes explicitly, not as “near wins”

Ambiguity that survives strong controls is information.

---

## 7. Interaction with Prior Literature

Phase 4 must treat prior work as test targets with respect:

- cite sources accurately
- implement methods fairly
- separate method performance from author intent
- avoid rhetorical framing

Phase 4’s contribution is not “debunking.”
It is clarifying what the methods can legitimately support.

---

## 8. Outcome Classes and Reporting Discipline

Each method tested in Phase 4 must end with:

- a one-sentence outcome classification
- a concise explanation of what was tested
- a list of conditions under which the method is valid or invalid
- a clear “what this does not imply” statement

No ambiguous victory language.
No “solved” language.

---

## 9. Termination Conditions

Phase 4 stops when:

- the method list is exhausted
- the corpus suite is frozen and fully evaluated
- results are stable under robustness checks
- conclusions reduce the space of admissible claims about semantics from structure

Stopping is not failure.
Stopping is evidence that the space has been bounded.

---

## 10. Final Statement

Phase 4 is where the temptation shifts:
not to interpret the manuscript, but to interpret the interpretations.

These principles exist to ensure that:
- phase4_inference remains testable
- critique remains fair
- results remain auditable
- conclusions remain bounded

If Phase 4 feels like it is closing doors without opening new stories, it is working.

---

This document is binding for all Phase 4 contributors.
