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
- Results stored in `results/data/phase10_/<method_name>.json`
- Run copies in `results/data/phase10_/by_run/<artifact>.<run_id>.json`

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
- `results/reports/phase10_/PHASE_10_RESULTS.md`
- `results/reports/phase10_/PHASE_10_CLOSURE_UPDATE.md`

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
