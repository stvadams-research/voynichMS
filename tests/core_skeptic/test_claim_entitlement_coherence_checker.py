import json
import subprocess
from pathlib import Path


def test_claim_entitlement_coherence_checker_passes_with_repo_policy() -> None:
    artifact = Path("core_status/core_audit/release_gate_health_status.json")
    if not artifact.exists():
        subprocess.run(
            ["python3", "scripts/core_audit/build_release_gate_health_status.py"],
            check=True,
        )
    result = subprocess.run(
        [
            "python3",
            "scripts/core_skeptic/check_claim_entitlement_coherence.py",
            "--mode",
            "ci",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_claim_entitlement_coherence_checker_flags_lane_mismatch(tmp_path) -> None:
    (tmp_path / "core_status/core_audit").mkdir(parents=True)
    gate_artifact = tmp_path / "core_status/core_audit/release_gate_health_status.json"
    gate_artifact.write_text(
        json.dumps(
            {
                "results": {
                    "status": "GATE_HEALTH_DEGRADED",
                    "reason_code": "GATE_CONTRACT_BLOCKED",
                    "entitlement_class": "ENTITLEMENT_DEGRADED",
                    "allowed_claim_class": "QUALIFIED",
                    "allowed_closure_class": "CONDITIONAL_CLOSURE_QUALIFIED",
                    "h2_4_closure_lane": "H2_4_ALIGNED",
                    "h2_4_residual_reason": "gate_contract_dependency_unresolved",
                    "h2_4_reopen_conditions": ["x"],
                    "generated_utc": "2026-02-10T00:00:00Z",
                    "gates": {},
                }
            }
        ),
        encoding="utf-8",
    )

    h2_policy_path = tmp_path / "h2_policy.json"
    h2_policy_path.write_text(
        json.dumps(
            {
                "version": "test",
                "tracked_files": [],
                "banned_patterns": [],
                "required_markers": [],
                "allowlist": [],
                "gate_health_policy": {
                    "artifact_path": "core_status/core_audit/release_gate_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "entitlement_class",
                        "allowed_claim_class",
                        "allowed_closure_class",
                        "h2_4_closure_lane",
                        "generated_utc",
                        "gates",
                    ],
                    "allowed_statuses": ["GATE_HEALTH_OK", "GATE_HEALTH_DEGRADED"],
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
        ),
        encoding="utf-8",
    )

    m1_policy_path = tmp_path / "m1_policy.json"
    m1_policy_path.write_text(
        json.dumps(
            {
                "version": "test",
                "tracked_files": [],
                "banned_patterns": [],
                "required_markers": [],
                "allowlist": [],
                "gate_health_policy": {
                    "artifact_path": "core_status/core_audit/release_gate_health_status.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "allowed_closure_class",
                        "h2_4_closure_lane",
                        "generated_utc",
                    ],
                    "allowed_statuses": ["GATE_HEALTH_OK", "GATE_HEALTH_DEGRADED"],
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
                    "required_closure_class_by_lane": {
                        "H2_4_ALIGNED": "CONDITIONAL_CLOSURE_ALIGNED",
                        "H2_4_QUALIFIED": "CONDITIONAL_CLOSURE_QUALIFIED",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "python3",
            "scripts/core_skeptic/check_claim_entitlement_coherence.py",
            "--mode",
            "ci",
            "--root",
            str(tmp_path),
            "--gate-health-path",
            str(gate_artifact),
            "--h2-policy-path",
            str(h2_policy_path),
            "--m1-policy-path",
            str(m1_policy_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "h2_4-lane" in (result.stdout + result.stderr)
