import importlib.util
import json
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/core_skeptic/check_multimodal_coupling.py")
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
            "path": "results/phase5_mechanism/anchor_coupling_confirmatory.json",
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

    (tmp_path / "results/phase5_mechanism").mkdir(parents=True)
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "reports/phase7_human").mkdir(parents=True)

    artifact = {
        "results": {
            "status": "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
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
            "phase4_inference": {
                "decision": "INCONCLUSIVE",
                "alpha": 0.05,
                "coupling_delta_abs_min": 0.03,
                "no_coupling_delta_abs_max": 0.015,
                "ci_crosses_zero": True,
                "abs_delta": 0.0,
            },
        }
    }
    (tmp_path / "results/phase5_mechanism/anchor_coupling_confirmatory.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md").write_text(
        "conclusively resolves illustration coupling",
        encoding="utf-8",
    )
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md").write_text(
        "ok", encoding="utf-8"
    )
    (tmp_path / "reports/phase7_human/PHASE_7B_RESULTS.md").write_text(
        "no conclusive claim is allowed",
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [
            "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md",
            "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md",
            "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md",
            "reports/phase7_human/PHASE_7B_RESULTS.md",
        ],
        "artifact_policy": {
            "path": "results/phase5_mechanism/anchor_coupling_confirmatory.json",
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
                "phase4_inference",
            ],
        },
        "status_policy": {
            "allowed_statuses": [
                "CONCLUSIVE_NO_COUPLING",
                "CONCLUSIVE_COUPLING_PRESENT",
                "INCONCLUSIVE_UNDERPOWERED",
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
                "BLOCKED_DATA_GEOMETRY",
            ]
        },
        "coherence_policy": {
            "allowed_status_reason_by_status": {
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY": ["inferential_ambiguity"]
            },
            "required_adequacy_pass_by_status": {
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY": True
            },
            "required_inference_decision_by_status": {
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY": "INCONCLUSIVE"
            },
        },
        "required_markers": [],
        "banned_patterns": [
            {
                "id": "b1",
                "for_statuses": [
                    "INCONCLUSIVE_UNDERPOWERED",
                    "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
                    "BLOCKED_DATA_GEOMETRY",
                ],
                "regex": True,
                "case_insensitive": True,
                "pattern": "conclusively\\s+resolves\\s+illustration\\s+coupling",
                "scopes": ["results/reports/phase5_mechanism/PHASE_5H_RESULTS.md"],
            }
        ],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_multimodal_checker_passes_with_repo_policy_ci_mode() -> None:
    checker = _load_checker_module()
    policy_path = Path("configs/core_skeptic/sk_h1_multimodal_status_policy.json")
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []


def test_multimodal_checker_flags_status_adequacy_coherence_violation(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "results/phase5_mechanism").mkdir(parents=True)
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "reports/phase7_human").mkdir(parents=True)

    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNDERPOWERED",
            "status_reason": "adequacy_thresholds_not_met",
            "allowed_claim": "Current evidence is underpowered.",
            "anchor_method": {"id": "m1", "name": "method", "parameters": {}},
            "policy": {},
            "cohorts": {},
            "effect": {
                "delta_mean_consistency": 0.0,
                "delta_ci_low": -0.01,
                "delta_ci_high": 0.01,
                "p_value": 0.9,
            },
            "adequacy": {"pass": True, "blocked": False, "reasons": [], "metrics": {}},
            "phase4_inference": {
                "decision": "INCONCLUSIVE",
                "alpha": 0.05,
                "coupling_delta_abs_min": 0.03,
                "no_coupling_delta_abs_max": 0.015,
                "ci_crosses_zero": True,
                "abs_delta": 0.0,
            },
        }
    }
    (tmp_path / "results/phase5_mechanism/anchor_coupling_confirmatory.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md").write_text(
        "status-gated by `results/phase5_mechanism/anchor_coupling_confirmatory.json`",
        encoding="utf-8",
    )
    (tmp_path / "reports/phase7_human/PHASE_7B_RESULTS.md").write_text(
        "no conclusive claim is allowed",
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [
            "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md",
            "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md",
            "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md",
            "reports/phase7_human/PHASE_7B_RESULTS.md",
        ],
        "artifact_policy": {
            "path": "results/phase5_mechanism/anchor_coupling_confirmatory.json",
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
                "phase4_inference",
            ],
        },
        "status_policy": {
            "allowed_statuses": [
                "CONCLUSIVE_NO_COUPLING",
                "CONCLUSIVE_COUPLING_PRESENT",
                "INCONCLUSIVE_UNDERPOWERED",
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
                "BLOCKED_DATA_GEOMETRY",
            ]
        },
        "coherence_policy": {
            "required_adequacy_pass_by_status": {
                "INCONCLUSIVE_UNDERPOWERED": False
            },
            "allowed_status_reason_by_status": {
                "INCONCLUSIVE_UNDERPOWERED": ["adequacy_thresholds_not_met"]
            },
        },
        "required_markers": [],
        "banned_patterns": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-coherence" in err for err in errors)


def test_multimodal_checker_flags_h1_4_lane_mismatch(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "results/phase5_mechanism").mkdir(parents=True)
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "reports/phase7_human").mkdir(parents=True)

    artifact = {
        "results": {
            "status": "CONCLUSIVE_NO_COUPLING",
            "status_reason": "adequacy_and_inference_support_no_coupling",
            "allowed_claim": "No robust image/layout coupling signal was detected.",
            "h1_4_closure_lane": "H1_4_ALIGNED",
            "h1_4_residual_reason": "robust_multilane_alignment",
            "h1_4_reopen_conditions": ["new_lane_runs"],
            "anchor_method": {"id": "m1", "name": "method", "parameters": {}},
            "policy": {},
            "cohorts": {},
            "effect": {
                "delta_mean_consistency": 0.0,
                "delta_ci_low": -0.01,
                "delta_ci_high": 0.01,
                "p_value": 0.9,
            },
            "adequacy": {"pass": True, "blocked": False, "reasons": [], "metrics": {}},
            "phase4_inference": {
                "decision": "NO_COUPLING",
                "alpha": 0.05,
                "coupling_delta_abs_min": 0.03,
                "no_coupling_delta_abs_max": 0.015,
                "ci_crosses_zero": True,
                "abs_delta": 0.0,
            },
            "robustness": {
                "matrix_id": "M1",
                "lane_id": "publication-default",
                "publication_lane_id": "publication-default",
                "robustness_class": "MIXED",
                "agreement_ratio": 0.5,
                "lane_outcomes_considered": [],
                "reopen_conditions": ["new_lane_runs"],
            },
        }
    }
    (tmp_path / "results/phase5_mechanism/anchor_coupling_confirmatory.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7B_RESULTS.md").write_text("ok", encoding="utf-8")

    policy = {
        "tracked_files": [
            "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md",
            "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md",
            "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md",
            "reports/phase7_human/PHASE_7B_RESULTS.md",
        ],
        "artifact_policy": {
            "path": "results/phase5_mechanism/anchor_coupling_confirmatory.json",
            "required_in_modes": ["ci"],
            "required_result_keys": [
                "status",
                "status_reason",
                "allowed_claim",
                "h1_4_closure_lane",
                "h1_4_residual_reason",
                "h1_4_reopen_conditions",
                "anchor_method",
                "policy",
                "cohorts",
                "effect",
                "adequacy",
                "phase4_inference",
                "robustness",
            ],
            "required_nested_keys": {
                "robustness": [
                    "matrix_id",
                    "lane_id",
                    "publication_lane_id",
                    "robustness_class",
                    "agreement_ratio",
                    "lane_outcomes_considered",
                    "reopen_conditions",
                ]
            },
        },
        "status_policy": {
            "allowed_statuses": [
                "CONCLUSIVE_NO_COUPLING",
                "CONCLUSIVE_COUPLING_PRESENT",
                "INCONCLUSIVE_UNDERPOWERED",
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
                "BLOCKED_DATA_GEOMETRY",
            ]
        },
        "h1_4_policy": {
            "allowed_robustness_classes": ["ROBUST", "MIXED", "FRAGILE"],
            "conclusive_statuses": ["CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"],
            "inconclusive_statuses": ["INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"],
            "blocked_statuses": ["BLOCKED_DATA_GEOMETRY"],
            "aligned_lane": "H1_4_ALIGNED",
            "qualified_lane": "H1_4_QUALIFIED",
            "blocked_lane": "H1_4_BLOCKED",
            "inconclusive_lane": "H1_4_INCONCLUSIVE",
            "required_robustness_keys": [
                "matrix_id",
                "lane_id",
                "publication_lane_id",
                "robustness_class",
                "agreement_ratio",
                "lane_outcomes_considered",
                "reopen_conditions",
            ],
        },
        "required_markers": [],
        "banned_patterns": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-h1_4" in err for err in errors)


def test_multimodal_checker_flags_h1_5_lane_mismatch(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "results/phase5_mechanism").mkdir(parents=True)
    (tmp_path / "results/reports").mkdir(parents=True)
    (tmp_path / "reports/phase7_human").mkdir(parents=True)

    artifact = {
        "results": {
            "status": "CONCLUSIVE_NO_COUPLING",
            "status_reason": "adequacy_and_inference_support_no_coupling",
            "allowed_claim": "No robust image/layout coupling signal was detected.",
            "h1_4_closure_lane": "H1_4_QUALIFIED",
            "h1_4_residual_reason": "registered_lane_fragility",
            "h1_4_reopen_conditions": ["new_lane_runs"],
            "h1_5_closure_lane": "H1_5_ALIGNED",
            "h1_5_residual_reason": "entitlement_lanes_robustly_aligned",
            "h1_5_reopen_conditions": ["new_lane_runs"],
            "anchor_method": {"id": "m1", "name": "method", "parameters": {}},
            "policy": {},
            "cohorts": {},
            "effect": {
                "delta_mean_consistency": 0.0,
                "delta_ci_low": -0.01,
                "delta_ci_high": 0.01,
                "p_value": 0.9,
            },
            "adequacy": {"pass": True, "blocked": False, "reasons": [], "metrics": {}},
            "phase4_inference": {
                "decision": "NO_COUPLING",
                "alpha": 0.05,
                "coupling_delta_abs_min": 0.03,
                "no_coupling_delta_abs_max": 0.015,
                "ci_crosses_zero": True,
                "abs_delta": 0.0,
            },
            "robustness": {
                "matrix_id": "M1",
                "lane_id": "publication-default",
                "publication_lane_id": "publication-default",
                "robustness_class": "MIXED",
                "agreement_ratio": 0.5,
                "lane_outcomes_considered": [],
                "reopen_conditions": ["new_lane_runs"],
                "entitlement_lane_outcomes": [],
                "diagnostic_lane_outcomes": [],
                "stress_lane_outcomes": [],
                "entitlement_robustness_class": "ROBUST",
                "entitlement_agreement_ratio": 1.0,
                "robust_closure_reachable": True,
                "robust_closure_reachable_reason": "entitlement_matrix_covered",
                "h1_5_reopen_conditions": ["new_lane_runs"],
                "observed_diagnostic_lane_count": 1,
                "observed_stress_lane_count": 0,
                "diagnostic_non_conclusive_lane_count": 1,
            },
        }
    }
    (tmp_path / "results/phase5_mechanism/anchor_coupling_confirmatory.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md").write_text("ok", encoding="utf-8")
    (tmp_path / "reports/phase7_human/PHASE_7B_RESULTS.md").write_text("ok", encoding="utf-8")

    policy = {
        "tracked_files": [
            "results/reports/phase5_mechanism/PHASE_5H_RESULTS.md",
            "results/reports/phase5_mechanism/PHASE_5I_RESULTS.md",
            "reports/phase7_human/PHASE_7_FINDINGS_SUMMARY.md",
            "reports/phase7_human/PHASE_7B_RESULTS.md",
        ],
        "artifact_policy": {
            "path": "results/phase5_mechanism/anchor_coupling_confirmatory.json",
            "required_in_modes": ["ci"],
            "required_result_keys": [
                "status",
                "status_reason",
                "h1_5_closure_lane",
                "h1_5_residual_reason",
                "h1_5_reopen_conditions",
                "robustness",
            ],
            "required_nested_keys": {
                "robustness": [
                    "entitlement_robustness_class",
                    "robust_closure_reachable",
                    "diagnostic_non_conclusive_lane_count",
                    "observed_diagnostic_lane_count",
                    "observed_stress_lane_count",
                    "entitlement_lane_outcomes",
                    "diagnostic_lane_outcomes",
                    "stress_lane_outcomes",
                ]
            },
        },
        "status_policy": {
            "allowed_statuses": [
                "CONCLUSIVE_NO_COUPLING",
                "CONCLUSIVE_COUPLING_PRESENT",
                "INCONCLUSIVE_UNDERPOWERED",
                "INCONCLUSIVE_INFERENTIAL_AMBIGUITY",
                "BLOCKED_DATA_GEOMETRY",
            ]
        },
        "h1_5_policy": {
            "aligned_lane": "H1_5_ALIGNED",
            "bounded_lane": "H1_5_BOUNDED",
            "qualified_lane": "H1_5_QUALIFIED",
            "blocked_lane": "H1_5_BLOCKED",
            "inconclusive_lane": "H1_5_INCONCLUSIVE",
            "allowed_entitlement_robustness_classes": ["ROBUST", "MIXED", "FRAGILE"],
            "conclusive_statuses": ["CONCLUSIVE_NO_COUPLING", "CONCLUSIVE_COUPLING_PRESENT"],
            "inconclusive_statuses": ["INCONCLUSIVE_UNDERPOWERED", "INCONCLUSIVE_INFERENTIAL_AMBIGUITY"],
            "blocked_statuses": ["BLOCKED_DATA_GEOMETRY"],
            "required_robustness_keys": [
                "entitlement_lane_outcomes",
                "diagnostic_lane_outcomes",
                "stress_lane_outcomes",
                "entitlement_robustness_class",
                "entitlement_agreement_ratio",
                "robust_closure_reachable",
                "robust_closure_reachable_reason",
                "h1_5_reopen_conditions",
            ],
        },
        "required_markers": [],
        "banned_patterns": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-h1_5" in err for err in errors)
