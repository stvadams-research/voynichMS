# Phase 19 Alignment Diagnostics (Workbench)

## Purpose

The Page Generator now reports a **Generated vs Actual** alignment scorecard for the selected folio.

This scorecard is diagnostic only. It measures how close generated text is to the bundled actual folio text under the current settings.

## Where It Appears

In `Page Generator`, directly below the main status box:

- `Generated vs Actual (Phase 19 Scorecard)`

## Metrics

1. `Line Count Error`: absolute line-count difference between generated and actual.
2. `Exact Token Rate`: position-aware token agreement after sanitizer normalization.
3. `Normalized Edit Distance`: line-level token edit distance, normalized.
4. `Affix Fidelity`: agreement rate for leading/trailing line affixes (e.g., `<%>`, `<$>`).
5. `Marker Fidelity`: agreement rate for IVTFF marker classes when markers are present.

## Normalization Notes

The scorecard uses the same workbench token hygiene path (`sanitizeToken`) and IVTFF parsing logic (`parseIVTFFLine`) where available.

## Interpretation Guardrails

- Higher alignment score does **not** imply decipherment.
- These metrics evaluate structural and lexical proximity only.
- Residual mismatch is expected and is part of the model boundary.
