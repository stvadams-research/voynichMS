import logging
import re
from abc import ABC, abstractmethod
from collections.abc import Generator
from pathlib import Path

from pydantic import BaseModel

logger = logging.getLogger(__name__)

class ParsedToken(BaseModel):
    token_index: int
    content: str

class ParsedLine(BaseModel):
    folio: str
    line_index: int
    content: str
    tokens: list[ParsedToken]

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
        with open(path) as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                match = self._line_pattern.match(line)
                if not match:
                    logger.debug("Skipped unparseable IVTFF line %d: %r", i + 1, line[:80])
                    continue

                folio = match.group(1)
                content = match.group(3)

                raw_tokens = [t for t in re.split(r'[.\s]+', content) if t]

                tokens = []
                for idx, t in enumerate(raw_tokens):
                    tokens.append(ParsedToken(token_index=idx, content=t))

                yield ParsedLine(
                    folio=folio,
                    line_index=i + 1,  # 1-based index from file
                    content=content,
                    tokens=tokens
                )
