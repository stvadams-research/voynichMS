"""
Phase 10 Admissibility — Unit Tests

Tests pipeline utility functions, dataclasses, metric calculations,
stage transitions, and priority gate logic. Complements the existing
integration tests in tests/integration/test_phase10_stage*_pipeline.py
which test high-level method decisions.
"""
from __future__ import annotations

import math
import pytest
import numpy as np

pytestmark = pytest.mark.unit

from phase10_admissibility.stage1_pipeline import (
    CorpusBundle,
    Stage1Config,
    extract_rule,
    token_entropy,
    compression_ratio,
    compression_bits_per_token,
    type_token_ratio,
    bigram_mutual_information,
    conditional_entropy_metrics,
    zipf_alpha,
    line_edge_entropies,
    sequence_metrics,
    extraction_metrics,
    summarize_stage1,
    now_utc_iso,
)

from phase10_admissibility.stage4_pipeline import (
    Stage4Config,
    collect_method_decisions,
    interpret_priority_urgent,
    synthesize_stage4,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bundle(
    dataset_id: str = "test",
    label: str = "Test",
    lines: list[list[str]] | None = None,
) -> CorpusBundle:
    if lines is None:
        lines = [["a", "b", "c", "d"], ["e", "f", "g", "h"], ["a", "b", "e", "f"]]
    tokens = [t for line in lines for t in line]
    pages = [lines]
    return CorpusBundle(
        dataset_id=dataset_id, label=label,
        tokens=tokens, lines=lines, pages=pages,
    )


BUNDLE_SMALL = _make_bundle()
TOKENS_VARIED = ["alpha", "beta", "gamma", "delta", "epsilon"] * 40
TOKENS_REPEAT = ["x"] * 100
TOKENS_ZIPF = (
    ["a"] * 100 + ["b"] * 50 + ["c"] * 25 + ["d"] * 12 +
    ["e"] * 6 + ["f"] * 3 + ["g"] * 2 + ["h"] * 1
)


# ===================================================================
# CorpusBundle dataclass
# ===================================================================

class TestCorpusBundle:
    def test_creation(self):
        b = _make_bundle("ds1", "Dataset 1")
        assert b.dataset_id == "ds1"
        assert b.label == "Dataset 1"

    def test_tokens_match_lines(self):
        b = _make_bundle()
        expected = [t for line in b.lines for t in line]
        assert b.tokens == expected

    def test_pages_contain_lines(self):
        b = _make_bundle()
        assert b.pages == [b.lines]


# ===================================================================
# Stage1Config dataclass
# ===================================================================

class TestStage1Config:
    def test_defaults(self):
        cfg = Stage1Config()
        assert cfg.seed == 42
        assert cfg.target_tokens == 120000
        assert cfg.method_j_null_runs == 100
        assert cfg.method_k_runs == 100

    def test_custom_values(self):
        cfg = Stage1Config(seed=7, target_tokens=5000, method_j_null_runs=10)
        assert cfg.seed == 7
        assert cfg.target_tokens == 5000


# ===================================================================
# Sequence Metrics (stage1_pipeline)
# ===================================================================

class TestTokenEntropy:
    def test_single_token_zero_entropy(self):
        assert token_entropy(TOKENS_REPEAT) == 0.0

    def test_positive_entropy(self):
        assert token_entropy(TOKENS_VARIED) > 0.0

    def test_uniform_distribution_max_entropy(self):
        # 5 equally frequent tokens => entropy = log2(5) ≈ 2.322
        h = token_entropy(TOKENS_VARIED)
        expected = math.log2(5)
        assert abs(h - expected) < 0.01

    def test_empty_sequence(self):
        h = token_entropy([])
        assert h == 0.0 or math.isnan(h)

    @pytest.mark.parametrize("tokens,expected_min,expected_max", [
        (["a"] * 50, 0.0, 0.0),                    # single type
        (["a", "b"] * 25, 0.9, 1.1),                # 2 equally frequent
        (["a", "b", "c", "d"] * 10, 1.9, 2.1),      # 4 equally frequent
    ])
    def test_entropy_parametrized(self, tokens, expected_min, expected_max):
        h = token_entropy(tokens)
        assert expected_min <= h <= expected_max


class TestCompressionRatio:
    def test_repeated_compresses_well(self):
        r = compression_ratio(TOKENS_REPEAT)
        assert r < 0.5  # Highly compressible

    def test_positive(self):
        assert compression_ratio(TOKENS_VARIED) > 0.0

    def test_ratio_below_one(self):
        # Any reasonable text should compress to below raw size
        r = compression_ratio(TOKENS_VARIED)
        assert r < 1.0


class TestCompressionBitsPerToken:
    def test_positive(self):
        bpt = compression_bits_per_token(TOKENS_VARIED)
        assert bpt > 0.0

    def test_repeated_fewer_bits(self):
        bpt_repeat = compression_bits_per_token(TOKENS_REPEAT)
        bpt_varied = compression_bits_per_token(TOKENS_VARIED)
        assert bpt_repeat < bpt_varied


class TestTypeTokenRatio:
    def test_all_same(self):
        assert type_token_ratio(TOKENS_REPEAT) == pytest.approx(1 / 100)

    def test_all_unique(self):
        tokens = list("abcdefghij")
        assert type_token_ratio(tokens) == 1.0

    def test_range(self):
        assert 0.0 <= type_token_ratio(TOKENS_VARIED) <= 1.0


class TestBigramMutualInformation:
    def test_non_negative(self):
        mi = bigram_mutual_information(TOKENS_VARIED)
        assert mi >= 0.0

    def test_deterministic_high_mi(self):
        # Perfectly deterministic sequence
        tokens = ["a", "b"] * 100
        mi = bigram_mutual_information(tokens)
        assert mi > 0.5


class TestConditionalEntropyMetrics:
    def test_output_keys(self):
        result = conditional_entropy_metrics(TOKENS_VARIED)
        for key in ("bigram_cond_entropy", "trigram_cond_entropy",
                     "bigram_mutual_information"):
            assert key in result

    def test_trigram_leq_bigram(self):
        result = conditional_entropy_metrics(TOKENS_VARIED)
        # More context => less uncertainty
        assert result["trigram_cond_entropy"] <= result["bigram_cond_entropy"] + 0.01


class TestZipfAlpha:
    def test_positive_for_zipf_distribution(self):
        alpha = zipf_alpha(TOKENS_ZIPF)
        assert alpha > 0.5

    def test_near_zero_for_uniform(self):
        tokens = list("abcde") * 100
        alpha = zipf_alpha(tokens)
        # Uniform distribution has no power-law, alpha should be small
        assert alpha < 0.5

    def test_rank_limit_parameter(self):
        alpha_500 = zipf_alpha(TOKENS_ZIPF, rank_limit=500)
        alpha_10 = zipf_alpha(TOKENS_ZIPF, rank_limit=10)
        # Both should be positive
        assert alpha_500 > 0
        assert alpha_10 > 0


class TestLineEdgeEntropies:
    def test_output_keys(self):
        lines = [["a", "b", "c"], ["d", "e", "f"], ["a", "g", "h"]]
        result = line_edge_entropies(lines)
        assert "line_initial_entropy" in result
        assert "line_final_entropy" in result

    def test_single_start_zero_entropy(self):
        lines = [["x", "b", "c"], ["x", "d", "e"], ["x", "f", "g"]]
        result = line_edge_entropies(lines)
        assert result["line_initial_entropy"] == 0.0


class TestSequenceMetrics:
    def test_output_keys(self):
        result = sequence_metrics(TOKENS_VARIED)
        for key in ("entropy", "compression_ratio", "bits_per_token",
                     "type_token_ratio", "bigram_mutual_information"):
            assert key in result


class TestExtractionMetrics:
    def test_output_keys(self):
        result = extraction_metrics(TOKENS_VARIED)
        for key in ("entropy", "compression_ratio", "type_token_ratio",
                     "bigram_mutual_information"):
            assert key in result


# ===================================================================
# Extraction Rules (stage1_pipeline)
# ===================================================================

class TestExtractRule:
    def test_line_initial_tokens(self):
        bundle = _make_bundle(lines=[["a", "b", "c"], ["d", "e", "f"]])
        assert extract_rule(bundle, "line_initial_tokens") == ["a", "d"]

    def test_line_final_tokens(self):
        bundle = _make_bundle(lines=[["a", "b", "c"], ["d", "e", "f"]])
        assert extract_rule(bundle, "line_final_tokens") == ["c", "f"]

    def test_nth_token(self):
        bundle = _make_bundle(lines=[["a", "b", "c"], ["d", "e", "f"], ["g", "h"]])
        result = extract_rule(bundle, "nth_token_3")
        assert result == ["c", "f"]  # Line 3 too short

    def test_word_initial_glyphs(self):
        bundle = _make_bundle(lines=[["alpha", "beta"], ["gamma", "delta"]])
        result = extract_rule(bundle, "word_initial_glyphs")
        assert result == ["a", "b", "g", "d"]

    def test_paragraph_initial_tokens(self):
        bundle = _make_bundle(
            lines=[["a", "b", "c"], ["d", "e", "f"]],
        )
        result = extract_rule(bundle, "paragraph_initial_tokens")
        # Page-initial tokens: first token of each page
        assert "a" in result

    def test_empty_bundle(self):
        bundle = _make_bundle(lines=[[]])
        result = extract_rule(bundle, "line_initial_tokens")
        assert isinstance(result, list)


# ===================================================================
# Stage 1 Summarization
# ===================================================================

class TestSummarizeStage1:
    def test_all_strengthened(self):
        result = summarize_stage1({
            "H": {"decision": "closure_strengthened"},
            "J": {"decision": "closure_strengthened"},
            "K": {"decision": "closure_strengthened"},
        })
        assert result["stage_decision"] == "closure_strengthened"

    def test_any_weakened_propagates(self):
        result = summarize_stage1({
            "H": {"decision": "closure_strengthened"},
            "J": {"decision": "closure_weakened"},
            "K": {"decision": "indeterminate"},
        })
        assert result["stage_decision"] == "closure_weakened"

    def test_indeterminate_without_weakened(self):
        result = summarize_stage1({
            "H": {"decision": "closure_strengthened"},
            "J": {"decision": "indeterminate"},
            "K": {"decision": "closure_strengthened"},
        })
        assert result["stage_decision"] in ("indeterminate", "closure_strengthened")

    def test_output_keys(self):
        result = summarize_stage1({
            "H": {"decision": "indeterminate"},
            "J": {"decision": "indeterminate"},
            "K": {"decision": "indeterminate"},
        })
        assert "status" in result
        assert "stage" in result
        assert "method_decisions" in result


# ===================================================================
# now_utc_iso utility
# ===================================================================

class TestNowUtcIso:
    def test_returns_string(self):
        assert isinstance(now_utc_iso(), str)

    def test_contains_t_separator(self):
        ts = now_utc_iso()
        assert "T" in ts or "t" in ts


# ===================================================================
# Stage 3 Priority Gate (stage3_pipeline)
# ===================================================================

class TestPriorityGate:
    @pytest.fixture(autouse=True)
    def _import(self):
        from phase10_admissibility.stage3_pipeline import evaluate_stage3_priority_gate
        self.gate = evaluate_stage3_priority_gate

    def test_urgent_on_weakened_stage1(self):
        result = self.gate(
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "indeterminate",
            }},
            stage2_summary={"method_decisions": {
                "G": "closure_strengthened",
                "I": "closure_strengthened",
            }},
        )
        assert result["priority"] == "urgent"

    def test_lower_when_all_strengthened(self):
        result = self.gate(
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_strengthened",
                "K": "closure_strengthened",
            }},
            stage2_summary={"method_decisions": {
                "G": "closure_strengthened",
                "I": "closure_strengthened",
            }},
        )
        assert result["priority"] == "lower"

    def test_none_inputs(self):
        result = self.gate(stage1_summary=None, stage2_summary=None)
        assert "priority" in result

    def test_output_keys(self):
        result = self.gate(
            stage1_summary={"method_decisions": {"H": "indeterminate"}},
            stage2_summary={"method_decisions": {"G": "indeterminate"}},
        )
        for key in ("status", "priority", "reason"):
            assert key in result


# ===================================================================
# Stage 3 TokenAttributes (stage3_pipeline)
# ===================================================================

class TestTokenAttributes:
    @pytest.fixture(autouse=True)
    def _import(self):
        from phase10_admissibility.stage3_pipeline import TokenAttributes
        self.TokenAttributes = TokenAttributes

    def test_creation(self):
        attr_stack = np.zeros((6, 10), dtype=np.int64)
        index = np.arange(10, dtype=np.int64)
        ta = self.TokenAttributes(
            attr_stack=attr_stack,
            attr_names=["a", "b", "c", "d", "e", "f"],
            index=index,
        )
        assert ta.length == 10

    def test_length_property(self):
        attr_stack = np.zeros((6, 25), dtype=np.int64)
        index = np.arange(25, dtype=np.int64)
        ta = self.TokenAttributes(
            attr_stack=attr_stack,
            attr_names=["a", "b", "c", "d", "e", "f"],
            index=index,
        )
        assert ta.length == 25


# ===================================================================
# Stage 4 Decision Collection
# ===================================================================

class TestCollectMethodDecisions:
    def test_all_stages_present(self):
        result = collect_method_decisions(
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "indeterminate",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "indeterminate",
                "I": "closure_strengthened",
            }},
            stage3_summary={"method_decisions": {"F": "indeterminate"}},
        )
        assert "H" in result
        assert "J" in result
        assert "K" in result
        assert "G" in result
        assert "I" in result
        assert "F" in result

    def test_none_stages(self):
        result = collect_method_decisions(
            stage1_summary=None,
            stage1b_replication=None,
            stage2_summary=None,
            stage3_summary=None,
        )
        assert isinstance(result, dict)

    def test_stage1b_overrides(self):
        result = collect_method_decisions(
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "closure_weakened",
            }},
            stage1b_replication={
                "method_j_status_after_gate": "closure_strengthened",
                "method_k_status_after_gate": "closure_weakened",
            },
            stage2_summary={"method_decisions": {"G": "indeterminate", "I": "indeterminate"}},
            stage3_summary={"method_decisions": {"F": "indeterminate"}},
        )
        # Stage1b should override J
        assert result["J"] == "closure_strengthened"


# ===================================================================
# Stage 4 Urgency Interpretation
# ===================================================================

class TestInterpretPriorityUrgent:
    def test_urgent_interpretation(self):
        result = interpret_priority_urgent(
            stage3_priority_gate={"priority": "urgent", "reason": "test"},
            stage1_summary={"method_decisions": {"J": "closure_weakened"}},
            stage2_summary={"method_decisions": {"G": "indeterminate", "I": "closure_strengthened"}},
        )
        assert result["priority"] == "urgent"
        assert "not itself evidence" in result["meaning"]

    def test_lower_interpretation(self):
        result = interpret_priority_urgent(
            stage3_priority_gate={"priority": "lower", "reason": "all ok"},
            stage1_summary={"method_decisions": {"J": "closure_strengthened"}},
            stage2_summary={"method_decisions": {"G": "closure_strengthened", "I": "closure_strengthened"}},
        )
        assert result["priority"] == "lower"

    def test_none_gate(self):
        result = interpret_priority_urgent(
            stage3_priority_gate=None,
            stage1_summary=None,
            stage2_summary=None,
        )
        assert "priority" in result


# ===================================================================
# Stage 4 Synthesis
# ===================================================================

class TestSynthesizeStage4:
    def test_mixed_results_tension(self):
        result = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "closure_weakened",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "indeterminate",
                "I": "closure_strengthened",
            }},
            stage3_summary={"method_decisions": {"F": "indeterminate"}},
            stage3_priority_gate={"priority": "urgent", "reason": "test"},
        )
        assert result["aggregate_class"] == "mixed_results_tension"
        assert result["closure_status"] == "in_tension"

    def test_all_strengthened_upgrades(self):
        result = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_strengthened",
                "K": "closure_strengthened",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "closure_strengthened",
                "I": "closure_strengthened",
            }},
            stage3_summary={"method_decisions": {"F": "closure_strengthened"}},
            stage3_priority_gate={"priority": "lower", "reason": "all ok"},
        )
        assert result["aggregate_class"] == "closure_upgraded"
        assert result["closure_status"] == "upgraded"

    def test_defeated_reopens(self):
        result = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary={"method_decisions": {
                "H": "closure_defeated",
                "J": "closure_strengthened",
                "K": "closure_strengthened",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "closure_strengthened",
                "I": "closure_strengthened",
            }},
            stage3_summary={"method_decisions": {"F": "closure_strengthened"}},
            stage3_priority_gate={"priority": "lower", "reason": "all ok"},
        )
        assert result["aggregate_class"] == "closure_revised"
        assert result["closure_status"] == "reopen_domain"

    def test_output_keys(self):
        result = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary={"method_decisions": {
                "H": "indeterminate",
                "J": "indeterminate",
                "K": "indeterminate",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "indeterminate",
                "I": "indeterminate",
            }},
            stage3_summary={"method_decisions": {"F": "indeterminate"}},
            stage3_priority_gate=None,
        )
        for key in ("status", "stage", "method_decisions", "outcome_counts",
                     "aggregate_class", "closure_status", "closure_reason"):
            assert key in result

    def test_outcome_counts_sum(self):
        result = synthesize_stage4(
            config=Stage4Config(),
            stage1_summary={"method_decisions": {
                "H": "closure_strengthened",
                "J": "closure_weakened",
                "K": "indeterminate",
            }},
            stage1b_replication=None,
            stage2_summary={"method_decisions": {
                "G": "indeterminate",
                "I": "closure_strengthened",
            }},
            stage3_summary={"method_decisions": {"F": "closure_strengthened"}},
            stage3_priority_gate=None,
        )
        counts = result["outcome_counts"]
        total = sum(counts.values())
        assert total == 6  # 6 methods total


# ===================================================================
# Stage 4 Config
# ===================================================================

class TestStage4Config:
    def test_default(self):
        cfg = Stage4Config()
        assert "structurally indistinguishable" in cfg.baseline_closure_statement

    def test_custom(self):
        cfg = Stage4Config(baseline_closure_statement="custom statement")
        assert cfg.baseline_closure_statement == "custom statement"
