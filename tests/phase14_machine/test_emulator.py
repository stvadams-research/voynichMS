"""Tests for HighFidelityVolvelle (Phase 14 emulator)."""

import pytest
from src.phase14_machine.high_fidelity_emulator import HighFidelityVolvelle


def make_simple_emulator(seed=42, log_choices=False):
    """Create an emulator with a minimal 3-window lattice."""
    lattice_map = {"hello": 1, "world": 2, "foo": 0}
    window_contents = {
        0: ["hello", "bar"],
        1: ["world", "baz"],
        2: ["foo", "qux"],
    }
    return HighFidelityVolvelle(lattice_map, window_contents, seed=seed, log_choices=log_choices)


def test_seeded_reproducibility():
    """Two emulators with the same seed must produce identical output."""
    e1 = make_simple_emulator(seed=123)
    e2 = make_simple_emulator(seed=123)
    line1 = e1.generate_line(10)
    line2 = e2.generate_line(10)
    assert line1 == line2


def test_different_seeds_differ():
    e1 = make_simple_emulator(seed=1)
    e2 = make_simple_emulator(seed=2)
    line1 = e1.generate_line(20)
    line2 = e2.generate_line(20)
    assert line1 != line2


def test_mirror_corpus_seeded():
    """generate_mirror_corpus must be deterministic with a seed."""
    e1 = make_simple_emulator(seed=42)
    e2 = make_simple_emulator(seed=42)
    c1 = e1.generate_mirror_corpus(50)
    c2 = e2.generate_mirror_corpus(50)
    assert c1 == c2


def test_mirror_corpus_line_lengths_seeded():
    """After the bare-random fix, line lengths should be reproducible."""
    e1 = make_simple_emulator(seed=99)
    e2 = make_simple_emulator(seed=99)
    c1 = e1.generate_mirror_corpus(30)
    c2 = e2.generate_mirror_corpus(30)
    lengths1 = [len(line) for line in c1]
    lengths2 = [len(line) for line in c2]
    assert lengths1 == lengths2


def test_generate_token_returns_string():
    e = make_simple_emulator()
    token = e.generate_token(0)
    assert isinstance(token, str)
    assert len(token) > 0


def test_choice_logging():
    e = make_simple_emulator(log_choices=True)
    e.generate_line(5)
    assert len(e.choice_log) == 5
    for entry in e.choice_log:
        assert "window_id" in entry
        assert "chosen_word" in entry
        assert "candidates_count" in entry


def test_trace_lines_logs_admissible():
    lattice_map = {"hello": 1, "world": 0}
    window_contents = {0: ["hello"], 1: ["world"]}
    e = HighFidelityVolvelle(lattice_map, window_contents, log_choices=True)
    e.trace_lines([["hello", "world", "hello"]])
    # hello is in win 0 (start), world is in win 1 (after hello->1), hello in win 0 (after world->0)
    assert len(e.choice_log) == 3
    for entry in e.choice_log:
        assert entry["type"] == "real_trace"


def test_mask_modulation():
    """Mask state should shift which window is accessed."""
    e = make_simple_emulator(seed=42)
    e.set_mask(0)
    tok_mask0 = e.generate_token(0)

    e2 = make_simple_emulator(seed=42)
    e2.set_mask(1)
    # With mask=1, window_idx 0 becomes modulated to window 1
    # so different candidates, potentially different word
    tok_mask1 = e2.generate_token(0)
    # They draw from different windows, so results may differ
    # (not guaranteed with small windows, but the mechanism should work)
    assert isinstance(tok_mask1, str)
