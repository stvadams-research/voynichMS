import importlib.util
import json
from pathlib import Path


def _load_checker_module():
    module_path = Path("scripts/skeptic/check_control_data_availability.py")
    spec = importlib.util.spec_from_file_location("check_control_data_availability", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_data_availability_checker_flags_missing_required_artifact(tmp_path) -> None:
    checker = _load_checker_module()
    policy = {
        "required_doc_markers": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status"],
                }
            ]
        },
        "status_policy": {},
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("missing-artifact" in err for err in errors)


def test_data_availability_checker_flags_disallowed_block_reason(tmp_path) -> None:
    checker = _load_checker_module()

    synth = tmp_path / "status/synthesis"
    synth.mkdir(parents=True)

    (synth / "TURING_TEST_RESULTS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "BLOCKED",
                    "strict_computed": True,
                    "reason_code": "DATA_AVAILABILITY",
                    "preflight": {
                        "dataset_id": "voynich_real",
                        "expected_pages": ["f91r", "f91v"],
                        "available_pages_normalized": [],
                        "missing_pages": ["f91r", "f91v"],
                        "missing_count": 2,
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    (synth / "CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "NON_COMPARABLE_BLOCKED",
                    "reason_code": "TARGET_LEAKAGE",
                    "allowed_claim": "data availability available-subset non-conclusive",
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                    "available_subset_status": "COMPARABLE_QUALIFIED",
                    "available_subset_reason_code": "AVAILABLE_SUBSET_PREFLIGHT",
                    "missing_pages": ["f91r", "f91v"],
                    "missing_count": 2,
                    "data_availability_policy_pass": True,
                }
            }
        ),
        encoding="utf-8",
    )

    (synth / "CONTROL_COMPARABILITY_DATA_AVAILABILITY.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "DATA_AVAILABILITY_BLOCKED",
                    "reason_code": "DATA_AVAILABILITY",
                    "dataset_id": "voynich_real",
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                    "expected_pages": ["f91r", "f91v"],
                    "available_pages_normalized": [],
                    "missing_pages": ["f91r", "f91v"],
                    "missing_count": 2,
                    "approved_lost_pages": ["f91r", "f91v"],
                    "unexpected_missing_pages": [],
                    "strict_preflight_status": "BLOCKED",
                    "strict_preflight_reason_code": "DATA_AVAILABILITY",
                    "strict_computed": True,
                    "policy_checks": {
                        "strict_preflight_policy_pass": True,
                        "approved_lost_pages_match": True,
                        "missing_count_consistent": True,
                        "unexpected_missing_pages_empty": True,
                    },
                    "policy_pass": True,
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "dataset_id": "voynich_real",
        "expected_pages": ["f91r", "f91v"],
        "approved_lost_pages": ["f91r", "f91v"],
        "allowed_reason_codes": ["DATA_AVAILABILITY"],
        "required_doc_markers": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "status/synthesis/TURING_TEST_RESULTS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status", "strict_computed", "preflight"],
                    "required_preflight_keys": [
                        "dataset_id",
                        "expected_pages",
                        "available_pages_normalized",
                        "missing_pages",
                        "missing_count",
                    ],
                },
                {
                    "path": "status/synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "allowed_claim",
                        "evidence_scope",
                        "full_data_closure_eligible",
                        "available_subset_status",
                        "available_subset_reason_code",
                        "missing_pages",
                        "missing_count",
                        "data_availability_policy_pass",
                    ],
                },
                {
                    "path": "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "dataset_id",
                        "evidence_scope",
                        "full_data_closure_eligible",
                        "expected_pages",
                        "available_pages_normalized",
                        "missing_pages",
                        "missing_count",
                        "approved_lost_pages",
                        "unexpected_missing_pages",
                        "strict_preflight_status",
                        "strict_preflight_reason_code",
                        "strict_computed",
                        "policy_checks",
                        "policy_pass",
                    ],
                },
            ]
        },
        "status_policy": {
            "blocked_status": "NON_COMPARABLE_BLOCKED",
            "blocked_reason_code": "DATA_AVAILABILITY",
            "blocked_evidence_scope": "available_subset",
            "allowed_evidence_scopes": ["available_subset", "full_dataset"],
            "allowed_claim_markers": ["data availability", "available-subset", "non-conclusive"],
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert any("expected DATA_AVAILABILITY reason" in err for err in errors)


def test_data_availability_checker_passes_with_aligned_blocked_artifacts(tmp_path) -> None:
    checker = _load_checker_module()

    synth = tmp_path / "status/synthesis"
    synth.mkdir(parents=True)

    (synth / "TURING_TEST_RESULTS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "BLOCKED",
                    "strict_computed": True,
                    "reason_code": "DATA_AVAILABILITY",
                    "preflight": {
                        "dataset_id": "voynich_real",
                        "expected_pages": ["f91r", "f91v"],
                        "available_pages_normalized": [],
                        "missing_pages": ["f91r", "f91v"],
                        "missing_count": 2,
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    (synth / "CONTROL_COMPARABILITY_STATUS.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "NON_COMPARABLE_BLOCKED",
                    "reason_code": "DATA_AVAILABILITY",
                    "allowed_claim": (
                        "Full-dataset comparability is blocked by data availability; "
                        "available-subset evidence is bounded and non-conclusive."
                    ),
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                    "available_subset_status": "COMPARABLE_QUALIFIED",
                    "available_subset_reason_code": "AVAILABLE_SUBSET_PREFLIGHT",
                    "missing_pages": ["f91r", "f91v"],
                    "missing_count": 2,
                    "data_availability_policy_pass": True,
                }
            }
        ),
        encoding="utf-8",
    )

    (synth / "CONTROL_COMPARABILITY_DATA_AVAILABILITY.json").write_text(
        json.dumps(
            {
                "results": {
                    "status": "DATA_AVAILABILITY_BLOCKED",
                    "reason_code": "DATA_AVAILABILITY",
                    "dataset_id": "voynich_real",
                    "evidence_scope": "available_subset",
                    "full_data_closure_eligible": False,
                    "expected_pages": ["f91r", "f91v"],
                    "available_pages_normalized": [],
                    "missing_pages": ["f91r", "f91v"],
                    "missing_count": 2,
                    "approved_lost_pages": ["f91r", "f91v"],
                    "unexpected_missing_pages": [],
                    "strict_preflight_status": "BLOCKED",
                    "strict_preflight_reason_code": "DATA_AVAILABILITY",
                    "strict_computed": True,
                    "policy_checks": {
                        "strict_preflight_policy_pass": True,
                        "approved_lost_pages_match": True,
                        "missing_count_consistent": True,
                        "unexpected_missing_pages_empty": True,
                    },
                    "policy_pass": True,
                }
            }
        ),
        encoding="utf-8",
    )

    policy = {
        "dataset_id": "voynich_real",
        "expected_pages": ["f91r", "f91v"],
        "approved_lost_pages": ["f91r", "f91v"],
        "allowed_reason_codes": ["DATA_AVAILABILITY"],
        "required_doc_markers": [],
        "artifact_policy": {
            "tracked_artifacts": [
                {
                    "path": "status/synthesis/TURING_TEST_RESULTS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": ["status", "strict_computed", "preflight"],
                    "required_preflight_keys": [
                        "dataset_id",
                        "expected_pages",
                        "available_pages_normalized",
                        "missing_pages",
                        "missing_count",
                    ],
                },
                {
                    "path": "status/synthesis/CONTROL_COMPARABILITY_STATUS.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "allowed_claim",
                        "evidence_scope",
                        "full_data_closure_eligible",
                        "available_subset_status",
                        "available_subset_reason_code",
                        "missing_pages",
                        "missing_count",
                        "data_availability_policy_pass",
                    ],
                },
                {
                    "path": "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json",
                    "required_in_modes": ["release"],
                    "required_result_keys": [
                        "status",
                        "reason_code",
                        "dataset_id",
                        "evidence_scope",
                        "full_data_closure_eligible",
                        "expected_pages",
                        "available_pages_normalized",
                        "missing_pages",
                        "missing_count",
                        "approved_lost_pages",
                        "unexpected_missing_pages",
                        "strict_preflight_status",
                        "strict_preflight_reason_code",
                        "strict_computed",
                        "policy_checks",
                        "policy_pass",
                    ],
                },
            ]
        },
        "status_policy": {
            "blocked_status": "NON_COMPARABLE_BLOCKED",
            "blocked_reason_code": "DATA_AVAILABILITY",
            "blocked_evidence_scope": "available_subset",
            "allowed_evidence_scopes": ["available_subset", "full_dataset"],
            "allowed_claim_markers": ["data availability", "available-subset", "non-conclusive"],
        },
    }

    errors = checker.run_checks(policy, root=tmp_path, mode="release")
    assert errors == []


def test_data_availability_checker_passes_with_repo_policy_ci_mode() -> None:
    checker = _load_checker_module()
    policy = json.loads(
        Path("configs/skeptic/sk_h3_data_availability_policy.json").read_text(
            encoding="utf-8"
        )
    )
    errors = checker.run_checks(policy, root=Path("."), mode="ci")
    assert errors == []
