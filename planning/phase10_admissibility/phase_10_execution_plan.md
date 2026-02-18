# Phase 10 Execution Plan: Adversarial Retest

**Project:** Voynich Manuscript, Structural Admissibility Program
**Phase:** 10
**Goal Type:** Adversarial stress-test of the project's own closure
**Primary Goal:** Design and execute tests that the current framework systematically avoided. Each test is constructed to either defeat or materially strengthen the Phase 4.5 closure determination. No test exists to confirm what we already believe.

---

## 1. Phase 10 Purpose and Core Question

### 1.1 Core question

Does the Voynich manuscript contain recoverable content or grounded correlations that survive the strongest null models this project can construct?

### 1.2 Relationship to closure

Phase 4.5 closed the project conditionally, defining three reopening criteria:
1. Irreducible signal
2. External grounding
3. Framework shift

Phase 10 invokes Criterion 3 (framework shift). The existing framework tests whether **statistical aggregates** can be reproduced mechanically. Phase 10 tests whether the **specific sequence** and its **relationship to non-textual content** can be explained mechanically.

### 1.3 What Phase 10 is

- An honest attempt to find something the previous phases missed
- A set of tests designed to break the current conclusion if it deserves breaking
- A pre-registered evaluation where every method has a defined defeat condition for the closure hypothesis

### 1.4 What Phase 10 is not

- A translation attempt
- A language identification campaign
- A defense of the procedural-artifact hypothesis
- An excuse to rerun Phase 4 with different parameters

Phase 10 asks new questions. It does not re-ask old ones.

### 1.5 Success criteria

Phase 10 is successful if it produces:
- A clear determination for each method: closure strengthened, closure weakened, or indeterminate
- At least one test that the current procedural-artifact model cannot trivially explain away
- An updated closure statement that accounts for the new evidence, in either direction

### 1.6 Primary outputs

- `results/data/phase10_admissibility/` containing run-linked result artifacts
- `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
- `results/reports/phase10_admissibility/PHASE_10_CLOSURE_UPDATE.md`
- `src/phase10_admissibility/` code modules implementing each method

---

## 2. Phase 10 Design Principles

### Principle 1: Adversarial to Self

Every test is designed to find evidence **against** the project's existing conclusion. If the conclusion survives, it is strengthened. If it doesn't, we learn something. Both outcomes are progress.

This is not advocacy for meaning. It is intellectual honesty about what was left untested.

### Principle 2: Sequence, Not Statistics

Phases 1-9 operate on statistical aggregates: entropy, frequency distributions, compression ratios, network metrics. These abstract away the specific token sequence.

Phase 10 operates on the **actual sequence**: the specific tokens on specific pages in specific positions, and what those specifics correlate with.

### Principle 3: Content Grounding Over Pattern Matching

Phase 10 tests whether the text relates to something outside itself: illustrations, physical structure, positional extraction. If all external correlations are null, the procedural-artifact hypothesis is strongly confirmed. If any survive, the framework must be revised.

### Principle 4: Pre-Registered Defeat Conditions

For each method, the execution plan defines in advance:
- What result would **defeat** the closure hypothesis
- What result would **strengthen** it
- What result would be **indeterminate**

No post-hoc reinterpretation.

---

## 3. Corpus and Data Requirements

### 3.1 Existing assets (reused from Phases 1-9)

- EVA-tokenized Voynich text (canonical via EVAParser)
- Phase 3 generators: table-grille, self-citation, constrained Markov, slot-logic
- Phase 4 generators: line-reset Markov, backoff, boundary-persistence
- Latin semantic baseline
- Non-semantic structured corpora (all Phase 4 families)
- Metadata: folio-to-section mapping, Currier hand assignments, quire structure

### 3.2 New assets required

#### A. Illustration feature vectors
Machine-extracted or manually coded visual features per folio:
- Illustration type (botanical, astronomical, biological, pharmaceutical, text-only)
- For botanical: plant morphology features (root system present, flower count, leaf shape class, overall plant height/complexity)
- For astronomical: diagram geometry (circular, radial, segmented)
- Label positions: bounding regions where "label" text appears adjacent to specific illustration features

Source options(in priority order). Note source images are available in /data/raw/scans :
1. Published catalogs of Voynich illustration classifications (e.g., Clemens & Harkness, Currier, d'Imperio)
2. Simple computational extraction from high-resolution scans (color histograms, edge density, connected components)
3. Manual coding from a small representative subset (~40 folios across sections)

#### B. Cross-linguistic comparison corpora
Tokenized text samples (50,000+ tokens each) from typologically diverse languages:
- **Fusional:** Latin (existing), Greek, Russian
- **Agglutinative:** Turkish, Finnish, Nahuatl, Hungarian
- **Isolating:** Mandarin (character-segmented), Vietnamese
- **Semitic (abjad):** Arabic, Hebrew
- **Syllabic:** Japanese (kana-only), Cherokee
- Minimum: 12 languages spanning at least 4 typological classes

Source: Project Gutenberg, UDHR corpus, Leipzig Corpora Collection, or similar freely available tokenized text.

#### C. Writing system reference data
Type-token ratio ranges, character-per-word distributions, and combinatorial productivity measurements for 10+ known writing systems. Available from published typological databases or computable from the cross-linguistic corpora above.

---

## 4. Method Targets

### 4.1 Method F: Reverse Mechanism Test

**Claim being tested:** The identified generative mechanisms (table-grille, slot-logic) could also function as encoding devices. If so, the actual Voynich sequence might decode into structured output.

**Implementation goal:**
For each mechanism class identified in Phase 5 (table-grille, slot-logic, constrained Markov):
1. Enumerate or sample the parameter space (grille configurations, slot assignments, transition tables)
2. For each parameterization, "decode" the Voynich token sequence by running the mechanism in reverse
3. Measure whether the decoded output has statistical properties (entropy, compression ratio, type-token ratio) significantly different from what random-input encoding would produce

**Key tests:**
- **Signal detection:** For each mechanism class, does any parameterization yield decoded output with entropy significantly lower than the bulk average? (Lower entropy = more structured = possible plaintext.)
- **Null calibration:** Generate 1000 random token sequences with Voynich-like statistics, encode them through the same mechanisms, then decode them through the same reverse parameterizations. This establishes the false-positive rate for "finding structure."
- **Stability test:** If a parameterization yields structured output, does it remain structured under small perturbations (shifting the grille by one position, swapping two slot assignments)?

**Artifacts to record:**
- Decoded output entropy distribution across parameterizations, compared to null distribution
- Any parameterization that falls below the 1st percentile of the null
- Stability scores for outlier parameterizations

**Decision rules:**
- **Defeats closure:** A parameterization yields decoded output with entropy below the 1st percentile of the null, stable under perturbation, and the decoded output shows frequency distributions consistent with a natural language or structured notation system.
- **Strengthens closure:** No parameterization yields decoded output distinguishable from random-input encoding. The mechanism is generation-only; it does not hide structure.
- **Indeterminate:** A few outliers exist but are unstable or not significantly below the null.

**Computational feasibility note:**
The parameter space for table-grilles is vast. Phase 10 does not require exhaustive search. It requires:
- Random sampling of 10,000+ configurations per mechanism class
- Guided search using any known constraints (slot-logic positions, known glyph positional biases)
- Clear statement of coverage: "We tested N configurations spanning X% of the constrained space"

---

### 4.2 Method G: Text-Illustration Content Correlation

**Claim being tested:** The text on each folio relates to the illustration on that folio at a level more specific than section-level frequency shifts.

**Implementation goal:**
1. Assign visual feature vectors to each illustrated folio (see Section 3.2A)
2. Assign textual feature vectors to each folio (token frequencies, TF-IDF, specific rare-token presence)
3. Compute pairwise folio similarity in both visual space and textual space
4. Measure correlation between visual similarity and textual similarity across all folio pairs
5. Compare against null models where folio-text assignments are permuted within and across sections

**Key tests:**
- **Cross-folio correlation:** Do folios with visually similar illustrations have textually similar content? Measured by Mantel test (correlation between visual distance matrix and textual distance matrix).
- **Within-section residual:** After removing section-level frequency effects (by demeaning within each section), does any residual correlation survive?
- **Label specificity:** For botanical folios with identifiable "label" text near specific plant parts, do the same label tokens recur near morphologically similar plant features on other folios?
- **Null calibration:** Permute folio-text assignments 1000 times. Report where the real correlation falls in the null distribution.

**Artifacts to record:**
- Mantel test r-value and p-value (full manuscript)
- Within-section residual correlation after demeaning
- Label token recurrence matrix (if labels are identifiable)
- Null distribution plots

**Decision rules:**
- **Defeats closure:** Cross-folio text-illustration correlation survives within-section demeaning AND falls below p < 0.01 against the permutation null. The text is not content-indifferent to the illustrations.
- **Strengthens closure:** No significant correlation between visual similarity and textual similarity, even before demeaning. The text and illustrations are independent productions pasted onto the same pages.
- **Indeterminate:** Correlation exists at the section level but vanishes after demeaning. This is already explained by section-level frequency models and adds no new information.

---

### 4.3 Method H: Writing System Typology

**Claim being tested:** The Voynich glyph inventory and word structure match a specific known writing system type (alphabet, syllabary, abugida, logography).

**Implementation goal:**
1. Compute for the Voynich: glyph type count, mean/median/mode word length (in glyphs), type-token ratio at multiple scales, combinatorial productivity (how many possible words vs. observed words for the given vocabulary)
2. Compute the same metrics for reference writing systems (see Section 3.2C)
3. Position the Voynich in writing-system feature space

**Key tests:**
- **Typological fit:** Does the Voynich cluster with any specific writing system type in the [glyph_count, mean_word_length, type_token_ratio, combinatorial_productivity] feature space?
- **Exclusion test:** Can any writing system types be ruled out? (e.g., if Voynich has 30 glyphs and 4.5 glyphs/word, logographic systems are excluded)
- **Mechanical comparison:** Where do the Phase 3/5 generators fall in the same space? If generators and Voynich occupy the same region, typological fit is non-diagnostic. If they diverge, the typological position of the Voynich is informative.

**Artifacts to record:**
- Feature table: Voynich, reference writing systems, Phase 3/5 generators
- 2D projection of writing-system feature space
- Nearest-neighbor distances

**Decision rules:**
- **Defeats closure (partially):** Voynich clusters with a specific writing system type AND the Phase 3/5 generators do not cluster there. The Voynich's combinatorial structure is not explained by the known generators.
- **Strengthens closure:** Voynich occupies the same region as generators, or falls outside all known writing system types. Its structure is better explained by a generative procedure than by any known encoding convention.
- **Indeterminate:** Voynich falls in an overlap region between multiple writing system types and generators.

---

### 4.4 Method I: Cross-Linguistic Positioning

**Claim being tested:** The project's discrimination results hold against a broad typological sample, not just Latin.

**Implementation goal:**
1. Compute the Phase 4 feature set (entropy, compression ratio, repetition rate, network metrics, morphological consistency, Zipf parameters, type-token ratio, positional entropy) for 12+ typologically diverse languages
2. Compute the same features for Voynich and for Phase 3/5 generators
3. Build a distance matrix and project into 2D
4. Measure where Voynich falls relative to the language cloud and the generator cloud

**Key tests:**
- **Nearest language:** Which natural language is Voynich statistically closest to? Is that distance comparable to inter-language distances, or is it an outlier?
- **Generator proximity:** Is Voynich closer to the generator cloud or the language cloud? Report the margin.
- **Typological pocket:** If Voynich is near a specific language family (e.g., agglutinative languages), does that survive cross-validation and resampling?
- **Null baseline:** Shuffle each language corpus to produce matched-statistics nulls. Report whether Voynich is closer to real languages or to shuffled-language nulls.

**Artifacts to record:**
- Feature table: all languages, Voynich, generators
- Distance matrix with bootstrap uncertainty
- 2D projection with confidence ellipses
- Nearest-neighbor table

**Decision rules:**
- **Defeats closure:** Voynich is closer to the language cloud than the generator cloud, AND closer to a specific typological group than to any generator, with bootstrap confidence > 95%.
- **Strengthens closure:** Voynich is closer to generators than to any natural language. The Latin-only result generalizes across language families.
- **Indeterminate:** Voynich falls in the overlap between language and generator clouds. The features are not discriminating at this scale.

---

### 4.5 Method J: Steganographic Extraction

**Claim being tested:** Meaningful content is hidden in a specific positional subsequence of the token stream, while the bulk statistics serve as a carrier.

**Implementation goal:**
1. Define a set of extraction rules:
   - Line-initial tokens (first token of each line)
   - Line-final tokens
   - Word-initial glyphs (first glyph of each word, concatenated)
   - Nth-token extraction (every 2nd, 3rd, 5th, 7th token)
   - Slot-position extraction (e.g., all tokens in position 3 of each word, if slot-logic applies)
   - Paragraph-initial tokens
2. For each extraction rule, compute: entropy, compression ratio, type-token ratio, bigram mutual information
3. Compare against the same extractions from Phase 3/5 generated text

**Key tests:**
- **Anomaly detection:** Does any extracted subsequence have significantly different statistical properties (especially lower entropy or higher mutual information) than the same extraction from generated text?
- **Null calibration:** Apply all extraction rules to 100 generated sequences. Report where the Voynich extraction falls in each null distribution.
- **Composability:** If an extracted subsequence shows anomalous structure, can it be further decomposed or does it remain structured under re-extraction?

**Artifacts to record:**
- Extraction-rule-by-metric table for Voynich and generators
- Z-scores for each Voynich extraction relative to generator null
- Any extraction where |z| > 3

**Decision rules:**
- **Defeats closure:** An extraction rule yields a Voynich subsequence with entropy or mutual information significantly different from generator extractions (|z| > 3), and the anomaly is stable under resampling and folio-order permutation.
- **Strengthens closure:** All extractions are statistically indistinguishable from generator extractions. There is no hidden channel.
- **Indeterminate:** Line-initial tokens show anomalous structure, but this is already explained by the line-reset phenomenon documented in Phase 4.

---

### 4.6 Method K: Residual Gap Anatomy

**Claim being tested:** The residual gap between the best generators and the Voynich is noise, not signal.

**Implementation goal:**
1. Take the best-performing generator from Phase 4 (likely boundary-persistence or line-reset backoff)
2. Generate 100 synthetic corpora
3. Compute the full Phase 4 feature set for each
4. For each feature dimension, compute the distribution of generator values and report where the Voynich falls
5. Identify the specific features where Voynich is an outlier (|z| > 2)
6. Test whether those outlier features are correlated or independent

**Key tests:**
- **Feature decomposition:** Which specific features contribute most to the Voynich-generator distance? Rank by z-score.
- **Correlation structure:** Are the outlier features independent (suggesting random deviation) or correlated (suggesting a systematic property the generator doesn't capture)?
- **Irreducibility test:** For each outlier feature, attempt to build a minimal generator modification that closes the gap. If the modification is trivial (adjust one parameter), the feature is explained. If it requires a qualitatively new mechanism, the feature is potentially irreducible.
- **Natural language comparison:** Do the outlier features place Voynich closer to or further from natural language? If the residuals pull toward language, they may be semantic. If they pull away from everything, they are likely artifacts.

**Artifacts to record:**
- Per-feature z-score table: Voynich vs. best generator
- Correlation matrix of outlier features
- Modification difficulty scores for each outlier
- Direction of outlier (toward language vs. toward noise)

**Decision rules:**
- **Defeats closure:** Two or more correlated outlier features that pull toward natural language, resist trivial generator modification, and survive resampling. The generator is missing something systematic.
- **Strengthens closure:** All outlier features are independent, small, and easily closed by minor parameter adjustments. The gap is measurement noise.
- **Indeterminate:** Outlier features exist but pull in no coherent direction. The gap is real but uninterpretable.

---

## 5. Run Structure, Provenance, and Reproducibility

All Phase 10 runs must follow the existing provenance framework:
- RunID assigned and registered
- Corpus hashes recorded
- Code version and commit hash locked
- RandomnessController set to SEEDED for all stochastic operations
- Results stored in `results/data/phase10_admissibility/<method_name>.json`
- Run copies in `results/data/phase10_admissibility/by_run/<artifact>.<run_id>.json`

---

## 6. Execution Order

### Stage 0: Data acquisition and corpus preparation
- Acquire cross-linguistic corpora (Method I)
- Build or acquire illustration feature vectors (Method G)
- Compile writing system reference data (Method H)

**Deliverables:**
- `data/corpora/cross_linguistic_manifest.json`
- `data/illustration_features.json` or equivalent
- `data/writing_system_reference.json`

### Stage 1: Quick wins (Methods H, J, K)
These three methods require no new external data beyond what the project already has or can compute from existing assets:
- **Method H** (Writing System Typology): computable from EVA transcription alone
- **Method J** (Steganographic Extraction): computable from EVA transcription and existing generators
- **Method K** (Residual Gap Anatomy): computable from existing Phase 4 generator outputs

Run these first. They establish whether the existing data already contains unexamined signal.

### Stage 2: External grounding (Methods G, I)
These require new data:
- **Method G** (Text-Illustration Correlation): requires illustration feature vectors
- **Method I** (Cross-Linguistic Positioning): requires multilingual corpora

These are the strongest tests. If Method G finds content correlation, it is the most difficult result for the procedural-artifact hypothesis to explain.

### Stage 3: Deep search (Method F)
- **Method F** (Reverse Mechanism Test): computationally expensive, requires careful null calibration

This is the most ambitious test. Run last, informed by the results of Stages 1-2. If Methods G and I both confirm closure, Method F becomes lower priority. If either finds anomalous signal, Method F becomes urgent.

### Stage 4: Synthesis
- Compile results across all six methods
- Write updated closure determination
- If any method defeats closure, explicitly revise the Phase 4.5 statement
- If all methods strengthen closure, write a substantially stronger closure with the new evidence base

**Deliverables:**
- `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
- `results/reports/phase10_admissibility/PHASE_10_CLOSURE_UPDATE.md`

---

## 7. Interpretation Framework

### 7.1 Method outcome classes

For each method, assign exactly one:
- **Closure defeated:** The test found evidence that the procedural-artifact hypothesis cannot explain without substantive modification
- **Closure strengthened:** The test confirmed the procedural-artifact hypothesis in a domain it had not previously been tested
- **Indeterminate:** The test was inconclusive or the result was already explained by known properties
- **Test invalid:** The test could not be executed with sufficient statistical power or data quality

### 7.2 Aggregate determination

Phase 10 updates the Phase 4.5 closure as follows:
- If **any** method defeats closure: closure is revised to acknowledge the specific domain where the procedural-artifact hypothesis is insufficient. The project reopens in that domain.
- If **all** methods strengthen closure: the closure statement is upgraded from "structurally indistinguishable under tested methods" to "structurally indistinguishable under tested methods AND content-ungrounded AND sequence-unexploitable."
- If **mixed** results: document the tension explicitly. Do not resolve it by fiat.

---

## 8. What Would Change Everything

The single most consequential possible finding, in order of impact:

1. **Method G finds content correlation:** If specific rare tokens consistently co-occur with specific visual features across unrelated folios, and this survives permutation testing, the text is not content-indifferent. The procedural-artifact hypothesis would need to explain why a meaningless generator produces output that correlates with hand-drawn illustrations across the manuscript. This is very difficult to explain mechanically.

2. **Method F finds decodable structure:** If a plausible mechanism parameterization yields decoded output with natural-language-like properties, the text may be a cipher. This would not identify the plaintext, but it would demonstrate that the sequence contains recoverable structure beyond its surface statistics.

3. **Method K finds correlated residuals toward language:** If the features where generators fail systematically pull the Voynich toward the natural-language cloud, the generators are missing something that languages have. This is the gentlest form of defeat for closure, but it points to where future work should focus.

---

## 9. Phase 10 Termination Statement (pre-written)

Phase 10 stress-tests the project's central conclusion by asking questions that Phases 1-9 systematically avoided. By testing the encoding direction of identified mechanisms, the content-level relationship between text and illustrations, and the statistical positioning against typologically diverse languages, Phase 10 determines whether the closure is robust or whether it rests on the specific limitations of the tests that produced it. Phase 10 terminates when all six methods are evaluated, results are stable, and the closure statement is either confirmed, revised, or explicitly left in tension.

---

## 10. Immediate Next Actions

1. Begin Stage 1 (Methods H, J, K) using existing project data
2. Acquire cross-linguistic corpora and begin illustration feature extraction for Stage 2
3. Do not begin Method F until Stages 1-2 inform its priority

### 10.1 Execution Status (Stage 1)

- **Status:** COMPLETE
- **Completed at:** 2026-02-18
- **Confirmatory run ID (#1):** `e34e89be-55f5-6028-9394-3d44b75f7fba`
- **Confirmatory execution profile (#1):** `target_tokens=30000`, `method_j_null_runs=100`, `method_k_runs=100`
- **Prior bounded run ID (historical):** `573ea975-a6d6-dbab-628f-9ee36f1887fe` (`target_tokens=10000`, `method_j_null_runs=20`, `method_k_runs=30`)
- **Provenance note:** Current canonical Method H/J/K artifacts and Stage 1 summary are from run `e34e89be-55f5-6028-9394-3d44b75f7fba`.
- **Console progress logging:** Enabled for long-running loops in `scripts/phase10_admissibility/run_stage1_hjk.py` and `src/phase10_admissibility/stage1_pipeline.py` (null calibration, anomaly stability checks, synthetic runs, parameter sweeps).
- **Method outcomes:**
  - Method H: `closure_strengthened`
  - Method J: `closure_weakened`
  - Method K: `closure_weakened`
  - Stage 1 aggregate: `closure_weakened`
- **Artifacts:**
  - `results/data/phase10_admissibility/method_h_typology.json`
  - `results/data/phase10_admissibility/method_j_steganographic.json`
  - `results/data/phase10_admissibility/method_k_residual_gap.json`
  - `results/data/phase10_admissibility/stage1_summary.json`
  - `results/reports/phase10_admissibility/PHASE_10_STAGE1_RESULTS.md`

### 10.1b Execution Status (J/K Confirmatory Gates)

- **Status:** COMPLETE
- **Completed at:** 2026-02-18
- **Primary compute run ID:** `8e8db350-fed8-a8d5-3e80-8adb5bbf9043` (all three seeds executed end-to-end)
- **Checkpoint resume/finalization run IDs:** `a19ce99e-c582-85fc-227a-76990250715d`, `90be725c-7807-2223-e4a5-39cbeef6bc8b`
- **Pre-registered gate config:** `configs/phase10_admissibility/stage1b_upgrade_gate.json`
- **Replication profile:** `seeds=[42,77,101]`, `target_tokens=30000`, `method_j_null_runs=100`, `method_k_runs=100`
- **Step 2 (multi-seed direction replication):**
  - Method J direction consensus: `closure_weakened` across all seeds
  - Method K direction consensus: `closure_weakened` across all seeds
- **Step 3 (Method J line-reset ablation + folio-order permutation stability):**
  - Edge-rule ablation applied to `line_initial_tokens` and `paragraph_initial_tokens`
  - Stable non-edge anomalies remained after ablation and permutation checks (`2` per seed), so Method J gate passed
- **Step 4 (Method K outlier robustness):**
  - Same outlier set/sign behavior persisted across seeds
  - Correlated residual requirement passed for all seeds
  - Language-ward hard-to-close residual features persisted across seeds, so Method K gate passed
- **Step 5 (upgrade gate decision):**
  - Method J stays `closure_weakened`
  - Method K stays `closure_weakened`
- **Step 6 (priority handoff):**
  - Next priority: `10.2_then_10.3`
- **Artifacts:**
  - `results/data/phase10_admissibility/method_j_seed_42.json`
  - `results/data/phase10_admissibility/method_j_seed_77.json`
  - `results/data/phase10_admissibility/method_j_seed_101.json`
  - `results/data/phase10_admissibility/method_k_seed_42.json`
  - `results/data/phase10_admissibility/method_k_seed_77.json`
  - `results/data/phase10_admissibility/method_k_seed_101.json`
  - `results/data/phase10_admissibility/stage1b_jk_multiseed_replication.json`
  - `results/reports/phase10_admissibility/PHASE_10_STAGE1B_JK_REPLICATION.md`
  - `results/data/phase10_admissibility/stage1b_jk_replication_status.json`

### 10.2 Execution Status (Stage 2)

- **Status:** COMPLETE (FOLLOW-UP RECOMPUTE COMPLETE)
- **Initial completion at:** 2026-02-18 (`07d99032-ed44-bfc0-22bb-65d2f72f2464`; Method I coverage invalid)
- **Resume verification run ID:** `070c6121-2eca-ef99-3953-fd4967f89092`
- **Follow-up corpus expansion window (UTC):** 2026-02-18 12:44 to 12:48
- **Follow-up Stage 2 recompute run ID:** `2c9d1421-498b-f264-bbf4-1ce6fbcfcaf5`
- **Execution profile:** `scan_resolution=folios_2000`, `scan_fallbacks=[folios_full,tiff,folios_1000]`, `image_max_side=1400`, `method_g_permutations=1000`, `method_i_bootstrap=500`, `method_i_min_languages=12`, `language_token_cap=50000`
- **Machine-extraction policy:** Applied end-to-end.
  - Illustration features: machine-extracted from scans, no manual folio labeling.
  - Cross-linguistic corpora: machine-extracted via scripted API ingestion, no manual corpus tagging.
- **Data resources explicitly inventoried from `/data`:**
  - Scans (JPG): `folios_1000=208`, `folios_2000=209`, `folios_full=209`
  - Scans (TIFF): `213` files in `data/raw/scans/tiff`
  - External corpora after follow-up: `13` usable language corpora (`>=2000` tokens each)
  - Typology classes after follow-up: `5` (`abjad`, `agglutinative`, `fusional`, `isolating`, `syllabic`)
- **Stage 2 method outcomes (latest recompute):**
  - Method G: `indeterminate` (full coupling significant; residual effect non-positive)
  - Method I: `closure_strengthened` (coverage met: `13` languages, `5` typology classes; generator-cloud proximity favored with bootstrap confidence `0.95`)
  - Stage 2 aggregate: `indeterminate`
- **Deliverables created/updated:**
  - `data/illustration_features.json` (refreshed)
  - `data/corpora/cross_linguistic_manifest.json` (refreshed)
  - `data/external_corpora/arabic.txt`
  - `data/external_corpora/finnish.txt`
  - `data/external_corpora/greek.txt`
  - `data/external_corpora/hebrew.txt`
  - `data/external_corpora/hungarian.txt`
  - `data/external_corpora/japanese.txt`
  - `data/external_corpora/mandarin.txt`
  - `data/external_corpora/russian.txt`
  - `data/external_corpora/turkish.txt`
  - `data/external_corpora/vietnamese.txt`
- **Artifacts/checkpoints:**
  - `results/data/phase10_admissibility/corpus_expansion_status.json`
  - `results/data/phase10_admissibility/stage2_data_inventory.json`
  - `results/data/phase10_admissibility/illustration_features_machine.json`
  - `results/data/phase10_admissibility/cross_linguistic_manifest_machine.json`
  - `results/data/phase10_admissibility/method_g_text_illustration.json`
  - `results/data/phase10_admissibility/method_i_cross_linguistic.json`
  - `results/data/phase10_admissibility/stage2_summary.json`
  - `results/reports/phase10_admissibility/PHASE_10_STAGE2_RESULTS.md`
  - `results/data/phase10_admissibility/stage2_execution_status.json`

### 10.3 Execution Status (Stage 3 Priority Gate)

- **Status:** COMPLETE
- **Completed at:** 2026-02-18
- **Primary compute run ID:** `0259b6fc-88c3-87e9-fb89-50bb56136638`
- **Priority gate outcome:** `urgent`
  - Gate reason: Stage 1/2 contained non-strengthening signals, so Method F stayed high-priority.
- **Execution profile:** `target_tokens=30000`, `param_samples_per_family=10000`, `null_sequences=1000`, `perturbations_per_candidate=12`, `max_outlier_probes=12`, `null_block=[2,12]`, `symbol_alphabet_size=64`
- **Method F outcomes:**
  - Table-grille reverse search: `indeterminate` (`118` low-entropy outliers, `0` stable-natural)
  - Slot-logic reverse search: `indeterminate` (`109` low-entropy outliers, `0` stable-natural)
  - Constrained-Markov reverse search: `indeterminate` (`67` low-entropy outliers, `0` stable-natural)
  - Method F aggregate: `indeterminate`
- **Interpretation note:** Outliers below null-q01 were found in all families, but none survived perturbation stability with language-like profile requirements.
- **Artifacts:**
  - `results/data/phase10_admissibility/stage3_priority_gate.json`
  - `results/data/phase10_admissibility/method_f_reverse_mechanism.json`
  - `results/data/phase10_admissibility/stage3_summary.json`
  - `results/reports/phase10_admissibility/PHASE_10_STAGE3_RESULTS.md`
  - `results/data/phase10_admissibility/stage3_execution_status.json`

### 10.4 Execution Status (Stage 4 Synthesis)

- **Status:** COMPLETE
- **Completed at:** 2026-02-18
- **Primary compute run ID:** `3e0a6664-c39d-fb61-8064-e24fd8922d11`
- **Stage 4 synthesis outcome:**
  - Aggregate class: `mixed_results_tension`
  - Closure status: `in_tension`
  - Outcome counts: strengthened=`2` (H, I), weakened=`2` (J, K), indeterminate=`2` (G, F), defeated=`0`
- **Urgent designation interpretation (explicit):**
  - Priority gate remained `urgent` because Stage 1/2 had non-strengthening signals.
  - `urgent` is a scheduling/compute-priority flag for Method F, not a closure-defeat verdict.
- **Deliverables created:**
  - `results/reports/phase10_admissibility/PHASE_10_RESULTS.md`
  - `results/reports/phase10_admissibility/PHASE_10_CLOSURE_UPDATE.md`
- **Artifacts/checkpoints:**
  - `results/data/phase10_admissibility/stage4_synthesis.json`
  - `results/data/phase10_admissibility/stage4_execution_status.json`

### 10.5 Execution Status (High-ROI Confirmatory Reruns)

- **Status:** COMPLETE
- **Completed at:** 2026-02-18
- **Primary compute run ID:** `5f85586d-01fc-30c0-61f8-0f34e003c82a`
- **High-ROI gate config:** `configs/phase10_admissibility/stage5_high_roi_gate.json`
- **Method F robustness matrix:**
  - Gate pass: `True`
  - Matrix size: `12` runs (`seeds=[42,77,101]`, `windows=[30000,45000]`, `null_profiles=[local_block,wide_block]`)
  - Family outcomes across matrix: table-grille=`12/12 indeterminate`, slot-logic=`12/12 indeterminate`, constrained-Markov=`12/12 indeterminate`
  - Stable-natural violations: `0`
- **Strict J/K recalibration:**
  - Method J strict gate pass (stays weakened): `True`
  - Method K strict gate pass (stays weakened): `False`
  - Method K failure reason: mixed direction (`42=closure_weakened`, `77=indeterminate`, `101=closure_weakened`) and one seed below correlation threshold (`0.3998 < 0.4`)
- **Resolution gate outcome:**
  - Upgrade rule satisfied: `False`
  - Resolution class: `partial_resolution_inconclusive`
  - Recommendation: collect an independent adjudicating test family before any closure upgrade attempt.
- **Artifacts/checkpoints:**
  - `results/data/phase10_admissibility/stage5_method_f_matrix.json`
  - `results/data/phase10_admissibility/stage5_jk_recalibration.json`
  - `results/data/phase10_admissibility/stage5_high_roi_summary.json`
  - `results/reports/phase10_admissibility/PHASE_10_STAGE5_HIGH_ROI.md`
  - `results/data/phase10_admissibility/stage5_high_roi_status.json`

### Restart/Resume Checkpoints

- Canonical checkpoint file: `results/data/phase10_admissibility/stage1_execution_status.json`
- The Stage 1 runner is resume-aware and skips completed steps unless forced.
- Resume command:
  - `python scripts/phase10_admissibility/run_stage1_hjk.py`
- Canonical Stage 1b checkpoint file: `results/data/phase10_admissibility/stage1b_jk_replication_status.json`
- The Stage 1b runner is resume-aware and reuses completed per-seed artifacts before finalization.
- Stage 1b resume command:
  - `python scripts/phase10_admissibility/run_stage1b_jk_replication.py --seeds 42,77,101 --target-tokens 30000 --method-j-null-runs 100 --method-k-runs 100`
- Canonical Stage 2 checkpoint file: `results/data/phase10_admissibility/stage2_execution_status.json`
- The Stage 2 runner is resume-aware and reuses completed step artifacts unless forced.
- Stage 2 resume command:
  - `python scripts/phase10_admissibility/run_stage2_gi.py --scan-resolution folios_2000 --scan-fallbacks folios_full,tiff,folios_1000 --image-max-side 1400 --method-g-permutations 1000 --method-i-bootstrap 500 --method-i-min-languages 12 --language-token-cap 50000`
- Canonical corpus-expansion checkpoint file: `results/data/phase10_admissibility/corpus_expansion_status.json`
- Corpus-expansion resume command (machine extraction only):
  - `python -m tools.download_corpora --languages finnish,hungarian,vietnamese,mandarin,japanese --target-tokens 5000 --min-article-tokens 40 --min-final-tokens 2200 --batch-size 10 --max-batches 40 --sleep-seconds 0.4 --max-retries-per-batch 8 --retry-backoff-seconds 1.5 --status-path results/data/phase10_admissibility/corpus_expansion_status.json`
- Canonical Stage 3 checkpoint file: `results/data/phase10_admissibility/stage3_execution_status.json`
- Stage 3 resume command:
  - `python scripts/phase10_admissibility/run_stage3_f.py --target-tokens 30000 --param-samples-per-family 10000 --null-sequences 1000 --perturbations-per-candidate 12 --max-outlier-probes 12 --null-block-min 2 --null-block-max 12 --symbol-alphabet-size 64`
- Canonical Stage 4 checkpoint file: `results/data/phase10_admissibility/stage4_execution_status.json`
- Stage 4 resume command:
  - `python scripts/phase10_admissibility/run_stage4_synthesis.py`
- Canonical Stage 5 checkpoint file: `results/data/phase10_admissibility/stage5_high_roi_status.json`
- Stage 5 resume command:
  - `python scripts/phase10_admissibility/run_stage5_high_roi.py --gate-config configs/phase10_admissibility/stage5_high_roi_gate.json`
