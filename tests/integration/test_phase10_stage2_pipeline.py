from __future__ import annotations

import numpy as np

import pytest

pytestmark = pytest.mark.integration

from phase10_admissibility.stage2_pipeline import (
    _tokenize_text_to_lines,
    folio_sort_key,
    mantel_correlation,
    section_for_folio,
    summarize_stage2,
)


def test_folio_sort_key_orders_recto_verso_and_suffix() -> None:
    folios = ["f10v", "f2r", "f10r2", "f10r1", "f10r"]
    ordered = sorted(folios, key=folio_sort_key)
    assert ordered == ["f2r", "f10r", "f10r1", "f10r2", "f10v"]


def test_section_for_folio_uses_range_mapping() -> None:
    assert section_for_folio("f1r") == "herbal"
    assert section_for_folio("f70v") == "astronomical"
    assert section_for_folio("f90r1") == "pharmaceutical"
    assert section_for_folio("bad_id") == "unknown"


def test_mantel_correlation_detects_positive_alignment() -> None:
    rng = np.random.default_rng(42)
    coords = np.linspace(0.0, 1.0, 10)
    visual = np.abs(coords[:, None] - coords[None, :])
    noise = rng.normal(loc=0.0, scale=0.01, size=visual.shape)
    text = np.clip(visual + noise, a_min=0.0, a_max=None)
    np.fill_diagonal(text, 0.0)

    result = mantel_correlation(visual, text, permutations=300, seed=42)
    assert result["r_observed"] > 0.8
    assert result["p_one_sided"] < 0.05


def test_summarize_stage2_prioritizes_weakened_over_invalid() -> None:
    summary = summarize_stage2(
        {
            "G": {"decision": "closure_weakened"},
            "I": {"decision": "test_invalid"},
        }
    )
    assert summary["stage_decision"] == "closure_weakened"


def test_tokenize_text_to_lines_handles_arabic_words() -> None:
    lines = _tokenize_text_to_lines("مرحبا بكم\nهذا اختبار")
    flat = [token for line in lines for token in line]
    assert "مرحبا" in flat
    assert "اختبار" in flat


def test_tokenize_text_to_lines_splits_cjk_runs_to_characters() -> None:
    lines = _tokenize_text_to_lines("这是一个测试。")
    flat = [token for line in lines for token in line]
    assert "这" in flat
    assert "测" in flat
    assert len(flat) >= 4
