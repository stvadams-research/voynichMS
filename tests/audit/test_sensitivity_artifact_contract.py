import importlib.util
import json
from pathlib import Path
from typing import Any, Dict


def _load_checker_module():
    module_path = Path("scripts/audit/check_sensitivity_artifact_contract.py")
    spec = importlib.util.spec_from_file_location("check_sensitivity_artifact_contract", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_summary() -> Dict[str, Any]:
    return {
        "schema_version": "2026-02-10",
        "policy_version": "2026-02-10",
        "generated_utc": "2026-02-10T00:00:00Z",
        "generated_by": "scripts/analysis/run_sensitivity_sweep.py",
        "dataset_id": "voynich_real",
        "dataset_pages": 240,
        "dataset_tokens": 210000,
        "dataset_policy_pass": True,
        "warning_policy_pass": True,
        "warning_density_per_scenario": 0.0,
        "total_warning_count": 0,
        "caveats": [],
        "quality_gate_passed": True,
        "robustness_conclusive": True,
        "execution_mode": "release",
        "scenario_count_expected": 17,
        "scenario_count_executed": 17,
        "release_readiness_failures": [],
        "release_evidence_ready": True,
        "robustness_decision": "PASS",
    }


def _write_fixture(
    tmp_path: Path,
    *,
    summary: Dict[str, Any],
    report_overrides: Dict[str, str] | None = None,
    include_none_caveat: bool = False,
) -> None:
    artifact_path = tmp_path / "status/audit/sensitivity_sweep.json"
    report_path = tmp_path / "reports/audit/SENSITIVITY_RESULTS.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    artifact_path.write_text(
        json.dumps({"results": {"summary": summary}}, indent=2), encoding="utf-8"
    )

    report_values = {
        "Dataset": str(summary.get("dataset_id", "MISSING")),
        "Dataset pages": str(summary.get("dataset_pages", "MISSING")),
        "Dataset tokens": str(summary.get("dataset_tokens", "MISSING")),
        "Execution mode": str(summary.get("execution_mode", "MISSING")),
        "Scenario execution": (
            f"{summary.get('scenario_count_executed', 'MISSING')}/"
            f"{summary.get('scenario_count_expected', 'MISSING')}"
        ),
        "Release evidence ready (full sweep + conclusive robustness + quality gate)": str(
            summary.get("release_evidence_ready", "MISSING")
        ),
        "Robustness decision": str(summary.get("robustness_decision", "MISSING")),
        "Dataset policy pass": str(summary.get("dataset_policy_pass", "MISSING")),
        "Warning policy pass": str(summary.get("warning_policy_pass", "MISSING")),
        "Warning density per scenario": (
            f"{float(summary.get('warning_density_per_scenario', 0.0)):.2f}"
        ),
        "Total warnings observed": str(summary.get("total_warning_count", "MISSING")),
    }
    if report_overrides:
        report_values.update(report_overrides)

    lines = ["# Sensitivity Results", ""]
    for label, value in report_values.items():
        lines.append(f"- {label}: `{value}`")

    if include_none_caveat:
        lines.append("- Caveat: none")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_policy() -> Dict[str, Any]:
    return json.loads(
        Path("configs/audit/sensitivity_artifact_contract.json").read_text(encoding="utf-8")
    )


def test_sensitivity_contract_checker_passes_for_valid_ci_fixture(tmp_path: Path) -> None:
    checker = _load_checker_module()
    _write_fixture(tmp_path, summary=_base_summary())

    errors, summary = checker.run_checks(_load_policy(), root=tmp_path, mode="ci")
    assert errors == []
    assert summary["dataset_id"] == "voynich_real"


def test_sensitivity_contract_checker_flags_missing_required_summary_field(tmp_path: Path) -> None:
    checker = _load_checker_module()
    summary = _base_summary()
    del summary["warning_policy_pass"]
    _write_fixture(tmp_path, summary=summary)

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="ci")
    assert any("missing-summary-field" in err for err in errors)


def test_sensitivity_contract_checker_flags_warning_caveat_contradiction(tmp_path: Path) -> None:
    checker = _load_checker_module()
    summary = _base_summary()
    summary["total_warning_count"] = 5
    summary["warning_density_per_scenario"] = 1.25
    summary["caveats"] = []
    _write_fixture(tmp_path, summary=summary, include_none_caveat=True)

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="ci")
    assert any("caveat-contract" in err for err in errors)


def test_sensitivity_contract_checker_flags_report_value_mismatch(tmp_path: Path) -> None:
    checker = _load_checker_module()
    _write_fixture(
        tmp_path,
        summary=_base_summary(),
        report_overrides={"Warning policy pass": "False"},
    )

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="ci")
    assert any("report-mismatch" in err for err in errors)


def test_sensitivity_contract_checker_release_mode_enforces_release_requirements(tmp_path: Path) -> None:
    checker = _load_checker_module()
    summary = _base_summary()
    summary["execution_mode"] = "iterative"
    summary["release_evidence_ready"] = False
    summary["release_readiness_failures"] = ["execution_mode_not_release"]
    _write_fixture(
        tmp_path,
        summary=summary,
        report_overrides={
            "Execution mode": "iterative",
            "Release evidence ready (full sweep + conclusive robustness + quality gate)": "False",
        },
    )

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="release")
    assert any("release-mode" in err for err in errors)
