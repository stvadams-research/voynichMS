import importlib.util
import json
import subprocess
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_claim_boundaries.py")
    spec = importlib.util.spec_from_file_location("check_claim_boundaries", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_claim_boundary_checker_passes_with_repo_policy() -> None:
    checker = _load_checker_module()
    artifact = Path("status/audit/release_gate_health_status.json")
    if not artifact.exists():
        subprocess.run(
            ["python3", "scripts/audit/build_release_gate_health_status.py"],
            check=True,
        )
    policy = json.loads(
        Path("configs/skeptic/sk_h2_claim_language_policy.json").read_text(
            encoding="utf-8"
        )
    )
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert release_errors == []


def test_claim_boundary_checker_enforces_gate_degraded_markers(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "## Operational Entitlement State\nstatus/audit/release_gate_health_status.json\n",
        encoding="utf-8",
    )
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "status/audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": ["status"],
            "allowed_statuses": ["GATE_HEALTH_DEGRADED", "GATE_HEALTH_OK"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "degraded_required_markers": [
                {
                    "id": "d1",
                    "scopes": ["README.md"],
                    "markers": ["Current gate-health class: `GATE_HEALTH_DEGRADED`"],
                }
            ],
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert any("missing-gate-marker" in err for err in errors)


def test_claim_boundary_checker_enforces_gate_degraded_bans(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "Language Hypothesis Falsified",
        encoding="utf-8",
    )
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "status/audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": ["status"],
            "allowed_statuses": ["GATE_HEALTH_DEGRADED", "GATE_HEALTH_OK"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "degraded_banned_patterns": [
                {
                    "id": "d2",
                    "pattern": "Language Hypothesis Falsified",
                    "scopes": ["README.md"],
                }
            ],
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert any("gate-degraded-banned-pattern" in err for err in errors)


def test_claim_boundary_checker_honors_allowlist_for_gate_degraded_ban(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "status/audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "Language Hypothesis Falsified",
        encoding="utf-8",
    )
    (tmp_path / "status/audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [{"pattern_id": "d2", "scope": "README.md"}],
        "gate_health_policy": {
            "artifact_path": "status/audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": ["status"],
            "allowed_statuses": ["GATE_HEALTH_DEGRADED", "GATE_HEALTH_OK"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "degraded_banned_patterns": [
                {
                    "id": "d2",
                    "pattern": "Language Hypothesis Falsified",
                    "scopes": ["README.md"],
                }
            ],
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors == []


def test_claim_boundary_checker_flags_banned_phrase(tmp_path) -> None:
    checker = _load_checker_module()
    doc = tmp_path / "README.md"
    doc.write_text("Language Hypothesis Falsified", encoding="utf-8")
    policy = {
        "banned_patterns": [
            {
                "id": "b1",
                "pattern": "Language Hypothesis Falsified",
                "scopes": ["README.md"],
            }
        ],
        "required_markers": [],
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert "banned-pattern" in errors[0]


def test_claim_boundary_checker_honors_allowlist(tmp_path) -> None:
    checker = _load_checker_module()
    doc = tmp_path / "README.md"
    doc.write_text("Language Hypothesis Falsified", encoding="utf-8")
    policy = {
        "banned_patterns": [
            {
                "id": "b1",
                "pattern": "Language Hypothesis Falsified",
                "scopes": ["README.md"],
            }
        ],
        "required_markers": [],
        "allowlist": [{"pattern_id": "b1", "scope": "README.md"}],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors == []


def test_claim_boundary_checker_flags_missing_required_marker(tmp_path) -> None:
    checker = _load_checker_module()
    doc = tmp_path / "README.md"
    doc.write_text("# Title\n", encoding="utf-8")
    policy = {
        "banned_patterns": [],
        "required_markers": [
            {
                "id": "r1",
                "scopes": ["README.md"],
                "markers": ["## Conclusion Scope"],
            }
        ],
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert "missing-marker" in errors[0]
