import importlib.util
import json
import subprocess
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_report_coherence.py")
    spec = importlib.util.spec_from_file_location("check_report_coherence", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sk_m3_checker_flags_pending_pattern(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "results/reports/PHASE_4_RESULTS.md").write_text(
        "| **B: Network Features**| PENDING | NOT STARTED |\n",
        encoding="utf-8",
    )

    policy = {
        "tracked_files": ["results/reports/PHASE_4_RESULTS.md"],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": r"\| \*\*[B-E]: [^|]+\*\*\|\s*PENDING",
                "regex": True,
                "scopes": ["results/reports/PHASE_4_RESULTS.md"],
            }
        ],
        "required_markers": [],
        "artifact_policy": {"tracked_artifacts": []},
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_sk_m3_checker_flags_missing_release_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "results/reports/PHASE_4_RESULTS.md").write_text(
        "Canonical status source:\nresults/reports/PHASE_4_STATUS_INDEX.json",
        encoding="utf-8",
    )

    policy = {
        "tracked_files": ["results/reports/PHASE_4_RESULTS.md"],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/reports/PHASE_4_STATUS_INDEX.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status", "methods"],
                }
            ]
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_sk_m3_checker_flags_method_policy_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/reports").mkdir(parents=True)
    artifact_path = tmp_path / "results/reports/PHASE_4_STATUS_INDEX.json"
    artifact_path.write_text(
        json.dumps(
            {
                "status": "COHERENCE_ALIGNED",
                "methods": [
                    {
                        "id": "A",
                        "execution_status": "IN_PROGRESS",
                        "determination": "NOT_DIAGNOSTIC",
                    }
                ],
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
                    "path": "results/reports/PHASE_4_STATUS_INDEX.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "methods"],
                    "allowed_statuses": ["COHERENCE_ALIGNED"],
                }
            ]
        },
        "method_policy": {
            "artifact_path": "results/reports/PHASE_4_STATUS_INDEX.json",
            "required_method_ids": ["A", "B"],
            "required_execution_status": "COMPLETE",
            "required_determination": "NOT_DIAGNOSTIC",
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-method" in err for err in errors)


def test_sk_m3_checker_passes_with_repo_policy_ci_and_release() -> None:
    checker = _load_checker_module()
    artifact = Path("status/audit/release_gate_health_status.json")
    if not artifact.exists():
        subprocess.run(
            ["python3", "scripts/audit/build_release_gate_health_status.py"],
            check=True,
        )
    policy = json.loads(
        Path("configs/skeptic/sk_m3_report_coherence_policy.json").read_text(encoding="utf-8")
    )

    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []
