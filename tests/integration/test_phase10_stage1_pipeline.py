from __future__ import annotations

from phase10_admissibility.stage1_pipeline import (
    CorpusBundle,
    extract_rule,
    run_method_h,
    run_method_j,
    summarize_stage1,
)


class DummyGenerator:
    def __init__(self, seed_tokens: list[str]):
        self.seed_tokens = list(seed_tokens)
        self.cursor = 0

    def generate(self, target_tokens: int) -> dict[str, object]:
        tokens: list[str] = []
        while len(tokens) < target_tokens:
            token = self.seed_tokens[self.cursor % len(self.seed_tokens)]
            tokens.append(token)
            self.cursor += 1
        lines = [tokens[i : i + 4] for i in range(0, len(tokens), 4)]
        return {"tokens": tokens, "lines": lines}


def _build_bundle(dataset_id: str, label: str, lines: list[list[str]]) -> CorpusBundle:
    pages = [lines]
    tokens = [token for line in lines for token in line]
    return CorpusBundle(dataset_id=dataset_id, label=label, tokens=tokens, lines=lines, pages=pages)


def test_extract_rule_nth_and_line_edges() -> None:
    bundle = _build_bundle(
        "voynich_real",
        "Voynich",
        [["a", "b", "c"], ["d", "e", "f"], ["g", "h"]],
    )

    assert extract_rule(bundle, "line_initial_tokens") == ["a", "d", "g"]
    assert extract_rule(bundle, "line_final_tokens") == ["c", "f", "h"]
    assert extract_rule(bundle, "nth_token_3") == ["c", "f"]


def test_run_method_h_returns_valid_decision() -> None:
    voynich = _build_bundle(
        "voynich_real",
        "Voynich",
        [["qokedy", "qokedy", "dain"], ["qokain", "otedy", "ol"]],
    )
    comparison = [
        _build_bundle("generator_a", "Generator A", [["abc", "abd", "abe"], ["abf", "abg"]]),
        _build_bundle("generator_b", "Generator B", [["tok", "tok", "tok"], ["tok", "tok"]]),
    ]

    result = run_method_h(voynich, comparison)
    assert result["status"] == "ok"
    assert result["decision"] in {"closure_strengthened", "closure_weakened", "indeterminate"}
    assert "voynich_real" in result["features"]


def test_run_method_j_with_dummy_generators() -> None:
    voynich = _build_bundle(
        "voynich_real",
        "Voynich",
        [["a", "b", "c", "d"], ["e", "f", "g", "h"], ["i", "j", "k", "l"]],
    )

    generators = {
        "line_reset_markov": DummyGenerator(["a", "a", "b", "c"]),
        "line_reset_backoff": DummyGenerator(["d", "e", "f", "g"]),
        "line_reset_persistence": DummyGenerator(["h", "i", "j", "k"]),
    }

    result = run_method_j(
        voynich_bundle=voynich,
        generators=generators,
        target_tokens=40,
        null_runs=6,
        seed=42,
    )
    assert result["status"] == "ok"
    assert result["decision"] in {"closure_strengthened", "closure_weakened", "indeterminate"}
    assert "line_initial_tokens" in result["null_summary"]


def test_summarize_stage1_decision_logic() -> None:
    summary_weakened = summarize_stage1(
        {
            "H": {"decision": "closure_strengthened"},
            "J": {"decision": "closure_weakened"},
            "K": {"decision": "closure_strengthened"},
        }
    )
    assert summary_weakened["stage_decision"] == "closure_weakened"

    summary_strengthened = summarize_stage1(
        {
            "H": {"decision": "closure_strengthened"},
            "J": {"decision": "closure_strengthened"},
            "K": {"decision": "closure_strengthened"},
        }
    )
    assert summary_strengthened["stage_decision"] == "closure_strengthened"
