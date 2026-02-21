import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from phase1_foundation.core.geometry import Box

logger = logging.getLogger(__name__)

class SegmentedLine(BaseModel):
    line_index: int
    bbox: Box
    confidence: float = 1.0

class SegmentedWord(BaseModel):
    word_index: int
    bbox: Box
    features: dict | None = None
    confidence: float = 1.0

class SegmentedGlyph(BaseModel):
    glyph_index: int
    bbox: Box
    confidence: float = 1.0

class LineSegmenter(ABC):
    @abstractmethod
    def segment_page(self, page_id: str, image_path: str) -> list[SegmentedLine]:
        pass

class WordSegmenter(ABC):
    @abstractmethod
    def segment_line(self, line_bbox: Box, image_path: str) -> list[SegmentedWord]:
        pass

class GlyphSegmenter(ABC):
    @abstractmethod
    def segment_word(self, word_bbox: Box, image_path: str) -> list[SegmentedGlyph]:
        pass
