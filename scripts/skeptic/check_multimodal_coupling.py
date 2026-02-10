#!/usr/bin/env python3
"""
Multimodal coupling status checker for SK-H1.4/SK-H1.5 claim-boundary guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h1_multimodal_status_policy.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _rule_applies_to_mode(rule: Mapping[str, Any], mode: str) -> bool:
    modes = set(_as_list(rule.get("modes")))
    return not modes or mode in modes


def _rule_applies_to_status(rule: Mapping[str, Any], status: str) -> bool:
    statuses = set(_as_list(rule.get("for_statuses")))
    return not statuses or status in statuses


def _rule_applies_to_h1_4_lane(rule: Mapping[str, Any], h1_4_lane: str) -> bool:
    lanes = set(_as_list(rule.get("for_h1_4_lanes")))
    return not lanes or h1_4_lane in lanes


def _rule_applies_to_h1_5_lane(rule: Mapping[str, Any], h1_5_lane: str) -> bool:
    lanes = set(_as_list(rule.get("for_h1_5_lanes")))
    return not lanes or h1_5_lane in lanes


def _load_results_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload.get("results"), dict):
        return payload["results"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


def _check_artifact_policy(
    *,
    policy: Dict[str, Any],
    root: Path,
    mode: str,
) -> tuple[List[str], Dict[str, Any]]:
    errors: List[str] = []
    artifact_spec = dict(policy.get("artifact_policy", {}))
    if not artifact_spec:
        errors.append("[policy] missing artifact_policy")
        return errors, {}

    rel_path = str(artifact_spec.get("path", "")).strip()
    if not rel_path:
        errors.append("[policy] artifact_policy.path is required")
        return errors, {}

    required_in_modes = set(_as_list(artifact_spec.get("required_in_modes")))
    required = mode in required_in_modes
    artifact_path = root / rel_path
    if not artifact_path.exists():
        if required:
            errors.append(f"[missing-artifact] required in mode={mode}: {rel_path}")
        return errors, {}

    try:
        results = _load_results_payload(artifact_path)
    except Exception as exc:
        errors.append(f"[artifact-parse] {rel_path}: {exc}")
        return errors, {}

    for key in _as_list(artifact_spec.get("required_result_keys")):
        if key not in results:
            errors.append(f"[artifact-field] {rel_path}: missing result key `{key}`")

    nested = artifact_spec.get("required_nested_keys")
    if isinstance(nested, dict):
        for parent, child_keys in nested.items():
            parent_key = str(parent)
            parent_payload = results.get(parent_key)
            if not isinstance(parent_payload, dict):
                errors.append(
                    f"[artifact-field] {rel_path}: expected object for `{parent_key}`"
                )
                continue
            for child_key in _as_list(child_keys):
                if child_key not in parent_payload:
                    errors.append(
                        f"[artifact-field] {rel_path}: missing nested key "
                        f"`{parent_key}.{child_key}`"
                    )

    return errors, results


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors: List[str] = []

    for scope in _as_list(policy.get("tracked_files")):
        if not (root / scope).exists():
            errors.append(f"[missing-file] tracked file missing: {scope}")

    artifact_errors, results = _check_artifact_policy(policy=policy, root=root, mode=mode)
    errors.extend(artifact_errors)

    status_policy = dict(policy.get("status_policy", {}))
    allowed_statuses = set(_as_list(status_policy.get("allowed_statuses")))
    status = str(results.get("status", ""))
    status_reason = str(results.get("status_reason", ""))
    h1_4_lane = str(results.get("h1_4_closure_lane", ""))
    h1_5_lane = str(results.get("h1_5_closure_lane", ""))
    if status and allowed_statuses and status not in allowed_statuses:
        errors.append(
            f"[artifact-status] invalid status `{status}`; "
            f"allowed={sorted(allowed_statuses)}"
        )

    coherence_policy = dict(policy.get("coherence_policy", {}))
    if status and coherence_policy:
        adequacy = results.get("adequacy")
        inference = results.get("inference")
        adequacy_pass = None
        adequacy_blocked = None
        if isinstance(adequacy, dict):
            adequacy_pass = _coerce_bool(adequacy.get("pass"))
            adequacy_blocked = _coerce_bool(adequacy.get("blocked"))

        allowed_reason_by_status = dict(
            coherence_policy.get("allowed_status_reason_by_status", {})
        )
        allowed_reasons = set(
            _as_list(allowed_reason_by_status.get(status))
        )
        if allowed_reasons and status_reason not in allowed_reasons:
            errors.append(
                f"[artifact-coherence] status `{status}` has invalid status_reason "
                f"`{status_reason}`; allowed={sorted(allowed_reasons)}"
            )

        required_pass_by_status = dict(
            coherence_policy.get("required_adequacy_pass_by_status", {})
        )
        if status in required_pass_by_status:
            expected = _coerce_bool(required_pass_by_status.get(status))
            if expected is not None:
                if adequacy_pass is None:
                    errors.append(
                        f"[artifact-coherence] status `{status}` requires adequacy.pass="
                        f"{expected}, but adequacy.pass is missing/non-boolean"
                    )
                elif adequacy_pass is not expected:
                    errors.append(
                        f"[artifact-coherence] status `{status}` requires adequacy.pass="
                        f"{expected}, observed={adequacy_pass}"
                    )

        required_blocked_by_status = dict(
            coherence_policy.get("required_adequacy_blocked_by_status", {})
        )
        if status in required_blocked_by_status:
            expected = _coerce_bool(required_blocked_by_status.get(status))
            if expected is not None:
                if adequacy_blocked is None:
                    errors.append(
                        f"[artifact-coherence] status `{status}` requires adequacy.blocked="
                        f"{expected}, but adequacy.blocked is missing/non-boolean"
                    )
                elif adequacy_blocked is not expected:
                    errors.append(
                        f"[artifact-coherence] status `{status}` requires adequacy.blocked="
                        f"{expected}, observed={adequacy_blocked}"
                    )

        required_inference_by_status = dict(
            coherence_policy.get("required_inference_decision_by_status", {})
        )
        if status in required_inference_by_status:
            expected = str(required_inference_by_status.get(status, "")).strip()
            observed = ""
            if isinstance(inference, dict):
                observed = str(inference.get("decision", ""))
            if not observed:
                errors.append(
                    f"[artifact-coherence] status `{status}` requires inference.decision="
                    f"`{expected}`, but inference.decision is missing"
                )
            elif expected and observed != expected:
                errors.append(
                    f"[artifact-coherence] status `{status}` requires inference.decision="
                    f"`{expected}`, observed=`{observed}`"
                )

    h1_4_policy = dict(policy.get("h1_4_policy", {}))
    if h1_4_policy:
        allowed_robustness_classes = set(
            _as_list(h1_4_policy.get("allowed_robustness_classes"))
        )
        robustness = results.get("robustness")
        if not isinstance(robustness, dict):
            errors.append("[artifact-h1_4] missing or invalid `robustness` object")
            robustness = {}

        for key in _as_list(h1_4_policy.get("required_robustness_keys")):
            if key not in robustness:
                errors.append(f"[artifact-h1_4] missing robustness key `{key}`")

        robustness_class = str(robustness.get("robustness_class", ""))
        if allowed_robustness_classes and robustness_class not in allowed_robustness_classes:
            errors.append(
                f"[artifact-h1_4] invalid robustness_class `{robustness_class}`; "
                f"allowed={sorted(allowed_robustness_classes)}"
            )

        if not str(results.get("h1_4_residual_reason", "")).strip():
            errors.append("[artifact-h1_4] h1_4_residual_reason is required")

        reopen_conditions = results.get("h1_4_reopen_conditions")
        if not isinstance(reopen_conditions, list) or len(reopen_conditions) == 0:
            errors.append("[artifact-h1_4] h1_4_reopen_conditions must be a non-empty list")

        conclusive_statuses = set(_as_list(h1_4_policy.get("conclusive_statuses")))
        inconclusive_statuses = set(_as_list(h1_4_policy.get("inconclusive_statuses")))
        blocked_statuses = set(_as_list(h1_4_policy.get("blocked_statuses")))
        aligned_lane = str(h1_4_policy.get("aligned_lane", "H1_4_ALIGNED"))
        qualified_lane = str(h1_4_policy.get("qualified_lane", "H1_4_QUALIFIED"))
        inconclusive_lane = str(h1_4_policy.get("inconclusive_lane", "H1_4_INCONCLUSIVE"))
        blocked_lane = str(h1_4_policy.get("blocked_lane", "H1_4_BLOCKED"))

        if status in conclusive_statuses:
            if robustness_class == "ROBUST":
                expected_lane = aligned_lane
            else:
                expected_lane = qualified_lane
        elif status in inconclusive_statuses:
            expected_lane = inconclusive_lane
        elif status in blocked_statuses:
            expected_lane = blocked_lane
        else:
            expected_lane = inconclusive_lane

        if h1_4_lane != expected_lane:
            errors.append(
                "[artifact-h1_4] h1_4_closure_lane mismatch "
                f"(status={status!r}, robustness_class={robustness_class!r}, "
                f"declared={h1_4_lane!r}, expected={expected_lane!r})"
            )

    h1_5_policy = dict(policy.get("h1_5_policy", {}))
    if h1_5_policy:
        robustness = results.get("robustness")
        if not isinstance(robustness, dict):
            errors.append("[artifact-h1_5] missing or invalid `robustness` object")
            robustness = {}

        for key in _as_list(h1_5_policy.get("required_robustness_keys")):
            if key not in robustness:
                errors.append(f"[artifact-h1_5] missing robustness key `{key}`")

        entitlement_class = str(robustness.get("entitlement_robustness_class", ""))
        allowed_entitlement_classes = set(
            _as_list(h1_5_policy.get("allowed_entitlement_robustness_classes"))
        )
        if (
            allowed_entitlement_classes
            and entitlement_class not in allowed_entitlement_classes
        ):
            errors.append(
                "[artifact-h1_5] invalid entitlement_robustness_class "
                f"`{entitlement_class}`; allowed={sorted(allowed_entitlement_classes)}"
            )

        robust_closure_reachable = _coerce_bool(robustness.get("robust_closure_reachable"))
        if robust_closure_reachable is None:
            errors.append(
                "[artifact-h1_5] robustness.robust_closure_reachable must be boolean"
            )
            robust_closure_reachable = False

        if not str(results.get("h1_5_residual_reason", "")).strip():
            errors.append("[artifact-h1_5] h1_5_residual_reason is required")

        h1_5_reopen_conditions = results.get("h1_5_reopen_conditions")
        if not isinstance(h1_5_reopen_conditions, list) or len(h1_5_reopen_conditions) == 0:
            errors.append("[artifact-h1_5] h1_5_reopen_conditions must be a non-empty list")

        conclusive_statuses = set(_as_list(h1_5_policy.get("conclusive_statuses")))
        inconclusive_statuses = set(_as_list(h1_5_policy.get("inconclusive_statuses")))
        blocked_statuses = set(_as_list(h1_5_policy.get("blocked_statuses")))
        aligned_lane = str(h1_5_policy.get("aligned_lane", "H1_5_ALIGNED"))
        bounded_lane = str(h1_5_policy.get("bounded_lane", "H1_5_BOUNDED"))
        qualified_lane = str(h1_5_policy.get("qualified_lane", "H1_5_QUALIFIED"))
        blocked_lane = str(h1_5_policy.get("blocked_lane", "H1_5_BLOCKED"))
        inconclusive_lane = str(h1_5_policy.get("inconclusive_lane", "H1_5_INCONCLUSIVE"))

        diagnostic_non_conclusive_count = int(
            robustness.get("diagnostic_non_conclusive_lane_count", 0) or 0
        )
        diagnostic_total = int(robustness.get("observed_diagnostic_lane_count", 0) or 0) + int(
            robustness.get("observed_stress_lane_count", 0) or 0
        )

        if robust_closure_reachable is False:
            expected_lane = blocked_lane
        elif status in conclusive_statuses:
            if entitlement_class == "ROBUST":
                if diagnostic_total > 0 and diagnostic_non_conclusive_count > 0:
                    expected_lane = bounded_lane
                else:
                    expected_lane = aligned_lane
            else:
                expected_lane = qualified_lane
        elif status in inconclusive_statuses:
            expected_lane = inconclusive_lane
        elif status in blocked_statuses:
            expected_lane = blocked_lane
        else:
            expected_lane = inconclusive_lane

        if h1_5_lane != expected_lane:
            errors.append(
                "[artifact-h1_5] h1_5_closure_lane mismatch "
                f"(status={status!r}, entitlement_robustness_class={entitlement_class!r}, "
                f"reachable={robust_closure_reachable!r}, "
                f"declared={h1_5_lane!r}, expected={expected_lane!r})"
            )

    guard_policy = dict(policy.get("non_blocking_h3_irrecoverability_guard", {}))
    if bool(guard_policy.get("enabled")):
        residual_text = str(results.get("h1_5_residual_reason", "")).lower()
        blocked_lane = str(
            h1_5_policy.get("blocked_lane", "H1_5_BLOCKED") if h1_5_policy else "H1_5_BLOCKED"
        )
        blocked_status_required = bool(
            guard_policy.get("blocked_status_required_for_h1_5_blocked", False)
        )
        if h1_5_lane == blocked_lane and blocked_status_required and status != "BLOCKED_DATA_GEOMETRY":
            if "contract_unreachable" not in residual_text:
                errors.append(
                    "[artifact-h1_5] H1_5_BLOCKED requires status=BLOCKED_DATA_GEOMETRY "
                    "unless residual reason is contract_unreachable"
                )

        if bool(guard_policy.get("disallow_folio_block_terms_for_non_blocked_status", False)):
            forbidden = [s.lower() for s in _as_list(guard_policy.get("forbidden_non_blocked_residual_keywords"))]
            if h1_5_lane != blocked_lane:
                for keyword in forbidden:
                    if keyword and keyword in residual_text:
                        errors.append(
                            "[artifact-h1_5] non-blocked H1.5 lane contains blocked-residual "
                            f"keyword `{keyword}`"
                        )

        blocked_keywords = [
            s.lower() for s in _as_list(guard_policy.get("blocked_residual_keywords"))
        ]
        if h1_5_lane == blocked_lane and blocked_keywords:
            if not any(keyword and keyword in residual_text for keyword in blocked_keywords):
                errors.append(
                    "[artifact-h1_5] H1_5_BLOCKED residual reason must include one of "
                    f"{blocked_keywords}"
                )

    for rule in list(policy.get("required_markers", [])):
        if not _rule_applies_to_mode(rule, mode):
            continue
        if not _rule_applies_to_status(rule, status):
            continue
        if not _rule_applies_to_h1_4_lane(rule, h1_4_lane):
            continue
        if not _rule_applies_to_h1_5_lane(rule, h1_5_lane):
            continue

        rule_id = str(rule.get("id", "unknown_requirement"))
        scopes = _as_list(rule.get("scopes"))
        markers = _as_list(rule.get("markers"))
        if not scopes or not markers:
            errors.append(f"[policy] required marker rule {rule_id} missing scopes/markers")
            continue

        for scope in scopes:
            file_path = root / scope
            if not file_path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {rule_id})")
                continue
            text = file_path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(
                        f"[missing-marker] {scope}: missing `{marker}` ({rule_id})"
                    )

    for rule in list(policy.get("banned_patterns", [])):
        if not _rule_applies_to_mode(rule, mode):
            continue
        if not _rule_applies_to_status(rule, status):
            continue
        if not _rule_applies_to_h1_4_lane(rule, h1_4_lane):
            continue
        if not _rule_applies_to_h1_5_lane(rule, h1_5_lane):
            continue

        rule_id = str(rule.get("id", "unknown_pattern"))
        pattern = str(rule.get("pattern", ""))
        scopes = _as_list(rule.get("scopes"))
        if not pattern or not scopes:
            errors.append(f"[policy] banned pattern {rule_id} missing pattern/scopes")
            continue

        flags = re.IGNORECASE if bool(rule.get("case_insensitive", False)) else 0
        matcher = re.compile(pattern, flags=flags) if bool(rule.get("regex", False)) else None
        for scope in scopes:
            file_path = root / scope
            if not file_path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {rule_id})")
                continue
            text = file_path.read_text(encoding="utf-8")
            hit = bool(matcher.search(text)) if matcher else (pattern in text)
            if hit:
                errors.append(
                    f"[banned-pattern] {scope}: matched `{pattern}` ({rule_id})"
                )

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-H1 multimodal coupling policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-H1 multimodal status policy JSON.",
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
        print(f"[FAIL] multimodal coupling policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] multimodal coupling policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
