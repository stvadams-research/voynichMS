import importlib.util
import json
import subprocess
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_closure_conditionality.py")
    spec = importlib.util.spec_from_file_location("check_closure_conditionality", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_closure_checker_flags_banned_pattern(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "reports/comparative").mkdir(parents=True)
    path = tmp_path / "reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md"
    path.write_text("No further amount of statistical or structural comparison", encoding="utf-8")

    policy = {
        "tracked_files": ["reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md"],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "No further amount of statistical or structural comparison",
                "scopes": ["reports/comparative/PHASE_B_BOUNDARY_STATEMENT.md"],
            }
        ],
        "required_markers": [],
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_closure_checker_flags_missing_marker(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "docs/REOPENING_CRITERIA.md").write_text("canonical criteria", encoding="utf-8")

    policy = {
        "tracked_files": ["docs/REOPENING_CRITERIA.md"],
        "banned_patterns": [],
        "required_markers": [
            {
                "id": "m1",
                "scopes": ["docs/REOPENING_CRITERIA.md"],
                "markers": ["Irreducible Signal", "External Grounding"],
            }
        ],
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-marker" in err for err in errors)


def test_closure_checker_honors_allowlist(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "results/reports").mkdir(parents=True)
    path = tmp_path / "results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"
    path.write_text("PROJECT CLOSED WITHIN CURRENT FRAMEWORK", encoding="utf-8")

    policy = {
        "tracked_files": ["results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "PROJECT CLOSED WITHIN CURRENT FRAMEWORK",
                "scopes": ["results/reports/PHASE_4_5_CLOSURE_STATEMENT.md"],
            }
        ],
        "required_markers": [],
        "allowlist": [
            {
                "pattern_id": "p1",
                "scope": "results/reports/PHASE_4_5_CLOSURE_STATEMENT.md",
            }
        ],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors == []


def test_closure_checker_passes_with_repo_policy_ci_and_release() -> None:
    checker = _load_checker_module()
    artifact = Path("status/audit/release_gate_health_status.json")
    if not artifact.exists():
        subprocess.run(
            ["python3", "scripts/audit/build_release_gate_health_status.py"],
            check=True,
        )
    policy = json.loads(
        Path("configs/skeptic/sk_m1_closure_policy.json").read_text(encoding="utf-8")
    )

    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []


def test_closure_checker_enforces_gate_degraded_marker_rules(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "reports/comparative").mkdir(parents=True)
    (tmp_path / "reports/comparative/PHASE_B_SYNTHESIS.md").write_text(
        "### Conditionally Closed Statement\n",
        encoding="utf-8",
    )
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": ["reports/comparative/PHASE_B_SYNTHESIS.md"],
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "status/audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": ["status"],
            "allowed_statuses": ["GATE_HEALTH_OK", "GATE_HEALTH_DEGRADED"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "degraded_required_markers": [
                {
                    "id": "d1",
                    "scopes": ["reports/comparative/PHASE_B_SYNTHESIS.md"],
                    "markers": ["Current gate-health class: `GATE_HEALTH_DEGRADED`"],
                }
            ],
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert any("missing-gate-marker" in err for err in errors)
