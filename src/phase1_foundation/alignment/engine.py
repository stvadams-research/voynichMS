"""
Alignment engine mapping transcript Tokens to visual Words.

Terminology:
- Token: transcript text unit (TranscriptionTokenRecord).
- Word: visual image segment (WordRecord).
"""

import logging

from sqlalchemy.orm import Session

from phase1_foundation.storage.metadata import (
    LineRecord,
    MetadataStore,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
    WordRecord,
)

logger = logging.getLogger(__name__)

class AlignmentEngine:
    def __init__(self, store: MetadataStore):
        self.store = store

    def align_page_lines(self, page_id: str, source_id: str) -> None:
        """
        Align image lines to transcription lines based on line index.
        """
        session = self.store.Session()
        try:
            # Get image lines
            img_lines = session.query(LineRecord).filter_by(page_id=page_id).order_by(LineRecord.line_index).all()

            # Get transcript lines
            trans_lines = session.query(TranscriptionLineRecord).filter_by(page_id=page_id, source_id=source_id).order_by(TranscriptionLineRecord.line_index).all()

            # Simple index matching
            # In real implementation, this would be much more complex (DTW, etc.)
            # For Level 2A, we just need to support the structure.

            # Map by index
            trans_map = {l.line_index: l for l in trans_lines}

            for img_line in img_lines:
                trans_line = trans_map.get(img_line.line_index)
                if trans_line:
                    self._align_words_in_line(session, img_line, trans_line)
                else:
                    # Image line with no transcript line
                    # Could log anomaly or create null alignment
                    pass

            session.commit()
        finally:
            session.close()

    def _align_words_in_line(
        self,
        session: Session,
        img_line: LineRecord,
        trans_line: TranscriptionLineRecord,
    ) -> None:
        """
        Align visual Words in a line to transcript Tokens.
        """
        words = session.query(WordRecord).filter_by(line_id=img_line.id).order_by(WordRecord.word_index).all()
        tokens = session.query(TranscriptionTokenRecord).filter_by(line_id=trans_line.id).order_by(TranscriptionTokenRecord.token_index).all()

        # Simple 1:1 alignment for now, handling length mismatch
        max_len = max(len(words), len(tokens))

        for i in range(max_len):
            word = words[i] if i < len(words) else None
            token = tokens[i] if i < len(tokens) else None

            type_ = "1:1"
            if word and not token:
                type_ = "image_only"
            elif token and not word:
                type_ = "transcript_only"

            alignment = WordAlignmentRecord(
                word_id=word.id if word else None,
                token_id=token.id if token else None,
                type=type_,
                score=1.0 if (word and token) else 0.0
            )
            session.add(alignment)
