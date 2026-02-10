import importlib.util
from pathlib import Path


def _load_builder_module():
    module_path = Path("scripts/audit/build_release_gate_health_status.py")
    spec = importlib.util.spec_from_file_location(
        "build_release_gate_health_status", module_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_release_gate_health_builder_emits_required_artifacts(tmp_path) -> None:
    builder = _load_builder_module()
    output_path = tmp_path / "release_gate_health_status.json"
    by_run_dir = tmp_path / "by_run"
    payload = builder.build_release_gate_health_status(
        output_path=output_path,
        by_run_dir=by_run_dir,
        python_bin="python3",
        sensitivity_path=Path("status/audit/sensitivity_sweep.json").resolve(),
    )

    assert output_path.exists()
    assert by_run_dir.exists()
    assert list(by_run_dir.glob("release_gate_health_status.*.json"))

    results = payload.get("results", {})
    for key in (
        "status",
        "reason_code",
        "entitlement_class",
        "allowed_claim_class",
        "allowed_closure_class",
        "gates",
    ):
        assert key in results
    assert results.get("status") in {"GATE_HEALTH_OK", "GATE_HEALTH_DEGRADED"}
