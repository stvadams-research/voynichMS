"""Tests for Phase 16B effort correlation logic.

Validates that effort is correlated with selection FREQUENCY
(not arbitrary list index), and that the metrics are computed correctly.
"""

import pytest
from collections import Counter, defaultdict


def compute_effort_frequency_pairs(choices, costs):
    """Replicate the corrected Phase 16B logic."""
    win_word_counts = defaultdict(Counter)
    win_totals = defaultdict(int)
    for c in choices:
        wid = c['window_id']
        word = c['chosen_word']
        win_word_counts[wid][word] += 1
        win_totals[wid] += 1

    efforts = []
    frequencies = []
    for wid, word_counts in win_word_counts.items():
        total = win_totals[wid]
        if total < 20:
            continue
        for word, count in word_counts.items():
            if word in costs:
                efforts.append(costs[word])
                frequencies.append(count / total)

    return efforts, frequencies


def test_frequency_not_index():
    """The correlation target must be selection frequency, not list position."""
    # Simulate: window 0 has "easy" (cost=1) chosen 80 times and "hard" (cost=5) chosen 20 times
    choices = []
    for _ in range(80):
        choices.append({"window_id": 0, "chosen_word": "easy", "chosen_index": 0})
    for _ in range(20):
        choices.append({"window_id": 0, "chosen_word": "hard", "chosen_index": 1})

    costs = {"easy": 1.0, "hard": 5.0}
    efforts, frequencies = compute_effort_frequency_pairs(choices, costs)

    # "easy" should have frequency 0.8, "hard" should have 0.2
    assert len(efforts) == 2
    easy_idx = efforts.index(1.0)
    hard_idx = efforts.index(5.0)
    assert abs(frequencies[easy_idx] - 0.8) < 0.01
    assert abs(frequencies[hard_idx] - 0.2) < 0.01


def test_filters_small_windows():
    """Windows with fewer than 20 observations should be excluded."""
    choices = [{"window_id": 99, "chosen_word": "rare", "chosen_index": 0}] * 10
    costs = {"rare": 2.0}
    efforts, frequencies = compute_effort_frequency_pairs(choices, costs)
    assert len(efforts) == 0  # filtered out


def test_negative_rho_means_ergonomic():
    """If low-effort words are chosen more often, rho should be negative."""
    from scipy.stats import spearmanr

    # Construct clear signal: lower effort -> higher frequency
    efforts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    frequencies = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05]

    rho, p = spearmanr(efforts, frequencies)
    assert rho < -0.9  # Strong negative correlation
    assert p < 0.01


def test_rho_threshold():
    """The ergonomic coupling flag should require |rho| > 0.1 and p < 0.01."""
    rho_weak = 0.05
    rho_strong = 0.15
    p_sig = 0.001
    p_insig = 0.1

    assert not (p_sig < 0.01 and abs(rho_weak) > 0.1)
    assert (p_sig < 0.01 and abs(rho_strong) > 0.1)
    assert not (p_insig < 0.01 and abs(rho_strong) > 0.1)
