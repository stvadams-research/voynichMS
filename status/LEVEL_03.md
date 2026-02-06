# Level 3 – Negative Controls and Baselines

**Status**: COMPLETED
**Prerequisites**: Level 2A and/or Level 2B complete (YES)

## Goals
- Determine which observed structures are meaningful and which are artifacts.

## Scope
- Synthetic null manuscripts
- Scrambled Voynich variants
- Metric evaluation under control conditions

## Dependencies
- Level 2A complete
- Level 2B complete

## Deliverables
- [x] **Control Generators**:
    - [x] Scrambled Control Generator (shuffles glyphs/words/regions)
    - [x] Synthetic Null Generator (creates noise pages)
- [x] **Metric Framework**:
    - [x] `Metric` interface
    - [x] Core metrics (`RepetitionRate`, `ClusterTightness`)
- [x] **Comparison Engine**:
    - [x] `Comparator` class
    - [x] Classification logic (`SURVIVES`, `PARTIAL`, `FAILS`)
- [x] **CLI**:
    - [x] `voynich controls generate-scrambled`
    - [x] `voynich controls generate-synthetic`
    - [x] `voynich metrics run`
    - [x] `voynich analysis compare`
- [x] **Verification**:
    - [x] Acceptance demo showing metrics degrading (or surviving) under controls.
