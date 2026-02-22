"""Tests for Phase 15C bias and compressibility calculations.

Tests the core logic extracted from run_15c_bias_and_compressibility.py.
"""

import math
from collections import Counter


def calculate_entropy(data):
    """Replicate the entropy function from 15C."""
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def test_entropy_uniform():
    """Uniform distribution over N items should give log2(N) bits."""
    data = [0, 1, 2, 3] * 100
    ent = calculate_entropy(data)
    assert abs(ent - 2.0) < 0.01  # log2(4) = 2.0


def test_entropy_deterministic():
    """Single-valued data should have 0 entropy."""
    data = [42] * 100
    ent = calculate_entropy(data)
    assert ent == 0.0


def test_entropy_empty():
    assert calculate_entropy([]) == 0.0


def test_skew_calculation_per_window():
    """Skew should use the specific window's candidate count, not a global one."""
    # Window with 8 candidates (max_ent = 3.0), perfectly uniform selection
    uniform_data = list(range(8)) * 50
    ent = calculate_entropy(uniform_data)
    max_ent = math.log2(8)
    skew = (max_ent - ent) / max_ent
    assert abs(skew) < 0.01  # Near-zero skew for uniform

    # Window with 8 candidates, but only 2 ever chosen (high skew)
    biased_data = [0, 1] * 200
    ent_biased = calculate_entropy(biased_data)
    skew_biased = (max_ent - ent_biased) / max_ent
    assert skew_biased > 0.3  # Significant skew


def test_skew_different_window_sizes():
    """Two windows with same observed entropy but different sizes should have different skew."""
    # Both windows: observed entropy = 1.0 bit (two equally likely outcomes)
    data = [0, 1] * 100
    ent = calculate_entropy(data)

    # Window A has 4 candidates: max_ent = 2.0, skew = (2.0 - 1.0) / 2.0 = 0.5
    skew_a = (math.log2(4) - ent) / math.log2(4)
    # Window B has 256 candidates: max_ent = 8.0, skew = (8.0 - 1.0) / 8.0 = 0.875
    skew_b = (math.log2(256) - ent) / math.log2(256)

    assert skew_b > skew_a
    assert abs(skew_a - 0.5) < 0.01
    assert abs(skew_b - 0.875) < 0.01


def test_compression_improvement_sign():
    """Positive improvement = real is more compressible than baseline.
    Negative = real is less compressible."""
    # Formula: (sim_ratio - real_ratio) / sim_ratio
    sim_ratio = 0.7
    real_compressible = 0.5   # better compression
    real_incompressible = 0.9  # worse compression

    improvement_good = (sim_ratio - real_compressible) / sim_ratio
    improvement_bad = (sim_ratio - real_incompressible) / sim_ratio

    assert improvement_good > 0   # real is more compressible
    assert improvement_bad < 0    # real is less compressible
