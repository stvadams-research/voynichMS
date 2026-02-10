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
    assert "dataset_policy_pass" in script
    assert "warning_policy_pass" in script
    assert "warning_density_per_scenario" in script
    assert "total_warning_count" in script
    assert "caveats" in script
    assert "robustness_decision" in script
    assert "quality_gate_passed" in script
    assert "robustness_conclusive" in script
    assert "scenario_count_expected" in script
    assert "scenario_count_executed" in script
    assert "status/by_run" in script
    assert "provenance.status" in script or "provenance\", {}).get(\"status\")" in script
    assert "check_sensitivity_artifact_contract.py --mode release" in script
    assert "check_provenance_runner_contract.py --mode release" in script
    assert "check_multimodal_coupling.py --mode release" in script
    assert "build_release_gate_health_status.py" in script
    assert "check_claim_boundaries.py --mode release" in script
    assert "check_closure_conditionality.py --mode release" in script
    assert "check_report_coherence.py --mode release" in script


def test_verify_reproduction_checks_sk_m4_provenance_contract() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "build_provenance_health_status.py" in script
    assert "sync_provenance_register.py" in script
    assert "check_provenance_uncertainty.py --mode release" in script
    assert "provenance_register_sync_status.json" in script
    assert "contract_coupling_pass" in script


def test_verify_reproduction_has_optional_strict_mode_gate() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "VERIFY_STRICT" in script
    assert "REQUIRE_COMPUTED=1" in script
    assert "--preflight-only" in script
    assert "TURING_TEST_RESULTS.json" in script
    assert "strict_computed" in script
    assert "DATA_AVAILABILITY" in script
    assert "reason_code" in script


def test_verify_reproduction_checks_sk_h3_comparability_contract() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "run_control_matching_audit.py --preflight-only" in script
    assert "check_control_comparability.py --mode release" in script
    assert "check_control_data_availability.py --mode release" in script
    assert "CONTROL_COMPARABILITY_STATUS.json" in script
    assert "CONTROL_COMPARABILITY_DATA_AVAILABILITY.json" in script
    assert "evidence_scope" in script
    assert "full_data_closure_eligible" in script
    assert "missing_count mismatch" in script
    assert "matching_metrics" in script
    assert "holdout_evaluation_metrics" in script
    assert "metric_overlap" in script
    assert "leakage_detected" in script


def test_verify_reproduction_checks_sk_m2_uncertainty_contract() -> None:
    script = Path("scripts/verify_reproduction.sh").read_text(encoding="utf-8")
    assert "run_proximity_uncertainty.py --iterations 2000 --seed 42" in script
    assert "check_comparative_uncertainty.py --mode release" in script
    assert "phase_7c_uncertainty.json" in script
    assert "rank_stability" in script
    assert "rank_stability_components" in script
    assert "nearest_neighbor_probability_margin" in script
    assert "metric_validity" in script


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
