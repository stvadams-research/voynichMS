from pathlib import Path


def test_pre_release_check_script_enforces_sensitivity_release_readiness() -> None:
    script = Path("scripts/audit/pre_release_check.sh").read_text(encoding="utf-8")
    assert "release_evidence_ready" in script
    assert "execution_mode" in script
    assert "robustness_decision" in script
    assert "quality_gate_passed" in script
    assert "robustness_conclusive" in script
    assert "ALLOW_DIRTY_RELEASE" in script
    assert "DIRTY_RELEASE_REASON" in script
    assert "at least 12 characters" in script
    assert "must include ':'" in script
    assert "legacy_provenance_status" in script or "provenance.status" in script
    assert "TURING_TEST_RESULTS.json" in script
    assert "strict_computed" in script
    assert "DATA_AVAILABILITY" in script
    assert "reason_code" in script


def test_cleanup_status_artifacts_supports_dry_run_summary() -> None:
    script = Path("scripts/audit/cleanup_status_artifacts.sh").read_text(encoding="utf-8")
    assert "dry-run" in script
    assert "legacy-report" in script
    assert "summary mode=" in script
