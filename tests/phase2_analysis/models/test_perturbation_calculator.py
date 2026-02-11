import math

import pytest

from phase2_analysis.models.perturbation import PerturbationCalculator


class _DummySession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class _DummyStore:
    def __init__(self):
        self.session = _DummySession()

    def Session(self):
        return self.session


def test_calculate_degradation_sanitizes_nan(monkeypatch):
    calc = PerturbationCalculator(_DummyStore())
    monkeypatch.setattr(
        calc,
        "_calculate_real",
        lambda *args, **kwargs: {"degradation": float("nan"), "computed_from": "real_data"},
    )

    result = calc.calculate_degradation("segmentation", "voynich_real", 0.1, {})
    assert result["degradation"] == 1.0


def test_calculate_real_routes_anchor_disruption_and_closes_session(monkeypatch):
    store = _DummyStore()
    calc = PerturbationCalculator(store)
    monkeypatch.setattr(
        calc,
        "_calculate_anchor_disruption",
        lambda *args, **kwargs: {"degradation": 0.25, "computed_from": "real_data"},
    )

    result = calc._calculate_real("anchor_disruption", "voynich_real", 0.2, {})
    assert result["degradation"] == 0.25
    assert store.session.closed is True


def test_calculate_real_rejects_unknown_type_and_closes_session():
    store = _DummyStore()
    calc = PerturbationCalculator(store)

    with pytest.raises(ValueError, match="Unknown perturbation type"):
        calc._calculate_real("unknown", "voynich_real", 0.2, {})

    assert store.session.closed is True


def test_insufficient_data_payload_is_explicit():
    calc = PerturbationCalculator(_DummyStore())
    result = calc._insufficient_data("ordering", 0.3, {"ordering": 0.25})

    assert not math.isnan(result["degradation"])
    assert 0.0 <= result["degradation"] <= 1.0
    assert result["computed_from"] == "sparse_data_estimate"
    assert result["base_sensitivity"] == 0.25
    assert result["strength"] == 0.3
    assert result["fallback_reason"] == "insufficient_records"


def test_sparse_data_estimate_scales_with_strength():
    calc = PerturbationCalculator(_DummyStore())
    low = calc._estimate_sparse_data_degradation("ordering", 0.1, {"ordering": 0.25})
    high = calc._estimate_sparse_data_degradation("ordering", 0.3, {"ordering": 0.25})

    assert high > low
    assert 0.0 <= low <= 1.0
    assert 0.0 <= high <= 1.0
