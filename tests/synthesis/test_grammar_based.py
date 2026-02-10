import json

from synthesis.generators.grammar_based import GrammarBasedGenerator


def _write_grammar(path, transitions):
    grammar = {
        "transitions": transitions,
        "positions": {},
        "word_lengths": {"1": 1.0},
    }
    path.write_text(json.dumps(grammar), encoding="utf-8")


def test_generate_word_is_deterministic_for_same_seed(tmp_path):
    grammar_path = tmp_path / "grammar.json"
    _write_grammar(
        grammar_path,
        {
            "<START>": {"a": 0.5, "b": 0.5},
            "a": {"a": 0.2, "b": 0.2, "<END>": 0.6},
            "b": {"a": 0.2, "b": 0.2, "<END>": 0.6},
        },
    )

    g1 = GrammarBasedGenerator(grammar_path, seed=42)
    g2 = GrammarBasedGenerator(grammar_path, seed=42)

    words1 = [g1.generate_word() for _ in range(30)]
    words2 = [g2.generate_word() for _ in range(30)]

    assert words1 == words2


def test_generate_word_varies_with_different_seed(tmp_path):
    grammar_path = tmp_path / "grammar.json"
    _write_grammar(
        grammar_path,
        {
            "<START>": {"a": 0.5, "b": 0.5},
            "a": {"a": 0.2, "b": 0.2, "<END>": 0.6},
            "b": {"a": 0.2, "b": 0.2, "<END>": 0.6},
        },
    )

    g1 = GrammarBasedGenerator(grammar_path, seed=1)
    g2 = GrammarBasedGenerator(grammar_path, seed=2)

    words1 = [g1.generate_word() for _ in range(30)]
    words2 = [g2.generate_word() for _ in range(30)]

    assert words1 != words2


def test_generate_word_respects_max_length(tmp_path):
    grammar_path = tmp_path / "looping_grammar.json"
    _write_grammar(
        grammar_path,
        {
            "<START>": {"a": 1.0},
            "a": {"a": 1.0},
        },
    )

    generator = GrammarBasedGenerator(grammar_path, seed=7)
    word = generator.generate_word(max_length=5)

    assert word == "aaaaa"
