import pytest

from phase3_synthesis.profile_extractor import PharmaceuticalProfileExtractor


def test_default_or_raise_obeys_require_computed(monkeypatch):
    extractor = PharmaceuticalProfileExtractor(store=None, seed=42)

    monkeypatch.setenv("REQUIRE_COMPUTED", "1")
    with pytest.raises(NotImplementedError, match="REQUIRE_COMPUTED=1"):
        extractor._default_or_raise("metric", 1.0, "missing")

    monkeypatch.setenv("REQUIRE_COMPUTED", "0")
    assert extractor._default_or_raise("metric", 1.5, "fallback") == 1.5


def test_extract_simulated_profile_and_section_envelopes():
    extractor = PharmaceuticalProfileExtractor(store=None, seed=42)

    page = extractor._extract_simulated_profile("f88r")
    assert page.page_id == "f88r"
    assert page.jar_count >= 1
    assert page.total_words > 0

    section = extractor.extract_section_profile()
    assert section.section_id == "pharmaceutical"
    assert len(section.pages) == len(extractor.SECTION_PAGES)
    assert section.jar_count_range[0] >= 1
    assert section.words_per_line_range[0] >= 1


def test_define_gaps_and_summary_with_simulated_storeless_profile():
    extractor = PharmaceuticalProfileExtractor(store=None, seed=42)
    extractor.extract_section_profile()

    gaps = extractor.define_gaps()
    summary = extractor.get_profile_summary()

    assert len(gaps) == 3
    assert all(gap.left_seam_tokens for gap in gaps)
    assert all(gap.right_seam_tokens for gap in gaps)
    assert summary["page_count"] == len(extractor.SECTION_PAGES)
