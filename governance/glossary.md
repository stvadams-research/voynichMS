# Glossary

Terms used throughout this codebase. Organized by domain: manuscript studies,
project-specific analysis, and codebase infrastructure.

---

## Manuscript & Paleography

- **Voynich Manuscript (MS 408):** An illustrated codex held by Yale's Beinecke
  Library, carbon-dated to c. 1404-1438. Written in an undeciphered script using
  an unknown writing system. Catalog: Beinecke MS 408.

- **Folio:** A single leaf of the manuscript. Identified by number and side:
  `f1r` (folio 1, recto/front) or `f1v` (folio 1, verso/back). In this
  codebase, folio identifiers are carried in `PageRecord.id`.

- **Bifolio:** A single sheet of parchment that, when folded, creates two
  folios (four pages). Adjacent bifolios are nested into quires.

- **Quire:** A gathering of nested bifolios sewn together as a unit. The
  Voynich Manuscript contains approximately 20 quires of varying size
  (typically 8 folios each).

- **Section:** A thematic division of the manuscript based on illustration
  content. The standard divisions (from Voynich scholarship, not this project)
  are: **Herbal** (plant illustrations), **Pharmaceutical** (jars and roots),
  **Astronomical** (circular diagrams), **Biological** (bathing figures), and
  **Stars** (star-like rosettes). Section assignments come from the IVTFF
  transcription file headers.

- **Currier A / Currier B:** Two statistically distinct "languages" or "hands"
  identified by Captain Prescott Currier (1976) based on character frequency
  differences. Pages are classified as Currier A or B. Currier hand boundaries
  roughly correspond to manuscript sections.

- **Scribe:** The person who physically wrote a portion of the manuscript. The
  number of scribes is debated (estimates range from 1 to 5+). This codebase
  treats scribe identity as an empirical question tested in Phase 7.

---

## Writing System & Transcription

- **EVA (Extensible Voynich Alphabet):** A Latin-letter encoding scheme for
  Voynich characters, created by Rene Zandbergen and Gabriel Landini. Each
  Voynich glyph maps to one or more Latin letters (e.g., `o`, `d`, `y`,
  `qo`, `ch`, `sh`). EVA is the standard encoding used by all major
  transliteration efforts.

- **IVTFF (Interlinear Voynich Transcription File Format):** A plain-text
  format (version 2.0) for storing Voynich transliterations. Each line begins
  with a location header (`<f1r.1,@P0;H>`) encoding folio, line number,
  transcriber, and section. The canonical input file is `ZL3b-n.txt`
  (Zandbergen-Landini transliteration).

- **Glyph:** The smallest visually distinct character unit in the Voynich
  script. In EVA encoding, a glyph may be one letter (`o`) or a ligature
  (`ch`, `sh`). In this codebase, glyphs are stored in `GlyphCandidateRecord`.

- **Token:** A single EVA-encoded character string parsed from the
  transliteration. Tokens are the atomic unit of computational analysis.
  Stored in `TranscriptionTokenRecord`. Distinguished from "word" (space-
  delimited sequence of tokens) and "line" (all tokens on one manuscript line).

- **Word:** A space-delimited sequence of tokens on a manuscript line. Words
  are the unit of vocabulary analysis (repetition rate, hapax ratio). Stored
  in `WordRecord` with geometric bounding boxes from segmentation.

- **Line:** All tokens on a single horizontal line of manuscript text,
  identified by folio + line index. Stored in `TranscriptionLineRecord`
  (transcription) and `LineRecord` (segmentation).

- **Page:** A database record (`PageRecord`) representing one side of a folio.
  Used for joins, grouping, and spatial queries. The `id` field holds the
  folio identifier (e.g., `f1r`).

- **Gallows:** Tall EVA characters (`t`, `k`, `p`, `f` and their variants)
  that extend above the normal line height. Their positional distribution is
  a key structural feature tested in Phase 5.

---

## Analysis & Methodology

- **Admissibility:** The state of an explanation class (e.g., "Natural
  Language", "Simple Cipher") being consistent with all observed structural
  constraints. An inadmissible class has been formally excluded by at least
  one falsification test.

- **Explanation Class:** A category of hypotheses about what the manuscript
  is (e.g., natural language, constructed language, mechanical cipher,
  random noise). Stored in `ExplanationClassRecord` with status
  admissible/inadmissible/underconstrained.

- **Indistinguishability:** A state where a synthetic artifact cannot be
  statistically separated from the real artifact by a specific set of metrics.
  Used in Phase 3 to test whether generated text matches the manuscript.

- **Noise Floor:** The baseline level of apparent "meaning" or "structure"
  that standard analysis tools find in random data. Established in Phase 4
  to prevent false-positive inferences about the manuscript.

- **Mapping Stability:** A metric measuring whether the identity of a text
  unit (word/glyph) persists when its geometric boundaries are slightly
  perturbed (5% boundary shift). Score of 0.02 indicates near-total collapse
  — the manuscript's text-image alignment is fragile.

- **Successor Entropy:** The entropy of the probability distribution over
  which token follows a given token. Low successor entropy means tokens are
  highly predictable from their predecessor — a hallmark of rule-governed
  systems.

- **Reset Score:** Measures how strongly line boundaries "reset" the
  statistical context. A high reset score (e.g., 0.96) means lines behave
  as independent constraint units, not as continuations of prior lines.

- **Implicit Constraint Lattice:** The identified mechanism class for the
  manuscript: a globally stable, deterministic rule-evaluated system where
  token selection is governed by intersecting positional, contextual, and
  structural constraints. Identified in Phase 5.

- **Generative Reconstruction:** The process of reverse-engineering the
  manuscript's mechanism by building a system that can reproduce it.

- **Mechanical Reuse:** The hypothesis that the scribe reused tokens from a
  limited pool without adaptive logic. Used as a control/baseline.

- **Procedural Generation:** Algorithmic creation of content based on rules,
  distinct from organic language production.

- **Glyph-Level Grammar:** Rules governing the sequence of individual
  characters (glyphs) rather than whole words. Constrains which glyphs can
  follow which others in specific positions.

- **Z-Score (Information Density):** A statistical measure of how much more
  information-dense the manuscript is compared to a scrambled version of itself.

---

## Phase 10 Methods

- **Method F (Generation vs Encoding):** Tests whether the manuscript could
  be the output of a reversible encoding of meaningful content. Searches for
  reverse parameterizations that decode into low-entropy text.

- **Method G (Illustration Grounding):** Tests whether illustration features
  correlate with adjacent text features, which would support semantic content.

- **Method H (Typological Comparison):** Compares Voynich statistical profiles
  against a typologically diverse set of natural languages.

- **Method I (Cross-Linguistic Comparison):** Compares Voynich structural
  features against specific historical languages (Latin, Hebrew, Arabic, etc.).

- **Method J (Empirical Discrimination):** Tests whether Voynich text can be
  reliably distinguished from synthetic rule-generated text by trained
  classifiers.

- **Method K (Focal-Depth Correlation):** Tests whether the decision to
  classify the manuscript correlates with analysis depth — i.e., whether
  conclusions are robust to how deeply you look.

---

## Codebase Infrastructure

- **MetricResult:** A standardized data structure capturing the output of a
  quantitative analysis, including the scalar value, scope (global/page), and
  computation method (computed/simulated).

- **HypothesisResult:** The outcome of a falsification test
  (SUPPORTED, WEAKLY_SUPPORTED, FALSIFIED), accompanied by the supporting
  metrics and a human-readable verdict.

- **Value:** A single numeric measurement (e.g., `MetricResult.value`).

- **Metric:** A named measurement type with a defined computation method
  (e.g., `RepetitionRate`).

- **Score:** A derived or aggregated assessment, often composed from one or
  more metric values (e.g., `stability_score`).

- **Result:** A container object that bundles values/scores together with
  provenance or metadata (e.g., stress-test and hypothesis result records).

- **ProvenanceWriter:** The standard mechanism for writing JSON result files.
  Wraps results in a `{"provenance": {...}, "results": {...}}` envelope
  containing run_id, git_commit, timestamp, seed, and command.

- **RandomnessController:** Enforces reproducibility constraints via three
  modes: FORBIDDEN (analytical code — no RNG allowed), SEEDED (control
  generation — RNG with explicit seed), UNRESTRICTED (legacy compatibility).

- **ComputationTracker:** Records whether each component's output was
  COMPUTED (from real data), SIMULATED (from fallback logic), or CACHED.
  When `REQUIRE_COMPUTED=1`, simulation fallbacks raise
  `SimulationViolationError`.

- **RunManager:** Thread-safe lifecycle manager for experimental runs.
  Handles initialization (seeding, environment capture), tracking, and
  completion. Integrates with ComputationTracker and ProvenanceWriter.

- **MetadataStore:** SQLAlchemy-based access layer for the SQLite database
  (`data/voynich.db`). Provides session management and helper methods for
  all 33+ tables.

- **Dataset:** A named collection of pages (e.g., `voynich_real`,
  `scrambled_v1`). Stored in `DatasetRecord` with path and checksum.

- **Anchor:** A scored link between a text element (word/line/glyph) and a
  spatial region on the manuscript page. Used in Phase 5 for multimodal
  coupling analysis (SK-H1).

- **Structure:** A detected pattern or relationship in the data (e.g., a
  glyph-level grammar rule) that can be accepted, rejected, or held for
  further analysis. Stored in `StructureRecord`.

- **Decision:** A recorded judgment about a structure, with reasoning and
  evidence links. Stored in `DecisionRecord`.
