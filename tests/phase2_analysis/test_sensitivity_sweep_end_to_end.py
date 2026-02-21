import importlib.util
import json
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


def test_main_writes_canonical_status_and_report(tmp_path, monkeypatch):
    sweep = _load_sweep_module()

    model_params_path = tmp_path / "model_params.json"
    model_params_path.write_text("{}", encoding="utf-8")
    status_path = tmp_path / "status" / "sensitivity_sweep.json"
    release_status_path = tmp_path / "status" / "sensitivity_sweep_release.json"
    report_path = tmp_path / "SENSITIVITY_RESULTS.md"
    release_report_path = tmp_path / "SENSITIVITY_RESULTS_RELEASE.md"
    progress_path = tmp_path / "status" / "sensitivity_progress.json"
    preflight_path = tmp_path / "status" / "sensitivity_release_preflight.json"
    checkpoint_path = tmp_path / "status" / "sensitivity_checkpoint.json"
    release_run_status_path = tmp_path / "status" / "sensitivity_release_run_status.json"
    diagnostics_path = tmp_path / "status" / "sensitivity_quality_diagnostics.json"
    release_diagnostics_path = (
        tmp_path / "status" / "sensitivity_quality_diagnostics_release.json"
    )

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "STATUS_PATH", status_path)
    monkeypatch.setattr(sweep, "RELEASE_STATUS_PATH", release_status_path)
    monkeypatch.setattr(sweep, "REPORT_PATH", report_path)
    monkeypatch.setattr(sweep, "RELEASE_REPORT_PATH", release_report_path)
    monkeypatch.setattr(sweep, "PROGRESS_PATH", progress_path)
    monkeypatch.setattr(sweep, "RELEASE_PREFLIGHT_PATH", preflight_path)
    monkeypatch.setattr(sweep, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(sweep, "RELEASE_RUN_STATUS_PATH", release_run_status_path)
    monkeypatch.setattr(sweep, "DIAGNOSTICS_PATH", diagnostics_path)
    monkeypatch.setattr(sweep, "RELEASE_DIAGNOSTICS_PATH", release_diagnostics_path)
    monkeypatch.setattr(
        sweep,
        "_load_release_evidence_policy",
        lambda: {
            "policy_version": "unit-test",
            "dataset_policy": {
                "allowed_dataset_ids": ["voynich_real"],
                "min_pages": 1,
                "min_tokens": 1,
            },
            "warning_policy": {
                "max_total_warning_count": 1000,
                "max_warning_density_per_scenario": 1000.0,
                "max_insufficient_data_scenarios": 0,
                "max_sparse_data_scenarios": 0,
                "max_nan_sanitized_scenarios": 0,
                "max_fallback_heavy_scenarios": 0,
                "fallback_heavy_threshold_per_scenario": 99,
                "max_fallback_warning_ratio_per_scenario": 1.0,
            },
        },
    )

    monkeypatch.setattr(
        sweep,
        "_load_dataset_profile",
        lambda _store, dataset_id: {"dataset_id": dataset_id, "pages": 1, "tokens": 5},
    )
    monkeypatch.setattr(
        sweep,
        "_build_scenarios",
        lambda _cfg: [{"id": "baseline", "family": "baseline", "config": {}}],
    )
    monkeypatch.setattr(
        sweep,
        "_run_model_evaluation_scenario",
        lambda _db_url, _dataset_id, _cfg, _warning_policy, **_kwargs: {
            "metrics": {
                "top_model": "m1",
                "top_score": 0.9,
                "surviving_models": 1,
                "falsified_models": 0,
                "anomaly_confirmed": True,
                "anomaly_stable": True,
            },
            "warnings": {
                "total_warnings": 0,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 0,
                "nan_sanitized_warnings": 0,
                "fallback_estimate_warnings": 0,
                "fallback_related_warnings": 0,
                "fallback_warning_ratio": 0.0,
                "sample_messages": [],
            },
            "quality_flags": [],
            "valid": True,
        },
    )

    class DummyStore:
        def __init__(self, _db_url):
            self.saved_runs = []

        def save_run(self, run):
            self.saved_runs.append(str(run.run_id))

    monkeypatch.setattr(sweep, "MetadataStore", DummyStore)

    sweep.main(dataset_id="voynich_real", db_url="sqlite:///tmp/test.db", mode="release")

    status_data = json.loads(release_status_path.read_text(encoding="utf-8"))
    provenance = status_data.get("provenance", {})
    summary = status_data.get("results", {}).get("summary", {})
    dataset_profile = status_data.get("results", {}).get("dataset_profile", {})

    assert provenance.get("command") == "run_sensitivity_sweep"
    assert summary.get("dataset_id") == "voynich_real"
    assert dataset_profile.get("dataset_id") == "voynich_real"
    assert summary.get("execution_mode") == "release"
    assert summary.get("scenario_count_expected") == 1
    assert summary.get("scenario_count_executed") == 1
    assert summary.get("schema_version") == sweep.SENSITIVITY_SCHEMA_VERSION
    assert summary.get("policy_version") == "unit-test"
    assert summary.get("generated_utc")
    assert summary.get("generated_by") == sweep.SENSITIVITY_GENERATED_BY
    assert summary.get("dataset_policy_pass") is True
    assert summary.get("warning_policy_pass") is True
    assert summary.get("quality_gate_passed") is True
    assert summary.get("robustness_conclusive") is True
    assert summary.get("release_evidence_ready") is True
    assert summary.get("release_readiness_failures") == []

    report_text = release_report_path.read_text(encoding="utf-8")
    assert "unknown_legacy" not in report_text
    assert "Schema version" in report_text
    assert "Policy version" in report_text
    assert "Generated by" in report_text
    assert "Robustness decision" in report_text
    assert "Robustness conclusive" in report_text
    assert "Dataset policy pass" in report_text
    assert "Warning policy pass" in report_text
    assert "Quality gate passed" in report_text
    assert "Release evidence ready" in report_text
    assert "Release readiness failures" in report_text
    assert release_diagnostics_path.exists()
    assert checkpoint_path.exists()
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint.get("status") == "COMPLETED"
    run_status = json.loads(release_run_status_path.read_text(encoding="utf-8"))
    assert run_status.get("status") == "COMPLETED"
    assert run_status.get("stage") == "run_completed"
    assert not status_path.exists()
    assert not report_path.exists()


def test_release_mode_rejects_max_scenarios() -> None:
    sweep = _load_sweep_module()
    with pytest.raises(ValueError, match="Release mode requires full scenario execution"):
        sweep.main(
            dataset_id="voynich_real",
            db_url="sqlite:///tmp/test.db",
            max_scenarios=1,
            mode="release",
        )


def test_quick_mode_uses_iterative_defaults_and_writes_progress(tmp_path, monkeypatch):
    sweep = _load_sweep_module()

    model_params_path = tmp_path / "model_params.json"
    model_params_path.write_text("{}", encoding="utf-8")
    status_path = tmp_path / "status" / "sensitivity_sweep.json"
    release_status_path = tmp_path / "status" / "sensitivity_sweep_release.json"
    report_path = tmp_path / "SENSITIVITY_RESULTS.md"
    release_report_path = tmp_path / "SENSITIVITY_RESULTS_RELEASE.md"
    diagnostics_path = tmp_path / "status" / "sensitivity_quality_diagnostics.json"
    release_diagnostics_path = (
        tmp_path / "status" / "sensitivity_quality_diagnostics_release.json"
    )
    progress_path = tmp_path / "status" / "sensitivity_progress.json"
    preflight_path = tmp_path / "status" / "sensitivity_release_preflight.json"
    checkpoint_path = tmp_path / "status" / "sensitivity_checkpoint.json"
    release_run_status_path = tmp_path / "status" / "sensitivity_release_run_status.json"

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "STATUS_PATH", status_path)
    monkeypatch.setattr(sweep, "RELEASE_STATUS_PATH", release_status_path)
    monkeypatch.setattr(sweep, "REPORT_PATH", report_path)
    monkeypatch.setattr(sweep, "RELEASE_REPORT_PATH", release_report_path)
    monkeypatch.setattr(sweep, "DIAGNOSTICS_PATH", diagnostics_path)
    monkeypatch.setattr(sweep, "RELEASE_DIAGNOSTICS_PATH", release_diagnostics_path)
    monkeypatch.setattr(sweep, "PROGRESS_PATH", progress_path)
    monkeypatch.setattr(sweep, "RELEASE_PREFLIGHT_PATH", preflight_path)
    monkeypatch.setattr(sweep, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(sweep, "RELEASE_RUN_STATUS_PATH", release_run_status_path)
    monkeypatch.setattr(
        sweep,
        "_load_release_evidence_policy",
        lambda: {
            "policy_version": "unit-test",
            "dataset_policy": {
                "allowed_dataset_ids": ["voynich_real", sweep.ITERATIVE_DEFAULT_DATASET_ID],
                "min_pages": 1,
                "min_tokens": 1,
            },
            "warning_policy": {
                "max_total_warning_count": 1000,
                "max_warning_density_per_scenario": 1000.0,
                "max_insufficient_data_scenarios": 0,
                "max_sparse_data_scenarios": 0,
                "max_nan_sanitized_scenarios": 0,
                "max_fallback_heavy_scenarios": 0,
                "fallback_heavy_threshold_per_scenario": 99,
                "max_fallback_warning_ratio_per_scenario": 1.0,
            },
        },
    )

    seen_dataset_ids = []
    monkeypatch.setattr(
        sweep,
        "_load_dataset_profile",
        lambda _store, dataset_id: (
            seen_dataset_ids.append(dataset_id) or
            {"dataset_id": dataset_id, "pages": 18, "tokens": 216}
        ),
    )
    monkeypatch.setattr(
        sweep,
        "_build_scenarios",
        lambda _cfg: [
            {"id": "baseline", "family": "baseline", "config": {}},
            {"id": "threshold_0.50", "family": "threshold_sweep", "config": {}},
            {"id": "threshold_0.70", "family": "threshold_sweep", "config": {}},
            {"id": "sensitivity_x1.20", "family": "sensitivity_scale", "config": {}},
            {"id": "weights_focus_robustness", "family": "weight_permutation", "config": {}},
            {"id": "extra", "family": "weight_permutation", "config": {}},
        ],
    )
    monkeypatch.setattr(
        sweep,
        "_run_model_evaluation_scenario",
        lambda _db_url, _dataset_id, _cfg, _warning_policy, **_kwargs: {
            "metrics": {
                "top_model": "m1",
                "top_score": 0.9,
                "surviving_models": 1,
                "falsified_models": 0,
                "anomaly_confirmed": True,
                "anomaly_stable": True,
            },
            "warnings": {
                "total_warnings": 0,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 0,
                "nan_sanitized_warnings": 0,
                "fallback_estimate_warnings": 0,
                "fallback_related_warnings": 0,
                "fallback_warning_ratio": 0.0,
                "sample_messages": [],
            },
            "quality_flags": [],
            "valid": True,
        },
    )

    class DummyStore:
        def __init__(self, _db_url):
            self.saved_runs = []

        def save_run(self, run):
            self.saved_runs.append(str(run.run_id))

    monkeypatch.setattr(sweep, "MetadataStore", DummyStore)

    sweep.main(
        dataset_id=sweep.DEFAULT_DATASET_ID,
        db_url="sqlite:///tmp/test.db",
        mode="smoke",
        quick=True,
    )

    assert seen_dataset_ids == [sweep.ITERATIVE_DEFAULT_DATASET_ID]
    status_data = json.loads(status_path.read_text(encoding="utf-8"))
    summary = status_data.get("results", {}).get("summary", {})
    assert summary.get("execution_mode") == "iterative"
    assert summary.get("scenario_count_executed") <= sweep.ITERATIVE_DEFAULT_MAX_SCENARIOS
    assert summary.get("release_evidence_ready") is False
    assert "execution_mode_not_release" in summary.get("release_readiness_failures", [])
    assert not release_status_path.exists()
    assert not release_report_path.exists()
    assert not release_diagnostics_path.exists()
    assert not release_run_status_path.exists()

    progress_data = json.loads(progress_path.read_text(encoding="utf-8"))
    assert progress_data.get("stage") == "run_completed"
    assert progress_data.get("eta_sec") is not None


def test_quick_mode_rejects_release_mode() -> None:
    sweep = _load_sweep_module()
    with pytest.raises(ValueError, match="Quick mode cannot be combined with release mode"):
        sweep.main(
            dataset_id="voynich_real",
            db_url="sqlite:///tmp/test.db",
            mode="release",
            quick=True,
        )


def test_preflight_only_writes_release_preflight_artifact(tmp_path, monkeypatch):
    sweep = _load_sweep_module()

    model_params_path = tmp_path / "model_params.json"
    model_params_path.write_text("{}", encoding="utf-8")
    release_status_path = tmp_path / "status" / "sensitivity_sweep_release.json"
    release_report_path = tmp_path / "SENSITIVITY_RESULTS_RELEASE.md"
    preflight_path = tmp_path / "status" / "sensitivity_release_preflight.json"
    checkpoint_path = tmp_path / "status" / "sensitivity_checkpoint.json"
    progress_path = tmp_path / "status" / "sensitivity_progress.json"
    release_run_status_path = tmp_path / "status" / "sensitivity_release_run_status.json"

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "RELEASE_STATUS_PATH", release_status_path)
    monkeypatch.setattr(sweep, "RELEASE_REPORT_PATH", release_report_path)
    monkeypatch.setattr(sweep, "RELEASE_PREFLIGHT_PATH", preflight_path)
    monkeypatch.setattr(sweep, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(sweep, "PROGRESS_PATH", progress_path)
    monkeypatch.setattr(sweep, "RELEASE_RUN_STATUS_PATH", release_run_status_path)
    monkeypatch.setattr(
        sweep,
        "_load_release_evidence_policy",
        lambda: {
            "policy_version": "unit-test",
            "dataset_policy": {
                "allowed_dataset_ids": ["voynich_real"],
                "min_pages": 1,
                "min_tokens": 1,
            },
            "warning_policy": {},
        },
    )
    monkeypatch.setattr(
        sweep,
        "_load_dataset_profile",
        lambda _store, dataset_id: {"dataset_id": dataset_id, "pages": 2, "tokens": 20},
    )
    monkeypatch.setattr(
        sweep,
        "_build_scenarios",
        lambda _cfg: [{"id": "baseline", "family": "baseline", "config": {}}],
    )

    class DummyStore:
        def __init__(self, _db_url):
            self.saved_runs = []

        def save_run(self, run):
            self.saved_runs.append(str(run.run_id))

    monkeypatch.setattr(sweep, "MetadataStore", DummyStore)

    sweep.main(
        dataset_id="voynich_real",
        db_url="sqlite:///tmp/test.db",
        mode="release",
        preflight_only=True,
    )

    assert preflight_path.exists()
    preflight_payload = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight_results = preflight_payload.get("results", {})
    assert preflight_results.get("status") == "PREFLIGHT_OK"
    assert preflight_results.get("reason_codes") == []
    assert not release_status_path.exists()
    assert not release_report_path.exists()
    assert not checkpoint_path.exists()
    assert not release_run_status_path.exists()


def test_release_mode_resume_from_checkpoint_skips_completed_scenarios(tmp_path, monkeypatch):
    sweep = _load_sweep_module()

    model_params_path = tmp_path / "model_params.json"
    model_params_path.write_text("{}", encoding="utf-8")
    release_status_path = tmp_path / "status" / "sensitivity_sweep_release.json"
    release_report_path = tmp_path / "SENSITIVITY_RESULTS_RELEASE.md"
    release_diagnostics_path = (
        tmp_path / "status" / "sensitivity_quality_diagnostics_release.json"
    )
    preflight_path = tmp_path / "status" / "sensitivity_release_preflight.json"
    checkpoint_path = tmp_path / "status" / "sensitivity_checkpoint.json"
    progress_path = tmp_path / "status" / "sensitivity_progress.json"
    release_run_status_path = tmp_path / "status" / "sensitivity_release_run_status.json"

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "RELEASE_STATUS_PATH", release_status_path)
    monkeypatch.setattr(sweep, "RELEASE_REPORT_PATH", release_report_path)
    monkeypatch.setattr(sweep, "RELEASE_DIAGNOSTICS_PATH", release_diagnostics_path)
    monkeypatch.setattr(sweep, "RELEASE_PREFLIGHT_PATH", preflight_path)
    monkeypatch.setattr(sweep, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(sweep, "PROGRESS_PATH", progress_path)
    monkeypatch.setattr(sweep, "RELEASE_RUN_STATUS_PATH", release_run_status_path)

    monkeypatch.setattr(
        sweep,
        "_load_release_evidence_policy",
        lambda: {
            "policy_version": "unit-test",
            "dataset_policy": {
                "allowed_dataset_ids": ["voynich_real"],
                "min_pages": 1,
                "min_tokens": 1,
            },
            "warning_policy": {
                "max_total_warning_count": 1000,
                "max_warning_density_per_scenario": 1000.0,
                "max_insufficient_data_scenarios": 0,
                "max_sparse_data_scenarios": 0,
                "max_nan_sanitized_scenarios": 0,
                "max_fallback_heavy_scenarios": 0,
                "fallback_heavy_threshold_per_scenario": 99,
                "max_fallback_warning_ratio_per_scenario": 1.0,
            },
        },
    )
    monkeypatch.setattr(
        sweep,
        "_load_dataset_profile",
        lambda _store, dataset_id: {"dataset_id": dataset_id, "pages": 3, "tokens": 30},
    )
    monkeypatch.setattr(
        sweep,
        "_build_scenarios",
        lambda _cfg: [
            {"id": "baseline", "family": "baseline", "config": {}},
            {"id": "threshold_0.50", "family": "threshold_sweep", "config": {}},
        ],
    )

    baseline_row = {
        "id": "baseline",
        "family": "baseline",
        "top_model": "m1",
        "top_score": 0.9,
        "surviving_models": 1,
        "falsified_models": 0,
        "anomaly_confirmed": True,
        "anomaly_stable": True,
        "warnings": {
            "total_warnings": 0,
            "insufficient_data_warnings": 0,
            "sparse_data_warnings": 0,
            "nan_sanitized_warnings": 0,
            "fallback_estimate_warnings": 0,
            "fallback_related_warnings": 0,
            "fallback_warning_ratio": 0.0,
            "sample_messages": [],
        },
        "quality_flags": [],
        "valid": True,
    }
    checkpoint_payload = {
        "signature": {
            "dataset_id": "voynich_real",
            "mode": "release",
            "scenario_ids": ["baseline", "threshold_0.50"],
            "policy_version": "unit-test",
        },
        "completed_scenarios": [
            {
                "id": "baseline",
                "scenario_index": 1,
                "result": baseline_row,
            }
        ],
    }
    checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
    checkpoint_path.write_text(json.dumps(checkpoint_payload, indent=2), encoding="utf-8")

    call_count = {"count": 0}

    def _fake_run(_db_url, _dataset_id, _cfg, _warning_policy, **_kwargs):
        call_count["count"] += 1
        return {
            "metrics": {
                "top_model": "m1",
                "top_score": 0.88,
                "surviving_models": 1,
                "falsified_models": 0,
                "anomaly_confirmed": True,
                "anomaly_stable": True,
            },
            "warnings": {
                "total_warnings": 0,
                "insufficient_data_warnings": 0,
                "sparse_data_warnings": 0,
                "nan_sanitized_warnings": 0,
                "fallback_estimate_warnings": 0,
                "fallback_related_warnings": 0,
                "fallback_warning_ratio": 0.0,
                "sample_messages": [],
            },
            "quality_flags": [],
            "valid": True,
        }

    monkeypatch.setattr(sweep, "_run_model_evaluation_scenario", _fake_run)

    class DummyStore:
        def __init__(self, _db_url):
            self.saved_runs = []

        def save_run(self, run):
            self.saved_runs.append(str(run.run_id))

    monkeypatch.setattr(sweep, "MetadataStore", DummyStore)

    sweep.main(
        dataset_id="voynich_real",
        db_url="sqlite:///tmp/test.db",
        mode="release",
        resume_from_checkpoint=True,
    )

    assert call_count["count"] == 1
    payload = json.loads(release_status_path.read_text(encoding="utf-8"))
    summary = payload.get("results", {}).get("summary", {})
    assert summary.get("scenario_count_executed") == 2
    assert summary.get("release_evidence_ready") is True
    run_status = json.loads(release_run_status_path.read_text(encoding="utf-8"))
    assert run_status.get("status") == "COMPLETED"


def test_release_mode_failure_writes_failed_run_status(tmp_path, monkeypatch):
    sweep = _load_sweep_module()

    model_params_path = tmp_path / "model_params.json"
    model_params_path.write_text("{}", encoding="utf-8")
    release_status_path = tmp_path / "status" / "sensitivity_sweep_release.json"
    release_report_path = tmp_path / "SENSITIVITY_RESULTS_RELEASE.md"
    release_diagnostics_path = (
        tmp_path / "status" / "sensitivity_quality_diagnostics_release.json"
    )
    preflight_path = tmp_path / "status" / "sensitivity_release_preflight.json"
    checkpoint_path = tmp_path / "status" / "sensitivity_checkpoint.json"
    progress_path = tmp_path / "status" / "sensitivity_progress.json"
    release_run_status_path = tmp_path / "status" / "sensitivity_release_run_status.json"

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "RELEASE_STATUS_PATH", release_status_path)
    monkeypatch.setattr(sweep, "RELEASE_REPORT_PATH", release_report_path)
    monkeypatch.setattr(sweep, "RELEASE_DIAGNOSTICS_PATH", release_diagnostics_path)
    monkeypatch.setattr(sweep, "RELEASE_PREFLIGHT_PATH", preflight_path)
    monkeypatch.setattr(sweep, "CHECKPOINT_PATH", checkpoint_path)
    monkeypatch.setattr(sweep, "PROGRESS_PATH", progress_path)
    monkeypatch.setattr(sweep, "RELEASE_RUN_STATUS_PATH", release_run_status_path)
    monkeypatch.setattr(
        sweep,
        "_load_release_evidence_policy",
        lambda: {
            "policy_version": "unit-test",
            "dataset_policy": {
                "allowed_dataset_ids": ["voynich_real"],
                "min_pages": 1,
                "min_tokens": 1,
            },
            "warning_policy": {
                "max_total_warning_count": 1000,
                "max_warning_density_per_scenario": 1000.0,
                "max_insufficient_data_scenarios": 0,
                "max_sparse_data_scenarios": 0,
                "max_nan_sanitized_scenarios": 0,
                "max_fallback_heavy_scenarios": 0,
                "fallback_heavy_threshold_per_scenario": 99,
                "max_fallback_warning_ratio_per_scenario": 1.0,
            },
        },
    )
    monkeypatch.setattr(
        sweep,
        "_load_dataset_profile",
        lambda _store, dataset_id: {"dataset_id": dataset_id, "pages": 2, "tokens": 20},
    )
    monkeypatch.setattr(
        sweep,
        "_build_scenarios",
        lambda _cfg: [{"id": "baseline", "family": "baseline", "config": {}}],
    )

    def _raise_failure(_db_url, _dataset_id, _cfg, _warning_policy, **_kwargs):
        raise RuntimeError("simulated sensitivity failure")

    monkeypatch.setattr(sweep, "_run_model_evaluation_scenario", _raise_failure)

    class DummyStore:
        def __init__(self, _db_url):
            self.saved_runs = []

        def save_run(self, run):
            self.saved_runs.append(str(run.run_id))

    monkeypatch.setattr(sweep, "MetadataStore", DummyStore)

    with pytest.raises(RuntimeError, match="simulated sensitivity failure"):
        sweep.main(dataset_id="voynich_real", db_url="sqlite:///tmp/test.db", mode="release")

    run_status = json.loads(release_run_status_path.read_text(encoding="utf-8"))
    assert run_status.get("status") == "FAILED"
    assert run_status.get("stage") == "run_failed"
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert checkpoint.get("status") == "FAILED"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert progress.get("stage") == "run_failed"
