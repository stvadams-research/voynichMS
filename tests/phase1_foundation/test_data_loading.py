"""Tests for the canonical data loading utility."""

import pytest
from phase1_foundation.core.data_loading import (
    DEFAULT_SOURCE_ID,
    load_canonical_lines,
    sanitize_token,
)


class TestSanitizeToken:
    """Unit tests for IVTFF token sanitization."""

    def test_plain_token_unchanged(self):
        assert sanitize_token("daiin") == "daiin"

    def test_removes_inline_metadata(self):
        assert sanitize_token("<%>fchaiin") == "fchaiin"

    def test_removes_end_marker(self):
        assert sanitize_token("chotaiin<$>") == "chotaiin"

    def test_removes_bracket_notation(self):
        # [o:a] is a transcription uncertainty marker
        assert sanitize_token("lchor[o:a]m") == "lchorm"

    def test_removes_embedded_comma(self):
        assert sanitize_token("chear,yteey") == "chearyteey"

    def test_removes_embedded_dot(self):
        assert sanitize_token("word.other") == "wordother"

    def test_removes_curly_braces(self):
        assert sanitize_token("{word}") == "word"

    def test_removes_asterisk(self):
        assert sanitize_token("*daiin") == "daiin"

    def test_empty_markup_returns_empty(self):
        assert sanitize_token("<%>") == ""

    def test_multiple_markers(self):
        assert sanitize_token("<!00:00>word<$>") == "word"

    def test_no_ivtff_markup_after_sanitize(self):
        """No angle brackets, square brackets, or symbols survive."""
        dirty_tokens = [
            "<%>fchaiin", "chotaiin<$>", "lchor[o:a]m",
            "<!00:00>test", "{word}", "*daiin",
        ]
        for t in dirty_tokens:
            clean = sanitize_token(t)
            for ch in "<>[]{}*$":
                assert ch not in clean, (
                    f"'{ch}' found in sanitize_token({t!r}) = {clean!r}"
                )

    def test_default_source_id(self):
        assert DEFAULT_SOURCE_ID == "zandbergen_landini"


class TestLoadCanonicalLines:
    """Integration tests (require database access)."""

    @pytest.fixture
    def store(self):
        """Create a MetadataStore pointing at the real database."""
        from phase1_foundation.storage.metadata import MetadataStore
        try:
            s = MetadataStore("sqlite:///data/voynich.db")
            # Quick check that the DB has data
            from phase1_foundation.core.queries import get_lines_from_store
            lines = get_lines_from_store(s, "voynich_real", source_id="zandbergen_landini")
            if not lines:
                pytest.skip("Database not populated with ZL data")
            return s
        except Exception:
            pytest.skip("Database not available")

    def test_returns_nonempty(self, store):
        lines = load_canonical_lines(store)
        assert len(lines) > 0
        assert all(len(line) > 0 for line in lines)

    def test_no_markup_in_tokens(self, store):
        """Verify no IVTFF markup survives sanitization."""
        lines = load_canonical_lines(store)
        all_tokens = [t for line in lines for t in line]
        for t in all_tokens[:5000]:  # sample for speed
            for ch in "<>[]{}*$":
                assert ch not in t, f"'{ch}' found in token: {t!r}"

    def test_unsanitized_returns_raw(self, store):
        """With sanitize=False, tokens are returned as-is."""
        raw = load_canonical_lines(store, sanitize=False)
        clean = load_canonical_lines(store, sanitize=True)
        # Raw should have at least as many unique tokens
        raw_unique = {t for line in raw for t in line}
        clean_unique = {t for line in clean for t in line}
        assert len(raw_unique) >= len(clean_unique)

    def test_source_filtering(self, store):
        """ZL-only lines should be fewer than all-source lines."""
        zl_lines = load_canonical_lines(store)
        all_lines = load_canonical_lines(
            store, source_id=None, sanitize=False
        )
        assert len(zl_lines) < len(all_lines)
