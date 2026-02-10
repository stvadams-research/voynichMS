from pathlib import Path


def test_verify_reproduction_uses_isolated_db_and_temp_outputs() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "VERIFY_DB_URL" in script
    assert "--db-url \"$VERIFY_DB_URL\"" in script
    assert "mktemp /tmp/verify_1" in script
    assert "mktemp /tmp/verify_2" in script


def test_verify_reproduction_checks_sensitivity_artifact_integrity() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "sensitivity_sweep_legacy_reconcile" in script
    assert "unknown_legacy" in script
    assert "sensitivity_sweep.json" in script
    assert "SENSITIVITY_RESULTS.md" in script
    assert "execution_mode" in script
    assert "release_evidence_ready" in script
    assert "robustness_decision" in script
    assert "quality_gate_passed" in script
    assert "robustness_conclusive" in script
    assert "scenario_count_expected" in script
    assert "scenario_count_executed" in script
    assert "status/by_run" in script
    assert "provenance.status" in script or "provenance\", {}).get(\"status\")" in script


def test_verify_reproduction_has_optional_strict_mode_gate() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "VERIFY_STRICT" in script
    assert "REQUIRE_COMPUTED=1" in script
    assert "--preflight-only" in script
    assert "TURING_TEST_RESULTS.json" in script
    assert "strict_computed" in script
    assert "DATA_AVAILABILITY" in script
    assert "reason_code" in script


def test_verify_reproduction_handles_unset_virtual_env_and_sets_completion_sentinel() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "${VIRTUAL_ENV:-}" in script
    assert "VERIFY_SENTINEL_PATH" in script
    assert "VERIFY_REPRODUCTION_COMPLETED" in script
    assert "VERIFICATION_COMPLETE=1" in script


def test_ci_check_requires_verifier_completion_sentinel() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert "VERIFY_SENTINEL" in script
    assert "VERIFY_SENTINEL_PATH" in script
    assert "VERIFY_REPRODUCTION_COMPLETED" in script
    assert "CRITICAL_MODULE_ENFORCE" in script
