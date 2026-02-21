import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

pytestmark = pytest.mark.integration


def _now_utc() -> str:
    """Current UTC timestamp for fixture freshness."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_checker_module():
    module_path = Path("scripts/core_audit/check_sensitivity_artifact_contract.py")
    spec = importlib.util.spec_from_file_location("check_sensitivity_artifact_contract", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_summary() -> Dict[str, Any]:
    return {
        "schema_version": "2026-02-10",
        "policy_version": "2026-02-10",
        "generated_utc": _now_utc(),
        "generated_by": "scripts/phase2_analysis/run_sensitivity_sweep.py",
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
    preflight_status: str | None = None,
    preflight_reason_codes: list[str] | None = None,
    run_status_payload: Dict[str, Any] | None = None,
) -> None:
    artifact_path = tmp_path / "core_status/core_audit/sensitivity_sweep.json"
    release_artifact_path = tmp_path / "core_status/core_audit/sensitivity_sweep_release.json"
    report_path = tmp_path / "reports/core_audit/SENSITIVITY_RESULTS.md"
    release_report_path = tmp_path / "reports/core_audit/SENSITIVITY_RESULTS_RELEASE.md"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    release_artifact_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    release_report_path.parent.mkdir(parents=True, exist_ok=True)

    for out_path in (artifact_path, release_artifact_path):
        out_path.write_text(
            json.dumps({"results": {"summary": summary}}, indent=2), encoding="utf-8"
        )

    if preflight_status is not None:
        preflight_path = tmp_path / "core_status/core_audit/sensitivity_release_preflight.json"
        preflight_path.parent.mkdir(parents=True, exist_ok=True)
        preflight_path.write_text(
            json.dumps(
                {
                    "results": {
                        "status": preflight_status,
                        "reason_codes": preflight_reason_codes or [],
                        "generated_utc": _now_utc(),
                    }
                },
                indent=2,
            ),
            encoding="utf-8",
        )

    if run_status_payload is not None:
        run_status_path = tmp_path / "core_status/core_audit/sensitivity_release_run_status.json"
        run_status_path.parent.mkdir(parents=True, exist_ok=True)
        run_status_path.write_text(json.dumps(run_status_payload, indent=2), encoding="utf-8")

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

    for out_path in (report_path, release_report_path):
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_policy() -> Dict[str, Any]:
    return json.loads(
        Path("configs/core_audit/sensitivity_artifact_contract.json").read_text(encoding="utf-8")
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


def test_release_mode_uses_release_artifact_path_contract(tmp_path: Path) -> None:
    checker = _load_checker_module()
    _write_fixture(tmp_path, summary=_base_summary())

    # Corrupt CI/latest artifact only; release-mode checks must still pass.
    ci_path = tmp_path / "core_status/core_audit/sensitivity_sweep.json"
    ci_payload = json.loads(ci_path.read_text(encoding="utf-8"))
    ci_summary = ci_payload["results"]["summary"]
    ci_summary["execution_mode"] = "iterative"
    ci_summary["release_evidence_ready"] = False
    ci_summary["release_readiness_failures"] = ["execution_mode_not_release"]
    ci_path.write_text(json.dumps(ci_payload, indent=2), encoding="utf-8")

    release_errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="release")
    ci_errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="ci")

    assert release_errors == []
    assert any("report-mismatch" in err or "release-readiness" in err for err in ci_errors)


def test_release_mode_missing_artifact_reports_preflight_guidance(tmp_path: Path) -> None:
    checker = _load_checker_module()

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="release")

    assert any("missing-artifact" in err for err in errors)
    assert any("sensitivity_release_preflight.json" in err for err in errors)
    assert any("--preflight-only" in err for err in errors)


def test_release_mode_missing_artifact_after_preflight_has_explicit_reason(tmp_path: Path) -> None:
    checker = _load_checker_module()
    preflight_path = tmp_path / "core_status/core_audit/sensitivity_release_preflight.json"
    preflight_path.parent.mkdir(parents=True, exist_ok=True)
    preflight_path.write_text(
        json.dumps(
            {
                "results": {
                    "status": "PREFLIGHT_OK",
                    "reason_codes": [],
                    "generated_utc": _now_utc(),
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    run_status_path = tmp_path / "core_status/core_audit/sensitivity_release_run_status.json"
    run_status_path.parent.mkdir(parents=True, exist_ok=True)
    run_status_path.write_text(
        json.dumps(
            {
                "status": "RUNNING",
                "reason_codes": ["RELEASE_RUN_SCENARIO_DISPATCHED"],
                "generated_utc": "2026-02-10T00:00:10Z",
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="release")

    assert any("preflight_ok_but_release_artifact_missing" in err for err in errors)
    assert any("[release-run-status]" in err for err in errors)


def test_release_mode_flags_stale_run_status_heartbeat(tmp_path: Path) -> None:
    checker = _load_checker_module()
    summary = _base_summary()
    summary["generated_utc"] = "2026-02-10T00:00:00Z"
    _write_fixture(
        tmp_path,
        summary=summary,
        preflight_status="PREFLIGHT_OK",
        run_status_payload={
            "status": "RUNNING",
            "reason_codes": ["RELEASE_RUN_SCENARIO_IN_PROGRESS"],
            "generated_utc": "2000-01-01T00:00:00Z",
        },
    )

    errors, _ = checker.run_checks(_load_policy(), root=tmp_path, mode="release")
    assert any("stale-heartbeat" in err for err in errors)
