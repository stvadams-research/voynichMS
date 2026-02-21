"""
Phase 6 Functional — Unit Tests

Tests all 6 modules: formal_system, efficiency, and adversarial
(both analyzers and simulators).
"""
from __future__ import annotations

import pytest
import numpy as np

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared synthetic corpora
# ---------------------------------------------------------------------------

LINES_SIMPLE = [
    ["a", "b", "c", "d"],
    ["e", "f", "g", "h"],
    ["a", "b", "e", "f"],
]

LINES_MEDIUM = [
    ["w" + str(j % 15) for j in range(i, i + 8)]
    for i in range(60)
]

LINES_REPEATED = [["x", "y", "z", "x"]] * 20

LINES_EMPTY: list[list[str]] = []


# ===================================================================
# FormalSystemAnalyzer (formal_system/analyzer)
# ===================================================================

class TestFormalSystemAnalyzerCoverage:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
        self.analyzer = FormalSystemAnalyzer()

    def test_coverage_output_keys(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        for key in ("total_visits", "unique_states", "coverage_ratio",
                     "hapax_ratio", "top_frequencies"):
            assert key in result

    def test_coverage_ratio_range(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        assert 0.0 <= result["coverage_ratio"] <= 1.0

    def test_hapax_ratio_range(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        assert 0.0 <= result["hapax_ratio"] <= 1.0

    def test_total_visits_positive(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        assert result["total_visits"] > 0

    def test_repeated_lines_lower_hapax(self):
        r_varied = self.analyzer.analyze_coverage(LINES_MEDIUM)
        r_repeat = self.analyzer.analyze_coverage(LINES_REPEATED)
        assert r_repeat["hapax_ratio"] <= r_varied["hapax_ratio"]


class TestFormalSystemAnalyzerRedundancy:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
        self.analyzer = FormalSystemAnalyzer()

    def test_redundancy_output_keys(self):
        result = self.analyzer.analyze_redundancy(LINES_MEDIUM)
        for key in ("path_overlap_rate_n3", "redundant_lines_count",
                     "mean_repetition_distance", "total_sequences_n3"):
            assert key in result

    def test_repeated_lines_have_redundancy(self):
        result = self.analyzer.analyze_redundancy(LINES_REPEATED)
        assert result["redundant_lines_count"] > 0

    def test_unique_lines_no_redundancy(self):
        unique_lines = [["w" + str(i), "x" + str(i), "y" + str(i)] for i in range(10)]
        result = self.analyzer.analyze_redundancy(unique_lines)
        assert result["redundant_lines_count"] == 0


class TestFormalSystemAnalyzerErrors:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
        self.analyzer = FormalSystemAnalyzer()

    def test_errors_output_keys(self):
        result = self.analyzer.analyze_errors(LINES_MEDIUM)
        for key in ("detected_deviations_count", "deviation_rate", "sample_deviations"):
            assert key in result

    def test_deviation_rate_range(self):
        result = self.analyzer.analyze_errors(LINES_MEDIUM)
        assert 0.0 <= result["deviation_rate"] <= 1.0

    def test_deterministic_lines_no_deviations(self):
        result = self.analyzer.analyze_errors(LINES_REPEATED)
        assert result["detected_deviations_count"] == 0


class TestFormalSystemAnalyzerExhaustion:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
        self.analyzer = FormalSystemAnalyzer()

    def test_exhaustion_output_keys(self):
        # Need enough lines for at least 2 chunks (200+ lines)
        lines = LINES_MEDIUM * 4  # 240 lines
        result = self.analyzer.analyze_exhaustion(lines)
        for key in ("novelty_curve", "final_novelty_rate",
                     "initial_novelty_rate", "is_converging"):
            assert key in result

    def test_novelty_curve_is_list(self):
        lines = LINES_MEDIUM * 4
        result = self.analyzer.analyze_exhaustion(lines)
        assert isinstance(result["novelty_curve"], list)

    def test_repeated_corpus_converges(self):
        lines = LINES_REPEATED * 15  # 300 lines, all identical
        result = self.analyzer.analyze_exhaustion(lines)
        assert result["is_converging"] is True


class TestFormalSystemAnalyzerFull:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.analyzer import FormalSystemAnalyzer
        self.analyzer = FormalSystemAnalyzer()

    def test_run_full_analysis_keys(self):
        result = self.analyzer.run_full_analysis(LINES_MEDIUM)
        for key in ("coverage", "redundancy", "errors", "exhaustion"):
            assert key in result

    def test_run_full_analysis_empty_lines(self):
        result = self.analyzer.run_full_analysis(LINES_EMPTY)
        # Should not crash on empty input
        assert "coverage" in result


# ===================================================================
# LatticeTraversalSimulator (formal_system/simulators)
# ===================================================================

class TestLatticeTraversalSimulator:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.formal_system.simulators import LatticeTraversalSimulator
        self.SimClass = LatticeTraversalSimulator

    def test_generate_line_length(self):
        sim = self.SimClass(vocab_size=100, seed=42)
        line = sim.generate_line(line_len=8)
        assert len(line) == 8

    def test_generate_corpus_shape(self):
        sim = self.SimClass(vocab_size=100, seed=42)
        corpus = sim.generate_corpus(num_lines=10, line_len=6)
        assert len(corpus) == 10
        assert all(len(line) == 6 for line in corpus)

    def test_tokens_are_strings(self):
        sim = self.SimClass(vocab_size=50, seed=42)
        line = sim.generate_line(5)
        assert all(isinstance(t, str) for t in line)

    def test_reproducibility(self):
        s1 = self.SimClass(vocab_size=100, seed=42)
        s2 = self.SimClass(vocab_size=100, seed=42)
        assert s1.generate_corpus(5, 6) == s2.generate_corpus(5, 6)

    def test_different_seeds_differ(self):
        s1 = self.SimClass(vocab_size=100, seed=42)
        s2 = self.SimClass(vocab_size=100, seed=99)
        c1 = s1.generate_corpus(10, 6)
        c2 = s2.generate_corpus(10, 6)
        assert c1 != c2

    def test_vocab_bounds(self):
        sim = self.SimClass(vocab_size=10, seed=42)
        corpus = sim.generate_corpus(20, 8)
        all_tokens = {t for line in corpus for t in line}
        # Tokens should be from w0..w9
        for t in all_tokens:
            assert t.startswith("w")


class TestExhaustiveFormalSimulator:
    def test_smaller_state_space(self):
        from phase6_functional.formal_system.simulators import ExhaustiveFormalSimulator
        sim = ExhaustiveFormalSimulator(vocab_size=20, seed=42)
        corpus = sim.generate_corpus(50, 5)
        assert len(corpus) == 50


# ===================================================================
# EfficiencyAnalyzer (efficiency/metrics)
# ===================================================================

class TestEfficiencyAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.efficiency.metrics import EfficiencyAnalyzer
        self.analyzer = EfficiencyAnalyzer()

    def test_reuse_suppression_keys(self):
        result = self.analyzer.calculate_reuse_suppression(LINES_MEDIUM)
        for key in ("total_visits", "unique_states", "state_entropy",
                     "reuse_suppression_index"):
            assert key in result

    def test_reuse_suppression_index_range(self):
        result = self.analyzer.calculate_reuse_suppression(LINES_MEDIUM)
        assert 0.0 <= result["reuse_suppression_index"] <= 1.0

    def test_path_efficiency_keys(self):
        result = self.analyzer.calculate_path_efficiency(LINES_MEDIUM)
        for key in ("total_tokens", "unique_tokens", "tokens_per_unique",
                     "path_efficiency"):
            assert key in result

    def test_path_efficiency_range(self):
        result = self.analyzer.calculate_path_efficiency(LINES_MEDIUM)
        assert 0.0 <= result["path_efficiency"] <= 1.0

    def test_redundancy_cost_keys(self):
        result = self.analyzer.calculate_redundancy_cost(LINES_MEDIUM)
        for key in ("total_lines", "unique_lines", "redundancy_rate",
                     "cost_per_unique_line"):
            assert key in result

    def test_redundancy_rate_range(self):
        result = self.analyzer.calculate_redundancy_cost(LINES_MEDIUM)
        assert 0.0 <= result["redundancy_rate"] <= 1.0

    def test_repeated_lines_high_redundancy(self):
        result = self.analyzer.calculate_redundancy_cost(LINES_REPEATED)
        assert result["redundancy_rate"] > 0.9

    def test_compressibility_keys(self):
        result = self.analyzer.calculate_compressibility(LINES_MEDIUM)
        for key in ("raw_size", "compressed_size", "compression_ratio"):
            assert key in result

    def test_compression_ratio_below_one(self):
        # Compressible text should have ratio < 1
        result = self.analyzer.calculate_compressibility(LINES_REPEATED)
        assert result["compression_ratio"] < 1.0

    def test_run_efficiency_audit_keys(self):
        result = self.analyzer.run_efficiency_audit(LINES_MEDIUM)
        for key in ("reuse_suppression", "path_efficiency",
                     "redundancy_cost", "compressibility"):
            assert key in result

    def test_total_tokens_correct(self):
        result = self.analyzer.calculate_path_efficiency(LINES_SIMPLE)
        expected = sum(len(line) for line in LINES_SIMPLE)
        assert result["total_tokens"] == expected


# ===================================================================
# OptimizedLatticeSimulator (efficiency/simulators)
# ===================================================================

class TestOptimizedLatticeSimulator:
    def test_generate_corpus(self):
        from phase6_functional.efficiency.simulators import OptimizedLatticeSimulator
        sim = OptimizedLatticeSimulator(vocab_size=100, seed=42)
        corpus = sim.generate_corpus(10, 8)
        assert len(corpus) == 10
        assert all(len(line) == 8 for line in corpus)

    def test_prefers_cheap_tokens(self):
        from phase6_functional.efficiency.simulators import OptimizedLatticeSimulator
        sim = OptimizedLatticeSimulator(vocab_size=100, seed=42)
        corpus = sim.generate_corpus(50, 8)
        all_tokens = [t for line in corpus for t in line]
        cheap = set(sim.preferred_tokens)
        cheap_ratio = sum(1 for t in all_tokens if t in cheap) / len(all_tokens)
        # Should use cheap tokens more than their share (10%) of vocabulary
        assert cheap_ratio > 0.15

    def test_reproducibility(self):
        from phase6_functional.efficiency.simulators import OptimizedLatticeSimulator
        s1 = OptimizedLatticeSimulator(vocab_size=100, seed=42)
        s2 = OptimizedLatticeSimulator(vocab_size=100, seed=42)
        assert s1.generate_corpus(5, 6) == s2.generate_corpus(5, 6)


# ===================================================================
# AdversarialAnalyzer (adversarial/metrics)
# ===================================================================

class TestAdversarialAnalyzerLearnability:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.adversarial.metrics import AdversarialAnalyzer
        self.analyzer = AdversarialAnalyzer()

    def test_learnability_gradient_keys(self):
        result = self.analyzer.analyze_learnability_gradient(LINES_MEDIUM, steps=5)
        for key in ("fractions", "accuracies", "is_monotonic", "final_accuracy"):
            assert key in result

    def test_fractions_length(self):
        result = self.analyzer.analyze_learnability_gradient(LINES_MEDIUM, steps=5)
        assert len(result["fractions"]) == 5

    def test_accuracies_range(self):
        result = self.analyzer.analyze_learnability_gradient(LINES_MEDIUM, steps=5)
        for acc in result["accuracies"]:
            assert 0.0 <= acc <= 1.0

    def test_deterministic_corpus_high_accuracy(self):
        # Perfectly deterministic => high final accuracy
        lines = [["a", "b", "c", "d"]] * 100
        result = self.analyzer.analyze_learnability_gradient(lines, steps=3)
        assert result["final_accuracy"] > 0.8


class TestAdversarialAnalyzerDecoy:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.adversarial.metrics import AdversarialAnalyzer
        self.analyzer = AdversarialAnalyzer()

    def test_decoy_regularity_keys(self):
        # Need enough lines for 500-line chunks
        lines = LINES_MEDIUM * 10  # 600 lines
        result = self.analyzer.analyze_decoy_regularity(lines)
        for key in ("decoy_rule_count", "mean_decoy_strength", "decoy_rate"):
            assert key in result

    def test_decoy_rate_range(self):
        lines = LINES_MEDIUM * 10
        result = self.analyzer.analyze_decoy_regularity(lines)
        assert 0.0 <= result["decoy_rate"] <= 1.0


class TestAdversarialAnalyzerConditioning:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.adversarial.metrics import AdversarialAnalyzer
        self.analyzer = AdversarialAnalyzer()

    def test_conditioning_sensitivity_keys(self):
        result = self.analyzer.analyze_conditioning_sensitivity(LINES_MEDIUM)
        for key in ("h_base", "h_conditioned", "entropy_reduction", "is_paradoxical"):
            assert key in result

    def test_entropy_values_non_negative(self):
        result = self.analyzer.analyze_conditioning_sensitivity(LINES_MEDIUM)
        assert result["h_base"] >= 0.0
        assert result["h_conditioned"] >= 0.0

    def test_deterministic_has_positive_reduction(self):
        lines = [["a", "b", "c", "d"]] * 100
        result = self.analyzer.analyze_conditioning_sensitivity(lines)
        # Deterministic corpus should not be paradoxical
        assert result["is_paradoxical"] is False


class TestAdversarialAnalyzerFull:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase6_functional.adversarial.metrics import AdversarialAnalyzer
        self.analyzer = AdversarialAnalyzer()

    def test_run_adversarial_audit_keys(self):
        lines = LINES_MEDIUM * 10
        result = self.analyzer.run_adversarial_audit(lines)
        for key in ("learnability", "decoy_regularity", "conditioning_sensitivity"):
            assert key in result


# ===================================================================
# AdversarialLatticeSimulator (adversarial/simulators)
# ===================================================================

class TestAdversarialLatticeSimulator:
    def test_generate_corpus_adversarial(self):
        from phase6_functional.adversarial.simulators import AdversarialLatticeSimulator
        sim = AdversarialLatticeSimulator(vocab_size=100, seed=42)
        corpus = sim.generate_corpus_adversarial(num_lines=20, line_len=6, sections=4)
        assert len(corpus) == 20
        assert all(len(line) == 6 for line in corpus)

    def test_section_rules_populated(self):
        from phase6_functional.adversarial.simulators import AdversarialLatticeSimulator
        sim = AdversarialLatticeSimulator(vocab_size=100, seed=42)
        sim.generate_corpus_adversarial(num_lines=20, line_len=6, sections=4)
        assert len(sim.section_rules) > 0

    def test_reproducibility(self):
        from phase6_functional.adversarial.simulators import AdversarialLatticeSimulator
        s1 = AdversarialLatticeSimulator(vocab_size=100, seed=42)
        s2 = AdversarialLatticeSimulator(vocab_size=100, seed=42)
        c1 = s1.generate_corpus_adversarial(10, 6, 2)
        c2 = s2.generate_corpus_adversarial(10, 6, 2)
        assert c1 == c2
