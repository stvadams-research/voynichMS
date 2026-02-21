import math

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.metrics.library import ClusterTightness, RepetitionRate
from phase1_foundation.storage.metadata import MetadataStore
from phase3_synthesis.interface import SectionProfile
from phase3_synthesis.refinement.feature_discovery import DiscriminativeFeatureDiscovery


@pytest.fixture
def empty_store(tmp_path):
    db_path = f"sqlite:///{tmp_path}/empty.db"
    return MetadataStore(db_path)


def _add_tokens(store: MetadataStore, dataset_id: str, page_id: str, line_id: str, tokens):
    store.add_dataset(dataset_id, "generated")
    store.add_page(page_id, dataset_id, "img.jpg", "h1", 100, 100)
    store.add_transcription_source("src", "Source")
    store.add_transcription_line(line_id, "src", page_id, 0, " ".join(tokens))
    for idx, token in enumerate(tokens):
        store.add_transcription_token(f"{line_id}_t{idx}", line_id, idx, token)


def test_repetition_rate_empty_dataset(empty_store):
    metric = RepetitionRate(empty_store)
    results = metric.calculate("non_existent")
    assert len(results) == 1
    assert math.isnan(results[0].value)
    assert results[0].details["error"] == "no_pages_found"


def test_cluster_tightness_insufficient_data(empty_store):
    empty_store.add_dataset("empty_ds", "real")
    empty_store.add_page("p1", "empty_ds", "img.jpg", "h1", 100, 100)

    metric = ClusterTightness(empty_store)
    results = metric.calculate("empty_ds")

    assert results[0].details["status"] == "no_data"
    assert results[0].details["error"] == "insufficient_regions"
    assert results[0].details["method"] == "bboxes"
    assert math.isnan(results[0].value)


def test_repetition_rate_single_token(empty_store):
    _add_tokens(
        empty_store,
        dataset_id="single",
        page_id="single_p1",
        line_id="single_l1",
        tokens=["token1"],
    )

    metric = RepetitionRate(empty_store)
    results = metric.calculate("single")

    assert results[0].value == pytest.approx(0.0)
    assert results[0].details["unique_tokens"] == 1
    assert results[0].details["total_tokens"] == 1
    assert results[0].details["vocabulary_coverage"] == pytest.approx(0.0)


def test_repetition_rate_all_same_tokens(empty_store):
    _add_tokens(
        empty_store,
        dataset_id="all_same",
        page_id="all_same_p1",
        line_id="all_same_l1",
        tokens=["a", "a", "a", "a"],
    )

    metric = RepetitionRate(empty_store)
    result = metric.calculate("all_same")[0]

    assert result.value == pytest.approx(1.0)
    assert result.details["token_repetition_rate"] == pytest.approx(1.0)
    assert result.details["vocabulary_coverage"] == pytest.approx(0.75)


def test_cluster_tightness_bbox_fallback_computes_value(empty_store):
    empty_store.add_dataset("bbox_ds", "real")
    empty_store.add_page("bbox_p1", "bbox_ds", "img.jpg", "h1", 100, 100)
    empty_store.add_region(
        id="r1",
        page_id="bbox_p1",
        scale="mid",
        method="manual",
        bbox={"x_min": 0.1, "y_min": 0.1, "x_max": 0.2, "y_max": 0.2},
    )
    empty_store.add_region(
        id="r2",
        page_id="bbox_p1",
        scale="mid",
        method="manual",
        bbox={"x_min": 0.8, "y_min": 0.8, "x_max": 0.9, "y_max": 0.9},
    )

    metric = ClusterTightness(empty_store)
    result = metric.calculate("bbox_ds")[0]

    assert math.isfinite(result.value)
    assert result.details["method"] == "bboxes"
    assert result.details["computation_path"] == "bboxes"


def test_feature_discovery_sanitizes_nan_values():
    discovery = DiscriminativeFeatureDiscovery(section_profile=SectionProfile())
    cleaned = discovery._sanitize_feature_map(
        {
            "finite": 1.23,
            "nan_value": float("nan"),
            "inf_value": float("inf"),
            "neg_inf_value": float("-inf"),
        },
        page_id="page_1",
    )

    assert cleaned == {"finite": 1.23}
