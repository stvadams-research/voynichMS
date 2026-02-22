# 10c. The Production Model

## 10c.1 From Emulation to Specification

Phases 10-14 identified *what* the production mechanism is and proved it can reproduce the manuscript's statistical properties. Phases 15-20 answer the remaining questions: *how* was it physically implemented, what are the production rules, and what form did the device take?

## 10c.2 Declarative Rule Extraction (Phase 15)

Phase 15 formalized the implicit lattice into a set of explicit, declarative production rules — the "DNA" of the Voynich engine. Using the full corpus, 7,717 rules were extracted (one per word type), each specifying a word's window assignment, its encoded next-window transition, and the contextual factors that influence its selection.

The dominant production driver is **bigram context**: the identity of the previous word contributes 2.43 bits of information to the next word's selection. This is followed by suffix bias (hand-specific suffix preferences) and positional constraints (position within the line).

| Driver | Information (bits) |
|:---|:---|
| Bigram context | 2.43 |
| Suffix bias | 1.2-1.8 (hand-dependent) |
| Positional constraint | 0.5-0.8 |
| Window constraint (lattice) | 9.57 (effective branching factor) |

The rules are deterministic at the window level (each word maps to exactly one next-window) but stochastic at the selection level (multiple words are admissible at each position, and the scribe's choice among them introduces the variance that makes each page unique).

## 10c.3 Physical Grounding (Phase 16)

Phase 16 tested whether the abstract lattice model is consistent with 15th-century physical production constraints.

### Ergonomic Modeling

The central ergonomic test was whether scribal effort correlates with page complexity. If the scribe were composing (choosing words for meaning), effort should vary with content density. If the scribe were operating a device, effort should be approximately uniform.

The result was a **null correlation**: Spearman rho = -0.0003 (p = 0.9926). Scribal effort is completely independent of page complexity. This is consistent with a mechanical process that imposes uniform effort regardless of content — the scribe performs the same sequence of operations (consult tabula, open codebook, select word, write, advance state) on every page.

### Grid Layout Efficiency

The 10x5 window layout was tested for geometric optimization. If the lattice transitions favor physically adjacent windows, the layout is optimized for ergonomic traversal.

Grid layout efficiency: **81.50% improvement over random layout**. The window arrangement is not arbitrary — it is optimized so that the most common transitions correspond to short physical distances on the device. This is consistent with a device designer who arranged the windows to minimize the scribe's hand movement.

## 10c.4 The Meaning Boundary (Phase 17)

Phase 17 addressed the most persistent question about the Voynich Manuscript: does the text carry hidden meaning?

### Steganographic Bandwidth

The lattice provides scribal choice at each position — the scribe selects one word from the current window's vocabulary. This choice freedom represents a potential information channel: if a meaning-encoding rule governed the selection, the text could carry hidden content.

| Metric | Value |
|:---|:---|
| Realized bandwidth | 7.53 bits per word |
| Admissible decisions | 12,519 |
| Total capacity | 11.5 KB (~23,000 Latin characters) |
| Steganographic threshold | 3.0 bits per word |

The realized bandwidth of 7.53 bits per word exceeds the 3.0-bit steganographic threshold, meaning the lattice has *sufficient* capacity for sparse encoding. The total capacity of 11.5 KB could contain approximately 23,000 characters of Latin text — roughly 4-5 chapters of the Vulgate.

### The Latin Test

To test whether the capacity is practically usable, a Latin Vulgate passage (Genesis 1:1-5, 339 characters) was encoded within the lattice constraints. The encoding succeeded: 342 of 12,519 admissible choices were sufficient to encode the passage, with a residual steganographic bandwidth of 2.21 bits per word.

**Verdict:** Steganographic feasibility is confirmed but not proven. The lattice has enough capacity for sparse encoding (verified by the Latin test), but high-density natural language is structurally unlikely given the entropy profile. The model bounds capacity but cannot prove the absence of hidden content.

## 10c.5 State Machine Architecture (Phase 20)

The final phase addressed the most concrete question: what physical form did the production device take?

### Candidate Evaluation

Phase 20 systematically evaluated all plausible physical implementations of the 50-window lattice:

| Candidate | Physical Size | Admissibility | Score | Verdict |
|:---|:---|---:|---:|:---|
| Flat tabula + codebook | 170 x 160mm | 64.94% | 0.865 | **RECOMMENDED** |
| 15-state merged volvelle | 193mm disc | 56.84% | 0.875 | Viable but incoherent |
| 10-state merged volvelle | 162mm disc | 44.36% | 0.817 | Too lossy |
| 50-state volvelle | 410mm disc | 64.94% | 0.620 | Physically implausible |

The volvelle (rotating disc) hypothesis — initially favored due to the sinusoidal offset correction topology — was systematically ruled out. A 50-state volvelle would require a 410mm disc, which exceeds all known 15th-century examples. Merging states to reduce the disc size destroys vocabulary coherence (Jaccard similarity = 0.000 for all merged states), making the merged discs functionally useless.

### The Tabula + Codebook

The recommended architecture is a flat tabula (state tracker card) paired with a vocabulary codebook:

- **Tabula:** A 170 x 160mm parchment card with a 10x5 grid. Each cell contains a window number (0-49) and its correction offset. The scribe uses this card to track which codebook section to consult next.

- **Codebook:** A bound booklet of approximately 154 pages (10 quires), organized by window number. Each section lists the admissible words for that window state. Window 18 alone occupies ~7 pages (396 words) and produces ~50% of all corpus tokens.

This architecture has direct historical parallels:
- **Alberti cipher disc (1467):** A 120mm rotating disc with 24 letter positions — a state tracker for polyalphabetic substitution.
- **Trithemius tabula recta (1508):** A flat reference table paired with word codebooks for steganographic encoding.
- **Llull Ars Magna (c.1305):** A 200mm combinatorial disc with 9-16 positions — a state machine for generating logical propositions.

The Voynich system is most similar to Trithemius's architecture: a flat reference table paired with a codebook organized by state. The key difference is scale — 50 states and 7,717 words versus Trithemius's simpler systems.

### Reconciliation with Sinusoidal Topology

The sinusoidal offset correction pattern (Moran's I = 0.915), initially interpreted as evidence for a rotating disc, is reconciled by the observation that a tabula laid out in circular window order would produce the same topological signature. The organizational principle is circular, but the physical form need not be a rotating disc — a flat card with windows numbered in a circular order produces identical results.

## 10c.6 The Complete Production Workflow

Consolidating all findings, the Voynich Manuscript was produced as follows:

1. **The scribe sits with two reference objects:** a flat tabula card (170 x 160mm) and a vocabulary codebook (154 pages).
2. **To begin a page:** Set the current window to W18 (the hub). Open the codebook to the W18 section.
3. **For each word:** Consult the tabula for the current window's correction offset. Open the codebook to the current window's section. Select a word (influenced by hand-specific suffix preference and ergonomic flow). Write the word on the manuscript. Look up the written word to determine the raw next-window. Apply the correction offset (modulo 50). The corrected window becomes the new current state.
4. **At line boundaries:** The current window carries over. No state reset.
5. **At page boundaries:** Reset to W18.
6. **Errors (mechanical slips):** Concentrate at W18 because its codebook section is the largest. Do not erase — the error self-corrects within one transition.

Two scribes operated the same device with different fluency profiles. Both traverse the same lattice with the same window distribution; they differ only in word selection preferences and accuracy. The entire manuscript (~35,000 tokens) required approximately 200-400 hours of scribal labor.
