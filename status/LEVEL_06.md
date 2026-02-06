# Level 6 – Hypothesis Testing

**Status**: COMPLETED
**Prerequisites**: Level 5 complete (YES)

## Goals
- Formulate and test specific hypotheses about the manuscript's structure and meaning, using the rigorous framework built in Levels 1-5.

## Scope
- Hypothesis definition
- Test execution
- Result analysis

## Dependencies
- Level 5 complete (Decision Discipline)

## Deliverables
- [x] **Database Schema**:
    - [x] `HypothesisRecord`, `HypothesisRunRecord`, `HypothesisMetricRecord`
- [x] **Plug-in Architecture**:
    - [x] `Hypothesis` interface
    - [x] `HypothesisManager`
- [x] **Example Hypothesis**:
    - [x] `GlyphPositionHypothesis` (tests positional entropy)
- [x] **CLI**:
    - [x] `voynich hypotheses register`
    - [x] `voynich hypotheses run`
    - [x] `voynich hypotheses list`
- [x] **Verification**:
    - [x] Acceptance demo showing hypothesis registration, execution against controls, and categorical outcome recording.
