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
    assert "Verifying SK-H3 semantic parity" in script
    assert "approved_lost_pages_policy_version" in script
    assert "irrecoverability metadata mismatch" in script
    assert "full_data_feasibility" in script
    assert "full_data_closure_terminal_reason" in script
    assert "full_data_closure_reopen_conditions" in script
    assert "h3_4_closure_lane" in script
    assert "h3_5_closure_lane" in script
    assert "h3_5_residual_reason" in script
    assert "h3_5_reopen_conditions" in script
    assert "run_id mismatch" in script
    assert "timestamp skew" in script
    assert "check_closure_conditionality.py --mode ci" in script
    assert "check_claim_entitlement_coherence.py --mode ci" in script
    assert "check_comparative_uncertainty.py --mode ci" in script
    assert "Verifying SK-M2.5 uncertainty lane semantics" in script
    assert "m2_5_closure_lane" in script
    assert "m2_5_data_availability_linkage" in script
    assert "check_report_coherence.py --mode ci" in script
    assert "build_provenance_health_status.py" in script
    assert "sync_provenance_register.py" in script
    assert "check_provenance_uncertainty.py --mode ci" in script
    assert "Verifying SK-M4.5 provenance lane semantics" in script
    assert "m4_5_historical_lane" in script
    assert "m4_5_residual_reason" in script
    assert "m4_5_reopen_conditions" in script
    assert "m4_5_data_availability_linkage" in script
    assert "objective_provenance_contract_incompleteness" in script
    assert "provenance_health_m4_5_lane" in script
    assert "check_provenance_runner_contract.py --mode ci" in script
    assert "check_sensitivity_artifact_contract.py --mode ci" in script
    assert "run_sensitivity_sweep.py" in script
    assert "--preflight-only" in script
    assert "check_sensitivity_artifact_contract.py --mode release" in script
    assert "check_multimodal_coupling.py --mode ci" in script
    assert "Verifying SK-H1.4/SK-H1.5 multimodal robustness parity" in script
    assert "h1_4_closure_lane" in script
    assert "h1_5_closure_lane" in script
    assert "robustness_class" in script
    assert "entitlement_robustness_class" in script
    assert "h1_4_reopen_conditions" in script
    assert "h1_5_reopen_conditions" in script
    assert "core_status/robustness mismatch" in script
