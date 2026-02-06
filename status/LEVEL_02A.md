# Level 2A – Text Ledger (Geometry-First)

**Status**: COMPLETED
**Date Completed**: 2026-02-06

## Goals
- Make text-like content queryable without assuming glyph identity.
- Establish a persistent ledger for segmentation and transcription alignment.

## Deliverables
- [x] Database Schema Expansion (Lines, Words, Glyphs, Transcriptions, Alignments)
- [x] Transcription Ingestion (`voynich transcription ingest`, `EVAParser`)
- [x] Segmentation Infrastructure (`LineSegmenter`, `WordSegmenter`, `GlyphSegmenter`)
- [x] Dummy Segmenter (for pipeline verification)
- [x] Alignment Engine (`AlignmentEngine` for line/word matching)
- [x] Query Interface (`voynich query token`, `voynich query word`)

## Verification
- [x] Query: transcription token → image instances.
- [x] Query: word → glyph candidate instances.
- [x] Alignment uncertainty is explicit (scores, types).
- [x] Acceptance demo passed (ingest -> segment -> align -> query).
