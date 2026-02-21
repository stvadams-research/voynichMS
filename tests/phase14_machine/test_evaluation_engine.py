import pytest

from phase14_machine.evaluation_engine import EvaluationEngine


def test_calculate_coverage():
    vocab = {"word1", "word2", "word3"}
    engine = EvaluationEngine(vocab)

    tokens = ["word1", "word2", "unknown", "word3"]
    assert engine.calculate_coverage(tokens) == 0.75

def test_calculate_admissibility():
    vocab = {"a", "b", "c", "d"}
    engine = EvaluationEngine(vocab)

    # K=4 windows. No drift allowed in this simplified view if we use 0, 2 jumps.
    # Simple lattice: a -> window 2, c -> window 0
    lattice_map = {"a": 2, "b": 0, "c": 0}
    window_contents = {0: ["a", "b"], 1: [], 2: ["c"], 3: ["d"]}

    # Path: a (start in win 0) -> c (in win 2) -> b (in win 0)
    # 1. 'a' in win 0. Valid. current_window -> 2.
    # 2. 'c' in win 2. Valid. current_window -> 0.
    # 3. 'b' in win 0. Valid. current_window -> 0.
    lines = [["a", "c", "b"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert res["admissibility_rate"] == 1.0

    # Failing path: a -> d (d is in window 3)
    # current_window=0. 'a' valid. current_window -> 2.
    # next word 'd'. check_win: 1, 2, 3.
    # 3 is a neighbor of 2 (drift +1). so it IS valid.
    # Let's use window 1 which is empty.
    # Failing path: a -> b (b is in window 0)
    # current_window=0. 'a' valid. current_window -> 2.
    # next word 'b'. check_win: 1, 2, 3. None have 'b'.
    lines = [["a", "b"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    # first 'a' is valid. 'b' is not in neighborhood of win 2.
    assert res["admissibility_rate"] == 0.5

def test_calculate_overgeneration():
    vocab = {"a", "b", "c"}
    engine = EvaluationEngine(vocab)

    real_lines = [["a", "b", "c"]]
    syn_lines = [["a", "b", "c"], ["a", "c", "b"]]

    res = engine.calculate_overgeneration(syn_lines, real_lines)
    # real bigrams: (a,b), (b,c)
    # syn bigrams: (a,b), (b,c), (a,c), (c,b)
    # unattested: (a,c), (c,b)
    assert res["BUR"]["unattested_count"] == 2
    assert res["BUR"]["rate"] == 0.5


# ── OOV Suffix Recovery Tests (Phase 14O) ────────────────────────────

def test_resolve_oov_window_hit():
    """Known suffix maps to expected window."""
    suffix_map = {"dy": 18, "in": 22, "ol": 5}
    # "chedy" ends with "dy" → window 18
    assert EvaluationEngine.resolve_oov_window("chedy", suffix_map) == 18
    # "daiin" ends with "in" → window 22
    assert EvaluationEngine.resolve_oov_window("daiin", suffix_map) == 22
    # "shol" ends with "ol" → window 5
    assert EvaluationEngine.resolve_oov_window("shol", suffix_map) == 5


def test_resolve_oov_window_miss():
    """No matching suffix returns None."""
    suffix_map = {"dy": 18, "in": 22}
    assert EvaluationEngine.resolve_oov_window("qokx", suffix_map) is None


def test_resolve_oov_window_short():
    """Word equal to suffix returns None for that suffix (length guard)."""
    suffix_map = {"dy": 18, "in": 22}
    # "dy" has len 2 == len("dy"), guard prevents "dy" suffix match.
    # No other suffix in map matches, so returns None.
    assert EvaluationEngine.resolve_oov_window("dy", suffix_map) is None
    # Single-char words can't match any multi-char suffix
    assert EvaluationEngine.resolve_oov_window("x", suffix_map) is None


def test_admissibility_with_suffix_map():
    """OOV word recovered via suffix map produces consolidated result."""
    vocab = {"a", "b"}
    engine = EvaluationEngine(vocab)

    # 3 windows: a,b in win 0; empty win 1; empty win 2
    lattice_map = {"a": 0, "b": 0}
    window_contents = {0: ["a", "b"], 1: [], 2: []}

    # Line has OOV word "xdy" between in-vocab words
    suffix_map = {"dy": 0}  # "xdy" → window 0
    lines = [["a", "xdy", "b"]]

    res = engine.calculate_admissibility(
        lines, lattice_map, window_contents, suffix_window_map=suffix_map
    )

    # "a" and "b" are in vocab → 2 in-vocab transitions
    assert res["total_clamped_tokens"] == 2
    # "xdy" is OOV → 1 OOV total, 1 recovered (suffix "dy" → win 0)
    assert res["oov_total"] == 1
    assert res["oov_recovered"] == 1
    # consolidated_admissibility includes OOV recovered tokens
    assert "consolidated_admissibility" in res


def test_admissibility_without_suffix_map():
    """Without suffix_window_map, behavior is identical to original."""
    vocab = {"a", "b"}
    engine = EvaluationEngine(vocab)

    lattice_map = {"a": 0, "b": 0}
    window_contents = {0: ["a", "b"], 1: [], 2: []}
    lines = [["a", "xdy", "b"]]

    # Without suffix map
    res_no_map = engine.calculate_admissibility(
        lines, lattice_map, window_contents
    )

    # Should not have OOV keys
    assert "oov_total" not in res_no_map
    assert "consolidated_admissibility" not in res_no_map

    # Core metrics should be the same as always
    assert res_no_map["total_clamped_tokens"] == 2
    assert "admissibility_rate" in res_no_map
