import importlib.util
from pathlib import Path


def _load_sweep_module():
    module_path = Path("scripts/analysis/run_sensitivity_sweep.py")
    spec = importlib.util.spec_from_file_location("run_sensitivity_sweep", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_robustness_decision_is_inconclusive_when_all_models_falsified():
    sweep = _load_sweep_module()
    results = [
        {
            "id": "baseline",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 0,
            "warnings": {"total_warnings": 3},
            "quality_flags": ["insufficient_data", "all_models_falsified"],
            "valid": False,
        },
        {
            "id": "threshold",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 0,
            "warnings": {"total_warnings": 2},
            "quality_flags": ["insufficient_data", "all_models_falsified"],
            "valid": False,
        },
    ]

    summary = sweep._decide_robustness(results)
    assert summary["robustness_decision"] == "INCONCLUSIVE"
    assert summary["robustness_conclusive"] is False
    assert summary["quality_gate_passed"] is False
    assert summary["robust"] is False
    assert summary["all_models_falsified_everywhere"] is True


def test_robustness_decision_passes_when_quality_and_stability_gates_pass():
    sweep = _load_sweep_module()
    results = [
        {
            "id": "baseline",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 2,
            "warnings": {"total_warnings": 0},
            "quality_flags": [],
            "valid": True,
        },
        {
            "id": "threshold",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 1,
            "warnings": {"total_warnings": 0},
            "quality_flags": [],
            "valid": True,
        },
        {
            "id": "weights",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 1,
            "warnings": {"total_warnings": 0},
            "quality_flags": [],
            "valid": True,
        },
    ]

    summary = sweep._decide_robustness(results)
    assert summary["robustness_decision"] == "PASS"
    assert summary["robustness_conclusive"] is True
    assert summary["quality_gate_passed"] is True
    assert summary["robust"] is True
    assert summary["valid_scenario_rate"] == 1.0


def test_release_evidence_ready_requires_conclusive_quality_and_full_release_mode():
    sweep = _load_sweep_module()
    summary = {
        "quality_gate_passed": True,
        "robustness_conclusive": True,
    }

    assert sweep._is_release_evidence_ready(
        summary,
        mode="release",
        max_scenarios=None,
        scenario_count_expected=17,
        scenario_count_executed=17,
    )
    assert not sweep._is_release_evidence_ready(
        summary,
        mode="release",
        max_scenarios=1,
        scenario_count_expected=17,
        scenario_count_executed=1,
    )
    assert not sweep._is_release_evidence_ready(
        {"quality_gate_passed": False, "robustness_conclusive": True},
        mode="release",
        max_scenarios=None,
        scenario_count_expected=17,
        scenario_count_executed=17,
    )
    assert not sweep._is_release_evidence_ready(
        {"quality_gate_passed": True, "robustness_conclusive": False},
        mode="release",
        max_scenarios=None,
        scenario_count_expected=17,
        scenario_count_executed=17,
    )
