from pathlib import Path


def test_pre_release_check_script_enforces_sensitivity_release_readiness() -> None:
    script = Path("scripts/audit/pre_release_check.sh").read_text(encoding="utf-8")
    assert "SENSITIVITY_RELEASE_STATUS_PATH" in script
    assert "SENSITIVITY_RELEASE_REPORT_PATH" in script
    assert "SENSITIVITY_RELEASE_PREFLIGHT_PATH" in script
    assert "sensitivity_sweep_release.json" in script
    assert "SENSITIVITY_RESULTS_RELEASE.md" in script
    assert "sensitivity_release_preflight.json" in script
    assert "run_sensitivity_sweep.py" in script
    assert "--preflight-only" in script
    assert "release_evidence_ready" in script
    assert "execution_mode" in script
    assert "dataset_policy_pass" in script
    assert "warning_policy_pass" in script
    assert "warning_density_per_scenario" in script
    assert "total_warning_count" in script
    assert "caveats" in script
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
    assert "CONTROL_COMPARABILITY_STATUS.json" in script
    assert "CONTROL_COMPARABILITY_DATA_AVAILABILITY.json" in script
    assert "check_control_data_availability.py --mode release" in script
    assert "evidence_scope" in script
    assert "full_data_closure_eligible" in script
    assert "approved_lost_pages_policy_version" in script
    assert "approved_lost_pages_source_note_path" in script
    assert "irrecoverability" in script
    assert "full_data_feasibility" in script
    assert "full_data_closure_terminal_reason" in script
    assert "full_data_closure_reopen_conditions" in script
    assert "h3_4_closure_lane" in script
    assert "h3_5_closure_lane" in script
    assert "h3_5_residual_reason" in script
    assert "h3_5_reopen_conditions" in script
    assert "provenance" in script
    assert "run_id" in script
    assert "timestamp" in script
    assert "available_subset_confidence" in script
    assert "missing_count mismatch across artifacts" in script
    assert "check_control_comparability.py --mode release" in script
    assert "build_release_gate_health_status.py" in script
    assert "check_claim_boundaries.py --mode release" in script
    assert "check_closure_conditionality.py --mode release" in script
    assert "check_claim_entitlement_coherence.py --mode release" in script
    assert "run_proximity_uncertainty.py --iterations 2000 --seed 42" in script
    assert "check_comparative_uncertainty.py --mode release" in script
    assert "SK-M2 release contract checks passed" in script
    assert "m2_4_residual_reason" in script
    assert "m2_5_closure_lane" in script
    assert "m2_5_residual_reason" in script
    assert "m2_5_reopen_triggers" in script
    assert "m2_5_data_availability_linkage" in script
    assert "check_report_coherence.py --mode release" in script
    assert "build_provenance_health_status.py" in script
    assert "sync_provenance_register.py" in script
    assert "check_provenance_uncertainty.py --mode release" in script
    assert "m4_5_historical_lane" in script
    assert "m4_5_residual_reason" in script
    assert "m4_5_reopen_conditions" in script
    assert "m4_5_data_availability_linkage" in script
    assert "objective_provenance_contract_incompleteness" in script
    assert "provenance_health_m4_5_lane" in script
    assert "provenance_health_m4_5_residual_reason" in script
    assert "check_provenance_runner_contract.py --mode release" in script
    assert "check_multimodal_coupling.py --mode release" in script
    assert "SK-H1.4/SK-H1.5 multimodal robustness contract" in script
    assert "h1_4_closure_lane" in script
    assert "h1_4_residual_reason" in script
    assert "h1_4_reopen_conditions" in script
    assert "h1_5_closure_lane" in script
    assert "h1_5_residual_reason" in script
    assert "h1_5_reopen_conditions" in script
    assert "robustness_class" in script
    assert "entitlement_robustness_class" in script
    assert "run_control_matching_audit.py --preflight-only" in script
    assert "leakage_detected" in script
    assert "check_sensitivity_artifact_contract.py --mode release" in script
    policy_path = Path("configs/audit/sensitivity_artifact_contract.json")
    assert policy_path.exists()
    assert "artifact_path" in policy_path.read_text(encoding="utf-8")
    provenance_policy = Path("configs/audit/provenance_runner_contract.json")
    assert provenance_policy.exists()
    assert "delegated_provenance" in provenance_policy.read_text(encoding="utf-8")
    multimodal_policy = Path("configs/skeptic/sk_h1_multimodal_status_policy.json")
    assert multimodal_policy.exists()
    assert "allowed_statuses" in multimodal_policy.read_text(encoding="utf-8")


def test_cleanup_status_artifacts_supports_dry_run_summary() -> None:
    script = Path("scripts/audit/cleanup_status_artifacts.sh").read_text(encoding="utf-8")
    assert "dry-run" in script
    assert "legacy-report" in script
    assert "summary mode=" in script
