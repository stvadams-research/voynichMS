import json

import pytest

from foundation.controls.mechanical_reuse import MechanicalReuseGenerator
from foundation.controls.self_citation import SelfCitationGenerator
from foundation.controls.synthetic import SyntheticNullGenerator
from foundation.controls.table_grille import TableGrilleGenerator
from foundation.storage.metadata import (
    MetadataStore,
    PageRecord,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)


@pytest.fixture
def store(tmp_path):
    db_url = f"sqlite:///{tmp_path}/controls.db"
    return MetadataStore(db_url)


def _seed_source_dataset(store: MetadataStore):
    store.add_dataset("source_ds", "fixtures/source_ds")
    store.add_page("source_p1", "source_ds", "img.jpg", "h1", 100, 100)
    store.add_transcription_source("source", "Fixture Source")
    store.add_transcription_line("source_l1", "source", "source_p1", 0, "qokedy chedy qokeedy")
    store.add_transcription_token("source_t1", "source_l1", 0, "qokedy")
    store.add_transcription_token("source_t2", "source_l1", 1, "chedy")
    store.add_transcription_token("source_t3", "source_l1", 2, "qokeedy")


def _tokens_for_dataset(store: MetadataStore, dataset_id: str):
    session = store.Session()
    try:
        rows = (
            session.query(TranscriptionTokenRecord.content)
            .join(
                TranscriptionLineRecord,
                TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id,
            )
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(
                PageRecord.id,
                TranscriptionLineRecord.line_index,
                TranscriptionTokenRecord.token_index,
            )
            .all()
        )
        return [r[0] for r in rows]
    finally:
        session.close()


def test_synthetic_null_generator_produces_tokens_and_is_deterministic(store):
    _seed_source_dataset(store)
    generator = SyntheticNullGenerator(store)
    params = {"num_pages": 1, "lines_per_page": 2, "tokens_per_line": 4}

    generator.generate("source_ds", "synthetic_a", seed=42, params=params)
    tokens_a = _tokens_for_dataset(store, "synthetic_a")
    generator.generate("source_ds", "synthetic_b", seed=42, params=params)
    tokens_b = _tokens_for_dataset(store, "synthetic_b")

    assert tokens_a
    assert len(tokens_a) == 8
    assert tokens_a == tokens_b


def test_self_citation_generator_is_deterministic(store):
    _seed_source_dataset(store)
    generator = SelfCitationGenerator(store)
    params = {"target_tokens": 60, "pool_size": 20, "mutation_rate": 0.15}

    generator.generate("source_ds", "self_a", seed=42, params=params)
    tokens_a = _tokens_for_dataset(store, "self_a")
    generator.generate("source_ds", "self_b", seed=42, params=params)
    tokens_b = _tokens_for_dataset(store, "self_b")

    assert tokens_a
    assert len(tokens_a) == 60
    assert tokens_a == tokens_b


def test_table_grille_generator_is_deterministic(store):
    _seed_source_dataset(store)
    generator = TableGrilleGenerator(store)
    params = {"target_tokens": 60}

    generator.generate("source_ds", "table_a", seed=42, params=params)
    tokens_a = _tokens_for_dataset(store, "table_a")
    generator.generate("source_ds", "table_b", seed=42, params=params)
    tokens_b = _tokens_for_dataset(store, "table_b")

    assert tokens_a
    assert len(tokens_a) == 60
    assert tokens_a == tokens_b


def test_mechanical_reuse_generator_produces_tokens_and_is_deterministic(store, tmp_path, monkeypatch):
    _seed_source_dataset(store)

    grammar_dir = tmp_path / "data" / "derived"
    grammar_dir.mkdir(parents=True, exist_ok=True)
    grammar_path = grammar_dir / "voynich_grammar.json"
    grammar = {
        "transitions": {
            "<START>": {"a": 1.0},
            "a": {"<END>": 1.0},
        },
        "positions": {},
        "word_lengths": {"1": 1.0},
    }
    grammar_path.write_text(json.dumps(grammar), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    generator = MechanicalReuseGenerator(store)
    params = {"target_tokens": 40, "pool_size": 10, "tokens_per_page": 8}

    generator.generate("source_ds", "mech_a", seed=42, params=params)
    tokens_a = _tokens_for_dataset(store, "mech_a")
    generator.generate("source_ds", "mech_b", seed=42, params=params)
    tokens_b = _tokens_for_dataset(store, "mech_b")

    assert tokens_a
    assert len(tokens_a) == 40
    assert tokens_a == tokens_b
