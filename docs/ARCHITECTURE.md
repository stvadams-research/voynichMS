# System Architecture

## 1. Foundation Layer (`src/foundation/`)
Provides the core infrastructure for data handling, metrics, and reproducibility.
- **Core:** ID generation, randomness control, geometry primitives.
- **Storage:** Database (SQLite/SQLAlchemy) and file system abstraction.
- **Runs:** Provenance tracking (RunID, inputs, outputs, environment).
- **Metrics:** Pure functions for calculating Repetition Rate, Entropy, etc.

## 2. Analysis Layer (`src/analysis/`)
Implements the "Assumption-Resistant" analytical framework.
- **Admissibility:** Rules for excluding explanation classes.
- **Stress Tests:** Perturbation analysis (mapping stability, information preservation).
- **Anomaly:** Characterization of structural anomalies (e.g., high z-score).

## 3. Synthesis Layer (`src/synthesis/`)
Implements the "Generative Reconstruction" framework.
- **Profile Extractor:** Derives constraints from real manuscript pages.
- **Generators:**
  - `ConstrainedMarkovGenerator`: Word-level (Legacy/Baseline).
  - `GrammarBasedGenerator`: Glyph-level probabilistic grammar (Phase 3.2).
- **Indistinguishability:** "Turing Test" comparing synthetic vs. real metrics.

## 4. Data Flow
1. **Raw Data** (Images, Transcriptions) -> **Ingestion** (Database).
2. **Database** -> **Profile Extraction** -> **Constraints**.
3. **Constraints** -> **Generator** -> **Synthetic Pages**.
4. **Synthetic + Real Pages** -> **Analysis Pipeline** -> **Metrics**.
5. **Metrics** -> **Comparison/Conclusion**.
