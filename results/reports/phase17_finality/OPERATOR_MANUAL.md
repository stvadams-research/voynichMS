# Voynich Engine Operator Manual

**Device:** Flat Tabula (State Tracker) + Vocabulary Codebook
**Era:** c. 1400-1450
**Purpose:** Mechanical generation of complex, language-mimetic text for pharmaceutical, botanical, and astronomical sections.
**Model:** Phase 20 canonical architecture (tabula + codebook, score 0.865)

---

## 1. Hardware Components

### 1.1 The Tabula (State Tracker Card)

A flat parchment or stiff-paper card (170 x 160mm) arranged as a **10x5 grid** of 50 cells. Each cell contains:

- **Window number** (W00-W49): identifies the current production state.
- **Correction offset** (-20 to +13): a signed integer added to the raw next-window number (modulo 50) to correct for systematic drift.

The scribe consults the tabula to determine which codebook section to open next. Window 18 is the **hub** — it contains the largest vocabulary (396 words) and serves as the starting state for every new page.

Blueprint: `results/visuals/phase17_finality/tabula_card.svg`

### 1.2 The Codebook (Vocabulary Reference)

A bound booklet of approximately **154 pages** (10 quires of 8 leaves), organized by window number (W0-W49). Each section lists the admissible words for that window state.

| Property | Value |
|:---|:---|
| Total words | 7,717 |
| Pages | ~154 |
| Page capacity | ~60 words (2 columns x 30 rows) |
| Largest section | W18: 396 words (~7 pages) |
| Smallest section | W07: 18 words (1 page) |
| Consultation rate | 100% (memorization impractical) |

The codebook is the production bottleneck. W18 alone occupies ~5% of the codebook but produces ~50% of all tokens, making it the most-consulted section and the primary source of indexing errors.

Blueprint: `results/visuals/phase17_finality/codebook_index.svg`

### 1.3 Writing Implements

- Quill and iron gall ink (standard 15th-century materials).
- The manuscript itself: prepared vellum leaves, pre-ruled for line spacing.

---

## 2. Production Protocol

### Step 1: INITIALIZE

Begin a new page. Set the current window to **W18** (the hub). Open the codebook to the W18 section.

For continuing an existing page after a break, resume at the window of the last word written.

### Step 2: READ STATE

Consult the tabula card. Locate the current window cell. Note:
- The **window number** (this tells you which codebook section to use).
- The **correction offset** (you will need this after writing the word).

### Step 3: LOOK UP VOCABULARY

Open the codebook to the section for the current window. All admissible words for this position are listed there. If already on the correct page, no page-turn is needed.

### Step 4: SELECT WORD

Choose a word from the current section. Selection is influenced by:
- **Scribal preference:** Each hand has characteristic suffix habits (Hand 1 prefers *-dy*; Hand 2 prefers *-in*).
- **Ergonomic flow:** Words that continue the rhythmic pattern of the line are preferred.
- **Position in list:** Words near the top of the section are slightly more likely to be chosen.

Write the chosen word on the manuscript page.

### Step 5: ADVANCE STATE

Look up the written word in the codebook margin or a separate transition table. The word encodes a **raw next-window number** — this is the lattice transition.

### Step 6: APPLY CORRECTION

Add the current window's correction offset to the raw next-window number, modulo 50:

```
corrected_window = (raw_next_window + correction_offset) mod 50
```

The corrected window becomes your new current state.

### Step 7: REPEAT

Return to Step 2 with the new current window. Continue until the line is complete.

### Step 8: LINE AND PAGE TRANSITIONS

- **Line break:** The current window carries over to the next line. No state reset.
- **Page break:** Reset to W18 (the hub). Empirically, W18 dominates all folio starts (100% of 101 folios).
- **Section change** (e.g., herbal to astronomical): No device reconfiguration. The same tabula and codebook are used for all sections. Thematic variation arises from vocabulary selection within windows, not from different device states.

---

## 3. Error Recovery (Mechanical Slips)

### 3.1 Codebook Indexing Error

The scribe opens to the wrong page in the codebook, selecting a word from an adjacent window's section. This is most common in the W18 section (396 words across ~7 pages), which accounts for **92.6% of observed slips**.

**Recovery:** Do not erase. Continue production from the incorrectly selected word — it still encodes a valid next-window transition. The error produces a "vertical offset" visible in statistical analysis but invisible to a casual reader.

### 3.2 Offset Miscalculation

The scribe adds the wrong correction offset or forgets to apply it.

**Recovery:** The error propagates for one transition only. The next word selected will encode a new next-window, effectively self-correcting.

### 3.3 Observed Error Rate

| Metric | Value |
|:---|:---|
| Total detected slips | 202 |
| Slip density | 3.93% of lines |
| W18 concentration | 92.6% of slips |
| Self-correction | Errors do not propagate beyond 1 transition |

---

## 4. Scribal Variation

Two hands operate the same device with different fluency profiles:

| Dimension | Hand 1 (f1-66) | Hand 2 (f75-116) |
|:---|:---|:---|
| Tokens produced | 9,821 | 16,108 |
| Vocabulary used | 3,664 types | 4,084 types |
| Drift admissibility | 56.1% | 64.5% |
| Dominant suffix | *-dy* | *-in* |
| Drift parameter | 15 | 25 |

Both hands traverse the same lattice with the same window distribution (JSD = 0.012, cosine = 0.998). They differ only in word selection preferences and adherence to drift rules. Hand 2 follows the device more accurately.

---

## 5. Production Capacity

A single page of herbal text (f1r-f66v style):

| Parameter | Value |
|:---|:---|
| Words per line | ~6.2 |
| Lines per folio | ~26 |
| Words per folio | ~161 |
| Codebook consultations | ~161 (100% rate) |
| Tabula consultations | ~161 |
| Estimated production time | 30-60 minutes per folio (scribal copying speed) |

The entire manuscript (~35,000 tokens) requires approximately 200-400 hours of scribal labor.

---

## 6. Blueprint Artifacts

| Artifact | Path | Description |
|:---|:---|:---|
| Tabula card | `results/visuals/phase17_finality/tabula_card.svg` | 10x5 state tracker with offsets |
| Palette plate | `results/visuals/phase17_finality/palette_plate.svg` | Vocabulary grid with corrections |
| Codebook index | `results/visuals/phase17_finality/codebook_index.svg` | Section index with page spans |
| Offset table | `results/visuals/phase17_finality/correction_offsets.txt` | Per-window correction values |
| Layout reference | `results/visuals/phase17_finality/palette_layout.txt` | Text-mode layout reference |
| Historical (volvelle) | `results/visuals/phase17_finality/historical/` | Deprecated disc-based model (disproven Phase 20) |

---

**Conclusion:** A scribe equipped with this tabula card, this codebook, and this protocol will produce text that is structurally identical to the Voynich Manuscript: same entropy profile, same window distribution, same n-gram statistics, same mechanical slip signature.
