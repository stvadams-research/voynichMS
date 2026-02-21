"""
Unit tests for Phase 2 Analysis modules.

Covers:
- Anomaly module: stability_analysis, semantic_necessity, constraint_analysis, capacity_bounding
- Models module: registry, evaluation, perturbation, visual_grammar, constructed_system

Uses synthetic data and mocks rather than real database records.
"""

import math
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers: lightweight stubs for MetadataStore and DB session
# ---------------------------------------------------------------------------

class _DummySession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True

    def query(self, model_class):
        return _DummyQuery()


class _DummyQuery:
    """Always-empty query so DB-dependent paths hit fallback branches."""

    def filter_by(self, **kwargs):
        return self

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def first(self):
        return None

    def all(self):
        return []

    def count(self):
        return 0


class _DummyStore:
    """Minimal MetadataStore stand-in."""

    def __init__(self):
        self._session = _DummySession()

    def Session(self):
        return self._session


# ===========================================================================
# 1. Anomaly / stability_analysis.py
# ===========================================================================

class TestAnomalyStabilityAnalyzer:

    def _make_analyzer(self, **kwargs):
        from phase2_analysis.anomaly.stability_analysis import AnomalyStabilityAnalyzer
        return AnomalyStabilityAnalyzer(**kwargs)

    # -- generate_variants -----------------------------------------------

    def test_generate_variants_returns_list(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        variants = analyzer.generate_variants()
        assert isinstance(variants, list)
        assert len(variants) >= 5

    def test_generate_variants_includes_baseline(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        variants = analyzer.generate_variants()
        names = [v.name for v in variants]
        assert "baseline" in names

    def test_generate_variants_baseline_uses_provided_values(self):
        analyzer = self._make_analyzer(
            baseline_info_density=5.5,
            baseline_locality=2.0,
            baseline_robustness=0.90,
        )
        variants = analyzer.generate_variants()
        baseline = next(v for v in variants if v.name == "baseline")
        assert baseline.info_density == 5.5
        assert baseline.locality_radius == 2.0
        assert baseline.robustness == 0.90

    def test_variant_names_are_unique(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        variants = analyzer.generate_variants()
        names = [v.name for v in variants]
        assert len(names) == len(set(names))

    # -- compute_stability_envelope ---------------------------------------

    def test_compute_stability_envelope_requires_variants(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        # No variants loaded yet -- envelope should have empty values
        env = analyzer.compute_stability_envelope(
            "info_density", 4.0, 1.2, 0.5
        )
        assert env.metric_name == "info_density"
        assert len(env.values_by_representation) == 0

    def test_compute_stability_envelope_populates_after_variants(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        analyzer.variants = analyzer.generate_variants()
        env = analyzer.compute_stability_envelope(
            "info_density", 4.0, 1.2, 0.5
        )
        assert len(env.values_by_representation) == len(analyzer.variants)
        assert env.mean_value > 0
        assert env.separation_z > 0

    def test_compute_stability_envelope_locality_metric(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        analyzer.variants = analyzer.generate_variants()
        env = analyzer.compute_stability_envelope(
            "locality_radius", 3.0, 8.0, 2.0
        )
        assert env.metric_name == "locality_radius"
        # All variants have locality_radius values > 0
        assert all(v > 0 for v in env.values_by_representation.values())

    # -- analyze ----------------------------------------------------------

    def test_analyze_returns_required_keys(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        result = analyzer.analyze()
        required = {
            "variants_tested",
            "metrics_analyzed",
            "all_stable",
            "anomaly_confirmed",
            "envelopes",
            "sensitivity_report",
        }
        assert required <= set(result.keys())

    def test_analyze_three_envelopes(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        result = analyzer.analyze()
        assert result["metrics_analyzed"] == 3
        metric_names = {e["metric"] for e in result["envelopes"]}
        assert metric_names == {"info_density", "locality_radius", "robustness"}

    def test_analyze_sensitivity_report_structure(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        result = analyzer.analyze()
        sr = result["sensitivity_report"]
        assert "segmentation_sensitivity" in sr
        assert "overall_sensitivity" in sr
        assert "notes" in sr

    # -- get_confirmation_status -----------------------------------------

    def test_get_confirmation_status_before_analysis(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        confirmed, msg = analyzer.get_confirmation_status()
        assert confirmed is False
        assert "not yet run" in msg.lower()

    def test_get_confirmation_status_after_analysis(self):
        analyzer = self._make_analyzer(
            baseline_info_density=4.0,
            baseline_locality=3.0,
            baseline_robustness=0.70,
        )
        analyzer.analyze()
        confirmed, msg = analyzer.get_confirmation_status()
        # The result depends on envelope stability; just verify types
        assert isinstance(confirmed, bool)
        assert isinstance(msg, str)
        assert len(msg) > 0


# ===========================================================================
# 2. Anomaly / semantic_necessity.py
# ===========================================================================

class TestSemanticNecessityAnalyzer:

    def _make_analyzer(self, store=None):
        from phase2_analysis.anomaly.semantic_necessity import SemanticNecessityAnalyzer
        return SemanticNecessityAnalyzer(store=store)

    # -- construct_maximal_nonsemantic_systems ----------------------------

    def test_construct_nonsemantic_systems_returns_list(self):
        analyzer = self._make_analyzer()
        systems = analyzer.construct_maximal_nonsemantic_systems()
        assert isinstance(systems, list)
        assert len(systems) >= 4

    def test_nonsemantic_systems_have_no_meaning(self):
        analyzer = self._make_analyzer()
        systems = analyzer.construct_maximal_nonsemantic_systems()
        for s in systems:
            assert s.uses_meaning is False

    def test_nonsemantic_systems_have_unique_names(self):
        analyzer = self._make_analyzer()
        systems = analyzer.construct_maximal_nonsemantic_systems()
        names = [s.name for s in systems]
        assert len(names) == len(set(names))

    # -- assess_necessity ------------------------------------------------

    def test_assess_necessity_all_fail_returns_definitely(self):
        from phase2_analysis.anomaly.interface import SemanticNecessity
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False),
            NonSemanticSystem(name="b", description="b", passes_all_constraints=False),
        ]
        assert analyzer.assess_necessity() == SemanticNecessity.DEFINITELY_NECESSARY

    def test_assess_necessity_all_pass_returns_not_necessary(self):
        from phase2_analysis.anomaly.interface import SemanticNecessity
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=True),
            NonSemanticSystem(name="b", description="b", passes_all_constraints=True),
            NonSemanticSystem(name="c", description="c", passes_all_constraints=True),
        ]
        assert analyzer.assess_necessity() == SemanticNecessity.NOT_NECESSARY

    def test_assess_necessity_only_reference_pass_returns_likely(self):
        from phase2_analysis.anomaly.interface import SemanticNecessity
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False),
            NonSemanticSystem(name="b", description="b", passes_all_constraints=True,
                              uses_reference=True),
        ]
        assert analyzer.assess_necessity() == SemanticNecessity.LIKELY_NECESSARY

    # -- compile_evidence ------------------------------------------------

    def test_compile_evidence_returns_two_lists(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False,
                              failure_reason="info density (2.0) below required (4.0)"),
        ]
        evidence_for, evidence_against = analyzer.compile_evidence()
        assert isinstance(evidence_for, list)
        assert isinstance(evidence_against, list)
        # At minimum, evidence_against always has glossolalia and diagram entries
        assert len(evidence_against) >= 2

    def test_compile_evidence_all_fail_has_strong_for(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False,
                              failure_reason="info density too low"),
            NonSemanticSystem(name="b", description="b", passes_all_constraints=False,
                              failure_reason="robustness too low"),
        ]
        evidence_for, _ = analyzer.compile_evidence()
        assert any("No non-semantic system" in e for e in evidence_for)

    # -- derive_semantic_conditions --------------------------------------

    def test_derive_semantic_conditions_with_info_failure(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False,
                              failure_reason="info density (2.0) below required (4.0)"),
        ]
        conditions = analyzer.derive_semantic_conditions()
        assert isinstance(conditions, list)
        assert len(conditions) >= 1
        # Should mention structural constraints
        assert any("info density" in c.lower() or "structural" in c.lower() for c in conditions)

    def test_derive_semantic_conditions_with_robustness_failure(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = [
            NonSemanticSystem(name="a", description="a", passes_all_constraints=False,
                              failure_reason="robustness (0.20) below required (0.60)"),
        ]
        conditions = analyzer.derive_semantic_conditions()
        assert any("robustness" in c.lower() or "perturbation" in c.lower() for c in conditions)

    def test_derive_semantic_conditions_always_has_fallback(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        analyzer.systems = []
        conditions = analyzer.derive_semantic_conditions()
        # The fallback condition is always appended
        assert any("reconstructed from structure" in c for c in conditions)

    # -- test_system (theoretical bounds path) ---------------------------

    def test_test_system_passes_when_bounds_sufficient(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        system = NonSemanticSystem(
            name="strong",
            description="strong system",
            max_info_density=5.0,
            min_locality=3.0,
            max_robustness=0.80,
        )
        thresholds = {"info_density": 4.0, "locality_max": 4.0, "robustness_min": 0.60}
        passed = analyzer.test_system(system, thresholds)
        assert passed is True
        assert system.passes_all_constraints is True

    def test_test_system_fails_when_info_density_low(self):
        from phase2_analysis.anomaly.semantic_necessity import NonSemanticSystem
        analyzer = self._make_analyzer()
        system = NonSemanticSystem(
            name="weak",
            description="weak system",
            max_info_density=2.0,
            min_locality=3.0,
            max_robustness=0.80,
        )
        thresholds = {"info_density": 4.0, "locality_max": 4.0, "robustness_min": 0.60}
        passed = analyzer.test_system(system, thresholds)
        assert passed is False
        assert "info density" in system.failure_reason


# ===========================================================================
# 3. Anomaly / constraint_analysis.py
# ===========================================================================

class TestConstraintIntersectionAnalyzer:

    def _make_analyzer(self):
        from phase2_analysis.anomaly.constraint_analysis import ConstraintIntersectionAnalyzer
        return ConstraintIntersectionAnalyzer()

    # -- load_constraints_from_phases ------------------------------------

    def test_load_constraints_returns_nonempty_list(self):
        analyzer = self._make_analyzer()
        constraints = analyzer.load_constraints_from_phases()
        assert isinstance(constraints, list)
        assert len(constraints) > 0

    def test_constraints_have_required_fields(self):
        analyzer = self._make_analyzer()
        constraints = analyzer.load_constraints_from_phases()
        for c in constraints:
            assert hasattr(c, "constraint_id")
            assert hasattr(c, "source")
            assert hasattr(c, "constraint_type")
            assert hasattr(c, "description")

    def test_constraint_ids_are_unique(self):
        analyzer = self._make_analyzer()
        constraints = analyzer.load_constraints_from_phases()
        ids = [c.constraint_id for c in constraints]
        assert len(ids) == len(set(ids))

    # -- compute_intersection --------------------------------------------

    def test_compute_intersection_single_constraint(self):
        analyzer = self._make_analyzer()
        analyzer.constraints = analyzer.load_constraints_from_phases()
        analyzer.models = analyzer.load_models()
        inter = analyzer.compute_intersection(["P1_C1"])
        assert isinstance(inter.excluded_models, set)
        assert "natural_language_fixed_alphabet" in inter.excluded_models

    def test_compute_intersection_pair_unions_exclusions(self):
        analyzer = self._make_analyzer()
        analyzer.constraints = analyzer.load_constraints_from_phases()
        analyzer.models = analyzer.load_models()
        inter = analyzer.compute_intersection(["P1_C1", "P1_C2"])
        # Union of both exclusions
        assert "natural_language_fixed_alphabet" in inter.excluded_models
        assert "random_generation" in inter.excluded_models

    def test_compute_intersection_nonexistent_id_excluded_empty(self):
        analyzer = self._make_analyzer()
        analyzer.constraints = analyzer.load_constraints_from_phases()
        analyzer.models = analyzer.load_models()
        inter = analyzer.compute_intersection(["NONEXISTENT"])
        assert len(inter.excluded_models) == 0

    # -- find_all_intersections ------------------------------------------

    def test_find_all_intersections_returns_nonempty(self):
        analyzer = self._make_analyzer()
        analyzer.constraints = analyzer.load_constraints_from_phases()
        analyzer.models = analyzer.load_models()
        results = analyzer.find_all_intersections()
        assert len(results) > 0

    # -- analyze ---------------------------------------------------------

    def test_analyze_returns_required_keys(self):
        analyzer = self._make_analyzer()
        result = analyzer.analyze()
        required = {
            "total_constraints",
            "total_models",
            "total_intersections",
            "minimal_impossibility_sets",
            "constraints_by_source",
            "constraints_by_type",
            "exclusion_summary",
        }
        assert required <= set(result.keys())

    def test_analyze_counts_are_positive(self):
        analyzer = self._make_analyzer()
        result = analyzer.analyze()
        assert result["total_constraints"] > 0
        assert result["total_models"] > 0
        assert result["total_intersections"] > 0


# ===========================================================================
# 4. Anomaly / capacity_bounding.py
# ===========================================================================

class TestCapacityBoundingAnalyzer:

    def _make_analyzer(self):
        from phase2_analysis.anomaly.capacity_bounding import CapacityBoundingAnalyzer
        return CapacityBoundingAnalyzer()

    # -- derive_bounds ---------------------------------------------------

    def test_derive_bounds_returns_nonempty(self):
        analyzer = self._make_analyzer()
        bounds = analyzer.derive_bounds()
        assert isinstance(bounds, list)
        assert len(bounds) >= 3

    def test_derive_bounds_has_lower_and_upper(self):
        analyzer = self._make_analyzer()
        bounds = analyzer.derive_bounds()
        types = {b.bound_type for b in bounds}
        assert "lower" in types
        assert "upper" in types

    def test_derive_bounds_memory_lower_uses_log2(self):
        analyzer = self._make_analyzer()
        bounds = analyzer.derive_bounds()
        memory_lower = next(
            b for b in bounds
            if b.property_name == "memory" and b.bound_type == "lower"
        )
        expected = round(math.log2(analyzer.observed_vocabulary_size), 2)
        assert memory_lower.bound_value == expected

    def test_derive_bounds_locality_upper_matches_config(self):
        analyzer = self._make_analyzer()
        bounds = analyzer.derive_bounds()
        locality_upper = next(
            b for b in bounds
            if b.property_name == "locality_radius" and b.bound_type == "upper"
        )
        assert locality_upper.bound_value == float(analyzer.observed_locality_max)

    # -- define_system_classes -------------------------------------------

    def test_define_system_classes_returns_nonempty(self):
        analyzer = self._make_analyzer()
        classes = analyzer.define_system_classes()
        assert isinstance(classes, list)
        assert len(classes) >= 5

    def test_system_classes_have_unique_names(self):
        analyzer = self._make_analyzer()
        classes = analyzer.define_system_classes()
        names = [c.name for c in classes]
        assert len(names) == len(set(names))

    # -- evaluate_system_classes -----------------------------------------

    def test_evaluate_system_classes_marks_consistency(self):
        analyzer = self._make_analyzer()
        analyzer.bounds = analyzer.derive_bounds()
        analyzer.system_classes = analyzer.define_system_classes()
        evaluated = analyzer.evaluate_system_classes()
        # At least some should be consistent, some not
        consistent = [sc for sc in evaluated if sc.consistent]
        excluded = [sc for sc in evaluated if not sc.consistent]
        assert len(consistent) + len(excluded) == len(evaluated)

    def test_evaluate_excluded_classes_have_reason(self):
        analyzer = self._make_analyzer()
        analyzer.bounds = analyzer.derive_bounds()
        analyzer.system_classes = analyzer.define_system_classes()
        analyzer.evaluate_system_classes()
        for sc in analyzer.system_classes:
            if not sc.consistent:
                assert len(sc.inconsistency_reason) > 0

    # -- build_feasibility_region ----------------------------------------

    def test_build_feasibility_region_returns_region(self):
        from phase2_analysis.anomaly.interface import StructuralFeasibilityRegion
        analyzer = self._make_analyzer()
        analyzer.bounds = analyzer.derive_bounds()
        analyzer.system_classes = analyzer.define_system_classes()
        analyzer.evaluate_system_classes()
        region = analyzer.build_feasibility_region()
        assert isinstance(region, StructuralFeasibilityRegion)
        assert len(region.bounds) > 0
        assert len(region.required_properties) > 0

    # -- analyze ---------------------------------------------------------

    def test_analyze_returns_required_keys(self):
        analyzer = self._make_analyzer()
        result = analyzer.analyze()
        required = {
            "total_bounds",
            "lower_bounds",
            "upper_bounds",
            "system_classes_evaluated",
            "consistent_classes",
            "excluded_classes",
            "feasibility_region",
            "bounds_detail",
        }
        assert required <= set(result.keys())

    def test_analyze_consistent_plus_excluded_equals_total(self):
        analyzer = self._make_analyzer()
        result = analyzer.analyze()
        assert (
            len(result["consistent_classes"]) + len(result["excluded_classes"])
            == result["system_classes_evaluated"]
        )

    def test_get_candidate_systems_after_analyze(self):
        analyzer = self._make_analyzer()
        analyzer.analyze()
        candidates = analyzer.get_candidate_systems()
        assert isinstance(candidates, list)
        # Should match consistent classes from analyze
        assert set(candidates) == {
            sc.name for sc in analyzer.system_classes if sc.consistent
        }


# ===========================================================================
# 5. Models / registry.py
# ===========================================================================

class TestModelRegistry:

    def _make_registry(self):
        from phase2_analysis.models.registry import ModelRegistry
        return ModelRegistry(store=_DummyStore())

    def _get_model_class(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        return AdjacencyGrammarModel

    def _get_second_model_class(self):
        from phase2_analysis.models.visual_grammar import ContainmentGrammarModel
        return ContainmentGrammarModel

    # -- register --------------------------------------------------------

    def test_register_returns_model_instance(self):
        from phase2_analysis.models.interface import ExplicitModel
        registry = self._make_registry()
        model = registry.register(self._get_model_class())
        assert isinstance(model, ExplicitModel)
        assert model.model_id == "vg_adjacency_grammar"

    def test_register_duplicate_raises(self):
        registry = self._make_registry()
        registry.register(self._get_model_class())
        with pytest.raises(ValueError, match="already registered"):
            registry.register(self._get_model_class())

    # -- get -------------------------------------------------------------

    def test_get_returns_registered_model(self):
        registry = self._make_registry()
        registry.register(self._get_model_class())
        model = registry.get("vg_adjacency_grammar")
        assert model.model_id == "vg_adjacency_grammar"

    def test_get_missing_raises(self):
        registry = self._make_registry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    # -- get_by_class ----------------------------------------------------

    def test_get_by_class_returns_matching(self):
        registry = self._make_registry()
        registry.register(self._get_model_class())
        registry.register(self._get_second_model_class())
        vg_models = registry.get_by_class("visual_grammar")
        assert len(vg_models) == 2

    def test_get_by_class_empty_for_unknown(self):
        registry = self._make_registry()
        result = registry.get_by_class("unknown_class")
        assert result == []

    # -- get_all / get_surviving -----------------------------------------

    def test_get_all_returns_all_registered(self):
        registry = self._make_registry()
        registry.register(self._get_model_class())
        registry.register(self._get_second_model_class())
        assert len(registry.get_all()) == 2

    def test_get_surviving_excludes_falsified(self):
        from phase2_analysis.models.interface import ModelStatus
        registry = self._make_registry()
        model = registry.register(self._get_model_class())
        registry.register(self._get_second_model_class())
        model.status = ModelStatus.FALSIFIED
        surviving = registry.get_surviving()
        assert len(surviving) == 1

    def test_get_surviving_excludes_discontinued(self):
        from phase2_analysis.models.interface import ModelStatus
        registry = self._make_registry()
        model = registry.register(self._get_model_class())
        registry.register(self._get_second_model_class())
        model.status = ModelStatus.DISCONTINUED
        surviving = registry.get_surviving()
        assert len(surviving) == 1


# ===========================================================================
# 6. Models / evaluation.py
# ===========================================================================

class TestCrossModelEvaluator:

    def _make_evaluator(self):
        from phase2_analysis.models.evaluation import CrossModelEvaluator
        from phase2_analysis.models.visual_grammar import (
            AdjacencyGrammarModel,
            ContainmentGrammarModel,
        )
        store = _DummyStore()
        models = [AdjacencyGrammarModel(store), ContainmentGrammarModel(store)]
        return CrossModelEvaluator(models)

    # -- evaluate_model --------------------------------------------------

    def test_evaluate_model_returns_all_dimensions(self):
        evaluator = self._make_evaluator()
        model = list(evaluator.models.values())[0]
        scores = evaluator.evaluate_model(model)
        for dim in evaluator.DIMENSIONS:
            assert dim in scores
            assert 0.0 <= scores[dim] <= 1.0

    def test_evaluate_model_untested_predictions_zero_accuracy(self):
        evaluator = self._make_evaluator()
        model = list(evaluator.models.values())[0]
        scores = evaluator.evaluate_model(model)
        # No predictions have been tested, so accuracy should be 0
        assert scores["prediction_accuracy"] == 0.0

    def test_evaluate_model_robustness_default_when_no_log(self):
        evaluator = self._make_evaluator()
        model = list(evaluator.models.values())[0]
        scores = evaluator.evaluate_model(model)
        assert scores["robustness"] == 0.5

    # -- generate_matrix -------------------------------------------------

    def test_generate_matrix_has_all_models(self):
        evaluator = self._make_evaluator()
        matrix = evaluator.generate_matrix()
        assert len(matrix.models) == 2
        assert len(matrix.scores) == 2

    def test_generate_matrix_rankings_per_dimension(self):
        evaluator = self._make_evaluator()
        matrix = evaluator.generate_matrix()
        for dim in evaluator.DIMENSIONS:
            assert dim in matrix.rankings
            assert len(matrix.rankings[dim]) == 2

    def test_generate_matrix_overall_ranking_sorted_descending(self):
        evaluator = self._make_evaluator()
        matrix = evaluator.generate_matrix()
        overall_scores = [score for _, score in matrix.overall_ranking]
        assert overall_scores == sorted(overall_scores, reverse=True)

    def test_generate_matrix_overall_scores_bounded(self):
        evaluator = self._make_evaluator()
        matrix = evaluator.generate_matrix()
        for _, score in matrix.overall_ranking:
            assert 0.0 <= score <= 1.0


# ===========================================================================
# 7. Models / perturbation.py
# ===========================================================================

class TestPerturbationCalculator:

    def _make_calculator(self):
        from phase2_analysis.models.perturbation import PerturbationCalculator
        return PerturbationCalculator(_DummyStore())

    # -- sparse-data fallback paths --------------------------------------

    def test_insufficient_data_returns_deterministic(self):
        calc = self._make_calculator()
        result = calc._insufficient_data("segmentation", 0.5, {"segmentation": 0.35})
        assert result["computed_from"] == "sparse_data_estimate"
        assert 0.0 <= result["degradation"] <= 1.0

    def test_sparse_data_ordering_scales_linearly(self):
        calc = self._make_calculator()
        d1 = calc._estimate_sparse_data_degradation("ordering", 0.1, {"ordering": 0.25})
        d2 = calc._estimate_sparse_data_degradation("ordering", 0.5, {"ordering": 0.25})
        assert d2 > d1

    def test_sparse_data_clamped_to_unit_interval(self):
        calc = self._make_calculator()
        result = calc._estimate_sparse_data_degradation("ordering", 1.0, {"ordering": 1.0})
        assert 0.0 <= result <= 1.0

    # -- unknown perturbation type raises --------------------------------

    def test_unknown_perturbation_type_raises(self):
        calc = self._make_calculator()
        with pytest.raises(ValueError, match="Unknown perturbation type"):
            calc._calculate_real("bogus_type", "ds", 0.5, {})

    # -- each real perturbation path falls back to insufficient data -----

    def test_anchor_disruption_empty_db_uses_fallback(self):
        calc = self._make_calculator()
        result = calc.calculate_degradation(
            "anchor_disruption", "empty_ds", 0.3, {"anchor_disruption": 0.50}
        )
        assert result["computed_from"] == "sparse_data_estimate"
        assert 0.0 <= result["degradation"] <= 1.0

    def test_segmentation_empty_db_uses_fallback(self):
        calc = self._make_calculator()
        result = calc.calculate_degradation(
            "segmentation", "empty_ds", 0.2, {"segmentation": 0.35}
        )
        assert result["computed_from"] == "sparse_data_estimate"

    def test_ordering_empty_db_uses_fallback(self):
        calc = self._make_calculator()
        result = calc.calculate_degradation(
            "ordering", "empty_ds", 0.4, {"ordering": 0.25}
        )
        assert result["computed_from"] == "sparse_data_estimate"

    def test_omission_empty_db_uses_fallback(self):
        calc = self._make_calculator()
        result = calc.calculate_degradation(
            "omission", "empty_ds", 0.1, {"omission": 0.40}
        )
        assert result["computed_from"] == "sparse_data_estimate"


# ===========================================================================
# 8. Models / visual_grammar.py  (model class tests)
# ===========================================================================

class TestVisualGrammarModels:

    def _store(self):
        return _DummyStore()

    # -- AdjacencyGrammarModel -------------------------------------------

    def test_adjacency_model_properties_are_strings(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        model = AdjacencyGrammarModel(self._store())
        assert isinstance(model.model_id, str)
        assert isinstance(model.model_name, str)
        assert isinstance(model.explanation_class, str)
        assert isinstance(model.description, str)

    def test_adjacency_model_predictions_nonempty(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        model = AdjacencyGrammarModel(self._store())
        preds = model.get_predictions()
        assert isinstance(preds, list)
        assert len(preds) >= 1

    def test_adjacency_model_predictions_have_ids(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        model = AdjacencyGrammarModel(self._store())
        for p in model.get_predictions():
            assert len(p.prediction_id) > 0
            assert len(p.description) > 0

    def test_adjacency_model_rules_nonempty(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        model = AdjacencyGrammarModel(self._store())
        assert len(model.rules) >= 3

    def test_adjacency_model_failure_conditions_nonempty(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        model = AdjacencyGrammarModel(self._store())
        assert len(model.failure_conditions) >= 2

    # -- ContainmentGrammarModel -----------------------------------------

    def test_containment_model_id(self):
        from phase2_analysis.models.visual_grammar import ContainmentGrammarModel
        model = ContainmentGrammarModel(self._store())
        assert model.model_id == "vg_containment_grammar"
        assert model.explanation_class == "visual_grammar"

    def test_containment_model_predictions_nonempty(self):
        from phase2_analysis.models.visual_grammar import ContainmentGrammarModel
        model = ContainmentGrammarModel(self._store())
        preds = model.get_predictions()
        assert len(preds) >= 1

    # -- DiagramAnnotationModel ------------------------------------------

    def test_diagram_model_id(self):
        from phase2_analysis.models.visual_grammar import DiagramAnnotationModel
        model = DiagramAnnotationModel(self._store())
        assert model.model_id == "vg_diagram_annotation"
        assert model.explanation_class == "visual_grammar"

    def test_diagram_model_predictions_nonempty(self):
        from phase2_analysis.models.visual_grammar import DiagramAnnotationModel
        model = DiagramAnnotationModel(self._store())
        preds = model.get_predictions()
        assert len(preds) >= 2

    # -- apply_perturbation (fallback path via empty DB) -----------------

    def test_adjacency_apply_perturbation_returns_result(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        from phase2_analysis.models.interface import DisconfirmationResult
        model = AdjacencyGrammarModel(self._store())
        result = model.apply_perturbation("segmentation", "empty_ds", 0.1)
        assert isinstance(result, DisconfirmationResult)
        assert result.model_id == "vg_adjacency_grammar"
        assert 0.0 <= result.degradation_score <= 1.0


# ===========================================================================
# 9. Models / constructed_system.py  (model class tests)
# ===========================================================================

class TestConstructedSystemModels:

    def _store(self):
        return _DummyStore()

    # -- ProceduralGenerationModel ---------------------------------------

    def test_procedural_model_properties(self):
        from phase2_analysis.models.constructed_system import ProceduralGenerationModel
        model = ProceduralGenerationModel(self._store())
        assert model.model_id == "cs_procedural_generation"
        assert model.explanation_class == "constructed_system"
        assert isinstance(model.model_name, str)

    def test_procedural_model_predictions_nonempty(self):
        from phase2_analysis.models.constructed_system import ProceduralGenerationModel
        model = ProceduralGenerationModel(self._store())
        preds = model.get_predictions()
        assert len(preds) >= 2

    def test_procedural_model_rules_nonempty(self):
        from phase2_analysis.models.constructed_system import ProceduralGenerationModel
        model = ProceduralGenerationModel(self._store())
        assert len(model.rules) >= 3

    # -- GlossalialSystemModel -------------------------------------------

    def test_glossolalia_model_properties(self):
        from phase2_analysis.models.constructed_system import GlossalialSystemModel
        model = GlossalialSystemModel(self._store())
        assert model.model_id == "cs_glossolalia"
        assert model.explanation_class == "constructed_system"

    def test_glossolalia_model_predictions_nonempty(self):
        from phase2_analysis.models.constructed_system import GlossalialSystemModel
        model = GlossalialSystemModel(self._store())
        preds = model.get_predictions()
        assert len(preds) >= 1
        for p in preds:
            assert len(p.prediction_id) > 0

    # -- MeaningfulConstructModel ----------------------------------------

    def test_meaningful_construct_model_properties(self):
        from phase2_analysis.models.constructed_system import MeaningfulConstructModel
        model = MeaningfulConstructModel(self._store())
        assert model.model_id == "cs_meaningful_construct"
        assert model.explanation_class == "constructed_system"

    def test_meaningful_construct_predictions_nonempty(self):
        from phase2_analysis.models.constructed_system import MeaningfulConstructModel
        model = MeaningfulConstructModel(self._store())
        preds = model.get_predictions()
        assert len(preds) >= 1

    def test_meaningful_construct_apply_perturbation_returns_result(self):
        from phase2_analysis.models.constructed_system import MeaningfulConstructModel
        from phase2_analysis.models.interface import DisconfirmationResult
        model = MeaningfulConstructModel(self._store())
        result = model.apply_perturbation("ordering", "empty_ds", 0.3)
        assert isinstance(result, DisconfirmationResult)
        assert result.model_id == "cs_meaningful_construct"
        assert isinstance(result.survived, bool)


# ===========================================================================
# 10. Interface data-class behaviour
# ===========================================================================

class TestInterfaceDataClasses:

    def test_stability_envelope_compute_stability(self):
        from phase2_analysis.anomaly.interface import StabilityEnvelope
        env = StabilityEnvelope(
            metric_name="test_metric",
            baseline_value=4.0,
            control_mean=1.0,
            control_std=0.5,
        )
        env.values_by_representation = {"a": 3.8, "b": 4.0, "c": 4.2}
        env.compute_stability()
        assert env.mean_value == pytest.approx(4.0, abs=0.01)
        assert env.std_dev > 0
        assert env.separation_z > 0
        assert isinstance(env.is_stable, bool)

    def test_stability_envelope_empty_values(self):
        from phase2_analysis.anomaly.interface import StabilityEnvelope
        env = StabilityEnvelope(metric_name="empty", baseline_value=0.0)
        env.compute_stability()
        assert env.mean_value == 0.0

    def test_constraint_intersection_post_init(self):
        from phase2_analysis.anomaly.interface import ConstraintIntersection
        ci = ConstraintIntersection(
            constraints=["A", "B", "C"],
            excluded_models={"m1", "m2"},
        )
        assert ci.constraint_count == 3

    def test_constraint_record_violated_by(self):
        from phase2_analysis.anomaly.interface import (
            ConstraintRecord,
            ConstraintSource,
            ConstraintType,
        )
        cr = ConstraintRecord(
            constraint_id="test",
            source=ConstraintSource.PHASE_1,
            constraint_type=ConstraintType.STRUCTURAL,
            description="test constraint",
            threshold=0.5,
        )
        assert cr.violated_by(0.6) is True
        assert cr.violated_by(0.4) is False

    def test_constraint_record_violated_by_no_threshold(self):
        from phase2_analysis.anomaly.interface import (
            ConstraintRecord,
            ConstraintSource,
            ConstraintType,
        )
        cr = ConstraintRecord(
            constraint_id="test2",
            source=ConstraintSource.PHASE_1,
            constraint_type=ConstraintType.STRUCTURAL,
            description="no threshold",
        )
        assert cr.violated_by(100.0) is False

    def test_feasibility_region_check_feasibility_contradictory(self):
        from phase2_analysis.anomaly.interface import (
            StructuralFeasibilityRegion,
            CapacityBound,
        )
        region = StructuralFeasibilityRegion()
        region.add_bound(CapacityBound(property_name="x", bound_type="lower", bound_value=10.0))
        region.add_bound(CapacityBound(property_name="x", bound_type="upper", bound_value=5.0))
        region.check_feasibility()
        assert region.is_feasible is False

    def test_feasibility_region_check_feasibility_consistent(self):
        from phase2_analysis.anomaly.interface import (
            StructuralFeasibilityRegion,
            CapacityBound,
        )
        region = StructuralFeasibilityRegion()
        region.add_bound(CapacityBound(property_name="x", bound_type="lower", bound_value=2.0))
        region.add_bound(CapacityBound(property_name="x", bound_type="upper", bound_value=8.0))
        region.check_feasibility()
        assert region.is_feasible is True

    def test_semantic_necessity_result_generate_decision(self):
        from phase2_analysis.anomaly.interface import (
            SemanticNecessity,
            SemanticNecessityResult,
        )
        r = SemanticNecessityResult(assessment=SemanticNecessity.DEFINITELY_NECESSARY)
        r.generate_decision()
        assert r.phase_3_justified is True
        assert "required" in r.justification.lower()

        r2 = SemanticNecessityResult(assessment=SemanticNecessity.NOT_NECESSARY)
        r2.generate_decision()
        assert r2.phase_3_justified is False

    def test_model_status_enum_values(self):
        from phase2_analysis.models.interface import ModelStatus
        assert ModelStatus.UNTESTED.value == "untested"
        assert ModelStatus.FALSIFIED.value == "falsified"

    def test_explicit_model_record_disconfirmation(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        from phase2_analysis.models.interface import DisconfirmationResult, ModelStatus
        model = AdjacencyGrammarModel(_DummyStore())
        # Record a surviving result
        result = DisconfirmationResult(
            model_id="vg_adjacency_grammar",
            test_id="t1",
            perturbation_type="segmentation",
            survived=True,
            degradation_score=0.2,
        )
        model.record_disconfirmation(result)
        assert len(model.disconfirmation_log) == 1
        assert model.status != ModelStatus.FALSIFIED

    def test_explicit_model_record_disconfirmation_failure(self):
        from phase2_analysis.models.visual_grammar import AdjacencyGrammarModel
        from phase2_analysis.models.interface import DisconfirmationResult, ModelStatus
        model = AdjacencyGrammarModel(_DummyStore())
        result = DisconfirmationResult(
            model_id="vg_adjacency_grammar",
            test_id="t1",
            perturbation_type="segmentation",
            survived=False,
            degradation_score=0.9,
        )
        model.record_disconfirmation(result)
        assert model.status == ModelStatus.FALSIFIED
