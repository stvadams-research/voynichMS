# Data Sources and Reproduction Guide

This document catalogs every external data file required by the project that is **not committed to the repository** (per `.gitignore`). A contributor who clones this repo must obtain these files before running the analysis pipeline.

---

## 1. Voynich Manuscript Scans (Yale / Beinecke MS 408)

High-resolution digital scans of the Voynich Manuscript, held by the Beinecke Rare Book & Manuscript Library at Yale University.

| Detail | Value |
|--------|-------|
| **Catalog page** | <https://collections.library.yale.edu/catalog/2002046> |
| **IIIF manifest** | <https://collections.library.yale.edu/manifests/2002046> |
| **Full PDF** | <https://collections.library.yale.edu/pdfs/2002046.pdf> |
| **OAI metadata** | <https://collections.library.yale.edu/catalog/oai?verb=GetRecord&metadataPrefix=oai_mods&identifier=oai:collections.library.yale.edu:2002046> |
| **License** | Public domain (manuscript dated c. 1404–1438) |

### Expected local layout

```
data/raw/
├── VoynichMS_Yale-2002046.pdf          # ~115 MB — full manuscript PDF
└── scans/
    ├── tiff/                            # ~7.0 GB — 217 full-resolution TIFF scans
    │   ├── 100r_1006248.tif
    │   ├── ...
    │   └── 9v_1006093.tif
    └── jpg/
        ├── folios_1000/                 # ~60 MB — 213 JPEGs (1000 px width)
        ├── folios_2000/                 # ~210 MB — 209 JPEGs (2000 px width)
        └── folios_full/                 # ~550 MB — 209 JPEGs (full resolution)
```

### How to obtain

1. **PDF**: Download directly from the Yale catalog link above.
2. **TIFF / JPEG scans**: The IIIF manifest URL above returns a JSON document listing every canvas and its image URLs. You can use any IIIF-compatible downloader (e.g. `iiif-dl`, or a simple script that walks the manifest) to batch-download TIFF or JPEG renditions. JPEGs at different widths can be requested via IIIF Image API size parameters (e.g. `/full/1000,/0/default.jpg`).

---

## 2. IVTFF Transliteration Files

Machine-readable transcriptions of the Voynich text in the Interlinear Voynich Transcription File Format (IVTFF 2.0), using the Extensible Voynich Alphabet (EVA).

| Detail | Value |
|--------|-------|
| **Source** | Voynich Manuscript Transliteration Archive |
| **Maintained by** | René Zandbergen & Gabriel Landini |
| **Website** | <https://www.voynich.nu/transcr/> |
| **Format** | IVTFF 2.0 (plain-text, EVA alphabet) |
| **Citation** | Zandbergen, R., & Landini, G. (2024). *The Voynich Manuscript Transliteration Archive*. |

### Expected local layout

```
data/raw/transliterations/ivtff2.0/
├── CD2a-n.txt       # 130 KB — Currier / D'Imperio
├── FG2a-n.txt       # 265 KB — Friedman Group
├── GC2a-n.txt       # 315 KB — Glen Claston
├── IT2a-n.txt       # 342 KB — Interim
├── RF1b-er.txt      # 342 KB — Rene / Friedman
├── VT0e-n.txt       # 335 KB — Voynich Transcription
└── ZL3b-n.txt       # 412 KB — Zandbergen / Landini (PRIMARY)
```

### How to obtain

Download the IVTFF files from the transliteration archive at <https://www.voynich.nu/transcr/>. The seven files above cover the major independent transcription efforts. `ZL3b-n.txt` (Zandbergen-Landini) is used as the primary source throughout the analysis.

---

## 3. External Corpora (Project Gutenberg)

Matched-length natural-language texts used as semantic baselines and comparative controls in Phase 4 (Inference Admissibility). All sourced from [Project Gutenberg](https://www.gutenberg.org/) and in the public domain.

### 3a. Latin corpus

| Detail | Value |
|--------|-------|
| **File** | `data/external_corpora/latin_corpus.txt` |
| **Contents** | *De Bello Gallico* by Julius Caesar (Books I–IV and V–VIII, concatenated) |
| **Gutenberg IDs** | [eBook #218](https://www.gutenberg.org/ebooks/218) and [eBook #18837](https://www.gutenberg.org/ebooks/18837) |
| **Purpose** | Semantic baseline — morphologically rich historical language |

### 3b. English corpus

| Detail | Value |
|--------|-------|
| **File** | `data/external_corpora/english.txt` |
| **Contents** | *Alice's Adventures in Wonderland* by Lewis Carroll |
| **Gutenberg ID** | [eBook #11](https://www.gutenberg.org/ebooks/11) |
| **Purpose** | Modern-language comparative baseline |

### 3c. German corpus

| Detail | Value |
|--------|-------|
| **File** | `data/external_corpora/german.txt` |
| **Contents** | *Die Verwandlung* (*The Metamorphosis*) by Franz Kafka |
| **Gutenberg ID** | [eBook #22367](https://www.gutenberg.org/ebooks/22367) |
| **Purpose** | Additional language comparative baseline |

### How to obtain

Download the plain-text UTF-8 versions from the Gutenberg URLs above and place them at the paths shown. No preprocessing is needed — the corpus builder (`scripts/phase4_inference/build_corpora.py`) handles tokenization.

### 3d. Phase 10 multilingual expansion corpora (machine-extracted)

Phase 10 Stage 2 follow-up adds additional typology coverage using automated extraction
from Wikipedia plaintext API endpoints (no manual tagging required).

Typical files produced under `data/external_corpora/`:

- `arabic.txt`
- `finnish.txt`
- `greek.txt`
- `hebrew.txt`
- `hungarian.txt`
- `japanese.txt`
- `mandarin.txt`
- `russian.txt`
- `turkish.txt`
- `vietnamese.txt`

Generation path:

```bash
python3 -m tools.download_corpora
```

Checkpoint artifact:

- `results/data/phase10_admissibility/corpus_expansion_status.json`

---

## 4. Derived / Generated Data (not committed)

The following are **generated by the pipeline** and do not need to be sourced externally. They are listed here for completeness, since they are also excluded from git.

| Path | Description | Generated by |
|------|-------------|--------------|
| `data/voynich.db` | SQLite database (~400 MB) — all transcriptions, segmentation, alignments | `scripts/phase1_foundation/populate_database.py` |
| `data/derived/` | Intermediate computed artifacts | Various phase scripts |
| `results/publication/` | Generated Word documents and publication drafts | `scripts/support_preparation/generate_publication.py` |
| `results/visuals/` | Generated visualization images | Visualization CLI |
| `runs/` | Experiment run logs | All phase runners |
| `core_status/` | Execution status and audit artifacts | All phase runners |

---

## 5. Quick-Start: Obtaining All Source Data

```bash
# 1. Clone the repository
git clone <repo-url> && cd voynichMS

# 2. Create the expected directory structure
mkdir -p data/raw/transliterations/ivtff2.0
mkdir -p data/raw/scans/tiff
mkdir -p data/raw/scans/jpg/{folios_1000,folios_2000,folios_full}
mkdir -p data/external_corpora

# 3. Download IVTFF transliterations from https://www.voynich.nu/transcr/
#    Place the 7 .txt files into data/raw/transliterations/ivtff2.0/

# 4. Download Yale PDF (optional, ~115 MB)
#    https://collections.library.yale.edu/pdfs/2002046.pdf
#    Save to data/raw/VoynichMS_Yale-2002046.pdf

# 5. Download scans via IIIF manifest (optional, ~7 GB for TIFFs)
#    https://collections.library.yale.edu/manifests/2002046

# 6. Download Project Gutenberg texts for external corpora
#    https://www.gutenberg.org/ebooks/218   → data/external_corpora/latin_corpus.txt
#    https://www.gutenberg.org/ebooks/18837  (append to latin_corpus.txt)
#    https://www.gutenberg.org/ebooks/11    → data/external_corpora/english.txt
#    https://www.gutenberg.org/ebooks/22367 → data/external_corpora/german.txt

# 7. Set up the environment and run the pipeline
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/support_preparation/replicate_all.py
```

---

## 6. Academic References

For the full bibliography of methodological sources (Montemurro, Rugg, Schinner, Timm, etc.) see `planning/support_preparation/content/13_references.md`.
