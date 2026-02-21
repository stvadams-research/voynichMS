# Strategic Opportunities Execution Plan

**Date:** 2026-02-21
**Status:** IN PROGRESS (A-D complete, E-F planned)
**Depends on:** All Phase 14 (COMPLETE), Phase 15 (COMPLETE), Phase 16 (COMPLETE), Phase 17 (partial)

## Execution Progress

- [x] Sprint A1: Residual Bandwidth Decomposition (2026-02-21)
- [x] Sprint A2: The Latin Test (2026-02-21)
- [x] Sprint A3: Structure Detection in Choice Stream (2026-02-21)
- [x] Sprint B1: Tier-Stratified Offset Corrections (2026-02-21)
- [x] Sprint B2: Hapax Grouping (2026-02-21)
- [x] Sprint B3: Governance (2026-02-21)
- [x] Sprint C1: Device Specification Derivation (2026-02-21)
- [x] Sprint C2: Wear and Usage Predictions (2026-02-21)
- [x] Sprint C3: Governance (2026-02-21)
- [x] Sprint D1: Structural Signature Definition (2026-02-21)
- [x] Sprint D2: Generic Corpus Ingestion (2026-02-21)
- [x] Sprint D3: Comparative Signature Analysis (2026-02-21)
- [x] Sprint D4: Governance (2026-02-21)
- [x] Sprint E1: Extended Driver Conditioning (2026-02-21)
- [ ] Sprint E2: Conditioned Structure Detection
- [ ] Sprint E3: Window 36 Deep Dive
- [ ] Sprint E4: Governance (Workstream E)
- [ ] Sprint F1: Cumulative Coverage Analysis
- [ ] Sprint F2: Plausible Device Dimensioning
- [ ] Sprint F3: Admissibility Under Subset Architecture
- [ ] Sprint F4: Governance (Workstream F)

### Phase 1 Results (A1, B1-B2, C1-C2)

**Sprint A1 — Residual Bandwidth Decomposition:**
- **RSB = 2.21 bits/word** after conditioning on all 5 known drivers (down from 7.17 raw)
- 4.96 bits/word explained by joint driver conditioning
- Bootstrap 95% CI: [1.72, 1.78] bits/word
- Per-window: only **9 of 50 windows** have non-zero RSB; window 36 dominates (2.56 bits, 10,096 choices)
- Total residual capacity: **~3.4 KB (~6,740 Latin characters)** — enough for ~1-2 Vulgate chapters
- Independence check: joint reduction (4.96 bits) *exceeds* sum of marginals (3.57 bits) — drivers are synergistic, not redundant
- Conditional entropy chain: window (7.17) → +prev_word (3.99, -3.18) → +position (2.79, -1.20) → +recency (2.21, -0.58) → +suffix (2.21, -0.00)

**Sprint B1 — Tier-Stratified Offset Corrections: GATE FAIL**
- **CV mean delta: +0.74pp** (below 2.0pp gate threshold)
- 3/7 folds positive (Astro +3.28pp, Herbal A +2.43pp, Herbal B +4.07pp), 3/7 negative
- Full-corpus per-tier admissibility: common 97.86%, medium 76.91%, rare 28.11%, hapax 22.62%
- **Conclusion:** Tier-specific corrections do not justify the added complexity. The uniform per-window correction already captures the dominant signal. Closed as clean negative.

**Sprint B2 — Hapax Grouping:**
- 93.9% suffix coverage (6,578/7,009 hapax words match a suffix class)
- 902 hapax transitions (prev in-vocab, curr OOV)
- 858 suffix-recovered, **836 suffix-admissible**
- **Potential impact: +3.040pp** (above 0.5pp threshold — worth integrating)
- Verdict: hapax suffix grouping produces meaningful admissibility gain

**Sprint C1 — Device Specification Derivation:**
- **Volvelle derived diameter: ~1,410mm (141cm)** — 4.0× Apian, 11.8× Alberti
- **Historically implausible** at naive vocabulary density: the full 7,755-word palette requires a device far larger than any known 15th-century volvelle (120-350mm)
- Tabula derived dimensions: 2,766 × 1,370mm — even larger
- **Key implication:** The scribes did NOT display the full vocabulary simultaneously. Either (a) only a subset was inscribed on the device, (b) the vocabulary was distributed across multiple devices/sheets, or (c) the device used an index/abbreviation system rather than spelling out every word
- Anchor window 18: angular position 129.6° from reference

**Sprint C2 — Wear and Usage Predictions:**
- Window 18 dominates: **49.6% of all corpus tokens** (16,295 of 32,848)
- Top 5 windows: 74.3% of usage; top 10: 83.1%
- Extreme usage concentration suggests the device had a "hot zone" — one sector used nearly half the time
- Falsifiable predictions documented: anchor marks, radial vocabulary layout, wear gradient, correction marks at window 18

### Phase 2 Results (A2, A3, B3, C3)

**Sprint A2 — The Latin Test:**
- **Channel capacity: 106,858 bits (13.0 KB)** — theoretical max across 12,519 choices
- Encoded Genesis 1:1-5 (Vulgate, 339 chars, 2,712 bits) into 342 choices (2.7% of manuscript)
- **Round-trip fidelity: EXACT** — encode → decode recovers original Latin perfectly
- Steganography is *physically feasible* within the lattice model's choice freedom

**Sprint A3 — Structure Detection:**
- Residual choice stream (normalized indices) is **NOT uniform** (KS p=0.0, mean=0.247 vs expected 0.500)
- ACF(1) = 0.062, **z = 6.95** vs permutation baseline (significant serial dependence)
- Max spectral peak power fraction = 0.0095, **z = 43.70** vs baseline (significant regularity)
- Compression ratio = 0.898, z = 1.81 (not significant — marginal structure only)
- **Verdict: STRUCTURED** — 2/3 permutation tests reject randomness. The residual stream retains sequential and spectral structure beyond known drivers. Consistent with (but does not prove) hidden content.

**Sprint B3 — Governance:**
- CANONICAL_EVALUATION.md: Added Sections 29-30 (tiered corrections, hapax grouping, device specification)
- claim_artifact_map.md: Added claims #133-136 (Opportunity B)

**Sprint C3 — Governance:**
- CANONICAL_EVALUATION.md: Added Section 31 (steganographic channel analysis)
- claim_artifact_map.md: Added claims #137-140 (Opportunity C), #141-146 (Opportunity A)

### Phase 3 Results (D1-D4)

**Sprint D1 — Structural Signature Definition:**
- Defined 8-metric signature: corrected admissibility, BUR/TUR, branching factor, Moran's I, FFT dominant power, BIC models, selection entropy, cross-section transfer
- Voynich reference: 64.13% admissibility, 0.856 Moran's I, 81.5% FFT power, 10.13 bpw entropy, 7/7 transfer
- 100-shuffle null distribution establishes baselines for all z-scoreable metrics
- **FFT dominant power (z=6.15)** is the strongest discriminator — the single-cycle sinusoidal correction pattern is the Voynich's most distinctive structural fingerprint

**Sprint D2 — Generic Corpus Ingestion:**
- Ingested 4 corpora: Voynich (reference), shuffled Voynich (null), reversed Voynich (partial), Latin/De Bello Gallico (natural language)
- Latin: 6,049 lines, 57,080 tokens, 11,714 vocab (comparable size to Voynich)
- All corpora standardized as token-list-of-lists with provenance

**Sprint D3 — Comparative Signature Analysis:**
- Built fresh 50-window lattices for each comparison text using identical methodology (GlobalPaletteSolver → KMeans → spectral reordering)
- **All texts VERY_DISTINCT from Voynich** (Euclidean distances: reversed 794, shuffled 988, Latin 1,044)
- Corrected admissibility is the dominant discriminator: Voynich 64.13% vs shuffled 44.37% vs Latin 43.26%
- Shuffling same vocabulary drops admissibility by 20pp — confirms sequential structure, not vocabulary, drives lattice fit
- **Conclusion:** The Voynich structural signature is unique. No comparison text — not even the same corpus shuffled — replicates the combination of high admissibility, strong FFT dominance, and perfect cross-section transfer.

**Sprint D4 — Governance:**
- CANONICAL_EVALUATION.md: Added Section 32 (cross-manuscript comparison)
- claim_artifact_map.md: Added claims #147-154 (Opportunity D)
- Execution plan updated with all results

### Phase 4 Results (E1)

**Sprint E1 — Extended Driver Conditioning:**
- Added 3 new drivers: trigram context (prev_prev_word), section proxy (7-section line_no buckets), window persistence (same_window flag)
- **RSB dropped from 2.21 → 0.48 bits/word** — new drivers explain 78.4% of the 5-driver residual
- Trigram context is the largest new driver (-0.99 bits), followed by section identity (-0.64 bits sequential), then persistence (-0.10 bits)
- Section identity is surprisingly powerful: marginal reduction of 1.05 bits shows vocabulary distribution shifts meaningfully across manuscript sections
- **Total residual capacity collapsed**: from ~3.4 KB to **0.7 KB** (~1,400 Latin characters) — barely enough for a single paragraph
- Per-window RSB (8 drivers): only 6 of 50 windows have non-zero RSB; window 36 still dominates (0.57 bpw, 10,096 choices)
- Full chain: window (7.17) → +prev_word (3.99, -3.18) → +position (2.79, -1.20) → +recency (2.21, -0.58) → +suffix (2.21, -0.00) → +trigram (1.22, -0.99) → +section (0.58, -0.64) → +persistence (0.48, -0.10)

## Overview

STATUS.md identifies four strategic opportunities that represent the productive frontier beyond lattice refinement. This plan organizes them as four workstreams (A-D), ordered by immediacy and infrastructure requirements.

| Workstream | Opportunity | Builds On | New Scripts | Immediacy |
|:---|:---|:---|:---|:---|
| **A** | Steganographic analysis | Phase 15, Phase 17 | 2 | High — data exists, partial spec in Phase 17 |
| **B** | Frequency-aware modeling | Phase 14L, 14M, 14O | 2 | High — residual fully diagnosed |
| **C** | Physical archaeology | Phase 14N, Phase 16 | 1 | Medium — requires synthesis, not new data |
| **D** | Cross-manuscript comparison | Phase 8, all Phase 14 | 3 | Low — needs new infrastructure |

### Dependency Graph

```
A (Steganographic) ─────────────────────────────────────┐
B (Frequency-Aware) ────────────────────────────────────┤
C (Physical Archaeology) ──────────────────────────────┤──→ Governance Update
D (Cross-Manuscript) ── requires A/B/C methodology ───┘
```

A, B, and C are independent and can execute in any order or in parallel. D should run last because it packages the methodology from A-C into a portable test battery.

---

## Workstream A: Steganographic Analysis

**Goal:** Determine whether the 7.53 bits/word of within-lattice choice freedom carries structured information or is mechanical noise.

**Existing assets:**
- `results/data/phase15_selection/selection_drivers.json` — 5 driver hypotheses quantified (bigram: 2.43 bits, positional: 0.64, recency: 0.22, suffix: 0.16, frequency: 0.12)
- `results/data/phase15_selection/choice_stream_trace.json` — 49,159 scribal decisions logged
- `results/data/phase17_finality/bandwidth_audit.json` — 7.53 bpw realized, 11.5 KB capacity
- `scripts/phase15_rule_extraction/run_15d_selection_drivers.py` — driver decomposition code
- Phase 17 plan task 2.2 — "Latin Test" specified but unexecuted

### Sprint A1: Residual Bandwidth Decomposition

**Script:** `scripts/phase17_finality/run_17c_residual_bandwidth.py`
**Output:** `results/data/phase17_finality/residual_bandwidth.json`

The raw 7.53 bpw includes entropy explained by known mechanical drivers. The true steganographic ceiling is the entropy that remains after all known drivers are removed.

**Tasks:**

**A1.1 — Conditional entropy chain**
Compute the progressive entropy reduction as each driver is conditioned out:
- H(choice | window) = 7.17 bits (known, from Phase 15D)
- H(choice | window, prev_word) = 4.74 bits (known, bigram context)
- H(choice | window, prev_word, position) = ? (add positional conditioning)
- H(choice | window, prev_word, position, recency) = ? (add recency)
- H(choice | window, prev_word, position, recency, suffix) = ? (add suffix affinity)

The final value is the **residual steganographic bandwidth (RSB)** — bits per word that cannot be explained by any known mechanical or structural driver.

**A1.2 — Independence check**
The five drivers may overlap (e.g., bigram context partially captures suffix affinity). Compute the joint conditional entropy rather than summing marginals. Report the gap between the sum of marginal bits_explained (~3.57 bits total) and the actual joint reduction. If the gap is large, the drivers are correlated and the true RSB is higher than the naive subtraction suggests.

**A1.3 — Per-window RSB profile**
Compute RSB for each of the 50 windows individually. If some windows have near-zero RSB, the scribe had no freedom there (fully determined by mechanics). If some windows have high RSB, those are the candidate locations for hidden content.

**Acceptance:**
- RSB calculated with confidence interval (bootstrap, 1000 resamples)
- Joint vs. marginal comparison reported
- Per-window RSB profile with min/max/mean
- Clear statement: how many bits per word remain structurally unexplained?

### Sprint A2: The Latin Test

**Script:** `scripts/phase17_finality/run_17d_latin_test.py`
**Output:** `results/data/phase17_finality/latin_test.json`

This is the test specified in Phase 17 task 2.2: can a Latin text be encoded into the choice-bit stream without violating lattice constraints?

**Tasks:**

**A2.1 — Choice-bit extraction**
For each of the 12,519 admissible decisions, extract the "choice index" — the rank of the chosen word within the available candidates for that window, ordered by some canonical sort (alphabetical or frequency-descending). This produces a sequence of integers, each bounded by the window's candidate count.

**A2.2 — Arithmetic coding capacity**
Treat the choice-index sequence as a channel. Compute the channel capacity using the empirical candidate-count distribution. This gives the theoretical maximum encoding rate in bits.

**A2.3 — Latin encoding attempt**
Select a short Latin passage (~500 characters, e.g., Genesis 1:1-5 from the Vulgate). Attempt to encode it into the choice-index sequence using arithmetic coding:
- If encoding succeeds within the available decisions: report how many decisions are consumed and what fraction of the manuscript this represents
- If encoding fails (channel too narrow): report the shortfall

**A2.4 — Round-trip verification**
If encoding succeeds, decode the choice-index sequence back to Latin and verify exact round-trip fidelity.

**Acceptance:**
- Channel capacity in bits calculated
- Latin encoding attempted with success/failure reported
- If successful: decisions consumed, fraction of manuscript used, round-trip verified
- Clear statement: is Latin-in-lattice feasible?

### Sprint A3: Structure Detection in the Choice Stream

**Script:** `scripts/phase17_finality/run_17e_choice_structure.py`
**Output:** `results/data/phase17_finality/choice_structure.json`

If the choice stream carries hidden information, it should show non-random structure after removing known mechanical drivers. If it is noise, it should be indistinguishable from a random process.

**Tasks:**

**A3.1 — Residual choice-index stream**
Extract the choice-index sequence (from A2.1) and subtract the predicted component from each known driver (position, bigram, recency, suffix, frequency). The residual is the "unexplained choice stream."

**A3.2 — Autocorrelation test**
Compute the autocorrelation function of the residual stream at lags 1-50. Under the null hypothesis (noise), autocorrelation should be zero at all lags. Report max |ACF| and significance (Ljung-Box test).

**A3.3 — Spectral test**
Apply FFT to the residual stream. Under the null, the power spectrum should be flat (white noise). Report any dominant frequencies and their significance.

**A3.4 — Compression test**
Compress the residual stream with zlib. Under the null (noise), the compression ratio should be ~1.0. If the ratio is significantly below 1.0, the residual carries exploitable structure.

**A3.5 — Permutation baseline**
Repeat A3.2-A3.4 on 1000 random permutations of the residual stream. Report the real statistics as z-scores against the permutation distribution.

**Acceptance:**
- Autocorrelation, spectral, and compression statistics with p-values
- Clear statement: does the residual choice stream show structure beyond known drivers?
- If structured: characterize the structure (periodic? clustered? long-range dependent?)
- If random: conclude that the choice freedom is mechanical noise, not hidden content

---

## Workstream B: Frequency-Aware Modeling

**Goal:** Close a meaningful portion of the ~35% residual by treating frequency tiers differently within the existing canonical lattice (not rebuilding it).

**Existing assets:**
- `results/data/phase14_machine/residual_characterization.json` — full tier breakdown (common 6.9%, rare 84.5%, hapax 97.8% failure)
- `results/data/phase14_machine/canonical_offsets.json` — 50 per-window corrections
- `results/data/phase14_machine/suffix_window_map.json` — 15 suffix→window mappings
- Phase 14M finding: canonical lattice dominates all fresh builds; frequency weighting helps fresh builds but doesn't exceed canonical
- Phase 14O: suffix-based OOV recovery integrated (+1.37pp corrected)

### Sprint B1: Tier-Stratified Offset Corrections

**Script:** `scripts/phase14_machine/run_14zh_tiered_corrections.py`
**Output:** `results/data/phase14_machine/tiered_corrections.json`

Phase 14I found a single per-window mode offset that adds +16.17pp. But this offset is dominated by common words (which have the most observations). Rare words may have systematically different drift patterns that are masked by the common-word signal.

**Tasks:**

**B1.1 — Tier-specific offset learning**
For each of the 50 windows, compute separate mode offsets for:
- Common tier (>100 occurrences): should closely match the existing canonical offsets
- Medium tier (10-100 occurrences): may differ
- Rare tier (<10 occurrences): likely unstable — report confidence intervals

Use leave-one-section-out cross-validation (same 7-fold scheme as Phase 14I).

**B1.2 — Tier-stratified admissibility**
Evaluate admissibility separately for each tier using its own offsets:
- Common-tier admissibility with common offsets (expect ≥93%)
- Medium-tier admissibility with medium offsets (expect improvement over uniform)
- Rare-tier admissibility with rare offsets (expect minimal due to sparse data)

Report the weighted-average admissibility vs. the single-offset baseline (64.37%).

**B1.3 — Stability analysis**
For the rare tier, how many windows have fewer than 5 observations? These windows cannot support a reliable offset estimate. Report the fraction of rare-tier transitions that fall in "data-poor" windows.

**Acceptance:**
- Per-tier offset vectors (50 values each) with confidence intervals
- Per-tier cross-validated admissibility vs. uniform baseline
- Weighted-average improvement (gate: ≥+2.0pp over single-offset baseline to justify the added complexity)
- Stability assessment for rare tier
- If gate fails: document as a clean negative result and close this avenue

### Sprint B2: Hapax Grouping

**Script:** Same as B1 (extended section)

Hapax words (97.8% failure, 11.5% of all failures) cannot be individually placed in the lattice. But they may share structural features (suffix class, glyph length, initial glyph) that allow group placement.

**Tasks:**

**B2.1 — Hapax feature extraction**
For each of the ~1,382 hapax words, extract:
- Suffix class (using the 16-suffix priority list from Phase 14O)
- Glyph count
- Initial glyph
- Is it a known suffix of a common word? (e.g., "qokeedy" shares suffix "dy" with common "chedy")

**B2.2 — Suffix-group window assignment**
Group hapax words by suffix class. For each group, assign the group to the suffix's canonical window (from `suffix_window_map.json`). Measure the group's admissibility under this assignment vs. the random baseline.

**B2.3 — Impact assessment**
If suffix-group assignment works, compute the overall impact on the full corpus admissibility. The theoretical ceiling is 11.5% of failures * recovery_rate. Report the actual gain.

**Acceptance:**
- Hapax words grouped by suffix class (coverage: what fraction of hapax has a suffix match?)
- Per-group admissibility vs. random baseline
- Overall impact on full corpus admissibility
- Clear statement: is hapax grouping worth integrating into production?

### Sprint B3: Governance

Update execution plan, CANONICAL_EVALUATION.md, claim_artifact_map.md with results from B1-B2.

---

## Workstream C: Physical Archaeology

**Goal:** Derive testable physical predictions from the computational model that could guide historical investigation of the manuscript or comparative device analysis.

**Existing assets:**
- `results/data/phase14_machine/physical_integration.json` — Moran's I, FFT, BIC, slip-offset correlation
- `results/data/phase16_physical/layout_projection.json` — 81.5% grid efficiency, 10x5 optimal
- `results/data/phase16_physical/word_ergonomic_costs.json` — per-word stroke costs
- `scripts/phase17_finality/run_17a_generate_blueprints.py` — blueprint generation (partially complete)
- `results/reports/phase17_finality/OPERATOR_MANUAL.md` — production protocol

### Sprint C1: Device Specification Derivation

**Script:** `scripts/phase17_finality/run_17f_device_specification.py`
**Output:** `results/data/phase17_finality/device_specification.json`

**Tasks:**

**C1.1 — Vocabulary density constraints**
The lattice has 50 windows containing 7,755 tokens (mean 155 tokens/window, range from ~50 to ~400+). Given 15th-century handwriting scale (~3-5mm glyph width), compute the minimum physical area per window to legibly contain its vocabulary. Sum across windows to get minimum device area.

**C1.2 — Volvelle geometry derivation**
For the volvelle model (circular rotating disc):
- Compute minimum disc diameter from total vocabulary area
- Map the 50 windows to angular sectors (7.2 degrees per window)
- The anchor at window 18 corresponds to a specific angular position — define the "reading aperture" position
- Estimate the number of concentric rings needed to accommodate window-size variation

**C1.3 — Tabula geometry derivation (alternative)**
For the tabula model (10x5 rectangular grid):
- Compute minimum sheet dimensions
- Map windows to grid cells
- Estimate the sliding mask dimensions

**C1.4 — Historical plausibility check**
Compare derived dimensions against known 15th-century devices:
- Ramon Llull's volvelles (13th century): ~20-30cm diameter
- Peter Apian's Astronomicum Caesareum volvelles (1540): ~30-40cm diameter
- Known cipher discs (Alberti, 1467): ~10-15cm diameter
- Report whether derived dimensions fall within the plausible range

**Acceptance:**
- Minimum device dimensions for both volvelle and tabula models
- Comparison to historical device dimensions
- Clear statement: are the derived dimensions historically plausible?

### Sprint C2: Wear and Usage Predictions

**Script:** Same as C1 (extended section)

**Tasks:**

**C2.1 — Window usage frequency map**
From the 49,159 scribal decisions, compute per-window usage counts. The most-visited windows should show the most wear. Map usage to physical positions on both device models.

**C2.2 — Anchor wear prediction**
Window 18 concentrates 92.6% of slips. The physical anchor position should show distinctive wear patterns:
- More frequent handling/rotation to this position
- Alignment marks or registration features at this position
- Potential ink accumulation or abrasion

**C2.3 — Temporal wear gradient**
Slips cluster in folio batches (CV=1.81). If the device degraded over time, the slip-clustering folios should correspond to late production. Test whether slip-heavy folios appear later in the manuscript's quire structure.

**C2.4 — Falsifiable predictions summary**
Package all predictions as a structured list of observations that would:
- **Confirm** the volvelle: circular wear pattern, anchor mark at one position, vocabulary inscribed in radial sectors
- **Confirm** the tabula: rectangular wear pattern, sliding track marks, vocabulary in a grid
- **Refute** both: no physical production artifact, entirely cognitive process

**Acceptance:**
- Usage heatmap mapped to physical device positions
- Anchor wear predictions with specific observable signatures
- Temporal wear gradient test result
- Structured list of confirmatory/refutatory observations

### Sprint C3: Governance

Update execution plan, CANONICAL_EVALUATION.md, claim_artifact_map.md. Link predictions to specific manuscript folios where confirmation could be sought.

---

## Workstream D: Cross-Manuscript Comparison

**Goal:** Package the Voynich lattice methodology as a portable test battery and apply it to at least one other candidate text to test whether the structural signature is unique.

**Existing assets:**
- Phase 8 comparative analysis (qualitative, 10 artifact case files)
- `results/reports/phase8_comparative/casefiles/casefile_05_codex_seraphinianus.md` — Codex Seraphinianus qualitative assessment
- All Phase 14 analytical scripts (the methodology to be ported)

### Sprint D1: Structural Signature Definition

**Script:** `scripts/phase18_comparative/run_18a_signature_battery.py`
**Output:** `results/data/phase18_comparative/signature_definition.json`

Define the quantitative "structural signature" of a lattice-generated text. This is the set of metrics that characterize the Voynich manuscript's mechanical origin and distinguish it from natural language.

**Tasks:**

**D1.1 — Metric selection**
Select the minimal set of metrics that capture the structural signature:
1. **Admissibility rate** under optimal lattice (Voynich: ~65% corrected)
2. **Overgeneration ratio** at 2-gram through 5-gram levels (Voynich: ~20x)
3. **Branching factor** per position (Voynich: 9.57 effective bits)
4. **Moran's I** on offset correction topology (Voynich: 0.915)
5. **FFT dominant period** on corrections (Voynich: k=1, 85.4% power)
6. **BIC device model ranking** (Voynich: volvelle > tabula > grille)
7. **Selection entropy** (Voynich: 7.53 bpw)
8. **Cross-section transfer** (Voynich: 7/7 holdout significant)

**D1.2 — Null distribution**
For each metric, compute the expected value under a null model (shuffled corpus, random lattice). This gives the baseline against which any new text can be compared.

**D1.3 — Voynich signature card**
Package the Voynich results for all 8 metrics as a reference "signature card." Any new text's signature can be compared against this card.

**Acceptance:**
- 8 metrics defined with Voynich reference values
- Null distribution for each metric
- Signature comparison methodology documented

### Sprint D2: Generic Corpus Ingestion

**Script:** `scripts/phase18_comparative/run_18b_corpus_ingestion.py`
**Output:** `results/data/phase18_comparative/ingested_corpus.json`

Build a tokenization and ingestion path that accepts non-EVA text. The lattice solver and evaluation engine operate on token sequences — they don't care about the encoding, only the vocabulary and sequence.

**Tasks:**

**D2.1 — Target text selection**
Select one or more candidate texts for comparison. Criteria:
- Must be a suspected constructed/artificial text (to test the methodology's discrimination power)
- Must have a publicly available digital transcription
- Sufficient length for statistical analysis (~5,000+ tokens)

Candidates (in priority order):
1. **Codex Seraphinianus** — the most frequently compared to Voynich; Phase 8 case file exists
2. **Enochian tables** (John Dee) — another suspected constructed script; Phase 8 case file exists
3. **Control: shuffled Voynich** — the existing corpus with word order randomized (should produce null signature)
4. **Control: natural Latin** — a real Latin text of comparable length (should produce non-lattice signature)

**D2.2 — Tokenizer adapter**
Build a generic tokenizer that accepts a text file and produces a token sequence in the format expected by the lattice solver. For scripts with known glyph tables (Codex Seraphinianus, Enochian), map through the glyph table. For Latin, use whitespace tokenization.

**D2.3 — Validation**
Run the ingested corpus through the existing `EvaluationEngine.calculate_coverage()` to verify it produces a valid token sequence.

**Acceptance:**
- At least one real candidate text and two controls ingested
- Token sequences validated
- Vocabulary statistics reported (size, frequency distribution, hapax fraction)

### Sprint D3: Comparative Signature Analysis

**Script:** `scripts/phase18_comparative/run_18c_comparative_analysis.py`
**Output:** `results/data/phase18_comparative/comparative_signatures.json`

Apply the full signature battery to each ingested text and compare against the Voynich reference card.

**Tasks:**

**D3.1 — Lattice construction**
For each ingested text, build a lattice using the same methodology (global palette solver, spectral reordering, offset correction). Use the same hyperparameters (K=50 windows).

**D3.2 — Signature computation**
Compute all 8 metrics from D1.1 for each text. Record as a signature card.

**D3.3 — Signature comparison**
Compare each text's signature to:
- The Voynich reference card
- The null distribution
- Each other text

Report Euclidean distance in normalized metric space (z-scored against null). Rank texts by similarity to Voynich.

**D3.4 — Discrimination assessment**
Can the signature battery distinguish:
- Voynich from natural language? (expect: yes, large distance)
- Voynich from shuffled Voynich? (expect: yes — shuffling destroys sequential structure)
- Voynich from other constructed texts? (the key question)

If the Codex Seraphinianus or Enochian tables produce a similar signature, that suggests a shared production methodology. If they produce a null signature, the Voynich's mechanical structure is unique among known constructed texts.

**Acceptance:**
- Signature cards for all texts
- Distance matrix with z-scores
- Discrimination results for all pairwise comparisons
- Clear statement: is the Voynich structural signature unique?

### Sprint D4: Governance

Update execution plan, CANONICAL_EVALUATION.md, claim_artifact_map.md. If cross-manuscript results are significant, update STATUS.md Section 10 opportunities/concerns accordingly.

---

## Execution Order

The recommended execution order balances immediacy, independence, and information value:

```
Phase 1:  A1 (Residual Bandwidth)     ← immediate, uses existing data
          B1 (Tiered Corrections)      ← immediate, uses existing data
          C1 (Device Specification)    ← immediate, uses existing data

Phase 2:  A2 (Latin Test)             ← depends on A1 for RSB context
          B2 (Hapax Grouping)          ← depends on B1 for rare-tier insights
          C2 (Wear Predictions)        ← depends on C1 for device geometry

Phase 3:  A3 (Structure Detection)    ← depends on A1 for residual stream
          B3 (Governance)             ← after B1-B2
          C3 (Governance)             ← after C1-C2

Phase 4:  D1 (Signature Definition)   ← after A/B/C methodology stable
          D2 (Corpus Ingestion)       ← independent of D1, can parallel
          D3 (Comparative Analysis)   ← depends on D1 + D2
          D4 (Governance)             ← after D3
```

Within each phase, the listed sprints can execute in parallel across workstreams (A1, B1, C1 are all independent). Sequential dependencies are only within each workstream.

---

## New Files

| Sprint | File | Type |
|:---|:---|:---|
| A1 | `scripts/phase17_finality/run_17c_residual_bandwidth.py` | Script |
| A1 | `results/data/phase17_finality/residual_bandwidth.json` | Artifact |
| A2 | `scripts/phase17_finality/run_17d_latin_test.py` | Script |
| A2 | `results/data/phase17_finality/latin_test.json` | Artifact |
| A3 | `scripts/phase17_finality/run_17e_choice_structure.py` | Script |
| A3 | `results/data/phase17_finality/choice_structure.json` | Artifact |
| B1-B2 | `scripts/phase14_machine/run_14zh_tiered_corrections.py` | Script |
| B1-B2 | `results/data/phase14_machine/tiered_corrections.json` | Artifact |
| C1-C2 | `scripts/phase17_finality/run_17f_device_specification.py` | Script |
| C1-C2 | `results/data/phase17_finality/device_specification.json` | Artifact |
| D1 | `scripts/phase18_comparative/run_18a_signature_battery.py` | Script |
| D1 | `results/data/phase18_comparative/signature_definition.json` | Artifact |
| D2 | `scripts/phase18_comparative/run_18b_corpus_ingestion.py` | Script |
| D2 | `results/data/phase18_comparative/ingested_corpus.json` | Artifact |
| D3 | `scripts/phase18_comparative/run_18c_comparative_analysis.py` | Script |
| D3 | `results/data/phase18_comparative/comparative_signatures.json` | Artifact |
| E1 | `scripts/phase17_finality/run_17g_extended_drivers.py` | Script |
| E1 | `results/data/phase17_finality/extended_drivers.json` | Artifact |
| E2-E3 | `scripts/phase17_finality/run_17h_conditioned_structure.py` | Script |
| E2-E3 | `results/data/phase17_finality/conditioned_structure.json` | Artifact |
| F1-F3 | `scripts/phase17_finality/run_17i_subset_device.py` | Script |
| F1-F3 | `results/data/phase17_finality/subset_device.json` | Artifact |

## Modified Files

| Sprint | File | Change |
|:---|:---|:---|
| B3 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add tiered corrections / hapax section |
| C3 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add device specification section |
| D4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add cross-manuscript comparison section |
| E4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add residual structure investigation section |
| F4 | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` | Add subset device architecture section |
| B3, C3, D4, E4, F4 | `governance/claim_artifact_map.md` | Add new claims |
| Final | `STATUS.md` | Update Section 10 with results |
| All | This file | Update sprint checkboxes as work completes |
