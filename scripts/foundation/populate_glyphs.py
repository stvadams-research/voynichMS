#!/usr/bin/env python3
"""
Glyph Population Script

Derives glyph candidates from transcription tokens.
Each EVA character in a token becomes a glyph candidate.

This enables the GlyphPositionHypothesis to compute real entropy values.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

import uuid
from rich.console import Console
from rich.progress import Progress

from foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    LineRecord,
    WordRecord,
    GlyphCandidateRecord,
    GlyphAlignmentRecord,
    WordAlignmentRecord,
    TranscriptionTokenRecord,
)
from foundation.runs.manager import active_run
from foundation.core.id_factory import DeterministicIDFactory

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def populate_glyphs(dataset_id: str = "voynich_real", seed: int = 42):
    """
    Create glyph candidates from transcription tokens.

    For each word:
    1. Get the aligned transcription token
    2. Split token into individual characters
    3. Create a GlyphCandidateRecord for each character
    """
    store = MetadataStore(DB_PATH)
    session = store.Session()
    id_factory = DeterministicIDFactory(seed=seed)

    try:
        # Get all pages for the dataset
        pages = session.query(PageRecord).filter_by(dataset_id=dataset_id).all()

        if not pages:
            console.print(f"[red]No pages found for dataset: {dataset_id}[/red]")
            return

        console.print(f"Processing {len(pages)} pages from {dataset_id}")

        # Clear existing glyphs for this dataset's words
        page_ids = [p.id for p in pages]
        existing_glyphs = (
            session.query(GlyphCandidateRecord)
            .join(WordRecord, GlyphCandidateRecord.word_id == WordRecord.id)
            .join(LineRecord, WordRecord.line_id == LineRecord.id)
            .filter(LineRecord.page_id.in_(page_ids))
            .all()
        )

        if existing_glyphs:
            console.print(f"Clearing {len(existing_glyphs)} existing glyphs and alignments...")
            # First clear alignments (foreign key constraint)
            glyph_ids = [g.id for g in existing_glyphs]
            session.query(GlyphAlignmentRecord).filter(
                GlyphAlignmentRecord.glyph_id.in_(glyph_ids)
            ).delete(synchronize_session=False)
            # Then clear glyphs
            for g in existing_glyphs:
                session.delete(g)
            session.commit()

        total_glyphs = 0
        total_words = 0
        words_with_tokens = 0

        with Progress() as progress:
            task = progress.add_task("Creating glyphs...", total=len(pages))

            for page in pages:
                lines = session.query(LineRecord).filter_by(page_id=page.id).all()

                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).all()

                    for word in words:
                        total_words += 1

                        # Get aligned token
                        alignment = (
                            session.query(WordAlignmentRecord)
                            .filter_by(word_id=word.id)
                            .first()
                        )

                        if not alignment or not alignment.token_id:
                            continue

                        token = (
                            session.query(TranscriptionTokenRecord)
                            .filter_by(id=alignment.token_id)
                            .first()
                        )

                        if not token or not token.content:
                            continue

                        words_with_tokens += 1
                        token_content = token.content

                        # Get word bbox for deriving glyph bboxes
                        word_bbox = word.bbox or {"x": 0, "y": 0, "w": 100, "h": 30}
                        word_x = word_bbox.get("x", 0)
                        word_y = word_bbox.get("y", 0)
                        word_w = word_bbox.get("w", 100)
                        word_h = word_bbox.get("h", 30)

                        # Create glyph for each character
                        num_chars = len(token_content)
                        glyph_width = word_w / max(num_chars, 1)

                        for i, char in enumerate(token_content):
                            glyph_id = id_factory.next_uuid(f"glyph:{word.id}")

                            # Derive glyph bbox from word bbox
                            glyph_bbox = {
                                "x": word_x + (i * glyph_width),
                                "y": word_y,
                                "w": glyph_width,
                                "h": word_h,
                            }

                            glyph = GlyphCandidateRecord(
                                id=glyph_id,
                                word_id=word.id,
                                glyph_index=i,
                                bbox=glyph_bbox,
                                confidence=0.9,
                            )
                            session.add(glyph)

                            # Create glyph alignment with EVA character as symbol
                            alignment = GlyphAlignmentRecord(
                                glyph_id=glyph_id,
                                symbol=char,
                                score=1.0,
                            )
                            session.add(alignment)

                            total_glyphs += 1

                progress.update(task, advance=1)

                # Commit periodically
                if total_glyphs % 10000 == 0:
                    session.commit()

        session.commit()

        console.print(f"\n[bold green]Glyph Population Complete[/bold green]")
        console.print(f"  Pages processed: {len(pages)}")
        console.print(f"  Words processed: {total_words}")
        console.print(f"  Words with tokens: {words_with_tokens}")
        console.print(f"  Glyphs created: {total_glyphs}")

        # Verify
        final_count = session.query(GlyphCandidateRecord).count()
        console.print(f"\n  Total glyphs in database: {final_count}")

    finally:
        session.close()


def main():
    console.print("[bold cyan]Glyph Population Script[/bold cyan]")
    console.print("Deriving glyphs from transcription tokens\n")

    with active_run(config={"command": "populate_glyphs"}) as run:
        populate_glyphs("voynich_real", seed=42)


if __name__ == "__main__":
    main()