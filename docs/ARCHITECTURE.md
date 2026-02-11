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

## 4. Inference Layer (`src/inference/`)
Evaluates the diagnostic validity of methods used to claim semantic content.
- **Cross-Dataset Validation:** Compares results on real vs. non-semantic controls.
- **False Positive Assessment:** Establishes the "noise floor" for language identification.

## 5. Visualization & Publication (`src/visualization/` & `scripts/preparation/`)
Formalizes findings for human interpretation and peer review.
- **Visualization:** Automated plotting of phase-specific metrics.
- **Publication Scaffolding:** Automated assembly of research drafts from latest data.

## 6. Data Flow
1. **Raw Data** (Images, Transcriptions) -> **Ingestion** (Database).
2. **Database** -> **Profile Extraction** -> **Constraints**.
3. **Constraints** -> **Generator** -> **Synthetic Pages**.
4. **Synthetic + Real Pages** -> **Analysis Pipeline** -> **Metrics**.
5. **Metrics** -> **Comparison/Conclusion**.
6. **Conclusion** -> **Visualization & Drafting** -> **Publication**.
