import numpy as np

from phase1_foundation.core.queries import QueryEngine, get_lines_from_store, get_tokens_and_boundaries
from phase1_foundation.storage.metadata import MetadataStore


def _build_store(tmp_path):
    store = MetadataStore(f"sqlite:///{tmp_path}/queries.db")
    store.add_dataset("ds", "generated")
    store.add_page("p1", "ds", "img.jpg", "hash", 100, 100)
    store.add_transcription_source("src", "source")

    store.add_line("l1", "p1", 0, {"x": 0, "y": 0, "w": 1, "h": 1}, 1.0)
    store.add_word("w1", "l1", 0, {"x": 0, "y": 0, "w": 1, "h": 1}, {}, 1.0)
    store.add_word("w2", "l1", 1, {"x": 1, "y": 0, "w": 1, "h": 1}, {}, 1.0)

    store.add_transcription_line("tl1", "src", "p1", 0, "foo bar")
    store.add_transcription_token("tt1", "tl1", 0, "foo")
    store.add_transcription_token("tt2", "tl1", 1, "bar")

    store.add_transcription_line("tl2", "src", "p1", 1, "baz")
    store.add_transcription_token("tt3", "tl2", 0, "baz")

    store.add_word_alignment("w1", "tt1", "exact", 1.0)
    store.add_word_alignment("w2", "tt2", "exact", 1.0)

    store.add_region("r1", "p1", "coarse", "dummy", {"x": 0, "y": 0, "w": 1, "h": 1}, {}, 1.0)
    store.add_region("r2", "p1", "coarse", "dummy", {"x": 1, "y": 0, "w": 1, "h": 1}, {}, 1.0)
    store.add_region("r3", "p1", "coarse", "dummy", {"x": 2, "y": 0, "w": 1, "h": 1}, {}, 1.0)
    store.add_region_embedding("r1", "emb", np.array([1.0, 0.0], dtype=np.float32).tobytes())
    store.add_region_embedding("r2", "emb", np.array([0.9, 0.1], dtype=np.float32).tobytes())
    store.add_region_embedding("r3", "emb", np.array([0.0, 1.0], dtype=np.float32).tobytes())

    return store


def test_get_lines_from_store_and_boundaries(tmp_path):
    store = _build_store(tmp_path)

    lines = get_lines_from_store(store, "ds")
    tokens, boundaries = get_tokens_and_boundaries(store, "ds")

    assert lines == [["foo", "bar"], ["baz"]]
    assert tokens == ["foo", "bar", "baz"]
    assert boundaries == [1]


def test_query_engine_get_words_for_token(tmp_path):
    store = _build_store(tmp_path)
    engine = QueryEngine(store)

    results = engine.get_words_for_token("foo")
    assert len(results) == 1
    assert results[0]["word_id"] == "w1"
    assert results[0]["token"] == "foo"


def test_query_engine_find_similar_regions_uses_embedding_similarity(tmp_path):
    store = _build_store(tmp_path)
    engine = QueryEngine(store)

    results = engine.find_similar_regions("r1", limit=2)
    assert len(results) == 2
    assert results[0]["region_id"] == "r2"
    assert results[0]["score"] > results[1]["score"]
