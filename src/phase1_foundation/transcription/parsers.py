from abc import ABC, abstractmethod
from typing import List, Generator
from pathlib import Path
from pydantic import BaseModel
import re
import logging
logger = logging.getLogger(__name__)

class ParsedToken(BaseModel):
    token_index: int
    content: str

class ParsedLine(BaseModel):
    folio: str
    line_index: int
    content: str
    tokens: List[ParsedToken]

class TranscriptionParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> Generator[ParsedLine, None, None]:
        pass

class EVAParser(TranscriptionParser):
    """
    Parses EVA format transcriptions (IVTFF style).
    Example: <f1r.P.1;H>       fachys.ykal.ar.ataiin...
    """
    # Regex to extract location and content
    # <f1r.P.1;H>
    # Group 1: folio (f1r)
    # Group 2: remaining location info (ignored for now)
    # Content follows >
    _line_pattern = re.compile(r"^<([a-z0-9]+)\.([^>]+)>\s*(.+)$")

    def parse(self, path: Path) -> Generator[ParsedLine, None, None]:
        with open(path, 'r') as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                match = self._line_pattern.match(line)
                if match:
                    folio = match.group(1)
                    # We might want to parse the line number from the location string, 
                    # but for now let's just use a sequential index or try to extract it.
                    # Location: P.1;H -> Paragraph 1?
                    # Let's just use the file line index as a fallback or try to extract digits.
                    
                    content = match.group(3)
                    
                    # Split into tokens
                    # EVA tokens are separated by . or spaces, usually . in IVTFF
                    # Some files use spaces. Let's assume . for now as per standard.
                    # Also handle - at end of line?
                    
                    raw_tokens = [t for t in re.split(r'[.\s]+', content) if t]
                    
                    tokens = []
                    for idx, t in enumerate(raw_tokens):
                        tokens.append(ParsedToken(token_index=idx, content=t))
                    
                    yield ParsedLine(
                        folio=folio,
                        line_index=i + 1, # 1-based index from file
                        content=content,
                        tokens=tokens
                    )
