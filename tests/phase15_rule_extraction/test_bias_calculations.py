"""Tests for Phase 15C bias and compressibility calculations."""

import math
import pytest
from phase15_rule_extraction.bias import calculate_entropy, BiasAnalyzer

def test_entropy_uniform():
    """Uniform distribution over N items should give log2(N) bits."""
    data = [0, 1, 2, 3] * 100
    ent = calculate_entropy(data)
    assert abs(ent - 2.0) < 0.01

def test_entropy_deterministic():
    """Single-valued data should have 0 entropy."""
    data = [42] * 100
    ent = calculate_entropy(data)
    assert ent == 0.0

def test_entropy_empty():
    assert calculate_entropy([]) == 0.0

def test_analyzer_window_bias():
    # Create 100 entries for window 'w1'
    # Alternating 0 and 1. 
    # candidates_count=4 implies max_entropy = log2(4) = 2.0
    # Observed entropy = log2(2) = 1.0
    # Skew = (2.0 - 1.0) / 2.0 = 0.5
    choices = [
        {'window_id': 'w1', 'chosen_index': i % 2, 'candidates_count': 4}
        for i in range(100)
    ]
    
    analyzer = BiasAnalyzer(choices)
    stats = analyzer.analyze_window_bias(min_samples=10)
    
    assert len(stats) == 1
    w1 = stats[0]
    assert w1['window_id'] == 'w1'
    assert abs(w1['entropy'] - 1.0) < 0.01
    assert abs(w1['max_entropy'] - 2.0) < 0.01
    assert abs(w1['skew'] - 0.5) < 0.01

def test_analyzer_compressibility():
    # 1000 choices of '0' -> highly compressible
    choices = [{'chosen_index': 0, 'candidates_count': 256}] * 1000
    analyzer = BiasAnalyzer(choices)
    res = analyzer.analyze_compressibility()
    
    # Real data (all zeros) should be very compressible
    assert res['real_ratio'] < 0.1  
    
    # Simulated data (random) should be less compressible
    assert res['sim_ratio'] > 0.1   
    
    # Improvement should be positive and significant
    assert res['improvement'] > 0.5
