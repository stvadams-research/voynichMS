import importlib.util
import json
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_comparative_uncertainty.py")
    spec = importlib.util.spec_from_file_location("check_comparative_uncertainty", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_sk_m2_checker_flags_missing_release_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "reports/comparative").mkdir(parents=True)
    (tmp_path / "reports/comparative/PROXIMITY_ANALYSIS.md").write_text(
        "95% CI Nearest-Neighbor Stability Comparative Uncertainty Status results/human/phase_7c_uncertainty.json",
        encoding="utf-8",
    )
    policy = {
        "tracked_files": ["reports/comparative/PROXIMITY_ANALYSIS.md"],
        "required_markers": [
            {
                "id": "m1",
                "scopes": ["reports/comparative/PROXIMITY_ANALYSIS.md"],
                "markers": ["95% CI"],
            }
        ],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status"],
                }
            ]
        },
        "allowlist": [],
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_sk_m2_checker_flags_banned_pattern(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "reports/comparative").mkdir(parents=True)
    path = tmp_path / "reports/comparative/PHASE_B_SYNTHESIS.md"
    path.write_text(
        "nearest structural neighbor to the Voynich Manuscript is the **Lullian Wheel (Dist: 5.1)**",
        encoding="utf-8",
    )
    policy = {
        "tracked_files": ["reports/comparative/PHASE_B_SYNTHESIS.md"],
        "required_markers": [],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "nearest structural neighbor to the Voynich Manuscript is the **Lullian Wheel (Dist: 5.1)**",
                "scopes": ["reports/comparative/PHASE_B_SYNTHESIS.md"],
            }
        ],
        "artifact_policy": {"tracked_artifacts": []},
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("banned-pattern" in err for err in errors)


def test_sk_m2_checker_passes_with_repo_policy_ci_and_release() -> None:
    checker = _load_checker_module()
    policy = json.loads(
        Path("configs/skeptic/sk_m2_comparative_uncertainty_policy.json").read_text(
            encoding="utf-8"
        )
    )
    ci_errors = checker.run_checks(policy, root=Path("."), mode="ci")
    release_errors = checker.run_checks(policy, root=Path("."), mode="release")
    assert ci_errors == []
    assert release_errors == []


def test_sk_m2_checker_flags_confirmed_status_below_thresholds(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "STABILITY_CONFIRMED",
            "reason_code": "ROBUST_NEAREST_NEIGHBOR",
            "allowed_claim": "ok",
            "nearest_neighbor": "A",
            "nearest_neighbor_distance": 1.0,
            "nearest_neighbor_stability": 0.51,
            "jackknife_nearest_neighbor_stability": 0.60,
            "rank_stability": 0.50,
            "rank_stability_components": {
                "top2_set_stability": 0.5,
                "top3_set_stability": 0.5,
                "full_ranking_match_rate": 0.2,
            },
            "nearest_neighbor_alternative": "B",
            "nearest_neighbor_alternative_probability": 0.41,
            "nearest_neighbor_probability_margin": 0.10,
            "distance_summary": {},
            "ranking_point_estimate": ["A", "B"],
            "top2_gap": {
                "mean": 0.1,
                "std": 0.1,
                "ci95_lower": 0.01,
                "ci95_upper": 0.2,
            },
            "top2_gap_fragile": True,
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
            "parameters": {},
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "nearest_neighbor_stability",
                        "jackknife_nearest_neighbor_stability",
                        "rank_stability",
                        "nearest_neighbor_probability_margin",
                        "top2_gap",
                    ],
                    "allowed_statuses": ["STABILITY_CONFIRMED"],
                }
            ]
        },
        "status_reason_codes": {
            "STABILITY_CONFIRMED": ["ROBUST_NEAREST_NEIGHBOR"]
        },
        "thresholds": {
            "min_nearest_neighbor_stability_for_confirmed": 0.75,
            "min_jackknife_stability_for_confirmed": 0.75,
            "min_rank_stability_for_confirmed": 0.65,
            "min_probability_margin_for_confirmed": 0.10,
            "min_top2_gap_ci_lower_for_confirmed": 0.05,
        },
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("artifact-threshold" in err for err in errors)


def test_sk_m2_checker_flags_reason_code_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNCERTAINTY",
            "reason_code": "BAD_REASON",
            "allowed_claim": "ok",
            "nearest_neighbor": "A",
            "nearest_neighbor_distance": 1.0,
            "nearest_neighbor_stability": 0.2,
            "jackknife_nearest_neighbor_stability": 0.3,
            "rank_stability": 0.2,
            "rank_stability_components": {
                "top2_set_stability": 0.1,
                "top3_set_stability": 0.2,
                "full_ranking_match_rate": 0.0,
            },
            "nearest_neighbor_alternative": "B",
            "nearest_neighbor_alternative_probability": 0.2,
            "nearest_neighbor_probability_margin": 0.01,
            "distance_summary": {},
            "ranking_point_estimate": ["A", "B"],
            "top2_gap": {
                "mean": 0.1,
                "std": 0.1,
                "ci95_lower": 0.0,
                "ci95_upper": 0.2,
            },
            "top2_gap_fragile": True,
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
            "parameters": {},
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": ["status", "reason_code"],
                    "allowed_statuses": ["INCONCLUSIVE_UNCERTAINTY"],
                }
            ]
        },
        "status_reason_codes": {
            "INCONCLUSIVE_UNCERTAINTY": ["RANK_UNSTABLE_UNDER_PERTURBATION"]
        },
        "thresholds": {},
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-reason" in err for err in errors)


def test_sk_m2_checker_flags_m2_4_lane_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "STABILITY_CONFIRMED",
            "reason_code": "ROBUST_NEAREST_NEIGHBOR",
            "m2_4_closure_lane": "M2_4_QUALIFIED",
            "m2_4_reopen_triggers": ["dummy"],
            "nearest_neighbor_stability": 0.9,
            "jackknife_nearest_neighbor_stability": 0.9,
            "rank_stability": 0.8,
            "nearest_neighbor_probability_margin": 0.2,
            "top2_gap": {"ci95_lower": 0.2},
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "m2_4_closure_lane",
                        "m2_4_reopen_triggers",
                        "metric_validity",
                        "top2_gap",
                    ],
                    "allowed_statuses": ["STABILITY_CONFIRMED"],
                }
            ]
        },
        "status_reason_codes": {"STABILITY_CONFIRMED": ["ROBUST_NEAREST_NEIGHBOR"]},
        "thresholds": {
            "min_nearest_neighbor_stability_for_confirmed": 0.75,
            "min_jackknife_stability_for_confirmed": 0.75,
            "min_rank_stability_for_confirmed": 0.65,
            "min_probability_margin_for_confirmed": 0.1,
            "min_top2_gap_ci_lower_for_confirmed": 0.05,
        },
        "m2_4_policy": {
            "required_lane_by_status": {"STABILITY_CONFIRMED": "M2_4_ALIGNED"},
            "inconclusive_lane_when_fields_missing": "M2_4_INCONCLUSIVE",
            "require_reopen_triggers_for_lanes": ["M2_4_ALIGNED"],
        },
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-lane" in err for err in errors)


def test_sk_m2_checker_flags_dominant_fragility_signal_mismatch(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNCERTAINTY",
            "reason_code": "TOP2_GAP_FRAGILE",
            "m2_4_closure_lane": "M2_4_BOUNDED",
            "m2_4_reopen_triggers": ["dummy"],
            "nearest_neighbor_stability": 0.4,
            "jackknife_nearest_neighbor_stability": 0.8,
            "rank_stability": 0.4,
            "nearest_neighbor_probability_margin": 0.02,
            "top2_gap": {"ci95_lower": 0.01},
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
            "fragility_diagnostics": {
                "dominant_fragility_signal": "MARGIN_VOLATILITY_DOMINANT"
            },
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "m2_4_closure_lane",
                        "m2_4_reopen_triggers",
                        "fragility_diagnostics",
                        "metric_validity",
                    ],
                    "allowed_statuses": ["INCONCLUSIVE_UNCERTAINTY"],
                }
            ]
        },
        "status_reason_codes": {
            "INCONCLUSIVE_UNCERTAINTY": ["TOP2_GAP_FRAGILE"]
        },
        "thresholds": {},
        "m2_4_policy": {
            "required_lane_by_status": {"INCONCLUSIVE_UNCERTAINTY": "M2_4_BOUNDED"},
            "inconclusive_lane_when_fields_missing": "M2_4_INCONCLUSIVE",
            "require_reopen_triggers_for_lanes": ["M2_4_BOUNDED"],
        },
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-fragility" in err for err in errors)


def test_sk_m2_checker_flags_missing_m2_5_residual_reason(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNCERTAINTY",
            "reason_code": "TOP2_IDENTITY_FLIP_DOMINANT",
            "m2_5_closure_lane": "M2_5_BOUNDED",
            "m2_5_residual_reason": "",
            "m2_5_reopen_triggers": ["rerun thresholds"],
            "m2_5_data_availability_linkage": {
                "missing_folio_blocking_claimed": False,
                "objective_comparative_validity_failure": False,
                "blocking_evidence": "",
                "classification": "NON_BLOCKING_EXTERNAL_CONSTRAINT",
            },
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
            "top2_gap": {"ci95_lower": 0.01},
            "nearest_neighbor_stability": 0.4,
            "jackknife_nearest_neighbor_stability": 0.8,
            "rank_stability": 0.4,
            "nearest_neighbor_probability_margin": 0.02,
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "m2_5_closure_lane",
                        "m2_5_residual_reason",
                        "m2_5_reopen_triggers",
                        "m2_5_data_availability_linkage",
                        "metric_validity",
                        "top2_gap",
                    ],
                    "allowed_statuses": ["INCONCLUSIVE_UNCERTAINTY"],
                }
            ]
        },
        "status_reason_codes": {
            "INCONCLUSIVE_UNCERTAINTY": ["TOP2_IDENTITY_FLIP_DOMINANT"]
        },
        "m2_5_policy": {
            "required_lane_by_status": {"INCONCLUSIVE_UNCERTAINTY": "M2_5_BOUNDED"},
            "inconclusive_lane_when_fields_missing": "M2_5_BLOCKED",
            "allowed_lanes": ["M2_5_BOUNDED", "M2_5_BLOCKED"],
            "blocked_lane": "M2_5_BLOCKED",
            "require_reopen_triggers_for_lanes": ["M2_5_BOUNDED"],
            "require_residual_reason_for_lanes": ["M2_5_BOUNDED"],
        },
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("m2_5_residual_reason" in err for err in errors)


def test_sk_m2_checker_flags_folio_block_without_objective_linkage(tmp_path) -> None:
    checker = _load_checker_module()
    (tmp_path / "results/human").mkdir(parents=True)
    artifact = {
        "results": {
            "status": "INCONCLUSIVE_UNCERTAINTY",
            "reason_code": "FIELD_INCOMPLETE",
            "m2_5_closure_lane": "M2_5_BLOCKED",
            "m2_5_residual_reason": "blocked_due_to_missing_folio_source_pages",
            "m2_5_reopen_triggers": ["restore fields"],
            "m2_5_data_availability_linkage": {
                "missing_folio_blocking_claimed": True,
                "objective_comparative_validity_failure": False,
                "blocking_evidence": "",
                "classification": "BLOCKING",
            },
            "metric_validity": {
                "required_fields_present": True,
                "missing_required_fields": [],
                "sufficient_iterations": True,
                "status_inputs": {},
            },
            "top2_gap": {"ci95_lower": 0.0},
            "nearest_neighbor_stability": 0.1,
            "jackknife_nearest_neighbor_stability": 0.1,
            "rank_stability": 0.1,
            "nearest_neighbor_probability_margin": 0.0,
        }
    }
    (tmp_path / "results/human/phase_7c_uncertainty.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    policy = {
        "tracked_files": [],
        "required_markers": [],
        "banned_patterns": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "results/human/phase_7c_uncertainty.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "m2_5_closure_lane",
                        "m2_5_residual_reason",
                        "m2_5_reopen_triggers",
                        "m2_5_data_availability_linkage",
                        "metric_validity",
                        "top2_gap",
                    ],
                    "allowed_statuses": ["INCONCLUSIVE_UNCERTAINTY"],
                }
            ]
        },
        "status_reason_codes": {"INCONCLUSIVE_UNCERTAINTY": ["FIELD_INCOMPLETE"]},
        "m2_5_policy": {
            "required_lane_by_status": {"INCONCLUSIVE_UNCERTAINTY": "M2_5_BLOCKED"},
            "inconclusive_lane_when_fields_missing": "M2_5_BLOCKED",
            "allowed_lanes": ["M2_5_BLOCKED"],
            "blocked_lane": "M2_5_BLOCKED",
            "require_reopen_triggers_for_lanes": ["M2_5_BLOCKED"],
            "require_residual_reason_for_lanes": ["M2_5_BLOCKED"],
        },
        "non_blocking_h3_irrecoverability_guard": {
            "enabled": True,
            "disallow_folio_block_terms_for_non_blocked_lane": True,
            "require_objective_linkage_for_blocked_lane": True,
            "blocked_residual_keywords": ["folio", "missing_page"],
            "forbidden_non_blocked_residual_keywords": ["folio", "missing_page"],
        },
        "allowlist": [],
    }
    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("objective comparative validity linkage" in err for err in errors)
