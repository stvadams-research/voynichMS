# Level 4 – Relational Grounding

**Status**: COMPLETED
**Prerequisites**: Level 3 complete (YES)

## Goals
- Establish explicit, purely geometric links between Text and Region ledgers without semantic interpretation.

## Scope
- Anchor data model
- Geometric anchor engine (overlaps, near, inside)
- Stability analysis under Level 3 controls

## Dependencies
- Level 3 complete (for controls)

## Deliverables
- [x] **Database Schema**:
    - [x] `AnchorRecord`, `AnchorMethodRecord`, `AnchorMetricRecord`
- [x] **Geometry Primitives**:
    - [x] Enhanced `Box` with `centroid`, `distance`, `contains`
- [x] **Anchor Engine**:
    - [x] `AnchorEngine` class
    - [x] O(N*M) geometric matching
- [x] **Query Engine**:
    - [x] `get_anchors_for_text`
    - [x] `get_anchors_for_region`
- [x] **Stability Analysis**:
    - [x] `AnchorStabilityAnalyzer`
    - [x] Comparison of anchor counts between Real and Scrambled data
- [x] **CLI**:
    - [x] `voynich anchors generate`
    - [x] `voynich anchors query`
    - [x] `voynich anchors analyze`
- [x] **Verification**:
    - [x] Acceptance demo showing anchors generated and degrading under scrambling.
