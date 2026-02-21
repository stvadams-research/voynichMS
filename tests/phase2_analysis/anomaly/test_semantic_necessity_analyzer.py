import pytest

pytestmark = pytest.mark.unit

from phase2_analysis.anomaly.interface import SemanticNecessity
from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem, SemanticNecessityAnalyzer


def test_construct_maximal_nonsemantic_systems_contains_expected_profiles():
    analyzer = SemanticNecessityAnalyzer(store=None)
    systems = analyzer.construct_maximal_nonsemantic_systems()

    assert len(systems) >= 5
    assert all(system.uses_meaning is False for system in systems)
    assert any(system.uses_reference is True for system in systems)


def test_test_system_uses_theoretical_bounds_when_store_unavailable():
    analyzer = SemanticNecessityAnalyzer(store=None)
    system = NonSemanticSystem(
        name="weak_system",
        description="test",
        max_info_density=2.5,
        min_locality=8.0,
        max_robustness=0.2,
    )

    passes = analyzer.test_system(
        system,
        thresholds={"info_density": 4.0, "locality_max": 4.0, "robustness_min": 0.6},
    )

    assert passes is False
    assert "info density" in system.failure_reason
    assert "locality" in system.failure_reason
    assert "robustness" in system.failure_reason


def test_assess_necessity_returns_expected_labels_for_pass_fail_mix():
    analyzer = SemanticNecessityAnalyzer(store=None)
    s1 = NonSemanticSystem(name="a", description="", uses_reference=False)
    s2 = NonSemanticSystem(name="b", description="", uses_reference=False)
    s3 = NonSemanticSystem(name="c", description="", uses_reference=True)

    s1.passes_all_constraints = False
    s2.passes_all_constraints = False
    s3.passes_all_constraints = False
    analyzer.systems = [s1, s2, s3]
    assert analyzer.assess_necessity() == SemanticNecessity.DEFINITELY_NECESSARY

    s1.passes_all_constraints = True
    s2.passes_all_constraints = False
    s3.passes_all_constraints = False
    analyzer.systems = [s1, s2, s3]
    assert analyzer.assess_necessity() == SemanticNecessity.POSSIBLY_NECESSARY


def test_analyze_without_store_returns_structured_result():
    analyzer = SemanticNecessityAnalyzer(store=None)
    result = analyzer.analyze(dataset_id="voynich_real", control_ids=[])

    assert result["systems_tested"] >= 5
    assert "assessment" in result
    assert "thresholds_used" in result
    assert "system_details" in result
