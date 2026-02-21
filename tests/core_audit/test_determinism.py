import json
import random

import pytest

from phase1_foundation.core.randomness import RandomnessViolationError, get_randomness_controller
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator

pytestmark = pytest.mark.integration

def test_grammar_generator_determinism(tmp_path):
    # Create a dummy grammar file
    grammar = {
        "transitions": {
            "<START>": {"a": 1.0},
            "a": {"b": 0.5, "c": 0.5, "<END>": 0.0},
            "b": {"<END>": 1.0},
            "c": {"<END>": 1.0}
        },
        "positions": {},
        "word_lengths": {"1": 1.0}
    }
    grammar_path = tmp_path / "grammar.json"
    with open(grammar_path, "w") as f:
        json.dump(grammar, f)

    # Same seed should produce same output
    gen1 = GrammarBasedGenerator(grammar_path, seed=42)
    gen2 = GrammarBasedGenerator(grammar_path, seed=42)

    words1 = [gen1.generate_word() for _ in range(10)]
    words2 = [gen2.generate_word() for _ in range(10)]

    assert words1 == words2

    # Different seed should likely produce different output
    gen3 = GrammarBasedGenerator(grammar_path, seed=43)
    words3 = [gen3.generate_word() for _ in range(10)]

    assert words1 != words3

def test_randomness_controller_forbidden():
    controller = get_randomness_controller()
    controller.patch_random_module()

    try:
        with controller.forbidden_context("test"), pytest.raises(RandomnessViolationError):
            random.random()
    finally:
        controller.unpatch_random_module()

def test_randomness_controller_seeded():
    controller = get_randomness_controller()
    controller.patch_random_module()

    try:
        with controller.seeded_context("test", seed=123):
            val1 = random.random()

        with controller.seeded_context("test", seed=123):
            val2 = random.random()

        assert val1 == val2
    finally:
        controller.unpatch_random_module()

def test_unrestricted_context():
    controller = get_randomness_controller()
    controller.patch_random_module()

    try:
        with controller.forbidden_context("test"), controller.unrestricted_context():
            # Should not raise
            random.random()
    finally:
        controller.unpatch_random_module()
