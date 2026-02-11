# Phase 3.3 Plan: Constraint Exhaustion and Robustness Closure

**Phase Name:** Phase 3.3 – Constraint Sufficiency and Invariance Tests  
**Status:** Pre-registered, terminal  
**Project:** Voynich Manuscript – Generative Reconstruction  
**Goal Type:** Falsification and robustness, not reconstruction  
**Date:** 2026-02-07

---

## 3.3.0 Purpose and Framing

Phase 3.3 is a deliberately narrow, terminal phase designed to exhaust the remaining **non-semantic, non-adaptive explanatory space** without introducing optimization, intent, or post hoc tuning.

This phase exists to answer questions that retain value even under null results. It is not intended to “solve” the Voynich Manuscript, improve generators, or close residual gaps by force.

**Success condition:**  
Either outcome meaningfully collapses the hypothesis space.

**Failure condition:**  
Any adaptive, goal-driven, or outcome-tuned phase5_mechanism is introduced.

---

## 3.3.1 Explicit Scope and Non-Goals

### In Scope
- Mechanical constraints only
- One-shot tests
- Predefined parameters and thresholds
- Robustness and invariance checks
- Null results treated as informative

### Explicitly Out of Scope
- Optimization or learning
- Feedback or adaptation
- Semantic interpretation
- Generator “improvement”
- Post hoc tuning to match target metrics
- Claims about authorial intent or meaning

If any out-of-scope element becomes necessary, Phase 3.3 terminates immediately.

---

## 3.3.2 Test A: Maximal Mechanical Reuse (One-Shot Falsification)

### Question Addressed
Even under maximal non-adaptive reuse constraints, does glyph-level grammar plus bounded token pools suffice to produce Voynich-level repetition?

### Hypotheses
- **H0:** Grammar plus bounded, non-adaptive reuse cannot reach a 0.90 repetition rate.
- **H1:** Grammar plus bounded, non-adaptive reuse is sufficient to reach a 0.90 repetition rate.

No intermediate hypotheses or graded success states are permitted.

### Mechanism Definition (Frozen Before Run)
- Glyph-level grammar fixed from Phase 3.2
- Token pools defined exogenously per page
- Pool sizes selected from a predeclared set (e.g., {10, 20, 30})
- Tokens generated once per page, then reused blindly
- No novelty penalties
- No scoring or ranking
- No memory of prior usage
- No pool resizing or regeneration

### Measurements
- Token repetition rate
- Information density
- Locality radius

### Interpretation Rules
- If repetition remains below threshold, algorithmic generation is insufficient even under extreme reuse.
- If repetition reaches threshold, grammar plus constraint is sufficient but does not imply intent, optimization, or meaning.

### Termination Clause
This test is executed once. No reruns. No parameter adjustment.

---

## 3.3.3 Test B: Transliteration Invariance Check

### Question Addressed
Are Phase 2 and Phase 3 admissibility conclusions invariant under reasonable transliteration choices?

### Scope Control
- Select no more than two alternative transliterations (e.g., EVA and one additional standard).
- No new features introduced.
- No metric thresholds redefined.

### What Is Tested
Directional stability of the following conclusions:
- Word-level inadmissibility
- Glyph-level necessity
- High repetition anomaly
- Strong locality effects

### What Is Explicitly Not Tested
- Fine-grained metric deltas
- Grammar rule discovery
- Generator performance

### Interpretation Rules
- If conclusions are invariant, transliteration choice is non-critical.
- If conclusions flip, prior claims must be downgraded as representation-dependent.

### Value Under Null
A null result increases confidence that earlier findings were not encoding artifacts.

---

## 3.3.4 Test C: Glyph Variant Sensitivity (Ablation Test)

### Question Addressed
Do glyph variants function as structural signals or as noise with respect to admissibility claims?

### Variant Handling Modes
- **Collapsed Mode:** Variants mapped to canonical glyphs
- **Expanded Mode:** Variants treated as distinct glyphs

No hybrid, weighted, or adaptive schemes are permitted.

### Measurements
- Stability of repetition anomaly
- Stability of locality effects
- Stability of grammar necessity

### Explicit Non-Claims
- No phase4_inference about scribal hands
- No semantic role for variants
- No decoding or cipher relevance

### Interpretation Rules
- If conclusions survive both modes, variants are non-critical.
- If conclusions fail only in expanded mode, claims are valid only under canonical representation.

### Value Under Null
Determines whether conclusions depend on representational choice rather than manuscript structure.

---

## 3.3.5 Pre-Registration and Integrity Safeguards

Before execution:
- All parameter ranges declared
- All metrics fixed
- All stopping criteria written
- All outcome interpretations predefined

During execution:
- REQUIRE_COMPUTED enforced
- No randomness outside seeded phase3_synthesis paths
- Full provenance and computation tracking enabled

After execution:
- No new hypotheses introduced
- No reframing of failure as partial success
- Results reported strictly as pass, fail, or indeterminate

---

## 3.3.6 Phase 3.3 Termination Statement (Prewritten)

Phase 3.3 exists to determine whether the remaining unexplained structure of the Voynich Manuscript can be eliminated through additional non-semantic mechanical constraints, or whether it reflects non-algorithmic process factors. Regardless of outcome, Phase 3.3 produces a terminal classification and does not define a continuation pathway.

---

## 3.3.7 Epistemic Position

Phase 3.3 is designed so that:
- Failure increases explanatory clarity
- Success does not imply semantics
- Null results strengthen stopping conditions

This phase closes the project harder, not longer.
