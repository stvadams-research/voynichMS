import pytest

pytestmark = pytest.mark.unit

from phase2_analysis.anomaly.capacity_bounding import CapacityBoundingAnalyzer
from phase2_analysis.anomaly.constraint_analysis import ConstraintIntersectionAnalyzer
from phase2_analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer


def test_stability_analysis_returns_expected_envelopes():
    result = AnomalyStabilityAnalyzer().analyze()
    assert result["metrics_analyzed"] == 3
    assert len(result["envelopes"]) == 3
    assert all("separation_z" in envelope for envelope in result["envelopes"])


def test_capacity_bounding_uses_configured_locality_upper_bound():
    analyzer = CapacityBoundingAnalyzer()
    result = analyzer.analyze()
    locality_upper = next(
        bound
        for bound in result["bounds_detail"]
        if bound["property"] == "locality_radius" and bound["type"] == "upper"
    )
    assert locality_upper["value"] == analyzer.observed_locality_max


def test_constraint_analysis_loads_observed_values_from_config():
    analyzer = ConstraintIntersectionAnalyzer()
    constraints = analyzer.load_constraints_from_phases()
    p1_c1 = next(c for c in constraints if c.constraint_id == "P1_C1")
    assert p1_c1.observed_value == float(analyzer.observed_values["P1_C1"])
