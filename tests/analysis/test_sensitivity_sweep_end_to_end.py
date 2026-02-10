import importlib.util
import json
from pathlib import Path
import pytest


def _load_sweep_module():
    module_path = Path("scripts/analysis/run_sensitivity_sweep.py")
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
    report_path = tmp_path / "SENSITIVITY_RESULTS.md"

    monkeypatch.setattr(sweep, "MODEL_PARAMS_PATH", model_params_path)
    monkeypatch.setattr(sweep, "STATUS_PATH", status_path)
    monkeypatch.setattr(sweep, "REPORT_PATH", report_path)

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
        lambda _db_url, _dataset_id, _cfg: {
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
                "nan_sanitized_warnings": 0,
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

    status_data = json.loads(status_path.read_text(encoding="utf-8"))
    provenance = status_data.get("provenance", {})
    summary = status_data.get("results", {}).get("summary", {})
    dataset_profile = status_data.get("results", {}).get("dataset_profile", {})

    assert provenance.get("command") == "run_sensitivity_sweep"
    assert summary.get("dataset_id") == "voynich_real"
    assert dataset_profile.get("dataset_id") == "voynich_real"
    assert summary.get("execution_mode") == "release"
    assert summary.get("scenario_count_expected") == 1
    assert summary.get("scenario_count_executed") == 1
    assert summary.get("quality_gate_passed") is True
    assert summary.get("robustness_conclusive") is True
    assert summary.get("release_evidence_ready") is True

    report_text = report_path.read_text(encoding="utf-8")
    assert "unknown_legacy" not in report_text
    assert "Robustness decision" in report_text
    assert "Robustness conclusive" in report_text
    assert "Quality gate passed" in report_text
    assert "Release evidence ready" in report_text


def test_release_mode_rejects_max_scenarios() -> None:
    sweep = _load_sweep_module()
    with pytest.raises(ValueError, match="Release mode requires full scenario execution"):
        sweep.main(
            dataset_id="voynich_real",
            db_url="sqlite:///tmp/test.db",
            max_scenarios=1,
            mode="release",
        )
