import pytest

pytestmark = pytest.mark.unit

from phase4_inference.projection_diagnostics.reference_number import (
    ReferenceNumberAnalyzer,
    ReferenceNumberConfig,
)


def test_reference_number_analyzer_detects_strong_target_signal() -> None:
    analyzer = ReferenceNumberAnalyzer(
        ReferenceNumberConfig(target_value=42, local_window_radius=2)
    )
    values = {
        "line_char_count": [42] * 18 + [40] * 2 + [41] * 3 + [43] * 2 + [44] * 1
    }

    result = analyzer.analyze(values)
    row = result["metrics"]["line_char_count"]

    assert row["status"] == "ok"
    assert row["target_count"] == 18
    assert row["classification"] == "STRONG_SIGNAL"
    assert row["local_window_test"]["z_score"] > 2.0
    assert row["neighborhood_test"]["z_score"] > 2.0


def test_reference_number_analyzer_marks_no_hit_when_target_absent() -> None:
    analyzer = ReferenceNumberAnalyzer(
        ReferenceNumberConfig(target_value=42, local_window_radius=3)
    )
    values = {"page_line_count": [10, 11, 12, 13, 14, 15, 16]}

    result = analyzer.analyze(values)
    row = result["metrics"]["page_line_count"]

    assert row["status"] == "ok"
    assert row["target_count"] == 0
    assert row["classification"] == "NO_HIT"
    assert result["aggregate"]["hit_metric_count"] == 0
    assert result["aggregate"]["assessment"] == "NO_REFERENCE_SIGNAL"


def test_reference_number_analyzer_aggregate_tracks_category_coverage() -> None:
    analyzer = ReferenceNumberAnalyzer(
        ReferenceNumberConfig(target_value=42, local_window_radius=1)
    )
    values = {
        "line_token_count": [42, 42, 11, 12, 13],
        "page_token_count": [20, 21, 22, 23, 24],
        "section_page_count": [41, 42, 43, 44, 45],
    }

    result = analyzer.analyze(values)
    agg = result["aggregate"]

    assert agg["metric_count"] == 3
    assert agg["hit_metric_count"] == 2
    assert agg["category_coverage"]["line"]["hit"] is True
    assert agg["category_coverage"]["page"]["hit"] is False
    assert agg["category_coverage"]["section"]["hit"] is True

