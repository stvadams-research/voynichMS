"""Tests for strict vs drift admissibility and chance baselines."""

import pytest
from phase14_machine.evaluation_engine import EvaluationEngine


def make_engine_and_lattice():
    """Create a simple 4-window lattice for testing."""
    vocab = {"a", "b", "c", "d", "e"}
    engine = EvaluationEngine(vocab)

    # 4 windows: 0=[a,b], 1=[c], 2=[d], 3=[e]
    lattice_map = {"a": 1, "b": 2, "c": 0, "d": 3, "e": 0}
    window_contents = {0: ["a", "b"], 1: ["c"], 2: ["d"], 3: ["e"]}
    return engine, lattice_map, window_contents


def test_strict_and_drift_both_reported():
    engine, lattice_map, window_contents = make_engine_and_lattice()
    lines = [["a", "c", "a"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert "strict_admissibility" in res
    assert "drift_admissibility" in res
    assert "strict_chance_baseline" in res
    assert "drift_chance_baseline" in res


def test_strict_equals_drift_when_all_exact():
    """When every word lands in the exact predicted window, strict == drift."""
    engine, lattice_map, window_contents = make_engine_and_lattice()
    # a is in win 0, maps to win 1. c is in win 1, maps to win 0. a is in win 0.
    lines = [["a", "c", "a"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert res["strict_admissibility"] == res["drift_admissibility"]
    assert res["strict_admissibility"] == 1.0


def test_drift_higher_than_strict():
    """When a word is in an adjacent window but not the current one,
    drift should count it but strict should not."""
    engine, lattice_map, window_contents = make_engine_and_lattice()
    # Start at window 0. 'a' is in win 0 (strict match). Maps to win 1.
    # 'd' is in win 2, which is neighbor of win 1 (drift match, not strict).
    lines = [["a", "d"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert res["strict_admissibility"] < res["drift_admissibility"]
    assert res["strict_admissibility"] == 0.5  # only 'a' is strict
    assert res["drift_admissibility"] == 1.0   # both valid with drift


def test_chance_baselines_are_reasonable():
    engine, lattice_map, window_contents = make_engine_and_lattice()
    lines = [["a"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    # With 4 windows of sizes [2, 1, 1, 1] and 5 total vocab:
    # avg_window_size = 5/4 = 1.25
    # strict_chance = 1.25/5 = 0.25
    # drift_chance = min(1.0, 3 * 0.25) = 0.75
    assert abs(res["strict_chance_baseline"] - 0.25) < 0.01
    assert abs(res["drift_chance_baseline"] - 0.75) < 0.01


def test_backward_compatible_key():
    """The old 'admissibility_rate' key should still exist and equal drift."""
    engine, lattice_map, window_contents = make_engine_and_lattice()
    lines = [["a", "c"]]
    res = engine.calculate_admissibility(lines, lattice_map, window_contents)
    assert res["admissibility_rate"] == res["drift_admissibility"]
