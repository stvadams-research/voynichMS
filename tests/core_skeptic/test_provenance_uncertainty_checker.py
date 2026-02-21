import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _load_checker_module():
    module_path = Path("scripts/core_skeptic/check_provenance_uncertainty.py")
    spec = importlib.util.spec_from_file_location("check_provenance_uncertainty", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sk_m4_checker_flags_banned_pattern(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/reports").mkdir(parents=True)
    path = tmp_path / "results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md"
    path.write_text("**Archive:** All runs, code, and data are frozen and traceable.", encoding="utf-8")

    policy = {
        "tracked_files": ["results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md"],
        "required_markers": [],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "**Archive:** All runs, code, and data are frozen and traceable.",
                "scopes": ["results/reports/phase4_inference/PHASE_4_5_CLOSURE_STATEMENT.md"],
            }
        ],
        "artifact_policy": {"tracked_artifacts": []},
        "threshold_policy": {},
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_sk_m4_checker_flags_missing_release_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "README.md").write_text("## Historical Provenance Confidence", encoding="utf-8")
    policy = {
        "tracked_files": ["README.md"],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status"],
                }
            ]
        },
        "threshold_policy": {"artifact_path": "core_status/core_audit/provenance_health_status.json"},
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_sk_m4_checker_flags_threshold_violation(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    artifact = tmp_path / "core_status/core_audit/provenance_health_status.json"
    artifact.write_text(
        json.dumps(
            {
                "status": "PROVENANCE_QUALIFIED",
                "reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "allowed_claim": "qualified",
                "total_runs": 10,
                "orphaned_rows": 8,
                "orphaned_ratio": 0.8,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": False,
                "generated_utc": "2026-02-10T00:00:00Z",
                "last_reviewed": "2026-02-10",
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": ["PROVENANCE_CONTRACT_BLOCKED"],
                "contract_coupling_pass": True,
            }
        ),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "orphaned_rows",
                        "orphaned_ratio",
                        "threshold_policy_pass",
                        "generated_utc",
                    ],
                    "allowed_statuses": ["PROVENANCE_ALIGNED", "PROVENANCE_QUALIFIED"],
                }
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 0.4,
            "orphaned_count_max": 80,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("threshold" in err for err in errors)


def test_sk_m4_checker_flags_contract_coupling_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "core_status/core_audit/provenance_health_status.json").write_text(
        json.dumps(
            {
                "status": "PROVENANCE_ALIGNED",
                "reason_code": "NO_HISTORICAL_GAPS_DETECTED",
                "allowed_claim": "aligned",
                "total_runs": 10,
                "orphaned_rows": 0,
                "orphaned_ratio": 0.0,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": True,
                "generated_utc": "2026-02-10T00:00:00Z",
                "last_reviewed": "2026-02-10",
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": [],
                "contract_coupling_pass": False,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED", "reason_code": "GATE_CONTRACT_BLOCKED"}}),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "contract_health_status",
                        "contract_reason_codes",
                        "contract_coupling_pass",
                    ],
                    "allowed_statuses": ["PROVENANCE_ALIGNED", "PROVENANCE_QUALIFIED"],
                }
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "core_status/core_audit/provenance_health_status.json",
            "gate_health_artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "degraded_gate_statuses": ["GATE_HEALTH_DEGRADED"],
            "disallow_provenance_statuses_when_gate_degraded": ["PROVENANCE_ALIGNED"],
            "require_contract_coupling_pass": True,
            "require_contract_reason_codes_when_gate_degraded": [
                "PROVENANCE_CONTRACT_BLOCKED"
            ],
            "fail_when_gate_health_missing": True,
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("contract-coupling" in err for err in errors)


def test_sk_m4_checker_flags_register_drift_status(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "core_status/core_audit/provenance_health_status.json").write_text(
        json.dumps(
            {
                "status": "PROVENANCE_QUALIFIED",
                "reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "allowed_claim": "qualified",
                "total_runs": 10,
                "orphaned_rows": 1,
                "orphaned_ratio": 0.1,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": True,
                "generated_utc": "2026-02-10T00:00:00Z",
                "last_reviewed": "2026-02-10",
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": ["PROVENANCE_CONTRACT_BLOCKED"],
                "contract_coupling_pass": True,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/provenance_register_sync_status.json").write_text(
        json.dumps(
            {
                "status": "DRIFT_DETECTED",
                "drift_detected": True,
                "provenance_status": "PROVENANCE_QUALIFIED",
                "provenance_reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "db_counts": {"success": 10},
                "artifact_counts": {"success": 9},
                "generated_utc": "2026-02-10T00:00:00Z",
                "contract_coupling_state": "COUPLED_DEGRADED",
                "gate_health_status": "GATE_HEALTH_DEGRADED",
                "register_path": "reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED", "reason_code": "GATE_CONTRACT_BLOCKED"}}),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc"],
                    "allowed_statuses": ["PROVENANCE_QUALIFIED"],
                },
                {
                    "path": "core_status/core_audit/provenance_register_sync_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "drift_detected"],
                    "allowed_statuses": ["IN_SYNC"],
                },
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "core_status/core_audit/provenance_health_status.json",
            "gate_health_artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "degraded_gate_statuses": ["GATE_HEALTH_DEGRADED"],
            "disallow_provenance_statuses_when_gate_degraded": ["PROVENANCE_ALIGNED"],
            "require_contract_coupling_pass": True,
            "require_contract_reason_codes_when_gate_degraded": [
                "PROVENANCE_CONTRACT_BLOCKED"
            ],
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-status" in err for err in errors)


def test_sk_m4_checker_passes_with_repo_policy_ci_and_release() -> None:
    checker = _load_checker_module()
    subprocess.run(["python3", "scripts/core_audit/build_release_gate_health_status.py"], check=True)
    subprocess.run(["python3", "scripts/core_audit/build_provenance_health_status.py"], check=True)
    subprocess.run(["python3", "scripts/core_audit/sync_provenance_register.py"], check=True)
    policy = json.loads(
        Path("configs/core_skeptic/sk_m4_provenance_policy.json").read_text(encoding="utf-8")
    )

    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []


def test_sk_m4_checker_flags_m4_4_lane_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "core_status/core_audit/provenance_health_status.json").write_text(
        json.dumps(
            {
                "status": "PROVENANCE_QUALIFIED",
                "reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "orphaned_rows": 5,
                "orphaned_ratio": 0.1,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": True,
                "generated_utc": "2026-02-10T00:00:00Z",
                "recoverability_class": "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
                "m4_4_historical_lane": "M4_4_QUALIFIED",
                "m4_4_residual_reason": "x",
                "m4_4_reopen_conditions": ["a"],
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": ["PROVENANCE_CONTRACT_BLOCKED"],
                "contract_coupling_pass": True,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/provenance_register_sync_status.json").write_text(
        json.dumps(
            {
                "status": "IN_SYNC",
                "drift_detected": False,
                "drift_by_status": {"orphaned": 0, "success": 0},
                "generated_utc": "2026-02-10T00:00:01Z",
                "provenance_status": "PROVENANCE_QUALIFIED",
                "provenance_reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "provenance_health_lane": "M4_4_QUALIFIED",
                "provenance_health_residual_reason": "x",
                "health_orphaned_rows": 5,
                "register_orphaned_rows": 5,
                "artifact_counts": {"orphaned": 5, "success": 10},
                "db_counts": {"orphaned": 5, "success": 10},
                "contract_coupling_state": "COUPLED_DEGRADED",
                "gate_health_status": "GATE_HEALTH_DEGRADED",
                "register_path": "reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED", "reason_code": "GATE_CONTRACT_BLOCKED"}}),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "generated_utc",
                        "recoverability_class",
                        "m4_4_historical_lane",
                        "m4_4_reopen_conditions",
                    ],
                    "allowed_statuses": ["PROVENANCE_QUALIFIED"],
                },
                {
                    "path": "core_status/core_audit/provenance_register_sync_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "drift_detected",
                        "generated_utc",
                        "provenance_health_lane",
                    ],
                    "allowed_statuses": ["IN_SYNC"],
                },
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
            "sync_artifact_path": "core_status/core_audit/provenance_register_sync_status.json",
            "max_sync_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "core_status/core_audit/provenance_health_status.json",
            "gate_health_artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "degraded_gate_statuses": ["GATE_HEALTH_DEGRADED"],
            "disallow_provenance_statuses_when_gate_degraded": ["PROVENANCE_ALIGNED"],
            "require_m4_4_lanes_when_gate_degraded": ["M4_4_QUALIFIED", "M4_4_BOUNDED"],
            "require_contract_coupling_pass": True,
            "require_contract_reason_codes_when_gate_degraded": [
                "PROVENANCE_CONTRACT_BLOCKED"
            ],
        },
        "m4_4_policy": {
            "required_lane_by_provenance_status": {"PROVENANCE_QUALIFIED": "M4_4_QUALIFIED"},
            "bounded_recoverability_classes": ["HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED"],
            "bounded_lane_name": "M4_4_BOUNDED",
            "inconclusive_lane_name": "M4_4_INCONCLUSIVE",
            "require_reopen_conditions_for_lanes": ["M4_4_BOUNDED"],
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("m4_4-lane" in err for err in errors)


def test_sk_m4_checker_flags_stale_sync_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "core_status/core_audit/provenance_health_status.json").write_text(
        json.dumps(
            {
                "status": "PROVENANCE_QUALIFIED",
                "reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "generated_utc": "2026-02-10T00:00:00Z",
                "orphaned_rows": 1,
                "orphaned_ratio": 0.1,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": True,
                "recoverability_class": "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
                "m4_4_historical_lane": "M4_4_BOUNDED",
                "m4_4_residual_reason": "x",
                "m4_4_reopen_conditions": ["a"],
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": ["PROVENANCE_CONTRACT_BLOCKED"],
                "contract_coupling_pass": True,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/provenance_register_sync_status.json").write_text(
        json.dumps(
            {
                "status": "IN_SYNC",
                "drift_detected": False,
                "drift_by_status": {"orphaned": 0},
                "generated_utc": "2000-01-01T00:00:00Z",
                "provenance_status": "PROVENANCE_QUALIFIED",
                "provenance_reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "provenance_health_lane": "M4_4_BOUNDED",
                "provenance_health_residual_reason": "x",
                "health_orphaned_rows": 1,
                "register_orphaned_rows": 1,
                "artifact_counts": {"orphaned": 1},
                "db_counts": {"orphaned": 1},
                "contract_coupling_state": "COUPLED_DEGRADED",
                "gate_health_status": "GATE_HEALTH_DEGRADED",
                "register_path": "reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md",
            }
        ),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc"],
                    "allowed_statuses": ["PROVENANCE_QUALIFIED"],
                },
                {
                    "path": "core_status/core_audit/provenance_register_sync_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc"],
                    "allowed_statuses": ["IN_SYNC"],
                },
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
            "sync_artifact_path": "core_status/core_audit/provenance_register_sync_status.json",
            "max_sync_artifact_age_hours": 1,
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("stale-artifact" in err for err in errors)


def test_sk_m4_checker_flags_missing_folio_block_without_objective_linkage(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "core_status/core_audit/provenance_health_status.json").write_text(
        json.dumps(
            {
                "status": "PROVENANCE_QUALIFIED",
                "reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "orphaned_rows": 5,
                "orphaned_ratio": 0.1,
                "running_rows": 0,
                "missing_manifests": 0,
                "threshold_policy_pass": True,
                "generated_utc": "2026-02-10T00:00:00Z",
                "recoverability_class": "HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED",
                "m4_5_historical_lane": "M4_5_BOUNDED",
                "m4_5_residual_reason": "historical_orphaned_rows_irrecoverable_with_current_source_scope",
                "m4_5_reopen_conditions": ["reopen_if_new_primary_source_added"],
                "m4_5_data_availability_linkage": {
                    "missing_folio_blocking_claimed": True,
                    "objective_provenance_contract_incompleteness": False,
                    "approved_irrecoverable_loss_classification": True,
                },
                "contract_health_status": "GATE_HEALTH_DEGRADED",
                "contract_health_reason_code": "GATE_CONTRACT_BLOCKED",
                "contract_reason_codes": ["PROVENANCE_CONTRACT_BLOCKED"],
                "contract_coupling_pass": True,
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/provenance_register_sync_status.json").write_text(
        json.dumps(
            {
                "status": "IN_SYNC",
                "drift_detected": False,
                "drift_by_status": {"orphaned": 0, "success": 0},
                "generated_utc": "2026-02-10T00:00:01Z",
                "provenance_status": "PROVENANCE_QUALIFIED",
                "provenance_reason_code": "HISTORICAL_ORPHANED_ROWS_PRESENT",
                "provenance_health_lane": "M4_5_BOUNDED",
                "provenance_health_residual_reason": "historical_orphaned_rows_irrecoverable_with_current_source_scope",
                "provenance_health_m4_5_lane": "M4_5_BOUNDED",
                "provenance_health_m4_5_residual_reason": "historical_orphaned_rows_irrecoverable_with_current_source_scope",
                "health_orphaned_rows": 5,
                "register_orphaned_rows": 5,
                "artifact_counts": {"orphaned": 5, "success": 10},
                "db_counts": {"orphaned": 5, "success": 10},
                "contract_coupling_state": "COUPLED_DEGRADED",
                "gate_health_status": "GATE_HEALTH_DEGRADED",
                "register_path": "reports/core_skeptic/SK_M4_PROVENANCE_REGISTER.md",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED", "reason_code": "GATE_CONTRACT_BLOCKED"}}),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/core_audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc", "m4_5_historical_lane"],
                    "allowed_statuses": ["PROVENANCE_QUALIFIED"],
                },
                {
                    "path": "core_status/core_audit/provenance_register_sync_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc", "provenance_health_lane"],
                    "allowed_statuses": ["IN_SYNC"],
                },
            ]
        },
        "threshold_policy": {
            "artifact_path": "core_status/core_audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
            "sync_artifact_path": "core_status/core_audit/provenance_register_sync_status.json",
            "max_sync_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "core_status/core_audit/provenance_health_status.json",
            "gate_health_artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "degraded_gate_statuses": ["GATE_HEALTH_DEGRADED"],
            "disallow_provenance_statuses_when_gate_degraded": ["PROVENANCE_ALIGNED"],
            "require_m4_5_lanes_when_gate_degraded": ["M4_5_QUALIFIED", "M4_5_BOUNDED"],
            "require_contract_coupling_pass": True,
            "require_contract_reason_codes_when_gate_degraded": [
                "PROVENANCE_CONTRACT_BLOCKED"
            ],
        },
        "m4_5_policy": {
            "required_lane_by_provenance_status": {"PROVENANCE_QUALIFIED": "M4_5_QUALIFIED"},
            "bounded_recoverability_classes": ["HISTORICAL_ORPHANED_BACKFILLED_QUALIFIED"],
            "bounded_lane_name": "M4_5_BOUNDED",
            "blocked_lane_name": "M4_5_BLOCKED",
            "inconclusive_lane_name": "M4_5_INCONCLUSIVE",
            "require_reopen_conditions_for_lanes": ["M4_5_BOUNDED"],
            "require_residual_reason_for_lanes": ["M4_5_BOUNDED"],
            "missing_folio_non_blocking_guard": {
                "linkage_key": "m4_5_data_availability_linkage",
                "required_boolean_keys": [
                    "missing_folio_blocking_claimed",
                    "objective_provenance_contract_incompleteness",
                    "approved_irrecoverable_loss_classification",
                ],
                "require_objective_linkage_when_missing_folio_blocking_claimed": True,
                "disallow_blocking_when_approved_irrecoverable_loss_without_objective_linkage": True,
            },
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("objective provenance-contract incompleteness linkage" in err for err in errors)
