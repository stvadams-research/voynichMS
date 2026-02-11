from phase3_synthesis.interface import PageProfile, SectionProfile, SyntheticPage
from phase3_synthesis.refinement.feature_discovery import (
    DiscriminativeFeatureDiscovery,
    FeatureComputer,
    FeatureVector,
    _stable_seed_fragment,
)


def test_stable_seed_fragment_is_deterministic() -> None:
    assert _stable_seed_fragment("feature_a") == _stable_seed_fragment("feature_a")
    assert _stable_seed_fragment("feature_a") != _stable_seed_fragment("feature_b")


def test_feature_computer_scrambled_fallback_is_seeded() -> None:
    computer = FeatureComputer(store=None, seed=123)

    computer._active_seed = 99
    first = computer._fallback_value("temp_token_burst_rate", True, (0.0, 1.0), 0.0)
    computer._active_seed = 99
    second = computer._fallback_value("temp_token_burst_rate", True, (0.0, 1.0), 0.0)

    assert first == second
    assert 0.0 <= first <= 1.0


def test_feature_computer_fixed_fallback_for_non_scrambled() -> None:
    computer = FeatureComputer(store=None, seed=123)
    value = computer._fallback_value("spatial_jar_variance", False, (0.2, 0.9), 0.42)
    assert value == 0.42


def test_alignment_group_counting() -> None:
    discovery = DiscriminativeFeatureDiscovery(SectionProfile())
    groups = discovery.feature_computer._count_alignment_groups([0.1, 0.11, 0.4, 0.8, 0.81], 0.05)
    assert groups == {0: 2, 1: 1, 2: 2}


def test_sanitize_and_finite_value_helpers() -> None:
    discovery = DiscriminativeFeatureDiscovery(SectionProfile())
    cleaned = discovery._sanitize_feature_map(
        {"ok": 0.5, "nan": float("nan"), "inf": float("inf"), "int_ok": 2},
        "f88r",
    )
    assert cleaned == {"ok": 0.5, "int_ok": 2.0}
    assert discovery._finite_values([1.0, float("nan"), 2, float("inf")]) == [1.0, 2]


def test_train_discriminator_assigns_importance_and_ranks() -> None:
    discovery = DiscriminativeFeatureDiscovery(SectionProfile())
    discovery.real_vectors = [
        FeatureVector("real_1", True, False, {"spatial_jar_variance": 1.00}),
        FeatureVector("real_2", True, False, {"spatial_jar_variance": 0.90}),
    ]
    discovery.synthetic_vectors = [
        FeatureVector("syn_1", False, False, {"spatial_jar_variance": 0.20}),
        FeatureVector("syn_2", False, False, {"spatial_jar_variance": 0.10}),
    ]
    discovery.scrambled_vectors = [
        FeatureVector("scr_1", False, True, {"spatial_jar_variance": 0.00}),
        FeatureVector("scr_2", False, True, {"spatial_jar_variance": 0.00}),
    ]

    importances = discovery.train_discriminator()

    assert len(importances) == 14
    assert importances[0].rank == 1
    assert importances[-1].rank == len(importances)

    spatial = next(
        feat for feat in discovery.discovered_features if feat.feature_id == "spatial_jar_variance"
    )
    assert spatial.importance_score > 0.0
    assert spatial.real_vs_synthetic_separation > 0.0


def test_analyze_runs_without_store_and_returns_summary() -> None:
    section = SectionProfile(
        pages=[
            PageProfile(page_id="f88r", jar_count=4),
            PageProfile(page_id="f88v", jar_count=4),
        ]
    )
    synthetic_pages = [
        SyntheticPage(page_id="syn_1", gap_id="gap_a"),
        SyntheticPage(page_id="syn_2", gap_id="gap_a"),
    ]
    discovery = DiscriminativeFeatureDiscovery(section_profile=section, store=None)

    result = discovery.analyze(synthetic_pages, seed=7)

    assert result["features_tested"] == 14
    assert "importances" in result
    assert isinstance(result["formalizable_features"], list)
