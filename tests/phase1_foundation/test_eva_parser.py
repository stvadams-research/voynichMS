"""Tests for EVAParser — the single canonical tokenization path.

Covers: valid IVTFF parsing, comment/blank handling, malformed lines,
token splitting, generator behavior, and edge cases.
"""

from pathlib import Path

import pytest

from phase1_foundation.transcription.parsers import EVAParser, ParsedLine, ParsedToken

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_ivtff(tmp_path: Path, content: str) -> Path:
    """Write content to a temp .txt file and return its path."""
    p = tmp_path / "test.txt"
    p.write_text(content, encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Basic parsing
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEVAParserBasic:
    """Core parsing of well-formed IVTFF lines."""

    def test_single_line(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> fachys.ykal.ar\n")
        results = list(EVAParser().parse(path))

        assert len(results) == 1
        line = results[0]
        assert line.folio == "f1r"
        assert line.content == "fachys.ykal.ar"
        assert len(line.tokens) == 3
        assert line.tokens[0].content == "fachys"
        assert line.tokens[1].content == "ykal"
        assert line.tokens[2].content == "ar"

    def test_multiple_lines_same_folio(self, tmp_path):
        content = (
            "<f1r.P.1;H> daiin.qokeey\n"
            "<f1r.P.2;H> otal.sheor\n"
        )
        path = _write_ivtff(tmp_path, content)
        results = list(EVAParser().parse(path))

        assert len(results) == 2
        assert results[0].folio == "f1r"
        assert results[1].folio == "f1r"

    def test_multiple_folios(self, tmp_path):
        content = (
            "<f1r.P.1;H> daiin\n"
            "<f2v.P.1;H> chedy\n"
        )
        path = _write_ivtff(tmp_path, content)
        results = list(EVAParser().parse(path))

        assert results[0].folio == "f1r"
        assert results[1].folio == "f2v"

    def test_token_indices_are_zero_based(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> a.b.c.d\n")
        line = list(EVAParser().parse(path))[0]

        for i, tok in enumerate(line.tokens):
            assert tok.token_index == i

    def test_line_index_is_one_based_file_position(self, tmp_path):
        content = (
            "# comment\n"
            "\n"
            "<f1r.P.1;H> daiin\n"
        )
        path = _write_ivtff(tmp_path, content)
        line = list(EVAParser().parse(path))[0]
        # The data line is the 3rd line in the file (index 2), so line_index = 3
        assert line.line_index == 3


# ---------------------------------------------------------------------------
# Skipped lines
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEVAParserSkipping:
    """Lines that should be silently skipped."""

    def test_empty_lines_skipped(self, tmp_path):
        content = "\n\n<f1r.P.1;H> daiin\n\n"
        path = _write_ivtff(tmp_path, content)
        results = list(EVAParser().parse(path))
        assert len(results) == 1

    def test_comment_lines_skipped(self, tmp_path):
        content = (
            "# This is a header comment\n"
            "#\n"
            "<f1r.P.1;H> daiin\n"
        )
        path = _write_ivtff(tmp_path, content)
        results = list(EVAParser().parse(path))
        assert len(results) == 1

    def test_malformed_lines_skipped(self, tmp_path):
        content = (
            "This line has no angle brackets\n"
            "<f1r.P.1;H> daiin\n"
            "f1r.P.1;H> missing opening bracket\n"
            "<f1r> missing dot separator\n"
        )
        path = _write_ivtff(tmp_path, content)
        results = list(EVAParser().parse(path))
        assert len(results) == 1
        assert results[0].tokens[0].content == "daiin"

    def test_empty_file(self, tmp_path):
        path = _write_ivtff(tmp_path, "")
        results = list(EVAParser().parse(path))
        assert results == []

    def test_comments_only_file(self, tmp_path):
        path = _write_ivtff(tmp_path, "# just comments\n# more comments\n")
        results = list(EVAParser().parse(path))
        assert results == []


# ---------------------------------------------------------------------------
# Token splitting
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEVAParserTokenSplitting:
    """Token delimiter handling."""

    def test_dot_separated(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin.qokeey.dal\n")
        tokens = list(EVAParser().parse(path))[0].tokens
        assert [t.content for t in tokens] == ["daiin", "qokeey", "dal"]

    def test_space_separated(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin qokeey dal\n")
        tokens = list(EVAParser().parse(path))[0].tokens
        assert [t.content for t in tokens] == ["daiin", "qokeey", "dal"]

    def test_mixed_dot_and_space(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin.qokeey dal\n")
        tokens = list(EVAParser().parse(path))[0].tokens
        assert [t.content for t in tokens] == ["daiin", "qokeey", "dal"]

    def test_consecutive_delimiters_collapsed(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin..qokeey\n")
        tokens = list(EVAParser().parse(path))[0].tokens
        assert [t.content for t in tokens] == ["daiin", "qokeey"]

    def test_single_token_line(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin\n")
        tokens = list(EVAParser().parse(path))[0].tokens
        assert len(tokens) == 1
        assert tokens[0].content == "daiin"


# ---------------------------------------------------------------------------
# Content preservation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEVAParserContent:
    """The raw content field preserves the original text."""

    def test_content_field_preserves_original(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> fachys.ykal.ar\n")
        line = list(EVAParser().parse(path))[0]
        assert line.content == "fachys.ykal.ar"

    def test_content_with_extra_whitespace(self, tmp_path):
        # Extra spaces between > and content
        path = _write_ivtff(tmp_path, "<f1r.P.1;H>    fachys.ykal\n")
        line = list(EVAParser().parse(path))[0]
        assert line.content == "fachys.ykal"


# ---------------------------------------------------------------------------
# Generator behavior
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestEVAParserGenerator:
    """parse() returns a generator, not a list."""

    def test_returns_generator(self, tmp_path):
        path = _write_ivtff(tmp_path, "<f1r.P.1;H> daiin\n")
        result = EVAParser().parse(path)
        import types
        assert isinstance(result, types.GeneratorType)

    def test_partial_iteration(self, tmp_path):
        content = "\n".join(
            f"<f1r.P.{i};H> token{i}" for i in range(1, 101)
        )
        path = _write_ivtff(tmp_path, content)
        gen = EVAParser().parse(path)
        first = next(gen)
        assert first.tokens[0].content == "token1"


# ---------------------------------------------------------------------------
# Model types
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParsedModels:
    """ParsedLine and ParsedToken are well-formed Pydantic models."""

    def test_parsed_token_fields(self):
        tok = ParsedToken(token_index=0, content="daiin")
        assert tok.token_index == 0
        assert tok.content == "daiin"

    def test_parsed_line_fields(self):
        tok = ParsedToken(token_index=0, content="daiin")
        line = ParsedLine(folio="f1r", line_index=1, content="daiin", tokens=[tok])
        assert line.folio == "f1r"
        assert line.line_index == 1
        assert len(line.tokens) == 1


# ---------------------------------------------------------------------------
# Integration with shared fixture
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_sample_ivtff_fixture(sample_ivtff_file):
    """Verify the shared sample_ivtff_file fixture works with EVAParser."""
    results = list(EVAParser().parse(sample_ivtff_file))
    assert len(results) == 3
    assert results[0].folio == "f1r"
    assert results[2].folio == "f2v"
