from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pydantic import BaseModel
from voynich.core.geometry import Box

class SegmentedLine(BaseModel):
    line_index: int
    bbox: Box
    confidence: float = 1.0

class SegmentedWord(BaseModel):
    word_index: int
    bbox: Box
    features: Optional[Dict] = None
    confidence: float = 1.0

class SegmentedGlyph(BaseModel):
    glyph_index: int
    bbox: Box
    confidence: float = 1.0

class LineSegmenter(ABC):
    @abstractmethod
    def segment_page(self, page_id: str, image_path: str) -> List[SegmentedLine]:
        pass

class WordSegmenter(ABC):
    @abstractmethod
    def segment_line(self, line_bbox: Box, image_path: str) -> List[SegmentedWord]:
        pass

class GlyphSegmenter(ABC):
    @abstractmethod
    def segment_word(self, word_bbox: Box, image_path: str) -> List[SegmentedGlyph]:
        pass
