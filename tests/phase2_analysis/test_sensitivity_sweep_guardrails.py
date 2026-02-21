import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def _load_sweep_module():
    module_path = Path("scripts/phase2_analysis/run_sensitivity_sweep.py")
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
        "dataset_policy_pass": True,
        "warning_policy_pass": True,
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
    assert not sweep._is_release_evidence_ready(
        {
            "quality_gate_passed": True,
            "robustness_conclusive": True,
            "dataset_policy_pass": False,
            "warning_policy_pass": True,
        },
        mode="release",
        max_scenarios=None,
        scenario_count_expected=17,
        scenario_count_executed=17,
    )
    assert not sweep._is_release_evidence_ready(
        {
            "quality_gate_passed": True,
            "robustness_conclusive": True,
            "dataset_policy_pass": True,
            "warning_policy_pass": False,
        },
        mode="release",
        max_scenarios=None,
        scenario_count_expected=17,
        scenario_count_executed=17,
    )


def test_dataset_policy_evaluation_fails_for_nonrepresentative_dataset():
    sweep = _load_sweep_module()
    policy = {
        "allowed_dataset_ids": ["voynich_real"],
        "min_pages": 200,
        "min_tokens": 200000,
    }
    profile = {"dataset_id": "voynich_synthetic_grammar", "pages": 18, "tokens": 216}
    result = sweep._evaluate_dataset_policy(profile, policy)
    assert result["dataset_policy_pass"] is False
    assert result["dataset_policy_reasons"]


def test_warning_policy_can_invalidate_otherwise_stable_run():
    sweep = _load_sweep_module()
    results = [
        {
            "id": "baseline",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 2,
            "warnings": {
                "total_warnings": 30,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 1,
                "nan_sanitized_warnings": 0,
            },
            "quality_flags": ["sparse_data", "warning_density_exceeded"],
            "valid": False,
        },
        {
            "id": "threshold",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 2,
            "warnings": {
                "total_warnings": 30,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 1,
                "nan_sanitized_warnings": 0,
            },
            "quality_flags": ["sparse_data", "warning_density_exceeded"],
            "valid": False,
        },
    ]
    warning_policy = {
        "max_total_warning_count": 20,
        "max_warning_density_per_scenario": 10.0,
        "max_insufficient_data_scenarios": 0,
        "max_sparse_data_scenarios": 0,
        "max_nan_sanitized_scenarios": 0,
        "max_fallback_heavy_scenarios": 0,
    }

    summary = sweep._decide_robustness(results, warning_policy)
    assert summary["warning_policy_pass"] is False
    assert summary["quality_gate_passed"] is False


def test_collect_release_readiness_failures_explains_false_ready_state():
    sweep = _load_sweep_module()
    failures = sweep._collect_release_readiness_failures(
        {
            "quality_gate_passed": False,
            "robustness_conclusive": False,
            "dataset_policy_pass": False,
            "warning_policy_pass": True,
        },
        mode="iterative",
        max_scenarios=3,
        scenario_count_expected=17,
        scenario_count_executed=3,
    )
    assert "execution_mode_not_release" in failures
    assert "max_scenarios_override_present" in failures
    assert "incomplete_scenario_execution" in failures
    assert "quality_gate_failed" in failures
    assert "robustness_not_conclusive" in failures
    assert "dataset_policy_failed" in failures


def test_decide_robustness_deduplicates_caveats():
    sweep = _load_sweep_module()
    results = [
        {
            "id": "baseline",
            "top_model": "m1",
            "anomaly_confirmed": True,
            "surviving_models": 1,
            "warnings": {
                "total_warnings": 30,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 1,
                "nan_sanitized_warnings": 0,
                "fallback_estimate_warnings": 0,
                "fallback_related_warnings": 0,
                "fallback_warning_ratio": 0.0,
            },
            "quality_flags": ["sparse_data", "warning_density_exceeded"],
            "valid": False,
        }
    ]
    warning_policy = {
        "max_total_warning_count": 20,
        "max_warning_density_per_scenario": 10.0,
        "max_insufficient_data_scenarios": 0,
        "max_sparse_data_scenarios": 0,
        "max_nan_sanitized_scenarios": 0,
        "max_fallback_heavy_scenarios": 0,
    }
    summary = sweep._decide_robustness(results, warning_policy)
    assert len(summary["caveats"]) == len(set(summary["caveats"]))
