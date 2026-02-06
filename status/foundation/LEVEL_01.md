# Level 1 – Data and Identity Foundation

**Status**: COMPLETED
**Date Activated**: 2026-02-06
**Date Completed**: 2026-02-06

## Goals
- Create a stable, reproducible substrate.
- Establish identity, geometry, storage, and provenance.

## Deliverables
- [x] Canonical IDs (`FolioID`, `PageID`)
- [x] Geometry conventions (`Box`, `Polygon`, `Transform`)
- [x] Storage and provenance (`MetadataStore`, `RunContext`)
- [x] Scale registry (`Scale` Enum)
- [x] Run and experiment management (`RunManager`, `manifest.json`)
- [x] Logging and QC scaffolding (`AnomalyLogger`)
- [x] Dataset registration CLI (`voynich data register`)

## Verification
- [x] Deterministic IDs exist for pages and objects.
- [x] Runs are reproducible with full provenance.
- [x] Scale boundaries are enforced in code.
- [x] Data products are queryable and auditable.
