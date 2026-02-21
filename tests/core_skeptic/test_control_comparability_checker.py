import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _load_checker_module():
    module_path = Path("scripts/core_skeptic/check_control_comparability.py")
    spec = importlib.util.spec_from_file_location("check_control_comparability", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_control_comparability_checker_flags_missing_required_artifact(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "governance").mkdir(parents=True)
    (tmp_path / "governance/GENERATOR_MATCHING.md").write_text(
        "matching_metrics holdout_evaluation_metrics target leakage", encoding="utf-8"
    )

    policy = {
        "tracked_files": ["governance/GENERATOR_MATCHING.md"],
        "required_doc_markers": [
            {
                "id": "m1",
                "scopes": ["governance/GENERATOR_MATCHING.md"],
                "markers": ["matching_metrics"],
            }
        ],
        "banned_patterns": [],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["b"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status"],
                }
            ]
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert errors
    assert "missing-artifact" in errors[0]


def test_control_comparability_checker_flags_overlap_leakage_mismatch(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "core_status/phase3_synthesis").mkdir(parents=True)
    (tmp_path / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "COMPARABLE_QUALIFIED",
                    "matching_metrics": ["a", "b"],
                    "holdout_evaluation_metrics": ["b"],
                    "metric_overlap": ["b"],
                    "leakage_detected": False,
                    "normalization_mode": "parser",
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_doc_markers": [],
        "banned_patterns": [],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["c"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["ci"],
                    "required_result_keys": [
                        "status",
                        "matching_metrics",
                        "holdout_evaluation_metrics",
                        "metric_overlap",
                        "leakage_detected",
                        "normalization_mode",
                    ],
                }
            ]
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert any("artifact-leakage" in err for err in errors)


def test_control_comparability_checker_honors_allowlist(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "governance").mkdir(parents=True)
    doc_path = tmp_path / "governance/GENERATOR_MATCHING.md"
    doc_path.write_text("forbidden phrase", encoding="utf-8")

    policy = {
        "tracked_files": ["governance/GENERATOR_MATCHING.md"],
        "required_doc_markers": [],
        "banned_patterns": [
            {
                "id": "p1",
                "pattern": "forbidden phrase",
                "scopes": ["governance/GENERATOR_MATCHING.md"],
            }
        ],
        "allowlist": [{"pattern_id": "p1", "scope": "governance/GENERATOR_MATCHING.md"}],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["b"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "artifact_policy": {"tracked_artifacts": []},
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="ci")
    assert errors == []


def test_control_comparability_checker_flags_disallowed_block_reason(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "core_status/phase3_synthesis").mkdir(parents=True)
    (tmp_path / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "NON_COMPARABLE_BLOCKED",
                    "reason_code": "UNAPPROVED_REASON",
                    "matching_metrics": ["a"],
                    "holdout_evaluation_metrics": ["b"],
                    "metric_overlap": [],
                    "leakage_detected": False,
                    "normalization_mode": "parser",
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_doc_markers": [],
        "banned_patterns": [],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["b"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "evidence_scope",
                        "full_data_closure_eligible",
                    ],
                    "allowed_statuses": ["NON_COMPARABLE_BLOCKED"],
                    "status_policy": {
                        "blocked_status": "NON_COMPARABLE_BLOCKED",
                        "allowed_block_reason_codes": ["DATA_AVAILABILITY", "TARGET_LEAKAGE"],
                        "required_block_fields": ["evidence_scope", "full_data_closure_eligible"],
                        "data_availability_reason_codes": ["DATA_AVAILABILITY"],
                        "data_availability_expected_scope": "available_subset",
                    },
                }
            ]
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("artifact-block-reason" in err for err in errors)


def test_control_comparability_checker_flags_data_availability_scope_mismatch(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "core_status/phase3_synthesis").mkdir(parents=True)
    (tmp_path / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "NON_COMPARABLE_BLOCKED",
                    "reason_code": "DATA_AVAILABILITY",
                    "matching_metrics": ["a"],
                    "holdout_evaluation_metrics": ["b"],
                    "metric_overlap": [],
                    "leakage_detected": False,
                    "normalization_mode": "parser",
                    "evidence_scope": "full_dataset",
                    "full_data_closure_eligible": False,
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_doc_markers": [],
        "banned_patterns": [],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["b"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "evidence_scope",
                        "full_data_closure_eligible",
                    ],
                    "allowed_statuses": ["NON_COMPARABLE_BLOCKED"],
                    "status_policy": {
                        "blocked_status": "NON_COMPARABLE_BLOCKED",
                        "allowed_block_reason_codes": ["DATA_AVAILABILITY"],
                        "required_block_fields": ["evidence_scope", "full_data_closure_eligible"],
                        "data_availability_reason_codes": ["DATA_AVAILABILITY"],
                        "data_availability_expected_scope": "available_subset",
                    },
                }
            ]
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("artifact-block-scope" in err for err in errors)


def test_control_comparability_checker_passes_with_repo_policy_ci_mode() -> None:
    checker = _load_checker_module()
    policy = json.loads(
        Path("configs/core_skeptic/sk_h3_control_comparability_policy.json").read_text(
            encoding="utf-8"
        )
    )
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []


def test_control_comparability_checker_flags_underpowered_transition_mismatch(tmp_path) -> None:
    checker = _load_checker_module()

    (tmp_path / "core_status/phase3_synthesis").mkdir(parents=True)
    (tmp_path / "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "INCONCLUSIVE_DATA_LIMITED",
                    "reason_code": "PREFLIGHT_ONLY",
                    "comparability_grade": "C",
                    "matching_metrics": ["a"],
                    "holdout_evaluation_metrics": ["b"],
                    "metric_overlap": [],
                    "leakage_detected": False,
                    "normalization_mode": "parser",
                    "allowed_claim": "bounded and non-conclusive",
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                    "available_subset_status": "INCONCLUSIVE_DATA_LIMITED",
                    "available_subset_reason_code": "AVAILABLE_SUBSET_QUALIFIED",
                    "available_subset_confidence": "UNDERPOWERED",
                    "available_subset_diagnostics": {
                        "control_card_count": 1,
                        "expected_control_class_count": 3,
                        "control_class_coverage_ratio": 0.33,
                        "mean_selected_composite_score": 0.8,
                        "max_selected_composite_score": 0.9,
                        "stability_margin_min": 0.01,
                        "stability_margin_mean": 0.01,
                        "stability_envelope": {
                            "min_selected_composite_score": 0.8,
                            "max_selected_composite_score": 0.9,
                            "range_selected_composite_score": 0.1,
                        },
                        "thresholds": {
                            "min_control_card_count": 3,
                            "min_control_class_coverage_ratio": 1.0,
                            "max_mean_selected_composite_score": 0.5,
                            "min_stability_margin": 0.05,
                        },
                        "passes_thresholds": False,
                    },
                    "available_subset_reproducibility": {
                        "preflight_only": True,
                        "dataset_id": "voynich_real",
                        "seed": 42,
                        "control_card_paths": [
                            "core_status/phase3_synthesis/control_matching_cards/self_citation.json"
                        ],
                        "control_card_count": 1,
                    },
                    "missing_pages": ["f91r"],
                    "missing_count": 1,
                    "approved_lost_pages_policy_version": "2026-02-10-h3.3",
                    "approved_lost_pages_source_note_path": "reports/core_skeptic/SK_H3_3_RESIDUAL_REGISTER.md",
                    "irrecoverability": {
                        "recoverable": False,
                        "approved_lost": True,
                        "unexpected_missing": False,
                        "classification": "APPROVED_LOST_IRRECOVERABLE",
                    },
                    "data_availability_policy_pass": True,
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "tracked_files": [],
        "required_doc_markers": [],
        "banned_patterns": [],
        "metric_partition_policy": {
            "matching_metrics": ["a"],
            "holdout_evaluation_metrics": ["b"],
            "max_metric_overlap": 0,
        },
        "normalization_policy": {"allowed_modes": ["parser"]},
        "available_subset_policy": {
            "allowed_statuses": [
                "COMPARABLE_CONFIRMED",
                "COMPARABLE_QUALIFIED",
                "INCONCLUSIVE_DATA_LIMITED",
                "NON_COMPARABLE_BLOCKED",
            ],
            "allowed_reason_codes": [
                "AVAILABLE_SUBSET_CONFIRMED",
                "AVAILABLE_SUBSET_QUALIFIED",
                "AVAILABLE_SUBSET_UNDERPOWERED",
                "TARGET_LEAKAGE",
            ],
            "underpowered_reason_code": "AVAILABLE_SUBSET_UNDERPOWERED",
            "required_diagnostic_keys": [
                "control_card_count",
                "expected_control_class_count",
                "control_class_coverage_ratio",
                "mean_selected_composite_score",
                "max_selected_composite_score",
                "stability_margin_min",
                "stability_margin_mean",
                "stability_envelope",
                "thresholds",
                "passes_thresholds",
            ],
            "required_reproducibility_keys": [
                "preflight_only",
                "dataset_id",
                "seed",
                "control_card_paths",
                "control_card_count",
            ],
            "thresholds": {
                "min_control_card_count": 3,
                "min_control_class_coverage_ratio": 1.0,
                "max_mean_selected_composite_score": 0.5,
                "min_stability_margin": 0.05,
            },
        },
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "comparability_grade",
                        "matching_metrics",
                        "holdout_evaluation_metrics",
                        "metric_overlap",
                        "leakage_detected",
                        "normalization_mode",
                        "allowed_claim",
                        "evidence_scope",
                        "full_data_closure_eligible",
                        "available_subset_status",
                        "available_subset_reason_code",
                        "available_subset_confidence",
                        "available_subset_diagnostics",
                        "available_subset_reproducibility",
                        "missing_pages",
                        "missing_count",
                        "approved_lost_pages_policy_version",
                        "approved_lost_pages_source_note_path",
                        "irrecoverability",
                        "data_availability_policy_pass",
                    ],
                    "allowed_statuses": [
                        "NON_COMPARABLE_BLOCKED",
                        "INCONCLUSIVE_DATA_LIMITED",
                        "COMPARABLE_QUALIFIED",
                        "COMPARABLE_CONFIRMED",
                    ],
                }
            ]
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("expected reason_code=AVAILABLE_SUBSET_UNDERPOWERED" in err for err in errors)
