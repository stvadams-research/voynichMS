"""Tests for RepetitionRate and ClusterTightness metrics."""

import math
import struct

import numpy as np
import pytest

from phase1_foundation.metrics.library import ClusterTightness, RepetitionRate
from phase1_foundation.storage.metadata import (
    DatasetRecord,
    LineRecord,
    MetadataStore,
    PageRecord,
    RegionEmbeddingRecord,
    RegionRecord,
    TranscriptionLineRecord,
    TranscriptionSourceRecord,
    TranscriptionTokenRecord,
    WordAlignmentRecord,
    WordRecord,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def store():
    """In-memory SQLite store with schema created."""
    return MetadataStore("sqlite:///:memory:")


def _seed_dataset(session, dataset_id="ds1"):
    """Insert a minimal dataset record."""
    session.add(DatasetRecord(id=dataset_id, path="/dev/null"))
    session.flush()


def _seed_transcription_source(session, source_id="src1"):
    """Insert a transcription source (required FK for tokens)."""
    session.add(TranscriptionSourceRecord(id=source_id, name="test"))
    session.flush()


def _seed_page(session, page_id="p1", dataset_id="ds1"):
    """Insert a page linked to a dataset."""
    session.add(PageRecord(
        id=page_id, dataset_id=dataset_id,
        image_path="/dev/null", checksum="abc",
    ))
    session.flush()


def _seed_tokens(session, page_id, token_contents):
    """Insert transcription tokens for a page via a single transcription line."""
    line_id = f"tl_{page_id}"
    session.add(TranscriptionLineRecord(
        id=line_id, source_id="src1", page_id=page_id,
        line_index=0, content=" ".join(token_contents),
    ))
    session.flush()
    for i, content in enumerate(token_contents):
        session.add(TranscriptionTokenRecord(
            id=f"tok_{page_id}_{i}", line_id=line_id,
            token_index=i, content=content,
        ))
    session.flush()


def _seed_tokens_via_alignments(session, page_id, token_contents):
    """Insert tokens reachable only via the word-alignment fallback path."""
    vis_line_id = f"vl_{page_id}"
    session.add(LineRecord(
        id=vis_line_id, page_id=page_id, line_index=0,
        bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
    ))
    session.flush()
    # Transcription line NOT linked to this page (so direct path finds nothing)
    other_tl_id = f"tl_other_{page_id}"
    session.add(TranscriptionLineRecord(
        id=other_tl_id, source_id="src1", page_id="other_page",
        line_index=0, content="placeholder",
    ))
    session.flush()
    for i, content in enumerate(token_contents):
        word_id = f"w_{page_id}_{i}"
        tok_id = f"atok_{page_id}_{i}"
        session.add(WordRecord(
            id=word_id, line_id=vis_line_id, word_index=i,
            bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        ))
        session.add(TranscriptionTokenRecord(
            id=tok_id, line_id=other_tl_id,
            token_index=i, content=content,
        ))
        session.flush()
        session.add(WordAlignmentRecord(
            word_id=word_id, token_id=tok_id, type="1:1",
        ))
    session.flush()


def _make_embedding_vector(values):
    """Create a binary float32 vector from a list of floats."""
    return struct.pack(f"{len(values)}f", *values)


# ---------------------------------------------------------------------------
# RepetitionRate
# ---------------------------------------------------------------------------

class TestRepetitionRate:

    def _setup_db(self, store):
        """Seed dataset + transcription source for RepetitionRate tests."""
        session = store.Session()
        _seed_transcription_source(session)
        _seed_dataset(session)
        return session

    def test_no_pages_returns_nan(self, store):
        metric = RepetitionRate(store)
        results = metric.calculate("nonexistent")
        assert len(results) == 1
        assert math.isnan(results[0].value)
        assert results[0].details["error"] == "no_pages_found"

    def test_no_tokens_returns_nan(self, store):
        session = self._setup_db(store)
        _seed_page(session, "p1")
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert len(results) == 1
        assert math.isnan(results[0].value)
        assert results[0].details["error"] == "no_tokens_found"

    def test_known_repetition_rate(self, store):
        """Tokens: [a, b, a, c, b, a] -> repeated = a(3) + b(2) = 5, total = 6, rate = 5/6."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["a", "b", "a", "c", "b", "a"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert len(results) == 1
        r = results[0]
        assert r.metric_name == "RepetitionRate"
        assert r.scope == "global"
        assert r.value == pytest.approx(5 / 6)
        assert r.details["total_tokens"] == 6
        assert r.details["unique_tokens"] == 3

    def test_no_repetitions(self, store):
        """All unique tokens -> repeated_occurrences = 0, rate = 0."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["a", "b", "c", "d"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert results[0].value == pytest.approx(0.0)
        assert results[0].details["unique_tokens"] == 4

    def test_all_identical_tokens(self, store):
        """All same -> repeated = total, rate = 1.0."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["x", "x", "x", "x"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert results[0].value == pytest.approx(1.0)

    def test_single_token(self, store):
        """One token -> count=1, not > 1, rate = 0."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["only"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert results[0].value == pytest.approx(0.0)
        assert results[0].details["total_tokens"] == 1
        assert results[0].details["unique_tokens"] == 1

    def test_vocabulary_coverage(self, store):
        """vocabulary_coverage = 1 - unique/total."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["a", "b", "a"])  # 2 unique / 3 total
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        assert results[0].details["vocabulary_coverage"] == pytest.approx(1 - 2 / 3)

    def test_top_5_tokens(self, store):
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["a", "a", "a", "b", "b", "c"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        top5 = results[0].details["top_5_tokens"]
        assert top5["a"] == 3
        assert top5["b"] == 2

    def test_multi_page_aggregation(self, store):
        """Tokens from multiple pages are aggregated."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_page(session, "p2")
        _seed_tokens(session, "p1", ["a", "b"])
        _seed_tokens(session, "p2", ["a", "c"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        # Total: [a, b, a, c] -> a(2) repeated. Rate = 2/4 = 0.5
        assert results[0].value == pytest.approx(0.5)
        assert results[0].details["total_tokens"] == 4

    def test_fallback_to_word_alignments(self, store):
        """When direct transcription path has no tokens, falls back to alignment path."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_page(session, "other_page")
        _seed_tokens_via_alignments(session, "p1", ["x", "y", "x"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        # x appears 2 times -> 2/3
        assert results[0].value == pytest.approx(2 / 3)

    def test_result_metadata(self, store):
        session = self._setup_db(store)
        _seed_page(session, "p1")
        _seed_tokens(session, "p1", ["a", "b"])
        session.commit()
        session.close()

        metric = RepetitionRate(store)
        results = metric.calculate("ds1")
        r = results[0]
        assert r.dataset_id == "ds1"
        assert r.calculation_method == "computed"
        assert r.is_real()


# ---------------------------------------------------------------------------
# ClusterTightness
# ---------------------------------------------------------------------------

class TestClusterTightness:

    def _setup_db(self, store):
        """Seed dataset for ClusterTightness tests."""
        session = store.Session()
        _seed_dataset(session)
        return session

    def test_no_pages_returns_nan(self, store):
        metric = ClusterTightness(store)
        results = metric.calculate("nonexistent")
        assert len(results) == 1
        assert math.isnan(results[0].value)
        assert results[0].details["method"] == "none"

    def test_identical_embeddings_tightness_one(self, store):
        """All embeddings at same point -> mean_dist = 0 -> tightness = 1.0."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        for i in range(5):
            rid = f"r_{i}"
            session.add(RegionRecord(
                id=rid, page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
            ))
            session.add(RegionEmbeddingRecord(
                region_id=rid, model_name="test",
                vector=_make_embedding_vector([1.0, 2.0, 3.0]),
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert len(results) == 1
        r = results[0]
        assert r.value == pytest.approx(1.0)
        assert r.details["method"] == "embeddings"
        assert r.details["mean_distance"] == pytest.approx(0.0)

    def test_known_embedding_tightness(self, store):
        """Two points at known distance -> verify formula."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        # Point A at [0, 0], Point B at [4, 0]
        # Centroid = [2, 0], distances = [2, 2], mean = 2
        # tightness = 1 / (1 + 2) = 1/3
        for rid, vec in [("r0", [0.0, 0.0]), ("r1", [4.0, 0.0])]:
            session.add(RegionRecord(
                id=rid, page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
            ))
            session.add(RegionEmbeddingRecord(
                region_id=rid, model_name="test",
                vector=_make_embedding_vector(vec),
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        r = results[0]
        assert r.value == pytest.approx(1 / 3)
        assert r.details["mean_distance"] == pytest.approx(2.0)
        assert r.details["embedding_count"] == 2

    def test_insufficient_embeddings_returns_nan(self, store):
        """Only 1 embedding -> insufficient, returns NaN."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        session.add(RegionRecord(
            id="r0", page_id="p1", scale="mid", method="grid",
            bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        ))
        session.add(RegionEmbeddingRecord(
            region_id="r0", model_name="test",
            vector=_make_embedding_vector([1.0, 2.0]),
        ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert math.isnan(results[0].value)
        assert results[0].details["error"] == "insufficient_embeddings"

    def test_bbox_fallback_when_no_embeddings(self, store):
        """No embeddings -> falls back to bbox computation."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        # Region A: center (1, 1), Region B: center (5, 1)
        # Centroid = (3, 1), distances = [2, 2], mean = 2
        # tightness = 1 / (1 + 2) = 1/3
        session.add(RegionRecord(
            id="r0", page_id="p1", scale="mid", method="grid",
            bbox={"x_min": 0, "y_min": 0, "x_max": 2, "y_max": 2},
        ))
        session.add(RegionRecord(
            id="r1", page_id="p1", scale="mid", method="grid",
            bbox={"x_min": 4, "y_min": 0, "x_max": 6, "y_max": 2},
        ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        r = results[0]
        assert r.value == pytest.approx(1 / 3)
        assert r.details["method"] == "bboxes"
        assert r.details["region_count"] == 2

    def test_bbox_insufficient_regions_returns_nan(self, store):
        """Only 1 mid-scale region -> insufficient, NaN."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        session.add(RegionRecord(
            id="r0", page_id="p1", scale="mid", method="grid",
            bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert math.isnan(results[0].value)
        assert results[0].details["method"] == "bboxes"
        assert results[0].details["error"] == "insufficient_regions"

    def test_bbox_ignores_non_mid_scale(self, store):
        """Bbox fallback only uses scale='mid' regions."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        session.add(RegionRecord(
            id="r0", page_id="p1", scale="primitive", method="grid",
            bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        ))
        session.add(RegionRecord(
            id="r1", page_id="p1", scale="primitive", method="grid",
            bbox={"x_min": 2, "y_min": 2, "x_max": 3, "y_max": 3},
        ))
        session.add(RegionRecord(
            id="r2", page_id="p1", scale="mid", method="grid",
            bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
        ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert math.isnan(results[0].value)

    def test_identical_bboxes_tightness_one(self, store):
        """All bboxes at same position -> tightness = 1.0."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        for i in range(3):
            session.add(RegionRecord(
                id=f"r{i}", page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 2, "y_max": 2},
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert results[0].value == pytest.approx(1.0)
        assert results[0].details["method"] == "bboxes"

    def test_embedding_details_include_stats(self, store):
        """Check that embedding results include std/min/max distance."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        # Three points: [0], [3], [6] -> centroid [3], dists [3, 0, 3]
        for rid, val in [("r0", [0.0]), ("r1", [3.0]), ("r2", [6.0])]:
            session.add(RegionRecord(
                id=rid, page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
            ))
            session.add(RegionEmbeddingRecord(
                region_id=rid, model_name="test",
                vector=_make_embedding_vector(val),
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        d = results[0].details
        assert d["mean_distance"] == pytest.approx(2.0)
        assert d["std_distance"] == pytest.approx(np.std([3.0, 0.0, 3.0]))
        assert d["min_distance"] == pytest.approx(0.0)
        assert d["max_distance"] == pytest.approx(3.0)
        assert d["embedding_count"] == 3

    def test_tightness_is_between_zero_and_one(self, store):
        """Tightness should always be in (0, 1]."""
        session = self._setup_db(store)
        _seed_page(session, "p1")
        for i, val in enumerate([0.0, 100.0, 50.0]):
            rid = f"r{i}"
            session.add(RegionRecord(
                id=rid, page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
            ))
            session.add(RegionEmbeddingRecord(
                region_id=rid, model_name="test",
                vector=_make_embedding_vector([val]),
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        assert 0 < results[0].value <= 1.0

    def test_result_metadata(self, store):
        session = self._setup_db(store)
        _seed_page(session, "p1")
        for i in range(2):
            rid = f"r{i}"
            session.add(RegionRecord(
                id=rid, page_id="p1", scale="mid", method="grid",
                bbox={"x_min": 0, "y_min": 0, "x_max": 1, "y_max": 1},
            ))
            session.add(RegionEmbeddingRecord(
                region_id=rid, model_name="test",
                vector=_make_embedding_vector([float(i)]),
            ))
        session.commit()
        session.close()

        metric = ClusterTightness(store)
        results = metric.calculate("ds1")
        r = results[0]
        assert r.metric_name == "ClusterTightness"
        assert r.dataset_id == "ds1"
        assert r.scope == "global"
        assert r.calculation_method == "computed"
