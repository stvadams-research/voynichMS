# Level 5 – Decision Discipline

**Status**: COMPLETED
**Prerequisites**: Level 4 complete (YES)

## Goals
- Establish a rigorous decision-making framework to filter structures and patterns.
- Force explicit acceptance/rejection of structures before hypothesis testing.

## Scope
- Decision Registry
- Sensitivity Analysis
- Structure Ledger

## Dependencies
- Level 4 complete

## Deliverables
- [x] **Database Schema**:
    - [x] `StructureRecord`, `DecisionRecord`, `SensitivityResultRecord`
- [x] **Decision Registry**:
    - [x] `StructureRegistry` class
    - [x] `register_structure`, `record_decision`
- [x] **Sensitivity Analysis**:
    - [x] `SensitivityAnalyzer` class
    - [x] Automated parameter sweeps
- [x] **CLI**:
    - [x] `voynich decisions register`
    - [x] `voynich decisions decide`
    - [x] `voynich decisions list`
    - [x] `voynich sensitivity run`
- [x] **Verification**:
    - [x] Acceptance demo showing structure registration, sensitivity sweep, decision recording, and ledger update.
