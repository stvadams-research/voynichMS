#!/usr/bin/env python3
"""
SK-H3.4 checker for control-comparability data-availability contracts.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h3_data_availability_policy.json"

TURING_ARTIFACT = "status/synthesis/TURING_TEST_RESULTS.json"
COMPARABILITY_ARTIFACT = "status/synthesis/CONTROL_COMPARABILITY_STATUS.json"
DATA_AVAILABILITY_ARTIFACT = "status/synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _load_artifact_bundle(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    provenance = {}
    if isinstance(payload, dict):
        provenance = _as_dict(payload.get("provenance"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        results = payload["results"]
    elif isinstance(payload, dict):
        results = payload
    else:
        raise ValueError(f"Artifact payload at {path} must be a JSON object")
    return {"results": _as_dict(results), "provenance": provenance}


def _is_allowlisted(allowlist: Sequence[Dict[str, Any]], marker_id: str, scope: str) -> bool:
    for entry in allowlist:
        if entry.get("marker_id") == marker_id and entry.get("scope") == scope:
            return True
    return False


def _check_doc_markers(policy: Dict[str, Any], *, root: Path) -> List[str]:
    errors: List[str] = []
    allowlist = list(policy.get("allowlist", []))

    for req in list(policy.get("required_doc_markers", [])):
        req_id = str(req.get("id", "unknown_requirement"))
        scopes = _as_list(req.get("scopes"))
        markers = _as_list(req.get("markers"))
        if not scopes or not markers:
            errors.append(f"[policy] required marker rule {req_id} missing scopes/markers")
            continue

        for scope in scopes:
            path = root / scope
            if not path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {req_id})")
                continue
            if _is_allowlisted(allowlist, req_id, scope):
                continue
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(f"[missing-marker] {scope}: missing `{marker}` ({req_id})")
    return errors


def _parse_artifacts(policy: Dict[str, Any], *, root: Path, mode: str) -> tuple[List[str], Dict[str, Dict[str, Any]]]:
    errors: List[str] = []
    parsed: Dict[str, Dict[str, Any]] = {}

    artifact_policy = dict(policy.get("artifact_policy", {}))
    specs = list(artifact_policy.get("tracked_artifacts", []))
    for spec in specs:
        rel_path = str(spec.get("path", "")).strip()
        if not rel_path:
            errors.append("[policy] artifact policy entry missing `path`")
            continue

        required_modes = set(_as_list(spec.get("required_in_modes")))
        required = mode in required_modes
        artifact_path = root / rel_path
        if not artifact_path.exists():
            if required:
                errors.append(f"[missing-artifact] required in mode={mode}: {rel_path}")
            continue

        try:
            bundle = _load_artifact_bundle(artifact_path)
        except Exception as exc:
            errors.append(f"[artifact-parse] {rel_path}: {exc}")
            continue

        parsed[rel_path] = bundle
        results = _as_dict(bundle.get("results"))

        for key in _as_list(spec.get("required_result_keys")):
            if key not in results:
                errors.append(f"[artifact-field] {rel_path}: missing result key `{key}`")

        allowed_statuses = set(_as_list(spec.get("allowed_statuses")))
        status_value = str(results.get("status"))
        if allowed_statuses and status_value not in allowed_statuses:
            errors.append(
                f"[artifact-status] {rel_path}: status `{status_value}` not in {sorted(allowed_statuses)}"
            )

        if "required_preflight_keys" in spec:
            preflight = results.get("preflight")
            if not isinstance(preflight, dict):
                errors.append(f"[artifact-field] {rel_path}: missing object key `preflight`")
            else:
                for key in _as_list(spec.get("required_preflight_keys")):
                    if key not in preflight:
                        errors.append(
                            f"[artifact-field] {rel_path}: preflight missing key `{key}`"
                        )

    return errors, parsed


def _cross_validate(
    *,
    policy: Dict[str, Any],
    mode: str,
    parsed: Mapping[str, Dict[str, Any]],
) -> List[str]:
    errors: List[str] = []

    status_policy = dict(policy.get("status_policy", {}))
    feasibility_policy = _as_dict(policy.get("feasibility_policy"))
    h3_5_policy = _as_dict(policy.get("h3_5_policy"))
    freshness_policy = _as_dict(policy.get("freshness_policy"))
    irrecoverability_policy = _as_dict(policy.get("irrecoverability_policy"))
    allowed_reason_codes = set(_as_list(policy.get("allowed_reason_codes")))
    approved_lost_pages = sorted(_as_list(policy.get("approved_lost_pages")))
    expected_pages = sorted(_as_list(policy.get("expected_pages")))
    policy_version = str(policy.get("version", ""))
    source_note_path = str(policy.get("approved_lost_pages_source_note_path", ""))

    availability_bundle = _as_dict(parsed.get(DATA_AVAILABILITY_ARTIFACT, {}))
    availability = _as_dict(availability_bundle.get("results"))
    if not availability:
        return errors

    missing_pages = sorted(_as_list(availability.get("missing_pages")))
    missing_count = _to_int(availability.get("missing_count"), -1)
    evidence_scope = str(availability.get("evidence_scope", ""))
    full_data_closure_eligible = bool(availability.get("full_data_closure_eligible", False))

    if missing_count != len(missing_pages):
        errors.append(
            "[availability] missing_count mismatch "
            f"(declared={missing_count}, computed={len(missing_pages)})"
        )

    if expected_pages and sorted(_as_list(availability.get("expected_pages"))) != expected_pages:
        errors.append("[availability] expected_pages mismatch with policy")

    artifact_approved = sorted(_as_list(availability.get("approved_lost_pages")))
    if artifact_approved != approved_lost_pages:
        errors.append("[availability] approved_lost_pages mismatch with policy")

    unexpected_missing_expected = sorted(set(missing_pages) - set(approved_lost_pages))
    unexpected_missing_declared = sorted(_as_list(availability.get("unexpected_missing_pages")))
    if unexpected_missing_declared != unexpected_missing_expected:
        errors.append(
            "[availability] unexpected_missing_pages mismatch "
            f"(declared={unexpected_missing_declared}, expected={unexpected_missing_expected})"
        )

    expected_scope = "available_subset" if missing_pages else "full_dataset"
    if evidence_scope != expected_scope:
        errors.append(
            f"[availability] evidence_scope `{evidence_scope}` does not match expected `{expected_scope}`"
        )

    if full_data_closure_eligible != (len(missing_pages) == 0):
        errors.append(
            "[availability] full_data_closure_eligible inconsistent with missing_pages"
        )

    expected_status = "DATA_AVAILABILITY_BLOCKED" if missing_pages else "DATA_AVAILABILITY_CLEAR"
    if str(availability.get("status")) != expected_status:
        errors.append(
            f"[availability] status `{availability.get('status')}` does not match `{expected_status}`"
        )

    expected_reason = "DATA_AVAILABILITY" if missing_pages else "NONE"
    if str(availability.get("reason_code")) != expected_reason:
        errors.append(
            f"[availability] reason_code `{availability.get('reason_code')}` does not match `{expected_reason}`"
        )

    allowed_feasibility = set(
        _as_list(feasibility_policy.get("allowed_full_data_feasibility"))
    )
    full_data_feasibility = str(availability.get("full_data_feasibility", ""))
    full_data_terminal_reason = str(
        availability.get("full_data_closure_terminal_reason", "")
    )
    full_data_reopen_conditions = _as_list(
        availability.get("full_data_closure_reopen_conditions")
    )
    declared_h3_lane = str(availability.get("h3_4_closure_lane", ""))
    declared_h3_5_lane = str(availability.get("h3_5_closure_lane", ""))
    declared_h3_5_residual_reason = str(
        availability.get("h3_5_residual_reason", "")
    )
    declared_h3_5_reopen_conditions = _as_list(
        availability.get("h3_5_reopen_conditions")
    )
    if allowed_feasibility and full_data_feasibility not in allowed_feasibility:
        errors.append(
            "[availability-feasibility] invalid full_data_feasibility "
            f"`{full_data_feasibility}` not in {sorted(allowed_feasibility)}"
        )
    if not full_data_terminal_reason:
        errors.append("[availability-feasibility] full_data_closure_terminal_reason is required")
    if not full_data_reopen_conditions:
        errors.append(
            "[availability-feasibility] full_data_closure_reopen_conditions must be non-empty"
        )

    feasible_terminal_reason = str(
        feasibility_policy.get("feasible_terminal_reason", "full_data_pages_available")
    )
    irrecoverable_terminal_reason = str(
        feasibility_policy.get(
            "irrecoverable_terminal_reason",
            "approved_lost_pages_not_in_source_corpus",
        )
    )
    review_required_terminal_reason = str(
        feasibility_policy.get(
            "review_required_terminal_reason",
            "unexpected_missing_pages_require_recovery",
        )
    )
    aligned_lane = str(feasibility_policy.get("aligned_lane", "H3_4_ALIGNED"))
    qualified_lane = str(feasibility_policy.get("qualified_lane", "H3_4_QUALIFIED"))
    blocked_lane = str(feasibility_policy.get("blocked_lane", "H3_4_BLOCKED"))

    if len(missing_pages) == 0:
        expected_feasibility = "feasible"
        expected_terminal_reason = feasible_terminal_reason
        expected_lane = aligned_lane
    elif len(unexpected_missing_expected) > 0:
        expected_feasibility = "feasible"
        expected_terminal_reason = review_required_terminal_reason
        expected_lane = blocked_lane
    else:
        expected_feasibility = "irrecoverable"
        expected_terminal_reason = irrecoverable_terminal_reason
        expected_lane = qualified_lane

    if full_data_feasibility and full_data_feasibility != expected_feasibility:
        errors.append(
            "[availability-feasibility] full_data_feasibility mismatch "
            f"(declared={full_data_feasibility!r}, expected={expected_feasibility!r})"
        )
    if full_data_terminal_reason and full_data_terminal_reason != expected_terminal_reason:
        errors.append(
            "[availability-feasibility] full_data_closure_terminal_reason mismatch "
            f"(declared={full_data_terminal_reason!r}, expected={expected_terminal_reason!r})"
        )
    if declared_h3_lane and declared_h3_lane != expected_lane:
        errors.append(
            "[availability-feasibility] h3_4_closure_lane mismatch "
            f"(declared={declared_h3_lane!r}, expected={expected_lane!r})"
        )

    if h3_5_policy:
        for field in _as_list(h3_5_policy.get("required_fields")):
            if field not in availability:
                errors.append(f"[availability-h3_5] missing required field `{field}`")

        h3_5_aligned_lane = str(h3_5_policy.get("aligned_lane", "H3_5_ALIGNED"))
        h3_5_terminal_lane = str(
            h3_5_policy.get("terminal_qualified_lane", "H3_5_TERMINAL_QUALIFIED")
        )
        h3_5_blocked_lane = str(h3_5_policy.get("blocked_lane", "H3_5_BLOCKED"))
        h3_5_inconclusive_lane = str(
            h3_5_policy.get("inconclusive_lane", "H3_5_INCONCLUSIVE")
        )

        if (
            full_data_feasibility == "feasible"
            and len(missing_pages) == 0
            and evidence_scope == "full_dataset"
            and full_data_closure_eligible is True
            and str(availability.get("status")) == "DATA_AVAILABILITY_CLEAR"
        ):
            expected_h3_5_lane = h3_5_aligned_lane
        elif (
            full_data_feasibility == "irrecoverable"
            and len(missing_pages) > 0
            and str(availability.get("reason_code")) == "DATA_AVAILABILITY"
            and evidence_scope == "available_subset"
            and full_data_closure_eligible is False
        ):
            expected_h3_5_lane = h3_5_terminal_lane
        elif str(availability.get("status")) == "INCONCLUSIVE_DATA_LIMITED":
            expected_h3_5_lane = h3_5_inconclusive_lane
        else:
            expected_h3_5_lane = h3_5_blocked_lane

        if declared_h3_5_lane and declared_h3_5_lane != expected_h3_5_lane:
            errors.append(
                "[availability-h3_5] h3_5_closure_lane mismatch "
                f"(declared={declared_h3_5_lane!r}, expected={expected_h3_5_lane!r})"
            )

        if expected_h3_5_lane == h3_5_aligned_lane:
            expected_h3_5_reason = str(
                h3_5_policy.get("aligned_residual_reason", "full_data_closure_aligned")
            )
            expected_h3_5_reopen = _as_list(
                h3_5_policy.get("aligned_reopen_conditions")
            ) or ["none_required_full_data_available"]
        elif expected_h3_5_lane == h3_5_terminal_lane:
            expected_h3_5_reason = str(
                h3_5_policy.get(
                    "terminal_qualified_residual_reason",
                    "approved_lost_pages_not_in_source_corpus",
                )
            )
            expected_h3_5_reopen = _as_list(
                h3_5_policy.get("terminal_qualified_reopen_conditions")
            ) or full_data_reopen_conditions
        elif expected_h3_5_lane == h3_5_inconclusive_lane:
            expected_h3_5_reason = str(
                h3_5_policy.get(
                    "inconclusive_residual_reason",
                    "evidence_incomplete_for_deterministic_lane",
                )
            )
            expected_h3_5_reopen = _as_list(
                h3_5_policy.get("inconclusive_reopen_conditions")
            ) or [
                "complete_evidence_bundle_for_lane_classification",
                "rerun_control_matching_with_full_contract_coverage",
            ]
        else:
            expected_h3_5_reason = str(
                h3_5_policy.get(
                    "blocked_residual_reason",
                    "artifact_or_policy_contract_incoherence_detected",
                )
            )
            expected_h3_5_reopen = _as_list(
                h3_5_policy.get("blocked_reopen_conditions")
            ) or [
                "repair_artifact_parity_and_freshness_contracts",
                "rerun_control_matching_and_data_availability_checks",
            ]

        if (
            declared_h3_5_residual_reason
            and declared_h3_5_residual_reason != expected_h3_5_reason
        ):
            errors.append(
                "[availability-h3_5] h3_5_residual_reason mismatch "
                f"(declared={declared_h3_5_residual_reason!r}, expected={expected_h3_5_reason!r})"
            )
        if (
            declared_h3_5_reopen_conditions
            and declared_h3_5_reopen_conditions != expected_h3_5_reopen
        ):
            errors.append(
                "[availability-h3_5] h3_5_reopen_conditions mismatch "
                f"(declared={declared_h3_5_reopen_conditions!r}, expected={expected_h3_5_reopen!r})"
            )

    declared_policy_version = str(availability.get("approved_lost_pages_policy_version", ""))
    if policy_version and declared_policy_version != policy_version:
        errors.append(
            "[availability] approved_lost_pages_policy_version mismatch "
            f"(declared={declared_policy_version!r}, policy={policy_version!r})"
        )

    declared_source_note_path = str(availability.get("approved_lost_pages_source_note_path", ""))
    if source_note_path and declared_source_note_path != source_note_path:
        errors.append(
            "[availability] approved_lost_pages_source_note_path mismatch "
            f"(declared={declared_source_note_path!r}, policy={source_note_path!r})"
        )

    irrecoverability = _as_dict(availability.get("irrecoverability"))
    if irrecoverability_policy:
        required_irrecoverability_keys = _as_list(
            irrecoverability_policy.get("required_fields")
        )
        for key in required_irrecoverability_keys:
            if key not in irrecoverability:
                errors.append(f"[availability] irrecoverability missing key `{key}`")

        has_unexpected_missing = len(unexpected_missing_expected) > 0
        has_approved_lost_only = len(missing_pages) > 0 and not has_unexpected_missing
        if len(missing_pages) == 0:
            expected_irrecoverability_classification = str(
                irrecoverability_policy.get("clear_classification", "FULL_DATA_AVAILABLE")
            )
        elif has_unexpected_missing:
            expected_irrecoverability_classification = str(
                irrecoverability_policy.get(
                    "unexpected_missing_classification", "UNEXPECTED_MISSING_REVIEW_REQUIRED"
                )
            )
        else:
            expected_irrecoverability_classification = str(
                irrecoverability_policy.get(
                    "approved_lost_classification", "APPROVED_LOST_IRRECOVERABLE"
                )
            )

        expected_recoverable = len(missing_pages) == 0 or has_unexpected_missing
        expected_approved_lost = has_approved_lost_only
        expected_unexpected_missing = has_unexpected_missing

        if irrecoverability.get("recoverable") != expected_recoverable:
            errors.append(
                "[availability] irrecoverability.recoverable mismatch "
                f"(declared={irrecoverability.get('recoverable')!r}, expected={expected_recoverable!r})"
            )
        if irrecoverability.get("approved_lost") != expected_approved_lost:
            errors.append(
                "[availability] irrecoverability.approved_lost mismatch "
                f"(declared={irrecoverability.get('approved_lost')!r}, expected={expected_approved_lost!r})"
            )
        if irrecoverability.get("unexpected_missing") != expected_unexpected_missing:
            errors.append(
                "[availability] irrecoverability.unexpected_missing mismatch "
                f"(declared={irrecoverability.get('unexpected_missing')!r}, expected={expected_unexpected_missing!r})"
            )
        if (
            str(irrecoverability.get("classification", ""))
            != expected_irrecoverability_classification
        ):
            errors.append(
                "[availability] irrecoverability.classification mismatch "
                f"(declared={irrecoverability.get('classification')!r}, "
                f"expected={expected_irrecoverability_classification!r})"
            )

    allowed_scopes = set(_as_list(status_policy.get("allowed_evidence_scopes")))
    if allowed_scopes and evidence_scope not in allowed_scopes:
        errors.append(
            f"[availability] evidence_scope `{evidence_scope}` not in allowed set {sorted(allowed_scopes)}"
        )

    policy_dataset = str(policy.get("dataset_id", ""))
    if policy_dataset and str(availability.get("dataset_id", "")) != policy_dataset:
        errors.append(
            "[availability] dataset_id mismatch "
            f"(artifact={availability.get('dataset_id')!r}, policy={policy_dataset!r})"
        )

    turing_bundle = _as_dict(parsed.get(TURING_ARTIFACT, {}))
    turing = _as_dict(turing_bundle.get("results"))
    if turing:
        preflight = dict(turing.get("preflight", {}))
        turing_missing_pages = sorted(_as_list(preflight.get("missing_pages")))
        turing_missing_count = _to_int(preflight.get("missing_count"), len(turing_missing_pages))

        if turing_missing_pages != missing_pages:
            errors.append(
                "[cross-artifact] TURING preflight missing_pages mismatch "
                f"(turing={turing_missing_pages}, availability={missing_pages})"
            )
        if turing_missing_count != len(missing_pages):
            errors.append(
                "[cross-artifact] TURING preflight missing_count mismatch "
                f"(turing={turing_missing_count}, availability={len(missing_pages)})"
            )

        strict_status = str(turing.get("status", ""))
        strict_reason = str(turing.get("reason_code", ""))
        strict_computed = bool(turing.get("strict_computed", False))

        if missing_pages and mode == "release":
            if strict_status != "BLOCKED":
                errors.append(
                    f"[strict-preflight] expected TURING status BLOCKED in release mode; got {strict_status!r}"
                )
            if strict_reason not in allowed_reason_codes:
                errors.append(
                    "[strict-preflight] TURING reason_code must be DATA_AVAILABILITY in release mode"
                )
            if strict_computed is not True:
                errors.append(
                    "[strict-preflight] TURING strict_computed must be true in release mode"
                )
        elif not missing_pages and mode == "release":
            if strict_status != "PREFLIGHT_OK":
                errors.append(
                    f"[strict-preflight] expected TURING status PREFLIGHT_OK in release mode; got {strict_status!r}"
                )
            if strict_computed is not True:
                errors.append(
                    "[strict-preflight] TURING strict_computed must be true in release mode"
                )

    comp_bundle = _as_dict(parsed.get(COMPARABILITY_ARTIFACT, {}))
    comp = _as_dict(comp_bundle.get("results"))
    if comp:
        comp_missing_pages = sorted(_as_list(comp.get("missing_pages")))
        comp_missing_count = _to_int(comp.get("missing_count"), -1)
        comp_scope = str(comp.get("evidence_scope", ""))
        comp_closure = bool(comp.get("full_data_closure_eligible", False))

        if comp_missing_pages != missing_pages:
            errors.append(
                "[cross-artifact] comparability missing_pages mismatch "
                f"(comparability={comp_missing_pages}, availability={missing_pages})"
            )
        if comp_missing_count != len(missing_pages):
            errors.append(
                "[cross-artifact] comparability missing_count mismatch "
                f"(comparability={comp_missing_count}, availability={len(missing_pages)})"
            )
        if comp_scope != evidence_scope:
            errors.append(
                "[cross-artifact] comparability evidence_scope mismatch "
                f"(comparability={comp_scope!r}, availability={evidence_scope!r})"
            )
        if comp_closure != full_data_closure_eligible:
            errors.append(
                "[cross-artifact] comparability full_data_closure_eligible mismatch"
            )
        if str(comp.get("approved_lost_pages_policy_version", "")) != declared_policy_version:
            errors.append(
                "[cross-artifact] comparability approved_lost_pages_policy_version mismatch "
                f"(comparability={comp.get('approved_lost_pages_policy_version')!r}, "
                f"availability={declared_policy_version!r})"
            )
        if str(comp.get("approved_lost_pages_source_note_path", "")) != declared_source_note_path:
            errors.append(
                "[cross-artifact] comparability approved_lost_pages_source_note_path mismatch "
                f"(comparability={comp.get('approved_lost_pages_source_note_path')!r}, "
                f"availability={declared_source_note_path!r})"
            )

        comp_irrecoverability = _as_dict(comp.get("irrecoverability"))
        if comp_irrecoverability != irrecoverability:
            errors.append(
                "[cross-artifact] comparability irrecoverability mismatch "
                f"(comparability={comp_irrecoverability}, availability={irrecoverability})"
            )
        if str(comp.get("full_data_feasibility", "")) != full_data_feasibility:
            errors.append(
                "[cross-artifact] comparability full_data_feasibility mismatch "
                f"(comparability={comp.get('full_data_feasibility')!r}, "
                f"availability={full_data_feasibility!r})"
            )
        if (
            str(comp.get("full_data_closure_terminal_reason", ""))
            != full_data_terminal_reason
        ):
            errors.append(
                "[cross-artifact] comparability full_data_closure_terminal_reason mismatch "
                f"(comparability={comp.get('full_data_closure_terminal_reason')!r}, "
                f"availability={full_data_terminal_reason!r})"
            )
        if _as_list(comp.get("full_data_closure_reopen_conditions")) != full_data_reopen_conditions:
            errors.append(
                "[cross-artifact] comparability full_data_closure_reopen_conditions mismatch"
            )
        if str(comp.get("h3_4_closure_lane", "")) != declared_h3_lane:
            errors.append(
                "[cross-artifact] comparability h3_4_closure_lane mismatch "
                f"(comparability={comp.get('h3_4_closure_lane')!r}, availability={declared_h3_lane!r})"
            )
        if str(comp.get("h3_5_closure_lane", "")) != declared_h3_5_lane:
            errors.append(
                "[cross-artifact] comparability h3_5_closure_lane mismatch "
                f"(comparability={comp.get('h3_5_closure_lane')!r}, availability={declared_h3_5_lane!r})"
            )
        if str(comp.get("h3_5_residual_reason", "")) != declared_h3_5_residual_reason:
            errors.append(
                "[cross-artifact] comparability h3_5_residual_reason mismatch "
                f"(comparability={comp.get('h3_5_residual_reason')!r}, "
                f"availability={declared_h3_5_residual_reason!r})"
            )
        if _as_list(comp.get("h3_5_reopen_conditions")) != declared_h3_5_reopen_conditions:
            errors.append(
                "[cross-artifact] comparability h3_5_reopen_conditions mismatch"
            )

        if missing_pages:
            blocked_status = str(status_policy.get("blocked_status", "NON_COMPARABLE_BLOCKED"))
            blocked_reason = str(status_policy.get("blocked_reason_code", "DATA_AVAILABILITY"))
            blocked_scope = str(status_policy.get("blocked_evidence_scope", "available_subset"))

            if str(comp.get("status")) != blocked_status:
                errors.append(
                    "[comparability-status] expected blocked status under missing pages "
                    f"(status={comp.get('status')!r}, expected={blocked_status!r})"
                )
            if str(comp.get("reason_code")) != blocked_reason:
                errors.append(
                    "[comparability-status] expected DATA_AVAILABILITY reason under missing pages "
                    f"(reason_code={comp.get('reason_code')!r})"
                )
            if comp_scope != blocked_scope:
                errors.append(
                    "[comparability-status] blocked evidence_scope mismatch "
                    f"(scope={comp_scope!r}, expected={blocked_scope!r})"
                )

            claim_markers = [marker.lower() for marker in _as_list(status_policy.get("allowed_claim_markers"))]
            allowed_claim = str(comp.get("allowed_claim", "")).lower()
            for marker in claim_markers:
                if marker not in allowed_claim:
                    errors.append(
                        f"[comparability-claim] blocked allowed_claim missing marker `{marker}`"
                    )

            if mode == "release" and comp.get("data_availability_policy_pass") is not True:
                errors.append(
                    "[comparability-status] data_availability_policy_pass must be true in release mode"
                )

    if comp:
        require_run_id = bool(freshness_policy.get("require_matching_run_id", False))
        require_timestamps = bool(freshness_policy.get("require_timestamps", False))
        max_skew = _to_int(freshness_policy.get("max_timestamp_skew_seconds"), 600)
        availability_prov = _as_dict(availability_bundle.get("provenance"))
        comparability_prov = _as_dict(comp_bundle.get("provenance"))
        if require_run_id:
            availability_run_id = str(availability_prov.get("run_id", ""))
            comparability_run_id = str(comparability_prov.get("run_id", ""))
            if (not availability_run_id) or (not comparability_run_id):
                errors.append(
                    "[freshness] missing provenance.run_id in comparability/data-availability artifacts"
                )
            elif availability_run_id != comparability_run_id:
                errors.append(
                    "[freshness] comparability/data-availability provenance.run_id mismatch "
                    f"(comparability={comparability_run_id!r}, availability={availability_run_id!r})"
                )
        if require_timestamps:
            availability_ts = _parse_iso_timestamp(availability_prov.get("timestamp"))
            comparability_ts = _parse_iso_timestamp(comparability_prov.get("timestamp"))
            if availability_ts is None or comparability_ts is None:
                errors.append(
                    "[freshness] missing/invalid provenance.timestamp in comparability/data-availability artifacts"
                )
            else:
                skew_seconds = abs(
                    (availability_ts - comparability_ts).total_seconds()
                )
                if skew_seconds > max_skew:
                    errors.append(
                        "[freshness] comparability/data-availability provenance timestamp skew "
                        f"{skew_seconds:.1f}s exceeds max {max_skew}s"
                    )

    if mode == "release" and availability.get("policy_pass") is not True:
        errors.append("[availability] policy_pass must be true in release mode")

    return errors


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors = _check_doc_markers(policy, root=root)
    artifact_errors, parsed = _parse_artifacts(policy, root=root, mode=mode)
    errors.extend(artifact_errors)
    errors.extend(_cross_validate(policy=policy, mode=mode, parsed=parsed))
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check SK-H3.4 data-availability contract for control comparability."
    )
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-H3.4 data-availability policy JSON.",
    )
    parser.add_argument(
        "--root",
        default=str(PROJECT_ROOT),
        help="Repository root used to resolve scoped files.",
    )
    parser.add_argument(
        "--mode",
        choices=["ci", "release"],
        default="ci",
        help="Enforcement mode.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    policy_path = Path(args.policy_path)
    root = Path(args.root)

    try:
        policy = _read_policy(policy_path)
    except Exception as exc:
        print(f"[FAIL] could not read policy: {exc}")
        return 1

    errors = run_checks(policy, root=root, mode=args.mode)
    if errors:
        print(f"[FAIL] control data-availability policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] control data-availability policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
