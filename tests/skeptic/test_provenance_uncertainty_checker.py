import importlib.util
import json
import subprocess
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_provenance_uncertainty.py")
    spec = importlib.util.spec_from_file_location("check_provenance_uncertainty", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sk_m4_checker_flags_banned_pattern(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/reports").mkdir(parents=True)
    path = tmp_path / "results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"
    path.write_text("**Archive:** All runs, code, and data are frozen and traceable.", encoding="utf-8")

    policy = {
        "tracked_files": ["results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"],
        "required_markers": [],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "**Archive:** All runs, code, and data are frozen and traceable.",
                "scopes": ["results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"],
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
                    "path": "status/audit/provenance_health_status.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status"],
                }
            ]
        },
        "threshold_policy": {"artifact_path": "status/audit/provenance_health_status.json"},
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_sk_m4_checker_flags_threshold_violation(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "status/audit").mkdir(parents=True)
    artifact = tmp_path / "status/audit/provenance_health_status.json"
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
                    "path": "status/audit/provenance_health_status.json",
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
            "artifact_path": "status/audit/provenance_health_status.json",
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
    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "status/audit/provenance_health_status.json").write_text(
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
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
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
                    "path": "status/audit/provenance_health_status.json",
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
            "artifact_path": "status/audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "status/audit/provenance_health_status.json",
            "gate_health_artifact_path": "status/audit/release_gate_health_status.json",
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
    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "status/audit/provenance_health_status.json").write_text(
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
    (tmp_path / "status/audit/provenance_register_sync_status.json").write_text(
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
                "register_path": "reports/skeptic/SK_M4_PROVENANCE_REGISTER.md",
            }
        ),
        encoding="utf-8",
    )
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
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
                    "path": "status/audit/provenance_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "generated_utc"],
                    "allowed_statuses": ["PROVENANCE_QUALIFIED"],
                },
                {
                    "path": "status/audit/provenance_register_sync_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "drift_detected"],
                    "allowed_statuses": ["IN_SYNC"],
                },
            ]
        },
        "threshold_policy": {
            "artifact_path": "status/audit/provenance_health_status.json",
            "orphaned_ratio_max": 1.0,
            "orphaned_count_max": 1000,
            "running_count_max": 0,
            "missing_manifests_max": 0,
            "max_artifact_age_hours": 100000,
        },
        "contract_coupling_policy": {
            "provenance_artifact_path": "status/audit/provenance_health_status.json",
            "gate_health_artifact_path": "status/audit/release_gate_health_status.json",
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
    subprocess.run(["python3", "scripts/audit/build_release_gate_health_status.py"], check=True)
    subprocess.run(["python3", "scripts/audit/build_provenance_health_status.py"], check=True)
    subprocess.run(["python3", "scripts/audit/sync_provenance_register.py"], check=True)
    policy = json.loads(
        Path("configs/skeptic/sk_m4_provenance_policy.json").read_text(encoding="utf-8")
    )

    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []
