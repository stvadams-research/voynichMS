import logging
from enum import Enum

logger = logging.getLogger(__name__)

class Scale(str, Enum):
    """
    Defines the strict hierarchical scales for the Voynich Manuscript project.
    
    Every object must belong to exactly one scale.
    Cross-scale operations must be explicit.
    """
    PAGE = "page"
    REGION = "region"
    LINE = "line"
    WORD = "word"
    GLYPH = "glyph"
    STROKE = "stroke"

    def __str__(self) -> str:
        return self.value
