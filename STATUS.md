# Where We Stand — Project Status

**Updated:** 2026-02-22
**Phase:** Post-analysis (mechanical reconstruction complete, publication generated)

---

## 1. The text is constructively generable — with context-dependent drift confirmed

A deterministic 50-window lattice maps 7,717 tokens (94.93% of the ZL corpus vocabulary) into a sequential constraint system where word(n) determines window(n+1).

**What "generable" actually means:**
- **43.44%** of token transitions are admissible under strict ±1 drift (memoryless baseline)
- **64.94%** under per-window mode offset correction + suffix-based OOV recovery (canonical rate, cross-validated)
- **57.73%** under extended ±3 drift
- **53.91%** with oracle per-line mask inference (upper bound for mask-based models)

The per-window offset correction (Phase 14I) + suffix recovery (Phase 14O) produces the canonical 64.94% rate with only 50 parameters. The correction transfers across sections (negative overfitting gap: -4.6pp), confirming a genuine structural property.

The model captures **roughly two-thirds** of sequential transitions under its best cross-validated configuration. The remaining third is structural, context-dependent, and dominated by rare-vocabulary effects.

## 2. The system is layered — confirmed by ablation

Multiple interacting constraint families are required:

| Layer | Admissibility | What it adds |
|:---|---:|:---|
| Random baseline (50 windows) | ~2% | Chance adjacency |
| Lexicon clamp (full vocab) | ~20% | Pre-reordering lattice structure |
| Spectral reordering | 43.44% | +23pp — sequential access optimization |
| Global mask offset | 45.91% | +2.5pp — single-parameter rotation |
| Window-level offset correction | ~64% | +18pp — context-dependent drift (cross-validated) |
| + Suffix OOV recovery | 64.94% | +0.96pp — hapax/OOV resolution |

Each layer captures a distinct structural property. Second-order context adds only +0.50pp (below the 2pp significance gate) — the system is first-order Markov at the window level.

## 3. The traversal is nondeterministic — confirmed and quantified

The constraint space is deterministic but the path through it branches freely:
- **0% word-level overgeneration** (lexicon clamp: only real words are generable)
- **~20× overgeneration at all n-gram orders** (2-gram: 24.1×, 3-gram: 21.9×, 4-gram: 21.3×, 5-gram: 19.9×)
- **Per-position branching factor: 761.7 candidates** (9.57 effective bits)
- **Within-window selection entropy:** 7.17 bits per choice (12,519 recorded choices)

The manuscript is one valid traversal. The constraint space admits ~20× more at every sequential order.

## 4. The remaining gap is diagnosed — frequency-dominated

**~35% of token transitions are not admissibly reached** under the canonical model. The residual has been fully characterized (Phase 14L):

| Frequency Tier | Total | Failures | Rate | Share of All Failures |
|:---|---:|---:|---:|---:|
| Common (>100 occ.) | 11,634 | 798 | **6.9%** | 6.8% |
| Medium (10-100) | 8,683 | 3,050 | 35.1% | 25.9% |
| Rare (<10) | 7,761 | 6,561 | **84.5%** | 55.8% |
| Hapax (1 occ.) | 1,382 | 1,351 | **97.8%** | 11.5% |

Low-frequency words account for **67.3% of all failures** despite being only 31% of transitions. Common words succeed at >93%. The ~35% residual is overwhelmingly a vocabulary frequency effect, not a missing constraint family.

## 5. Meaning is structurally bounded — not eliminated

Steganographic bandwidth analysis (Phase 17): **7.53 bits/word** of choice freedom within the lattice, yielding total capacity of **~11.5 KB (~23K Latin characters)** across the full corpus. The "Latin Test" (Phase 17, Opportunity A) confirmed:
- RSB = 2.21 bits/word of residual steganographic bandwidth
- A Latin Vulgate passage can be encoded within the lattice constraints
- Steganographic feasibility is confirmed but not proven

What this means:
- High-density linguistic meaning (natural language) is structurally unlikely — the entropy profile is wrong
- Efficient cipher is structurally unlikely — the per-word bandwidth is low
- **But absolute absence of meaning cannot be proven** — 7.53 bits/word is enough for a sparse code

## 6. The physical device is a flat tabula + codebook — NOT a volvelle

**This section is substantially revised from 2026-02-21.** Phase 20 (9 sprints) systematically tested all physically plausible device architectures and reached a definitive conclusion.

### The volvelle problem

Early phases (14N) identified sinusoidal offset correction topology (Moran's I = 0.915, FFT k=1 captures 85.4% of power) suggesting a circular rotating device. However, Phase 20 proved that **all disc-based device forms are physically implausible** due to the angular sector bottleneck:

- **50 angular sectors at 7.2° each** require minimum 549mm diameter even for a state-only indicator with no vocabulary
- State machine + codebook hybrid: still 549mm for the state disc alone
- **Every volvelle configuration exceeds the Apian range (350mm)**

The sinusoidal topology is consistent with a **circular organizational principle** (windows numbered in circular order) but does not require a physical rotating disc. A flat tabula laid out in circular window order produces the same topological signature.

### The 15-state merged volvelle exception

State merging (Phase 20, Sprint 3) found that reducing 50 windows to 15 states produces a viable 193mm disc (within the Llull range). Two configurations meet both size (≤350mm) and admissibility (≥55%) thresholds:

| Strategy | States | Diameter | Drift Admissibility |
|:---|---:|---:|---:|
| Size-based merge | 15 | 193mm | 56.84% |
| Correction-based merge | 15 | 193mm | 55.93% |

However, this requires merging 35 of 50 windows — a fundamental simplification that may not be historically defensible.

### The recommended architecture

Phase 20, Sprint 4 ranked 5 non-circular device forms:

| Rank | Device | Max Dim | Combined Score | Verdict |
|:---|:---|---:|---:|:---|
| 1 | **Tabula + codebook** | **170mm** | **0.865** | **PLAUSIBLE** |
| 2 | Folding tabula (annotated) | 170mm | 0.840 | PLAUSIBLE |
| 3 | Folding tabula (state-only) | 170mm | 0.833 | PLAUSIBLE |
| 4 | Sliding strip (10-fold) | 160mm | 0.713 | PLAUSIBLE |
| 5 | Cipher grille | 170mm | 0.590 | MARGINAL |

**The recommended production tool is a flat tabula card (170×160mm, 10×5 grid) paired with a separate vocabulary codebook (154 pages, ~10 quires).** This has direct historical parallels in Alberti's cipher disc + external alphabet (1467) and Trithemius's key table + word codebook (1499).

### The complete production model

| Component | Specification |
|:---|:---|
| State tracker | Flat tabula card, 170×160mm, 10×5 grid of window labels + corrections |
| Vocabulary reference | Codebook, 154 pages organized by window number |
| Traversal | 50-window lattice with per-window corrections |
| Consultation rate | 100% (annotation impractical — W18 has 396 words producing 49.6% of tokens) |
| Error model | Slips concentrate at W18 (92.6% of observed slips), consistent with codebook-indexing errors in the largest section |

### Manuscript organization

The manuscript shows **no codebook-like organization** (Phase 20, Sprint 6):
- All 101 folios have W18 as dominant window (100%)
- Within-section similarity ≈ between-section similarity (p=1.00)
- Folio order is independent of window order (Spearman ρ = -0.013)

Every folio is produced by the same device traversal process. Thematic variation arises from section-specific vocabulary selection within windows, not from different device configurations.

## 7. Two scribes use the same device with different fluency profiles

Phase 20, Sprint 8 tested whether the two scribal hands (Currier Hand 1: f1-66, Hand 2: f75-84 + f103-116) use the production device differently:

| Dimension | Finding | Detail |
|:---|:---|:---|
| Window profiles | SIMILAR | JSD=0.012, cosine=0.998 |
| Vocabulary overlap | LOW | 15.6% shared types, but 66-72% shared token coverage |
| Drift admissibility | **SIGNIFICANTLY DIFFERENT** | H1=56.1%, H2=64.5% (z=-13.60, p≈0) |
| Suffix preference | DIFFERENT | H1: -dy dominant, H2: -in dominant |

**Verdict: SPECIALIST PROFILES.** Both hands traverse the same 50-window lattice with the same window distribution, but they differ in:
- Which words they select from each window (low vocabulary overlap)
- How accurately they follow the drift rules (H2 is 8.5pp better)
- Which suffixes they prefer

This is consistent with two scribes operating the same physical tool with individual "fluency" — different familiarity with codebook sections, different motor habits producing different drift rates.

## 8. What is not yet proven — all analytical questions closed

All six open questions identified at Phase 14 are now closed:

| Question | Resolution | Phase |
|:---|:---|:---|
| Minimality of 50 windows | MDL optimal K=3-7; K=50 over-specified but structurally maximal | 14H |
| Overgeneration rate | ~20× at all n-gram orders through 5-grams | 14H |
| Branching factor | 761.7 candidates/position = 9.57 effective bits | 14H |
| Description length efficiency | Lattice wins MDL by 2.12 BPT under corrected encoding | 14H |
| Full failure taxonomy | 93.6% wrong-window, context-dependent, mask-unrecoverable | 14H |
| Holdout robustness | 7/7 leave-one-section-out splits significant (mean z=29.1σ) | 14H |

**No remaining analytical gaps threaten the model's validity.**

## 9. What this does not tell you

- **Author intent:** The model is agnostic. Medical reference, philosophical exercise, hoax, and devotional artifact could all produce this structure.
- **Hoax vs. intellectual artifact:** The constraint system is equally consistent with deliberate deception and sincere production ritual.
- **Absolute absence of meaning:** 7.53 bits/word is enough for sparse encoding. The model bounds capacity but cannot prove emptiness.
- **Whether the residual carries information:** ~35% of transitions are unexplained. If the residual is structured, it could contain information the model doesn't capture.
- **Physical existence of the tool:** The model specifies the tool's functional requirements. Whether a specific artifact survives is an archaeological question outside the analysis scope.

## 10. Open paths

### Phase 17 — COMPLETE (2026-02-22)
All 4 tasks finished: blueprints (tabula model), bandwidth audit, operator manual, research monograph.

### Cleanup — COMPLETE (5/5 tasks)
- ~~Hardcoded /reports/ path audit~~ — all paths correct
- ~~Phase 5 data cleanup~~ — already clean
- ~~Post-cleanup architecture review~~ — 7 missing `__init__.py` added to src/ submodules
- ~~Phase 1 report consolidation~~ — no action needed (findings in CANONICAL_EVALUATION + monograph)
- ~~Phase 2 planning standardization~~ — YAML frontmatter added to 2.3/2.4

### Publication pipeline
- Validate replication process (fresh repo pull)
- Zenodo retag + documentation
- arXiv submission

## 11. Project quantitative summary

| Metric | Value |
|:---|:---|
| Phases completed | 20 (Phases 1-8, 10-20) |
| CANONICAL_EVALUATION sections | 44 |
| Verified claims (claim_artifact_map) | 251 |
| Strategic opportunity sprints | 27 (workstreams A-H, all complete) |
| Phase 20 sprints | 12 (all complete) |
| Corpus tokens analyzed | 32,852 |
| Lattice vocabulary | 7,717 words across 50 windows |
| Canonical admissibility | 64.94% (corrected + suffix recovery) |
| Physical device specification | Flat tabula 170×160mm + 154pp codebook |
| Scribal hands characterized | 2 (H1: 9,821 tokens, H2: 16,108 tokens) |

### Phase completion status

| Phase | Topic | Status |
|:---|:---|:---|
| 1-8 | Foundation through Comparative | COMPLETE |
| 10 | Admissibility retest | COMPLETE |
| 11 | Stroke topology | COMPLETE |
| 12 | Mechanical reconstruction | COMPLETE |
| 13 | Interactive demonstration | COMPLETE |
| 14 | Voynich Engine (15 sub-phases) | COMPLETE |
| 15 | Rule extraction & selection drivers | COMPLETE |
| 16 | Physical grounding & ergonomics | COMPLETE (null ergonomic result) |
| 17 | Physical synthesis & monograph | COMPLETE |
| 18 | Cross-manuscript comparative | COMPLETE |
| 19 | Sequence alignment | COMPLETE |
| 20 | State machine codebook architecture | COMPLETE |

### Key artifacts

| Artifact | Path |
|:---|:---|
| Canonical evaluation (44 sections) | `results/reports/phase14_machine/CANONICAL_EVALUATION.md` |
| Claim-artifact map (251 claims) | `governance/claim_artifact_map.md` |
| Production model specification | `results/reports/phase20_state_machine/PRODUCTION_MODEL.md` |
| Phase 20 execution plan | `planning/phase20_state_machine/phase_20_execution_plan.md` |
| Opportunities execution plan (27 sprints) | `planning/opportunities_execution_plan.md` |
| Operator manual | `results/reports/phase17_finality/OPERATOR_MANUAL.md` |
| Tabula card blueprint | `results/visuals/phase17_finality/tabula_card.svg` |
| Codebook index | `results/visuals/phase17_finality/codebook_index.svg` |
| Research monograph (full) | `results/publication/Voynich_Structural_Identification_Full.docx` |
| Research summary | `results/publication/Voynich_Research_Summary.docx` |
| Formal specification | `results/reports/phase14_machine/FORMAL_SPECIFICATION.md` |
