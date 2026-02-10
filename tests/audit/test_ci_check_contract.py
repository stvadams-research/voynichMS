from pathlib import Path


def test_ci_check_uses_stage_3_default_and_50_percent_floor() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert 'COVERAGE_STAGE="${COVERAGE_STAGE:-3}"' in script
    assert "3) COVERAGE_MIN=50" in script


def test_ci_check_enforces_critical_module_and_verifier_completion() -> None:
    script = Path("scripts/ci_check.sh").read_text(encoding="utf-8")
    assert 'CRITICAL_MODULE_ENFORCE", "1"' in script
    assert "VERIFY_SENTINEL_PATH" in script
    assert "VERIFY_REPRODUCTION_COMPLETED" in script
    assert "build_release_gate_health_status.py" in script
    assert "check_claim_boundaries.py --mode ci" in script
    assert "run_control_matching_audit.py --preflight-only" in script
    assert "check_control_comparability.py --mode ci" in script
    assert "check_control_data_availability.py --mode ci" in script
    assert "check_closure_conditionality.py --mode ci" in script
    assert "check_comparative_uncertainty.py --mode ci" in script
    assert "check_report_coherence.py --mode ci" in script
    assert "build_provenance_health_status.py" in script
    assert "sync_provenance_register.py" in script
    assert "check_provenance_uncertainty.py --mode ci" in script
    assert "check_provenance_runner_contract.py --mode ci" in script
    assert "check_sensitivity_artifact_contract.py --mode ci" in script
    assert "check_multimodal_coupling.py --mode ci" in script
