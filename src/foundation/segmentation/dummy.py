from typing import List
from foundation.segmentation.interface import (
    LineSegmenter, WordSegmenter, GlyphSegmenter,
    SegmentedLine, SegmentedWord, SegmentedGlyph
)
from foundation.core.geometry import Box

class DummyLineSegmenter(LineSegmenter):
    def segment_page(self, page_id: str, image_path: str) -> List[SegmentedLine]:
        # Create 5 dummy lines
        lines = []
        for i in range(5):
            lines.append(SegmentedLine(
                line_index=i + 1,
                bbox=Box(x_min=0.1, y_min=0.1 + i*0.15, x_max=0.9, y_max=0.1 + i*0.15 + 0.1),
                confidence=0.9
            ))
        return lines

class DummyWordSegmenter(WordSegmenter):
    def segment_line(self, line_bbox: Box, image_path: str) -> List[SegmentedWord]:
        # Create 3 dummy words per line
        words = []
        width = line_bbox.width / 3
        for i in range(3):
            words.append(SegmentedWord(
                word_index=i,
                bbox=Box(
                    x_min=line_bbox.x_min + i*width,
                    y_min=line_bbox.y_min,
                    x_max=line_bbox.x_min + (i+1)*width - 0.01,
                    y_max=line_bbox.y_max
                ),
                confidence=0.8
            ))
        return words

class DummyGlyphSegmenter(GlyphSegmenter):
    def segment_word(self, word_bbox: Box, image_path: str) -> List[SegmentedGlyph]:
        # Create 2 dummy glyphs per word
        glyphs = []
        width = word_bbox.width / 2
        for i in range(2):
            glyphs.append(SegmentedGlyph(
                glyph_index=i,
                bbox=Box(
                    x_min=word_bbox.x_min + i*width,
                    y_min=word_bbox.y_min,
                    x_max=word_bbox.x_min + (i+1)*width,
                    y_max=word_bbox.y_max
                ),
                confidence=0.7
            ))
        return glyphs
