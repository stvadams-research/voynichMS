# Glossary

- **Admissibility:** The state of an explanation class (e.g., "Natural Language") being consistent with all observed structural constraints.
- **Indistinguishability:** A state where a synthetic artifact cannot be statistically separated from the real artifact by a specific set of metrics.
- **Generative Reconstruction:** The process of reverse-engineering the manuscript's phase5_mechanism by building a system that can reproduce it.
- **Mechanical Reuse:** The hypothesis that the scribe reused tokens from a limited pool without adaptive logic.
- **Procedural Generation:** Algorithmic creation of content based on rules, distinct from organic language production.
- **Glyph-Level Grammar:** Rules governing the sequence of individual characters (glyphs) rather than whole words.
- **Mapping Stability:** A metric measuring whether the identity of a text unit (word/glyph) persists when its geometric boundaries are slightly perturbed.
- **Z-Score (Information Density):** A statistical measure of how much more information-dense the manuscript is compared to a scrambled version of itself.
- **MetricResult:** A standardized data structure capturing the output of a quantitative phase2_analysis, including the scalar value, scope (global/page), and computation method (computed/simulated).
- **HypothesisResult:** The outcome of a falsification test (SUPPORTED, WEAKLY_SUPPORTED, FALSIFIED), accompanied by the supporting metrics and a phase7_human-readable verdict.
- **Page:** A database record in `PageRecord` used by pipeline storage and joins.
- **Folio:** A manuscript leaf identifier such as `f1r` or `f2v`; in this codebase, folio identifiers are carried in `PageRecord.id`.
- **Value:** A single numeric measurement (for example, `MetricResult.value`).
- **Metric:** A named measurement type with a defined computation method (for example, `RepetitionRate`).
- **Score:** A derived or aggregated assessment, often composed from one or more metric values (for example, `stability_score`).
- **Result:** A container object that bundles values/scores together with provenance or metadata (for example, stress-test and hypothesis result records).
