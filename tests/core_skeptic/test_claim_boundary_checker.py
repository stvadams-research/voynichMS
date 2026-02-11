import importlib.util
import json
import subprocess
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/core_skeptic/check_claim_boundaries.py")
    spec = importlib.util.spec_from_file_location("check_claim_boundaries", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_claim_boundary_checker_passes_with_repo_policy() -> None:
    checker = _load_checker_module()
    artifact = Path("core_status/core_audit/release_gate_health_status.json")
    if not artifact.exists():
        subprocess.run(
            ["python3", "scripts/core_audit/build_release_gate_health_status.py"],
            check=True,
        )
    policy = json.loads(
        Path("configs/core_skeptic/sk_h2_claim_language_policy.json").read_text(
            encoding="utf-8"
        )
    )
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert release_errors == []


def test_claim_boundary_checker_enforces_gate_degraded_markers(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "## Operational Entitlement State\ncore_status/core_audit/release_gate_health_status.json\n",
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "core_status/core_audit/release_gate_health_status.json",
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
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "Language Hypothesis Falsified",
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "core_status/core_audit/release_gate_health_status.json",
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


def test_claim_boundary_checker_flags_stale_gate_health_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text("ok", encoding="utf-8")
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "GATE_HEALTH_DEGRADED",
                    "generated_utc": "2000-01-01T00:00:00Z",
                }
            }
        ),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": ["status", "generated_utc"],
            "allowed_statuses": ["GATE_HEALTH_DEGRADED", "GATE_HEALTH_OK"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "timestamp_keys": ["generated_utc"],
            "max_age_seconds": 60,
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert any("gate-health-freshness" in err for err in errors)


def test_claim_boundary_checker_flags_h2_4_lane_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text("ok", encoding="utf-8")
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "GATE_HEALTH_DEGRADED",
                    "generated_utc": "2026-02-10T00:00:00Z",
                    "h2_4_closure_lane": "H2_4_ALIGNED",
                    "allowed_claim_class": "QUALIFIED",
                    "allowed_closure_class": "CONDITIONAL_CLOSURE_QUALIFIED",
                }
            }
        ),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [],
        "gate_health_policy": {
            "artifact_path": "core_status/core_audit/release_gate_health_status.json",
            "required_in_modes": ["ci"],
            "required_result_keys": [
                "status",
                "generated_utc",
                "h2_4_closure_lane",
                "allowed_claim_class",
                "allowed_closure_class",
            ],
            "allowed_statuses": ["GATE_HEALTH_DEGRADED", "GATE_HEALTH_OK"],
            "degraded_statuses": ["GATE_HEALTH_DEGRADED"],
            "timestamp_keys": ["generated_utc"],
            "max_age_seconds": 365 * 24 * 3600,
        },
        "h2_4_policy": {
            "allowed_lanes": [
                "H2_4_ALIGNED",
                "H2_4_QUALIFIED",
                "H2_4_BLOCKED",
                "H2_4_INCONCLUSIVE",
            ],
            "lane_by_gate_status": {
                "GATE_HEALTH_OK": "H2_4_ALIGNED",
                "GATE_HEALTH_DEGRADED": "H2_4_QUALIFIED",
            },
            "required_claim_class_by_lane": {
                "H2_4_ALIGNED": "CONCLUSIVE_WITHIN_SCOPE",
                "H2_4_QUALIFIED": "QUALIFIED",
            },
            "required_closure_class_by_lane": {
                "H2_4_ALIGNED": "CONDITIONAL_CLOSURE_ALIGNED",
                "H2_4_QUALIFIED": "CONDITIONAL_CLOSURE_QUALIFIED",
            },
        },
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors
    assert any("h2_4-lane" in err for err in errors)


def test_claim_boundary_checker_honors_allowlist_for_gate_degraded_ban(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    (tmp_path / "README.md").write_text(
        "Language Hypothesis Falsified",
        encoding="utf-8",
    )
    (tmp_path / "core_status/core_audit/release_gate_health_status.json").write_text(
        json.dumps({"results": {"status": "GATE_HEALTH_DEGRADED"}}),
        encoding="utf-8",
    )
    policy = {
        "banned_patterns": [],
        "required_markers": [],
        "allowlist": [{"pattern_id": "d2", "scope": "README.md"}],
        "gate_health_policy": {
            "artifact_path": "core_status/core_audit/release_gate_health_status.json",
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
