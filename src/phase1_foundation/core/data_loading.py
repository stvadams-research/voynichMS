"""Canonical data loading for all analysis scripts.

Provides a single, consistent data path for loading Voynich manuscript
tokenized lines.  Every Phase 12+ script should use ``load_canonical_lines``
(or ``sanitize_token``) so that the vocabulary seen during palette
construction matches the vocabulary used during validation.
"""

import re

from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.storage.metadata import MetadataStore

# Default canonical source — Zandbergen-Landini IVTFF 2.0
DEFAULT_SOURCE_ID = "zandbergen_landini"

# Compiled regexes for token sanitization
_RE_INLINE_META = re.compile(r"<!.*?>")       # e.g. <!00:00>
_RE_ANGLE_TAGS = re.compile(r"<.*?>")         # e.g. <%>, <$>
_RE_ANGLE_UNCLOSED = re.compile(r"<[!%\$].*")  # unclosed: <!top, <%foo
_RE_BRACKET_CONTENT = re.compile(r"\[.*?\]")  # e.g. [o:a]
_RE_SYMBOLS = re.compile(r"[{}\*\$<>]")       # leftover transcription symbols
_RE_PUNCT = re.compile(r"[,\.;]")             # embedded punctuation


def sanitize_token(token: str) -> str:
    """Clean a single IVTFF token for analysis.

    Removes inline metadata, angle-bracket tags, bracket notation,
    transcription symbols, and embedded punctuation.  Returns the
    stripped result (may be empty string if the token was pure markup).
    """
    t = _RE_INLINE_META.sub("", token)
    t = _RE_ANGLE_TAGS.sub("", t)
    t = _RE_ANGLE_UNCLOSED.sub("", t)
    t = _RE_BRACKET_CONTENT.sub("", t)
    t = _RE_SYMBOLS.sub("", t)
    t = _RE_PUNCT.sub("", t)
    return t.strip()


def load_canonical_lines(
    store: MetadataStore,
    dataset_id: str = "voynich_real",
    source_id: str | None = DEFAULT_SOURCE_ID,
    sanitize: bool = True,
) -> list[list[str]]:
    """Load tokenized lines from the canonical transcription source.

    All Phase 12+ scripts should call this function to ensure the same
    source filtering and token sanitization used during palette construction.

    Args:
        store: MetadataStore instance.
        dataset_id: Dataset identifier (default ``"voynich_real"``).
        source_id: Transcription source to load.  Pass ``None`` to load
            all sources (legacy behaviour).  Default is Zandbergen-Landini.
        sanitize: If True (default), apply IVTFF markup removal to every
            token and drop empty results.

    Returns:
        List of lines, each a list of clean token strings.
    """
    raw_lines = get_lines_from_store(store, dataset_id, source_id=source_id)

    if not sanitize:
        return raw_lines

    clean_lines: list[list[str]] = []
    for line in raw_lines:
        clean_line = [sanitize_token(t) for t in line]
        clean_line = [t for t in clean_line if t]  # drop empty
        if clean_line:
            clean_lines.append(clean_line)
    return clean_lines
