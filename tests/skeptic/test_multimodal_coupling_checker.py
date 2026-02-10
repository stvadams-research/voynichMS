import importlib.util
import json
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_multimodal_coupling.py")
    spec = importlib.util.spec_from_file_location("check_multimodal_coupling", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_multimodal_checker_flags_missing_required_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    policy = {
        "tracked_files": [],
        "artifact_policy": {
            "path": "results/mechanism/anchor_coupling_confirmatory.json",
            "required_in_modes": ["release"],
            "required_result_keys": ["status"],
        },
        "status_policy": {"allowed_statuses": ["INCONCLUSIVE_UNDERPOWERED"]},
        "required_markers": [],
        "banned_patterns": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_multimodal_checker_blocks_unqualified_resolution_in_non_conclusive_mode(
    tmp_path,
) -> None:
    checker = _load_checker_module()

    (tmp_path / "results/mechanism").mkdir(parents=True)
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "reports/human").mkdir(parents=True)

    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNDERPOWERED",
            "status_reason": "inferential_ambiguity",
            "allowed_claim": "No conclusive claim is allowed.",
            "anchor_method": {"id": "m1", "name": "method", "parameters": {}},
            "policy": {},
            "cohorts": {},
            "effect": {
                "delta_mean_consistency": 0.0,
                "delta_ci_low": -0.01,
                "delta_ci_high": 0.01,
                "p_value": 0.7,
            },
            "adequacy": {"pass": True, "blocked": False, "reasons": [], "metrics": {}},
            "inference": {
                "decision": "INCONCLUSIVE",
                "alpha": 0.05,
                "coupling_delta_abs_min": 0.03,
                "no_coupling_delta_abs_max": 0.015,
                "ci_crosses_zero": True,
                "abs_delta": 0.0,
            },
        }
    }
    (tmp_path / "results/mechanism/anchor_coupling_confirmatory.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    (tmp_path / "results/reports/PHASE_5H_RESULTS.md").write_text(
        "conclusively resolves illustration coupling",
        encoding="utf-8",
    )
    (tmp_path / "results/reports/PHASE_5I_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/human/PHASE_7_FINDINGS_SUMMARY.md").write_text(
        "ok", encoding="utf-8"
    )
    (tmp_path / "reports/human/PHASE_7B_RESULTS.md").write_text(
        "no conclusive claim is allowed",
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [
            "results/reports/PHASE_5H_RESULTS.md",
            "results/reports/PHASE_5I_RESULTS.md",
            "reports/human/PHASE_7_FINDINGS_SUMMARY.md",
            "reports/human/PHASE_7B_RESULTS.md",
        ],
        "artifact_policy": {
            "path": "results/mechanism/anchor_coupling_confirmatory.json",
            "required_in_modes": ["ci"],
            "required_result_keys": [
                "status",
                "status_reason",
                "allowed_claim",
                "anchor_method",
                "policy",
                "cohorts",
                "effect",
                "adequacy",
                "inference",
            ],
        },
        "status_policy": {
            "allowed_statuses": [
                "CONCLUSIVE_NO_COUPLING",
                "CONCLUSIVE_COUPLING_PRESENT",
                "INCONCLUSIVE_UNDERPOWERED",
                "BLOCKED_DATA_GEOMETRY",
            ]
        },
        "required_markers": [],
        "banned_patterns": [
            {
                "id": "b1",
                "for_statuses": ["INCONCLUSIVE_UNDERPOWERED", "BLOCKED_DATA_GEOMETRY"],
                "regex": True,
                "case_insensitive": True,
                "pattern": "conclusively\\s+resolves\\s+illustration\\s+coupling",
                "scopes": ["results/reports/PHASE_5H_RESULTS.md"],
            }
        ],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_multimodal_checker_passes_with_repo_policy_ci_mode() -> None:
    checker = _load_checker_module()
    policy_path = Path("configs/skeptic/sk_h1_multimodal_status_policy.json")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []
