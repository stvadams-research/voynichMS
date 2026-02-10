#!/usr/bin/env python3
"""
SK-H3.2 checker for control-comparability data-availability contracts.
"""

from __future__ import annotations

import argparse
import json
import sys
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


def _load_results_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return payload["results"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


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
            results = _load_results_payload(artifact_path)
        except Exception as exc:
            errors.append(f"[artifact-parse] {rel_path}: {exc}")
            continue

        parsed[rel_path] = results

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
    allowed_reason_codes = set(_as_list(policy.get("allowed_reason_codes")))
    approved_lost_pages = sorted(_as_list(policy.get("approved_lost_pages")))
    expected_pages = sorted(_as_list(policy.get("expected_pages")))

    availability = dict(parsed.get(DATA_AVAILABILITY_ARTIFACT, {}))
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

    turing = dict(parsed.get(TURING_ARTIFACT, {}))
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

    comp = dict(parsed.get(COMPARABILITY_ARTIFACT, {}))
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
        description="Check SK-H3.2 data-availability contract for control comparability."
    )
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-H3.2 data-availability policy JSON.",
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
