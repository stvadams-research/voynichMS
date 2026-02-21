import json

import pytest

pytestmark = pytest.mark.unit

from phase5_mechanism.generators.pool_generator import PoolGenerator


def _write_grammar(path):
    grammar = {
        "transitions": {
            "<START>": {"a": 0.5, "b": 0.5},
            "a": {"<END>": 1.0},
            "b": {"<END>": 1.0},
        },
        "positions": {},
        "word_lengths": {"1": 1.0},
    }
    path.write_text(json.dumps(grammar), encoding="utf-8")


def test_pool_generator_is_deterministic_for_fixed_seed(tmp_path):
    grammar_path = tmp_path / "grammar.json"
    _write_grammar(grammar_path)

    g1 = PoolGenerator(grammar_path, pool_size=8, seed=42)
    g2 = PoolGenerator(grammar_path, pool_size=8, seed=42)

    tokens1 = g1.generate(target_tokens=200)
    tokens2 = g2.generate(target_tokens=200)

    assert tokens1 == tokens2


def test_pool_replenishment_updates_pool_state(tmp_path):
    grammar_path = tmp_path / "grammar.json"
    _write_grammar(grammar_path)

    generator = PoolGenerator(grammar_path, pool_size=2, seed=1)

    counter = {"n": 0}

    def next_word():
        value = f"w{counter['n']}"
        counter["n"] += 1
        return value

    class AlwaysReplenishRNG:
        @staticmethod
        def choice(seq):
            return seq[0]

        @staticmethod
        def random():
            return 0.0  # Always trigger replenishment.

        @staticmethod
        def randint(a, b):
            return 0

    generator.generator.generate_word = next_word
    generator.rng = AlwaysReplenishRNG()

    tokens = generator.generate(target_tokens=5)

    assert tokens == ["w0", "w2", "w3", "w4", "w5"]
    assert generator.pool == ["w6", "w1"]
