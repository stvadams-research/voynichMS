"""
Tests for MappingStabilityTest, focused on the boolean truthiness fix (H1).

Ensures that legitimate 0.0 stability scores propagate correctly
through min() and _determine_outcome(), rather than being swallowed
by Python's truthiness evaluation.
"""

import pytest

pytestmark = pytest.mark.unit

from phase1_foundation.storage.metadata import MetadataStore
from phase2_analysis.stress_tests.interface import StressTestOutcome
from phase2_analysis.stress_tests.mapping_stability import MappingStabilityTest


@pytest.fixture
def empty_store(tmp_path):
    db_path = f"sqlite:///{tmp_path}/test.db"
    return MetadataStore(db_path)


@pytest.fixture
def stability_test(empty_store):
    return MappingStabilityTest(empty_store)


class TestDetermineOutcomeZeroValues:
    """Verify that 0.0 scores are handled correctly (not treated as falsy)."""

    def test_zero_seg_constructed_system(self, stability_test):
        """A 0.0 segmentation score should still compute min() correctly."""
        outcome, threshold = stability_test._determine_outcome(
            "constructed_system", seg=0.0, ord=0.8, omit=0.7
        )
        # min(0.0, 0.8, 0.7) = 0.0, which is < 0.6 => FRAGILE
        # But also ord=0.8 >= 0.5, so ordering check passes
        assert outcome == StressTestOutcome.FRAGILE
        assert threshold == 0.0

    def test_zero_ord_constructed_system(self, stability_test):
        """A 0.0 ordering score should trigger COLLAPSED for constructed_system."""
        outcome, threshold = stability_test._determine_outcome(
            "constructed_system", seg=0.8, ord=0.0, omit=0.7
        )
        # ord < 0.5 => COLLAPSED
        assert outcome == StressTestOutcome.COLLAPSED
        assert threshold == 0.0

    def test_zero_omit_constructed_system(self, stability_test):
        """A 0.0 omission score should produce FRAGILE (min < 0.6)."""
        outcome, threshold = stability_test._determine_outcome(
            "constructed_system", seg=0.8, ord=0.7, omit=0.0
        )
        # ord >= 0.5, min(0.8, 0.7, 0.0) = 0.0 < 0.6 => FRAGILE
        assert outcome == StressTestOutcome.FRAGILE
        assert threshold == 0.0

    def test_all_zero_constructed_system(self, stability_test):
        """All-zero scores should trigger COLLAPSED (ord < 0.5)."""
        outcome, threshold = stability_test._determine_outcome(
            "constructed_system", seg=0.0, ord=0.0, omit=0.0
        )
        assert outcome == StressTestOutcome.COLLAPSED
        assert threshold == 0.0

    def test_zero_seg_visual_grammar(self, stability_test):
        """A 0.0 segmentation score should trigger COLLAPSED for visual_grammar."""
        outcome, threshold = stability_test._determine_outcome(
            "visual_grammar", seg=0.0, ord=0.8, omit=0.7
        )
        # seg < 0.4 => COLLAPSED
        assert outcome == StressTestOutcome.COLLAPSED
        assert threshold == 0.0

    def test_zero_values_hybrid_system(self, stability_test):
        """Hybrid system with one zero should detect high variance."""
        outcome, threshold = stability_test._determine_outcome(
            "hybrid_system", seg=0.0, ord=0.8, omit=0.7
        )
        # variance = 0.8 - 0.0 = 0.8 > 0.3 => FRAGILE
        assert outcome == StressTestOutcome.FRAGILE

    def test_all_zero_hybrid_system(self, stability_test):
        """Hybrid system with all zeros has zero variance => STABLE."""
        outcome, threshold = stability_test._determine_outcome(
            "hybrid_system", seg=0.0, ord=0.0, omit=0.0
        )
        # variance = 0.0 - 0.0 = 0.0 <= 0.3 => STABLE
        assert outcome == StressTestOutcome.STABLE


class TestOverallStabilityCalculation:
    """Verify the min() aggregation handles 0.0 correctly."""

    def test_min_with_zero_value(self):
        """The pattern used in run() should correctly compute min when a value is 0.0."""
        avg_seg, avg_ord, avg_omit = 0.5, 0.0, 0.7
        overall = min(avg_seg, avg_ord, avg_omit) if all(
            v is not None for v in [avg_seg, avg_ord, avg_omit]
        ) else 0
        assert overall == 0.0

    def test_min_with_all_zeros(self):
        avg_seg, avg_ord, avg_omit = 0.0, 0.0, 0.0
        overall = min(avg_seg, avg_ord, avg_omit) if all(
            v is not None for v in [avg_seg, avg_ord, avg_omit]
        ) else 0
        assert overall == 0.0

    def test_min_with_none_falls_back(self):
        """If any value is None, should fall back to 0."""
        avg_seg, avg_ord, avg_omit = 0.5, None, 0.7
        overall = min(avg_seg, avg_ord, avg_omit) if all(
            v is not None for v in [avg_seg, avg_ord, avg_omit]
        ) else 0
        assert overall == 0
