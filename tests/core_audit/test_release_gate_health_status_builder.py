import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _load_builder_module():
    module_path = Path("scripts/core_audit/build_release_gate_health_status.py")
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
        sensitivity_path=Path("core_status/core_audit/sensitivity_sweep.json").resolve(),
    )

    assert output_path.exists()
    assert by_run_dir.exists()
    assert list(by_run_dir.glob("release_gate_health_status.*.json"))

    results = payload.get("results", {})
    for key in (
        "status",
        "reason_code",
        "version",
        "generated_utc",
        "generated_at",
        "entitlement_class",
        "allowed_claim_class",
        "allowed_closure_class",
        "h2_4_closure_lane",
        "h2_4_residual_reason",
        "h2_4_reopen_conditions",
        "gates",
    ):
        assert key in results
    assert results.get("status") in {"GATE_HEALTH_OK", "GATE_HEALTH_DEGRADED"}
    dependency_snapshot = results.get("dependency_snapshot", {})
    assert "control_h3_4_closure_lane" in dependency_snapshot
    assert "control_h3_5_closure_lane" in dependency_snapshot
    assert "multimodal_h1_4_derived_closure_lane" in dependency_snapshot
    assert "multimodal_h1_5_derived_closure_lane" in dependency_snapshot
    assert "multimodal_robustness_class" in dependency_snapshot
    assert "multimodal_entitlement_robustness_class" in dependency_snapshot
    assert "comparative_status" in dependency_snapshot
    assert "comparative_reason_code" in dependency_snapshot
    assert "comparative_m2_4_closure_lane" in dependency_snapshot
    assert "comparative_m2_5_derived_closure_lane" in dependency_snapshot
    assert "comparative_m2_5_residual_reason" in dependency_snapshot
    assert "provenance_status" in dependency_snapshot
    assert "provenance_reason_code" in dependency_snapshot
    assert "provenance_m4_5_historical_lane" in dependency_snapshot
    assert "provenance_m4_5_residual_reason" in dependency_snapshot
    assert "provenance_m4_5_data_availability_linkage" in dependency_snapshot
    assert "provenance_sync_status" in dependency_snapshot
    assert "provenance_sync_drift_detected" in dependency_snapshot


def test_release_gate_health_default_sensitivity_path_targets_release_artifact() -> None:
    builder = _load_builder_module()
    assert str(builder.DEFAULT_SENSITIVITY_PATH).endswith(
        "core_status/core_audit/sensitivity_sweep_release.json"
    )


def test_release_gate_health_default_sensitivity_preflight_path_is_canonical() -> None:
    builder = _load_builder_module()
    assert str(builder.DEFAULT_SENSITIVITY_PREFLIGHT_PATH).endswith(
        "core_status/core_audit/sensitivity_release_preflight.json"
    )


def test_release_gate_health_default_sensitivity_run_status_path_is_canonical() -> None:
    builder = _load_builder_module()
    assert str(builder.DEFAULT_SENSITIVITY_RUN_STATUS_PATH).endswith(
        "core_status/core_audit/sensitivity_release_run_status.json"
    )


def test_release_gate_health_default_multimodal_status_path_is_canonical() -> None:
    builder = _load_builder_module()
    assert str(builder.DEFAULT_MULTIMODAL_STATUS_PATH).endswith(
        "results/data/phase5_mechanism/anchor_coupling_confirmatory.json"
    )
