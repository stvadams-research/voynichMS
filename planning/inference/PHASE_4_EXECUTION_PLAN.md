# Phase 4 Execution Plan: Inference Admissibility Evaluation
**Project:** Voynich Manuscript, Structural Admissibility Program  
**Phase:** 4  
**Goal Type:** External method stress-testing, falsification, and boundary setting  
**Primary Goal:** Evaluate whether widely cited inference methods that imply language, semantics, or meaningful structure are actually diagnostic, by testing them against controlled non-semantic corpora that match Voynich-like structure.

---

## 1. Phase 4 Purpose and Core Question

### 1.1 Core question
Which published inference methods (statistical, network, topic-modeling, AI decipherment style) reliably distinguish semantic texts from non-semantic but structurally constrained texts, at Voynich scale?

### 1.2 What Phase 4 is not
- Not a translation attempt
- Not a new generative mechanism hunt
- Not an argument that any author is “wrong”
- Not a refutation campaign

Phase 4 evaluates inference methods, not people.

### 1.3 Success criteria
Phase 4 is successful if it produces:
- A method map showing what each inference technique can and cannot conclude
- A set of results showing whether those methods produce false positives on non-semantic controls that are structurally Voynich-like
- A small number of durable, reusable tests that future claims must pass

### 1.4 Primary outputs
- `reports/PHASE_4_METHOD_MAP.md`
- `reports/PHASE_4_RESULTS.md`
- `reports/PHASE_4_CONCLUSIONS.md`
- `results/phase_4/` containing run-linked tables, plots, and artifacts
- `src/inference_suite/` code modules implementing each method with strict provenance

---

## 2. Phase 4 Design Principles

### 2.1 Pre-registered intent
Every method test must be defined before running:
- What the method claims
- What the method measures
- What constitutes a false positive
- What constitutes a pass, fail, or indeterminate outcome

No post hoc redefinitions.

### 2.2 Separation of evidence types
Phase 4 distinguishes:
- Structural sufficiency: non-semantic processes can reproduce a signal
- Historical identification: this is how the manuscript was actually made

Phase 4 only addresses the first.

### 2.3 Control-first evaluation
A method is only considered evidence for semantics if it:
- Separates semantic texts from non-semantic structured texts
- Not just from random noise

---

## 3. Corpus Set, the Heart of Phase 4

Phase 4 is only as good as its corpus design. Use the same datasets across methods.

### 3.1 Required corpus families

#### A. Real Voynich corpora
- Primary transliteration used in earlier work
- Alternative transliterations for robustness checks, if practical

#### B. Semantic baseline corpora
A set of natural language corpora matched for:
- length
- segmentation into sections of similar size
- tokenization style similar to Voynich pipeline where feasible

#### C. Non-semantic structured corpora
These are the decisive controls.

Minimum set:
1) Self-citation style generation (Timm and Schinner family)
2) Table and grille style generation (Rugg, Zandbergen family)
3) Your Phase 3 generators that match repetition and locality constraints

Optional, high value:
4) Human-generated nonsense corpora, if obtainable and compatible with your pipeline

#### D. Negative controls
- Fully shuffled token order
- Fully shuffled within-section
- Random character-level baselines

### 3.2 Sectioning rules
Many methods rely on sections, topics, or partitions.
Define sectioning consistently:
- Equal-length bins, for example 20 bins
- Natural manuscript sections, if you have robust mappings
- Both, where feasible, because some methods are sensitive to partition definition

---

## 4. Method Targets and Test Modules

Phase 4 implements and tests a defined set of inference methods.

### 4.1 Method A: Montemurro and Zanette style information clustering
**Claim type:** Language-like topical structure via informative word distributions across sections.

**Implementation goal**
- Compute information per token about section identity across scales
- Replicate the curve shape and peak behavior
- Identify high-information tokens

**Key tests**
- False positive test: Do non-semantic structured corpora produce similar curves and peaks?
- Specificity test: Do semantic corpora produce curves distinct from non-semantic structured corpora?
- Sensitivity test: Do curves collapse under shuffling, as expected?

**Artifacts to record**
- Information vs scale curves
- Top N “keywords” per corpus
- Section distribution heatmaps for top tokens

**Decision rule**
- If non-semantic structured corpora routinely show similar information peaks and stable keyword lists, the method is not semantics-diagnostic.
- If Voynich is separable from all non-semantic structured corpora while semantic corpora cluster with Voynich, the method gains diagnostic credibility.

---

### 4.2 Method B: Amancio style network and multi-feature language-likeness
**Claim type:** Voynich word network metrics and distributions are compatible with natural language, incompatible with random text.

**Implementation goal**
Compute a stable feature set including:
- Zipf curve fit features
- Vocabulary growth features
- Word adjacency network metrics, degree distribution shape, clustering, assortativity
- Dispersion and intermittency measures

**Key tests**
- False positive test: Do non-semantic structured corpora fall in the “language-like” region?
- Robustness test: Are results stable under transliteration and variant handling?
- Discrimination test: Can a simple classifier separate semantic from non-semantic structured corpora better than chance?

**Artifacts to record**
- Feature tables per corpus
- PCA or similar projection for visualization, used only as descriptive aid
- Classifier performance with cross-validation, clearly separated train and test

**Decision rule**
- If features label non-semantic structured corpora as language-like, they are not semantics-diagnostic.
- If Voynich is closer to non-semantic structured corpora than to semantic corpora, it supports non-semantic admissibility.

---

### 4.3 Method C: Topic modeling claims tied to manuscript sections
**Claim type:** Topic models align with illustrated sections and scribal divisions, implying semantic linkage.

**Implementation goal**
- Implement LDA and one alternative model
- Evaluate topic coherence and alignment with known partitions

**Key tests**
- Partition susceptibility test: Do topic partitions align with any artificial section boundaries that you deliberately inserted into non-semantic corpora?
- Alignment significance test: Compare observed alignment to a null distribution from permuted labels
- False positive test: Does topic modeling yield convincing section alignment for non-semantic corpora with stable distribution differences?

**Artifacts to record**
- Topic composition summaries
- Section alignment scores and p-values from permutation tests
- Visualizations of topic prevalence per section

**Decision rule**
- If topic models readily align with non-semantic section boundaries, alignment is not strong evidence of semantics.
- If Voynich alignment is significantly stronger than all non-semantic controls and cannot be replicated by controlled sectioned gibberish, this may indicate a distinctive signal, but still not semantics by itself.

---

### 4.4 Method D: AI-assisted decipherment style claims, language ID under flexible transforms
**Claim type:** Under assumed transforms, Voynich matches a language and can be decoded.

**Implementation goal**
Do not chase full replication of any proprietary pipeline.
Instead test the inference pattern:
- Many languages tried
- Flexible transformations allowed
- A best match is declared

**Key tests**
- False positive test: Run the same “language match under transform” pipeline on known non-semantic corpora and measure how often it yields high-confidence language matches.
- Multiple comparisons control: quantify expected best-match scores under null corpora
- Sensitivity test: see if a small change in preprocessing flips the best match language

**Artifacts to record**
- Best language match distributions across many null corpora
- Confidence calibration curves
- Stability analysis of top results under small perturbations

**Decision rule**
- If null corpora frequently yield plausible-looking language matches and translations under flexibility, then such claims are not evidential without strong external validation.

---

### 4.5 Method E: Unsupervised morphology and grammar induction claims
**Claim type:** Voynich contains stable morphological operators, affixes, and syntax-like structure.

**Implementation goal**
- Apply unsupervised segmentation and morphology induction to:
  - Voynich
  - non-semantic structured corpora
  - semantic corpora

**Key tests**
- False morphology test: Do structured generators with prefix-suffix tables produce equally strong “morphological” structure?
- Comparative stability test: Are induced units consistent across sections, or do they reflect drift and mechanical constraints?

**Artifacts to record**
- Induced affix lists
- Segmentation stability scores
- Cross-section consistency measures

**Decision rule**
- If the same induction produces convincing morphology on non-semantic structured corpora, then morphology induction alone cannot imply semantics.

---

## 5. Run Structure, Provenance, and Reproducibility

Phase 4 must be run like a benchmark suite.

### 5.1 Canonical run template
Each method evaluation run must record:
- RunID
- corpus set and hashes
- method configuration
- code version, commit hash
- computed-only enforcement status
- output artifact list

### 5.2 Standard folder structure
- `configs/phase_4/` method configs
- `runs/phase_4/<run_id>/` immutable run artifacts
- `results/phase_4/` aggregated tables and plots derived from runs
- `reports/` narrative conclusions tied to RunIDs

### 5.3 Minimum test coverage before running Phase 4
- Enforcement tests pass
- Determinism tests pass on a small fixture
- Schema tests validate run artifact structure

No Phase 4 run begins until the foundation is green.

---

## 6. Execution Order and Timeline, bounded and finite

### 6.1 Stage 0: Method map, paper selection, and pre-registration
Deliverable:
- `reports/PHASE_4_METHOD_MAP.md`
Contents:
- method name
- core claim
- primary metrics
- required assumptions
- test plan and false positive definition

### 6.2 Stage 1: Corpus assembly and freezing
Deliverable:
- `data/corpora_manifest.json`
- `docs/CORPUS_CONSTRUCTION.md`

### 6.3 Stage 2: Implement modules, one method at a time
Priority order:
1) Montemurro and Zanette style info clustering
2) Amancio multi-feature and networks
3) Topic modeling and alignment testing
4) AI-style language ID under flexible transforms
5) Morphology and grammar induction

Rationale:
- Start with the most cited and most likely to generate false positives from structured controls.

### 6.4 Stage 3: Run the full benchmark suite
- Run each method on all corpora families
- Aggregate results into standard tables
- Generate a pass, fail, indeterminate label for each method

### 6.5 Stage 4: Synthesis and stopping
Deliverables:
- `reports/PHASE_4_RESULTS.md`
- `reports/PHASE_4_CONCLUSIONS.md`

Stop when:
- Each target method is tested against the full corpus set
- Robustness checks are complete
- You can clearly state what each method can and cannot infer

---

## 7. Interpretation Framework, what Phase 4 is allowed to conclude

### 7.1 Method outcome classes
For each method, assign exactly one:
- **Not diagnostic:** produces similar signals on non-semantic structured corpora
- **Partially diagnostic:** discriminates against random noise, but not against structured non-semantic
- **Conditionally diagnostic:** diagnostic only under constrained assumptions and validated controls
- **Potentially diagnostic:** separates Voynich from all tested non-semantic structured corpora, with robust significance testing

### 7.2 How Phase 4 narrows feasible theories
Phase 4 can conclude:
- Which inference methods are unreliable evidence for semantics
- Which signals remain distinctive after strong non-semantic controls
- Which claims in the literature rest on methods that fail falsification

Phase 4 cannot conclude:
- That Voynich has no meaning
- That any particular historical mechanism is true
- That any particular language is the plaintext

---

## 8. High-Impact Demonstrations for the Community

Phase 4 should include a small set of “headline” demonstrations that matter to readers.

Suggested demonstrations:
- A non-semantic structured corpus triggers Montemurro-style keyword clustering, showing semantic-like signals can arise from structure alone.
- Topic models align strongly with section labels in a deliberately sectioned non-semantic corpus, showing alignment is not proof of semantics.
- AI language identification under flexible transforms yields confident language matches on null corpora, showing multiple-comparisons risk.

Each demonstration must be backed by:
- controlled corpus design
- explicit null distributions
- RunIDs and code references

---

## 9. Phase 4 Deliverables Checklist

### Code deliverables
- `src/inference_suite/info_clustering/`
- `src/inference_suite/network_features/`
- `src/inference_suite/topic_models/`
- `src/inference_suite/lang_id_transforms/`
- `src/inference_suite/morph_induction/`
- Shared corpus loader and sectioning utilities

### Data and run artifacts
- Frozen corpus manifest
- Run manifests for each method and corpus
- Aggregated results tables

### Reports
- Method map
- Results
- Conclusions
- Non-claims and limitations

---

## 10. Phase 4 Termination Statement, pre-written

Phase 4 evaluates the inferential validity of methods commonly used to claim that the Voynich Manuscript contains meaningful language. By applying these methods to both the manuscript and to structurally similar non-semantic corpora with known ground truth, Phase 4 determines whether each method is semantics-diagnostic or susceptible to false positives. Phase 4 terminates when all selected methods are tested against the full corpus suite, robustness checks are complete, and the admissibility boundary for semantic inference is explicitly documented.

---

## 11. Immediate Next Actions
1) Freeze corpus set and write the corpus manifest
2) Write the method map document with pre-registered test rules
3) Implement Montemurro-style module first and run it on:
   - Voynich
   - self-citation control
   - shuffled control
4) Only then expand to the full benchmark suite
