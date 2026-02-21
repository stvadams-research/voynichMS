"""Tests for MetadataStore — the central persistence layer.

Covers: schema creation, CRUD for all 6 database levels, session lifecycle,
merge/upsert behavior, relationship navigation, status cascades, and queries.
"""

import pytest

from phase1_foundation.storage.metadata import (
    AnchorMethodRecord,
    AnchorRecord,
    ControlDatasetRecord,
    DatasetRecord,
    GlyphCandidateRecord,
    HypothesisRecord,
    LineRecord,
    MetadataStore,
    MetricResultRecord,
    PageRecord,
    StructureRecord,
    TranscriptionLineRecord,
    TranscriptionSourceRecord,
    TranscriptionTokenRecord,
    WordRecord,
)

# ---------------------------------------------------------------------------
# Schema creation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSchemaCreation:
    def test_store_creates_all_tables(self, store):
        """MetadataStore constructor should create 33 tables."""
        from sqlalchemy import inspect
        inspector = inspect(store.engine)
        tables = inspector.get_table_names()
        assert len(tables) >= 33

    def test_store_creates_without_error(self, tmp_db):
        """Construction with a valid SQLite URL should not raise."""
        s = MetadataStore(tmp_db)
        assert s is not None


# ---------------------------------------------------------------------------
# Level 1: Infrastructure — Datasets
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestDatasets:
    def test_add_dataset(self, store):
        store.add_dataset("ds1", "/path/to/data", checksum="abc123")
        session = store.Session()
        try:
            ds = session.query(DatasetRecord).filter_by(id="ds1").first()
            assert ds is not None
            assert ds.path == "/path/to/data"
            assert ds.checksum == "abc123"
        finally:
            session.close()

    def test_add_dataset_upsert(self, store):
        """Calling add_dataset twice with same ID should update, not duplicate."""
        store.add_dataset("ds1", "/old", checksum="old")
        store.add_dataset("ds1", "/new", checksum="new")
        session = store.Session()
        try:
            results = session.query(DatasetRecord).filter_by(id="ds1").all()
            assert len(results) == 1
            assert results[0].path == "/new"
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Level 2A: Pages, Lines, Words, Glyphs, Transcription
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPages:
    def test_add_page(self, store):
        store.add_dataset("ds1", "/path")
        store.add_page("f1r", "ds1", "/img/f1r.jpg", "hash1", 800, 600)
        session = store.Session()
        try:
            page = session.query(PageRecord).filter_by(id="f1r").first()
            assert page is not None
            assert page.dataset_id == "ds1"
            assert page.width == 800
        finally:
            session.close()

    def test_add_page_upsert(self, store):
        store.add_dataset("ds1", "/path")
        store.add_page("f1r", "ds1", "/img/f1r.jpg", "hash1", 800, 600)
        store.add_page("f1r", "ds1", "/img/f1r_v2.jpg", "hash2", 1600, 1200)
        session = store.Session()
        try:
            pages = session.query(PageRecord).filter_by(id="f1r").all()
            assert len(pages) == 1
            assert pages[0].width == 1600
        finally:
            session.close()


@pytest.mark.unit
class TestLines:
    def test_add_line(self, populated_store):
        session = populated_store.Session()
        try:
            line = session.query(LineRecord).filter_by(id="f1r_L1").first()
            assert line is not None
            assert line.page_id == "f1r"
            assert line.line_index == 1
        finally:
            session.close()


@pytest.mark.unit
class TestWords:
    def test_add_word(self, populated_store):
        session = populated_store.Session()
        try:
            word = session.query(WordRecord).filter_by(id="f1r_W1").first()
            assert word is not None
            assert word.line_id == "f1r_L1"
            assert word.word_index == 0
        finally:
            session.close()


@pytest.mark.unit
class TestGlyphs:
    def test_add_glyph_candidate(self, populated_store):
        populated_store.add_glyph_candidate(
            "f1r_G1", "f1r_W1", 0, {"x": 0, "y": 0, "w": 20, "h": 30}
        )
        session = populated_store.Session()
        try:
            glyph = session.query(GlyphCandidateRecord).filter_by(id="f1r_G1").first()
            assert glyph is not None
            assert glyph.word_id == "f1r_W1"
        finally:
            session.close()


@pytest.mark.unit
class TestTranscription:
    def test_add_transcription_source(self, populated_store):
        session = populated_store.Session()
        try:
            src = session.query(TranscriptionSourceRecord).filter_by(id="eva_test").first()
            assert src is not None
            assert src.name == "EVA Test Source"
        finally:
            session.close()

    def test_add_transcription_line(self, populated_store):
        session = populated_store.Session()
        try:
            tl = session.query(TranscriptionLineRecord).filter_by(id="f1r_TL1").first()
            assert tl is not None
            assert tl.content == "daiin.qokeey.dal"
        finally:
            session.close()

    def test_add_transcription_token(self, populated_store):
        session = populated_store.Session()
        try:
            tokens = (
                session.query(TranscriptionTokenRecord)
                .filter_by(line_id="f1r_TL1")
                .order_by(TranscriptionTokenRecord.token_index)
                .all()
            )
            assert len(tokens) == 3
            assert tokens[0].content == "daiin"
            assert tokens[1].content == "qokeey"
            assert tokens[2].content == "dal"
        finally:
            session.close()

    def test_transcription_source_upsert(self, store):
        store.add_transcription_source("eva_v1", "EVA v1")
        store.add_transcription_source("eva_v1", "EVA v1 Updated")
        session = store.Session()
        try:
            results = session.query(TranscriptionSourceRecord).filter_by(id="eva_v1").all()
            assert len(results) == 1
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Level 3: Controls & Metrics
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestControls:
    def test_add_control_dataset(self, populated_store):
        populated_store.add_control_dataset(
            "ctrl1", "test_ds", "scrambled", {"method": "shuffle"}, seed=42
        )
        session = populated_store.Session()
        try:
            ctrl = session.query(ControlDatasetRecord).filter_by(id="ctrl1").first()
            assert ctrl is not None
            assert ctrl.source_dataset_id == "test_ds"
            assert ctrl.seed == 42
        finally:
            session.close()


@pytest.mark.unit
class TestMetrics:
    def test_add_metric_result(self, populated_store):
        populated_store.add_metric_result(
            "run1", "test_ds", "repetition_rate", "global", 0.85
        )
        session = populated_store.Session()
        try:
            mr = (
                session.query(MetricResultRecord)
                .filter_by(metric_name="repetition_rate")
                .first()
            )
            assert mr is not None
            assert mr.value == pytest.approx(0.85)
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Level 4: Anchors
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestAnchors:
    def test_add_anchor_method(self, store):
        store.add_anchor_method("cooccurrence", "Co-occurrence", parameters={"window": 5})
        session = store.Session()
        try:
            am = session.query(AnchorMethodRecord).filter_by(id="cooccurrence").first()
            assert am is not None
            assert am.name == "Co-occurrence"
        finally:
            session.close()

    def test_add_anchor(self, populated_store):
        populated_store.add_anchor_method("cooccurrence", "Co-occurrence")
        populated_store.add_anchor(
            id="a1", run_id="run1", page_id="f1r",
            source_type="word", source_id="f1r_W1",
            target_type="region", target_id="r1",
            relation_type="cooccurrence", method_id="cooccurrence",
            score=0.9,
        )
        session = populated_store.Session()
        try:
            anchor = session.query(AnchorRecord).filter_by(id="a1").first()
            assert anchor is not None
            assert anchor.score == pytest.approx(0.9)
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Level 5: Structures & Decisions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestStructures:
    def test_add_structure(self, store):
        store.add_structure("s1", "Gallows Position", "desc", "level_2", "candidate")
        session = store.Session()
        try:
            s = session.query(StructureRecord).filter_by(id="s1").first()
            assert s is not None
            assert s.status == "candidate"
        finally:
            session.close()

    def test_decision_updates_structure_status(self, store):
        """add_decision should cascade status to parent structure."""
        store.add_structure("s1", "Test", "desc", "level_2", "candidate")
        store.add_decision("s1", "ACCEPT", "Strong evidence", "run1")

        session = store.Session()
        try:
            s = session.query(StructureRecord).filter_by(id="s1").first()
            assert s.status == "accepted"
        finally:
            session.close()

    def test_decision_reject_status(self, store):
        store.add_structure("s1", "Test", "desc", "level_2", "candidate")
        store.add_decision("s1", "REJECT", "Insufficient evidence", "run1")

        session = store.Session()
        try:
            s = session.query(StructureRecord).filter_by(id="s1").first()
            assert s.status == "rejected"
        finally:
            session.close()

    def test_decision_hold_status(self, store):
        store.add_structure("s1", "Test", "desc", "level_2", "candidate")
        store.add_decision("s1", "HOLD", "Needs more data", "run1")

        session = store.Session()
        try:
            s = session.query(StructureRecord).filter_by(id="s1").first()
            assert s.status == "inconclusive"
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Level 6: Hypotheses
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestHypotheses:
    def test_add_hypothesis(self, store):
        store.add_hypothesis(
            "h1", "Token distribution is non-random",
            "Assumes EVA encoding", "Kolmogorov complexity test"
        )
        session = store.Session()
        try:
            h = session.query(HypothesisRecord).filter_by(id="h1").first()
            assert h is not None
            assert h.status == "active"
        finally:
            session.close()

    def test_hypothesis_run_updates_status(self, store):
        store.add_hypothesis("h1", "Test claim", "none", "criteria")
        store.add_hypothesis_run("h1", "run1", "SUPPORTED", {"z_score": 3.5})

        session = store.Session()
        try:
            h = session.query(HypothesisRecord).filter_by(id="h1").first()
            assert h.status == "supported"
        finally:
            session.close()

    def test_hypothesis_falsified_status(self, store):
        store.add_hypothesis("h1", "Test claim", "none", "criteria")
        store.add_hypothesis_run("h1", "run1", "FALSIFIED")

        session = store.Session()
        try:
            h = session.query(HypothesisRecord).filter_by(id="h1").first()
            assert h.status == "falsified"
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Explanation Classes (Admissibility)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestExplanationClasses:
    def test_add_explanation_class(self, store):
        store.add_explanation_class(
            "natural_language", "Natural Language", "Encodes natural language"
        )
        ec = store.get_explanation_class("natural_language")
        assert ec is not None
        assert ec.status == "underconstrained"

    def test_update_explanation_class_status(self, store):
        store.add_explanation_class("nl", "Natural Language", "desc")
        store.update_explanation_class_status("nl", "inadmissible")
        ec = store.get_explanation_class("nl")
        assert ec.status == "inadmissible"

    def test_get_all_explanation_classes(self, store):
        store.add_explanation_class("nl", "Natural Language", "desc")
        store.add_explanation_class("cipher", "Simple Cipher", "desc")
        classes = store.get_all_explanation_classes()
        assert len(classes) == 2

    def test_add_admissibility_constraint(self, store):
        store.add_explanation_class("nl", "Natural Language", "desc")
        cid = store.add_admissibility_constraint("nl", "required", "Must have Zipf distribution")
        assert isinstance(cid, int)

    def test_get_constraints_for_class(self, store):
        store.add_explanation_class("nl", "Natural Language", "desc")
        store.add_admissibility_constraint("nl", "required", "Constraint A")
        store.add_admissibility_constraint("nl", "forbidden", "Constraint B")
        constraints = store.get_constraints_for_class("nl")
        assert len(constraints) == 2

    def test_add_admissibility_evidence(self, store):
        store.add_explanation_class("nl", "Natural Language", "desc")
        cid = store.add_admissibility_constraint("nl", "required", "Test constraint")
        store.add_structure("s1", "Test structure", "desc", "level_2")
        store.add_admissibility_evidence("nl", cid, "s1", "strong", "Evidence reasoning")
        evidence = store.get_evidence_for_class("nl")
        assert len(evidence) == 1
        assert evidence[0].support_level == "strong"


# ---------------------------------------------------------------------------
# Session lifecycle
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSessionLifecycle:
    def test_multiple_operations_in_sequence(self, store):
        """Multiple add operations should not leak sessions."""
        store.add_dataset("ds1", "/path1")
        store.add_dataset("ds2", "/path2")
        store.add_dataset("ds3", "/path3")
        session = store.Session()
        try:
            count = session.query(DatasetRecord).count()
            assert count == 3
        finally:
            session.close()

    def test_store_with_in_memory_db(self):
        """MetadataStore should work with in-memory SQLite."""
        store = MetadataStore("sqlite:///:memory:")
        store.add_dataset("test", "/path")
        session = store.Session()
        try:
            ds = session.query(DatasetRecord).filter_by(id="test").first()
            assert ds is not None
        finally:
            session.close()


# ---------------------------------------------------------------------------
# JSON column handling
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestJSONColumns:
    def test_line_bbox_stored_as_json(self, populated_store):
        session = populated_store.Session()
        try:
            line = session.query(LineRecord).filter_by(id="f1r_L1").first()
            assert line.bbox == {"x": 0, "y": 0, "w": 800, "h": 30}
        finally:
            session.close()

    def test_metric_result_details_json(self, populated_store):
        populated_store.add_metric_result(
            "run1", "test_ds", "test_metric", "global", 1.0,
            details={"method": "exact", "samples": 100},
        )
        session = populated_store.Session()
        try:
            mr = (
                session.query(MetricResultRecord)
                .filter_by(metric_name="test_metric")
                .first()
            )
            assert mr.details["method"] == "exact"
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Sensitivity results
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestSensitivity:
    def test_add_sensitivity_result(self, store):
        store.add_structure("s1", "Test", "desc", "level_2")
        store.add_sensitivity_result("s1", "threshold", "0.5", 0.92, "run1")

        from phase1_foundation.storage.metadata import SensitivityResultRecord
        session = store.Session()
        try:
            sr = session.query(SensitivityResultRecord).first()
            assert sr is not None
            assert sr.parameter_name == "threshold"
            assert sr.metric_value == pytest.approx(0.92)
        finally:
            session.close()


# ---------------------------------------------------------------------------
# Relationship navigation
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRelationships:
    def test_page_dataset_relationship(self, populated_store):
        session = populated_store.Session()
        try:
            page = session.query(PageRecord).filter_by(id="f1r").first()
            assert page.dataset.id == "test_ds"
        finally:
            session.close()

    def test_line_page_relationship(self, populated_store):
        session = populated_store.Session()
        try:
            line = session.query(LineRecord).filter_by(id="f1r_L1").first()
            assert line.page.id == "f1r"
        finally:
            session.close()

    def test_word_line_relationship(self, populated_store):
        session = populated_store.Session()
        try:
            word = session.query(WordRecord).filter_by(id="f1r_W1").first()
            assert word.line.id == "f1r_L1"
        finally:
            session.close()

    def test_token_line_relationship(self, populated_store):
        session = populated_store.Session()
        try:
            token = (
                session.query(TranscriptionTokenRecord)
                .filter_by(id="f1r_T1")
                .first()
            )
            assert token.line.id == "f1r_TL1"
        finally:
            session.close()
