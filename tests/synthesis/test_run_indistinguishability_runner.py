import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_runner_module():
    module_path = Path("scripts/synthesis/run_indistinguishability_test.py")
    spec = importlib.util.spec_from_file_location("run_indistinguishability_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_indistinguishability_runner_has_no_hardcoded_decision_metrics() -> None:
    script = Path("scripts/synthesis/run_indistinguishability_test.py").read_text(
        encoding="utf-8"
    )

    forbidden = [
        "real_z =",
        "syn_z =",
        "real_rad =",
        "syn_rad =",
        "From final report",
        "Estimated",
    ]
    for pattern in forbidden:
        assert pattern not in script


def test_indistinguishability_runner_uses_computed_stress_tests() -> None:
    script = Path("scripts/synthesis/run_indistinguishability_test.py").read_text(
        encoding="utf-8"
    )
    assert "InformationPreservationTest(store)" in script
    assert "LocalityTest(store)" in script


def test_indistinguishability_runner_has_strict_preflight_guard() -> None:
    script = Path("scripts/synthesis/run_indistinguishability_test.py").read_text(
        encoding="utf-8"
    )
    assert "REQUIRE_COMPUTED" in script
    assert "_preflight_real_profile_inputs(store, strict_computed)" in script
    assert "--preflight-only" in script
    assert "--strict-computed" in script
    assert "--allow-fallback" in script
    assert "PREFLIGHT_OK" in script
    assert "BLOCKED" in script
    assert "reason_code" in script
    assert "DATA_AVAILABILITY" in script


def test_indistinguishability_runner_emits_sk_h3_comparability_fields() -> None:
    script = Path("scripts/synthesis/run_indistinguishability_test.py").read_text(
        encoding="utf-8"
    )
    assert "CONTROL_COMPARABILITY_STATUS.json" in script
    assert "matching_metrics" in script
    assert "holdout_evaluation_metrics" in script
    assert "metric_overlap" in script
    assert "leakage_detected" in script
    assert "normalization_mode" in script


def test_preflight_page_id_normalization_handles_split_folios() -> None:
    runner = _load_runner_module()
    assert runner._normalize_pharma_page_id("f89r1") == "f89r"
    assert runner._normalize_pharma_page_id("f95v2") == "f95v"
    assert runner._normalize_pharma_page_id("f93r") == "f93r"


def test_preflight_available_index_groups_split_and_base_ids() -> None:
    runner = _load_runner_module()
    indexed = runner._index_available_pages({"f89r1", "f89r2", "f88v", "f95v2"})
    assert indexed["f89r"] == ["f89r1", "f89r2"]
    assert indexed["f88v"] == ["f88v"]
    assert indexed["f95v"] == ["f95v2"]


def test_resolve_strict_mode_defaults_to_true(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.delenv("REQUIRE_COMPUTED", raising=False)
    args = SimpleNamespace(strict_computed=False, allow_fallback=False)
    assert runner._resolve_strict_mode(args) is True


def test_resolve_strict_mode_allows_explicit_fallback(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv("REQUIRE_COMPUTED", "1")
    args = SimpleNamespace(strict_computed=False, allow_fallback=True)
    assert runner._resolve_strict_mode(args) is False
