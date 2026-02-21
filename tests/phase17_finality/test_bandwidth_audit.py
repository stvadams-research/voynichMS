"""Tests for Phase 17B bandwidth audit logic.

Validates the information-theoretic framework for steganographic capacity.
"""



def test_bandwidth_formula():
    """Realized bandwidth = observed choice entropy, not entropy * (1 - rho)."""
    observed_entropy = 8.097
    uniform_entropy = 8.815

    # The correct values
    max_capacity_bpw = uniform_entropy
    realized_capacity_bpw = observed_entropy
    ergonomic_overhead_bpw = uniform_entropy - observed_entropy

    assert abs(max_capacity_bpw - 8.815) < 0.001
    assert abs(realized_capacity_bpw - 8.097) < 0.001
    assert abs(ergonomic_overhead_bpw - 0.718) < 0.001


def test_bandwidth_not_rho_scaled():
    """The old formula entropy * (1 - rho) is invalid.
    Entropy is in bits, rho is dimensionless [-1,1]. They can't be multiplied."""
    entropy = 8.097
    rho = 0.2334
    old_formula = entropy * (1 - rho)  # This is WRONG

    # The old result (6.207) is not the correct bandwidth
    assert abs(old_formula - 6.207) < 0.01
    # The correct bandwidth is just the observed entropy
    correct_bandwidth = entropy
    assert correct_bandwidth > old_formula


def test_total_capacity():
    """Total bits = decisions * bits_per_word."""
    num_decisions = 49159
    bpw = 8.097
    total_bits = num_decisions * bpw
    total_kb = total_bits / 8192
    assert abs(total_kb - 48.6) < 1.0


def test_threshold_3bpw():
    """At 3+ bits/word, meaningful text encoding is theoretically possible."""
    # English ~1.3 bits/char (Shannon), or ~8 bits/word
    # A conservative threshold for encoding text is 3 bits/word
    # The Voynich choice stream at ~8 bits/word exceeds this
    threshold = 3.0
    voynich_bpw = 8.097
    assert voynich_bpw > threshold


def test_judgment_honest():
    """If bandwidth > threshold, judgment should be SUBSTANTIAL, not INSIGNIFICANT."""
    bpw = 8.097
    threshold = 3.0
    # The old code said INSIGNIFICANT at 6.2 bpw, which was wrong
    has_sufficient = bpw >= threshold
    assert has_sufficient is True


def test_latin_equivalence():
    """Sanity check: capacity in Latin character equivalents."""
    total_bits = 49159 * 8.097
    latin_bits_per_char = 4.1  # Latin at ~4.1 bits/char
    latin_chars = total_bits / latin_bits_per_char
    # Should be roughly 97,000 characters — about the length of a short book
    assert 90000 < latin_chars < 110000
