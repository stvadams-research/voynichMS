"""
Phase 5 Mechanism — Unit Tests for analysis/signature modules

Tests the non-simulator modules that don't require grammar_path.
Simulators are excluded because they depend on GrammarBasedGenerator
and grammar file fixtures.
"""
from __future__ import annotations

import math
import pytest
import numpy as np

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared synthetic data
# ---------------------------------------------------------------------------

LINES_SIMPLE = [
    ["a", "b", "c", "d"],
    ["e", "f", "g", "h"],
    ["a", "b", "e", "f"],
    ["c", "d", "g", "h"],
]

LINES_MEDIUM = [
    ["w" + str(j % 20) for j in range(i, i + 6)]
    for i in range(50)
]

LINES_DETERMINISTIC = [
    ["x", "y", "z", "x"],
    ["x", "y", "z", "x"],
    ["x", "y", "z", "x"],
]

TOKENS_FLAT = [t for line in LINES_MEDIUM for t in line]


# ===================================================================
# PathCollisionTester (large_object/collision_testing)
# ===================================================================

class TestPathCollisionTester:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.large_object.collision_testing import PathCollisionTester
        self.tester = PathCollisionTester(context_len=2)

    def test_empty_input(self):
        result = self.tester.calculate_successor_consistency([])
        assert result["mean_consistency"] == 0.0

    def test_single_short_line(self):
        result = self.tester.calculate_successor_consistency([["a", "b"]])
        # Too short for context_len=2 successors
        assert "mean_consistency" in result

    def test_deterministic_lines_high_consistency(self):
        result = self.tester.calculate_successor_consistency(LINES_DETERMINISTIC)
        assert result["mean_consistency"] >= 0.9

    def test_output_keys(self):
        result = self.tester.calculate_successor_consistency(LINES_MEDIUM)
        assert "mean_consistency" in result
        assert "num_recurring_contexts" in result

    def test_context_len_1(self):
        from phase5_mechanism.large_object.collision_testing import PathCollisionTester
        tester = PathCollisionTester(context_len=1)
        result = tester.calculate_successor_consistency(LINES_SIMPLE)
        assert "mean_consistency" in result

    def test_consistency_range(self):
        result = self.tester.calculate_successor_consistency(LINES_MEDIUM)
        assert 0.0 <= result["mean_consistency"] <= 1.0


# ===================================================================
# TokenFeatureExtractor (dependency_scope/features)
# ===================================================================

class TestTokenFeatureExtractor:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.dependency_scope.features import TokenFeatureExtractor
        self.extractor = TokenFeatureExtractor()

    def test_extract_features_keys(self):
        features = self.extractor.extract_features("hello")
        for key in ("length", "prefix_1", "prefix_2", "suffix_1", "suffix_2",
                     "has_repeated", "vowel_like_count", "char_entropy"):
            assert key in features, f"Missing key: {key}"

    def test_length_correct(self):
        assert self.extractor.extract_features("abc")["length"] == 3
        assert self.extractor.extract_features("x")["length"] == 1

    def test_prefix_suffix(self):
        f = self.extractor.extract_features("hello")
        assert f["prefix_1"] == "h"
        assert f["prefix_2"] == "he"
        assert f["suffix_1"] == "o"
        assert f["suffix_2"] == "lo"

    def test_single_char_token(self):
        f = self.extractor.extract_features("x")
        assert f["prefix_1"] == "x"
        assert f["suffix_1"] == "x"

    def test_has_repeated_flag(self):
        f_repeated = self.extractor.extract_features("aab")
        f_unique = self.extractor.extract_features("abc")
        assert f_repeated["has_repeated"] == 1.0
        assert f_unique["has_repeated"] == 0.0

    def test_char_entropy_single_char_is_zero(self):
        f = self.extractor.extract_features("aaaa")
        assert f["char_entropy"] == 0.0

    def test_char_entropy_positive_for_varied(self):
        f = self.extractor.extract_features("abcd")
        assert f["char_entropy"] > 0.0

    def test_positional_features_keys(self):
        line = ["a", "b", "c", "d"]
        pf = self.extractor.extract_positional_features(line, 0)
        for key in ("pos_index", "pos_ratio", "is_start", "is_end"):
            assert key in pf

    def test_positional_start_end(self):
        line = ["a", "b", "c"]
        assert self.extractor.extract_positional_features(line, 0)["is_start"] == 1.0
        assert self.extractor.extract_positional_features(line, 0)["is_end"] == 0.0
        assert self.extractor.extract_positional_features(line, 2)["is_end"] == 1.0
        assert self.extractor.extract_positional_features(line, 2)["is_start"] == 0.0

    def test_positional_ratio(self):
        line = ["a", "b", "c", "d"]
        pf = self.extractor.extract_positional_features(line, 1)
        # pos_ratio = index / len(line) = 1/4 = 0.25
        assert abs(pf["pos_ratio"] - 0.25) < 0.01


# ===================================================================
# DependencyScopeAnalyzer (dependency_scope/analysis)
# ===================================================================

class TestDependencyScopeAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.dependency_scope.analysis import DependencyScopeAnalyzer
        self.analyzer = DependencyScopeAnalyzer()

    def test_predictive_lift_keys(self):
        result = self.analyzer.analyze_predictive_lift(LINES_MEDIUM)
        for key in ("h_node", "h_node_feat", "predictive_lift", "rel_lift"):
            assert key in result

    def test_predictive_lift_non_negative(self):
        result = self.analyzer.analyze_predictive_lift(LINES_MEDIUM)
        assert result["predictive_lift"] >= 0.0

    def test_equivalence_splitting_keys(self):
        result = self.analyzer.analyze_equivalence_splitting(LINES_MEDIUM)
        for key in ("h_node", "h_node_pos", "pos_predictive_lift", "pos_rel_lift"):
            assert key in result

    def test_equivalence_splitting_non_negative(self):
        result = self.analyzer.analyze_equivalence_splitting(LINES_MEDIUM)
        assert result["pos_predictive_lift"] >= 0.0

    def test_empty_lines(self):
        result = self.analyzer.analyze_predictive_lift([])
        assert "h_node" in result


# ===================================================================
# SlotBoundaryDetector (deterministic_grammar/boundary_detection)
# ===================================================================

class TestSlotBoundaryDetector:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.deterministic_grammar.boundary_detection import SlotBoundaryDetector
        self.detector = SlotBoundaryDetector(max_pos=10)

    def test_positional_entropy_keys(self):
        result = self.detector.calculate_positional_entropy(LINES_MEDIUM)
        assert isinstance(result, dict)
        # Should have entries for positions 0..min(max_pos, line_len)
        assert 0 in result

    def test_positional_entropy_non_negative(self):
        result = self.detector.calculate_positional_entropy(LINES_MEDIUM)
        for pos, entropy in result.items():
            assert entropy >= 0.0

    def test_deterministic_position_zero_entropy(self):
        # All lines start with same token
        lines = [["START", "b", "c"], ["START", "d", "e"], ["START", "f", "g"]]
        result = self.detector.calculate_positional_entropy(lines)
        assert result[0] == 0.0

    def test_successor_sharpness_length(self):
        result = self.detector.calculate_successor_sharpness(LINES_MEDIUM)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_successor_sharpness_non_negative(self):
        result = self.detector.calculate_successor_sharpness(LINES_MEDIUM)
        for val in result:
            assert val >= 0.0


# ===================================================================
# EntryPointAnalyzer (entry_selection/prefix_analysis)
# ===================================================================

class TestEntryPointAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.entry_selection.prefix_analysis import EntryPointAnalyzer
        self.analyzer = EntryPointAnalyzer()

    def test_start_distribution_keys(self):
        result = self.analyzer.calculate_start_distribution(LINES_SIMPLE)
        for key in ("num_lines", "unique_starts", "start_entropy", "max_freq_start", "top_starts"):
            assert key in result

    def test_num_lines_correct(self):
        result = self.analyzer.calculate_start_distribution(LINES_SIMPLE)
        assert result["num_lines"] == len(LINES_SIMPLE)

    def test_unique_starts_count(self):
        lines = [["a", "b"], ["a", "c"], ["d", "e"]]
        result = self.analyzer.calculate_start_distribution(lines)
        assert result["unique_starts"] == 2  # "a" and "d"

    def test_start_entropy_uniform(self):
        # All different starts => max entropy
        lines = [["a", "x"], ["b", "x"], ["c", "x"], ["d", "x"]]
        result = self.analyzer.calculate_start_distribution(lines)
        assert result["start_entropy"] > 1.0

    def test_start_entropy_single_start(self):
        lines = [["a", "x"], ["a", "y"], ["a", "z"]]
        result = self.analyzer.calculate_start_distribution(lines)
        assert result["start_entropy"] == 0.0

    def test_adjacency_coupling_keys(self):
        result = self.analyzer.calculate_adjacency_coupling(LINES_SIMPLE)
        for key in ("num_pairs", "start_word_matches", "coupling_score"):
            assert key in result

    def test_adjacency_coupling_count(self):
        result = self.analyzer.calculate_adjacency_coupling(LINES_SIMPLE)
        assert result["num_pairs"] == len(LINES_SIMPLE) - 1

    def test_coupling_score_range(self):
        result = self.analyzer.calculate_adjacency_coupling(LINES_MEDIUM)
        assert 0.0 <= result["coupling_score"] <= 1.0

    def test_empty_lines(self):
        result = self.analyzer.calculate_start_distribution([])
        assert result.get("num_lines", 0) == 0


# ===================================================================
# LatentStateAnalyzer (constraint_geometry/latent_state)
# ===================================================================

class TestLatentStateAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.constraint_geometry.latent_state import LatentStateAnalyzer
        self.analyzer = LatentStateAnalyzer(top_n=100)

    def test_basic_output_keys(self):
        result = self.analyzer.estimate_dimensionality(TOKENS_FLAT)
        if "error" not in result:
            assert "vocab_size" in result
            assert "singular_values" in result
            assert "effective_rank_90" in result

    def test_vocab_size_correct(self):
        result = self.analyzer.estimate_dimensionality(TOKENS_FLAT)
        if "error" not in result:
            assert result["vocab_size"] == len(set(TOKENS_FLAT))

    def test_effective_rank_positive(self):
        result = self.analyzer.estimate_dimensionality(TOKENS_FLAT)
        if "error" not in result:
            assert result["effective_rank_90"] > 0

    def test_empty_input(self):
        result = self.analyzer.estimate_dimensionality([])
        assert "error" in result or result.get("vocab_size", 0) == 0


# ===================================================================
# LocalityResetAnalyzer (constraint_geometry/locality_resets)
# ===================================================================

class TestLocalityResetAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.constraint_geometry.locality_resets import LocalityResetAnalyzer
        self.analyzer = LocalityResetAnalyzer(min_freq=2)

    def test_basic_output_keys(self):
        boundaries = [len(TOKENS_FLAT) // 3, 2 * len(TOKENS_FLAT) // 3]
        result = self.analyzer.analyze_resets(TOKENS_FLAT, boundaries)
        assert "avg_successor_overlap" in result
        assert "reset_score" in result

    def test_no_boundaries(self):
        result = self.analyzer.analyze_resets(TOKENS_FLAT, [])
        assert "reset_score" in result

    def test_reset_score_range(self):
        boundaries = [50, 100, 150]
        result = self.analyzer.analyze_resets(TOKENS_FLAT, boundaries)
        assert 0.0 <= result["reset_score"] <= 1.0


# ===================================================================
# ParsimonyAnalyzer (parsimony/analysis)
# ===================================================================

class TestParsimonyAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.parsimony.analysis import ParsimonyAnalyzer
        self.analyzer = ParsimonyAnalyzer()

    def test_node_explosion_keys(self):
        result = self.analyzer.analyze_node_explosion(LINES_MEDIUM)
        for key in ("vocab_size", "state_count", "explosion_factor", "transition_count"):
            assert key in result

    def test_explosion_factor_geq_1(self):
        result = self.analyzer.analyze_node_explosion(LINES_MEDIUM)
        assert result["explosion_factor"] >= 1.0

    def test_state_count_geq_vocab(self):
        result = self.analyzer.analyze_node_explosion(LINES_MEDIUM)
        assert result["state_count"] >= result["vocab_size"]

    def test_residual_dependency_keys(self):
        result = self.analyzer.analyze_residual_dependency(LINES_MEDIUM)
        for key in ("h_word_pos", "h_word_pos_hist", "entropy_reduction", "rel_reduction"):
            assert key in result

    def test_entropy_reduction_non_negative(self):
        result = self.analyzer.analyze_residual_dependency(LINES_MEDIUM)
        assert result["entropy_reduction"] >= 0.0

    def test_empty_lines(self):
        result = self.analyzer.analyze_node_explosion([])
        assert result["vocab_size"] == 0 or result.get("state_count", 0) == 0


# ===================================================================
# TopologySignatureAnalyzer (topology_collapse/signatures)
# ===================================================================

class TestTopologySignatureAnalyzer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.topology_collapse.signatures import TopologySignatureAnalyzer
        self.analyzer = TopologySignatureAnalyzer(prefix_len=2)

    def test_overlap_keys(self):
        result = self.analyzer.analyze_overlap(LINES_MEDIUM)
        for key in ("total_prefixes", "unique_prefixes", "collision_rate", "max_collision_depth"):
            assert key in result

    def test_collision_rate_range(self):
        result = self.analyzer.analyze_overlap(LINES_MEDIUM)
        assert 0.0 <= result["collision_rate"] <= 1.0

    def test_coverage_keys(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        for key in ("unique_nodes_visited", "gini_coefficient", "mean_visitation"):
            assert key in result

    def test_gini_range(self):
        result = self.analyzer.analyze_coverage(LINES_MEDIUM)
        assert 0.0 <= result["gini_coefficient"] <= 1.0

    def test_convergence_keys(self):
        result = self.analyzer.analyze_convergence(LINES_MEDIUM)
        assert "avg_successor_convergence" in result
        assert "max_successor_fanout" in result

    def test_empty_lines(self):
        result = self.analyzer.analyze_overlap([])
        assert result["total_prefixes"] == 0


# ===================================================================
# CopyingSignatureTest (tests/copying_signatures)
# ===================================================================

class TestCopyingSignatureTest:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.tests.copying_signatures import CopyingSignatureTest
        self.test_obj = CopyingSignatureTest(window_size=10, max_edit_dist=1)

    def test_basic_output_keys(self):
        tokens = ["abc", "abd", "xyz", "abc", "abe", "xyz"] * 5
        result = self.test_obj.calculate_variant_clustering(tokens)
        assert "clustering_score" in result

    def test_clustering_score_non_negative(self):
        tokens = ["abc", "abd", "xyz", "abc", "abe", "xyz"] * 5
        result = self.test_obj.calculate_variant_clustering(tokens)
        assert result["clustering_score"] >= 0.0

    def test_identical_tokens_have_high_clustering(self):
        tokens = ["abc"] * 30
        result = self.test_obj.calculate_variant_clustering(tokens)
        assert result["clustering_score"] > 0.0

    def test_edit_distance_method(self):
        assert self.test_obj._edit_distance("abc", "abc") == 0
        assert self.test_obj._edit_distance("abc", "abd") == 1
        assert self.test_obj._edit_distance("abc", "xyz") == 3
        assert self.test_obj._edit_distance("", "abc") == 3
        assert self.test_obj._edit_distance("abc", "") == 3


# ===================================================================
# TableSignatureTest (tests/table_signatures)
# ===================================================================

class TestTableSignatureTest:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.tests.table_signatures import TableSignatureTest
        self.test_obj = TableSignatureTest(min_freq=3)

    def test_basic_output_keys(self):
        result = self.test_obj.calculate_successor_sharpness(TOKENS_FLAT)
        assert "mean_successor_entropy" in result

    def test_insufficient_data(self):
        result = self.test_obj.calculate_successor_sharpness(["a", "b"])
        assert result.get("status") == "insufficient_data" or result["mean_successor_entropy"] == 0.0

    def test_deterministic_successors_low_entropy(self):
        # Token "a" always followed by "b", "b" always by "c"
        tokens = ["a", "b", "c"] * 20
        result = self.test_obj.calculate_successor_sharpness(tokens)
        assert result["mean_successor_entropy"] < 0.5

    def test_entropy_non_negative(self):
        result = self.test_obj.calculate_successor_sharpness(TOKENS_FLAT)
        assert result["mean_successor_entropy"] >= 0.0


# ===================================================================
# WorkflowParameterInferrer (workflow/parameter_inference)
# ===================================================================

class TestWorkflowParameterInferrer:
    @pytest.fixture(autouse=True)
    def _setup(self):
        from phase5_mechanism.workflow.parameter_inference import WorkflowParameterInferrer
        self.inferrer = WorkflowParameterInferrer()

    def test_line_parameters_keys(self):
        result = self.inferrer.infer_line_parameters(["a", "b", "c", "a"])
        for key in ("num_tokens", "num_unique", "ttr", "successor_entropy"):
            assert key in result

    def test_ttr_correct(self):
        result = self.inferrer.infer_line_parameters(["a", "b", "c", "a"])
        assert abs(result["ttr"] - 3 / 4) < 0.01

    def test_empty_line(self):
        result = self.inferrer.infer_line_parameters([])
        assert result == {} or result.get("num_tokens", 0) == 0

    def test_aggregate_keys(self):
        result = self.inferrer.aggregate_distributions(LINES_MEDIUM)
        for key in ("mean_ttr", "std_ttr", "mean_entropy", "std_entropy", "num_lines"):
            assert key in result

    def test_aggregate_num_lines_correct(self):
        result = self.inferrer.aggregate_distributions(LINES_MEDIUM)
        assert result["num_lines"] == len(LINES_MEDIUM)

    def test_aggregate_empty(self):
        result = self.inferrer.aggregate_distributions([])
        assert result == {} or result.get("num_lines", 0) == 0

    def test_ttr_range(self):
        result = self.inferrer.aggregate_distributions(LINES_MEDIUM)
        assert 0.0 <= result["mean_ttr"] <= 1.0
