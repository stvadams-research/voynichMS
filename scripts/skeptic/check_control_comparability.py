#!/usr/bin/env python3
"""
Control-comparability policy checker for SK-H3 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h3_control_comparability_policy.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _is_allowlisted(allowlist: Sequence[Dict[str, Any]], pattern_id: str, scope: str) -> bool:
    for entry in allowlist:
        if entry.get("pattern_id") == pattern_id and entry.get("scope") == scope:
            return True
    return False


def _load_results_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return payload["results"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors: List[str] = []
    allowlist = list(policy.get("allowlist", []))

    tracked_files = _as_list(policy.get("tracked_files"))
    for scope in tracked_files:
        if not (root / scope).exists():
            errors.append(f"[missing-file] tracked file missing: {scope}")

    banned_patterns = list(policy.get("banned_patterns", []))
    for banned in banned_patterns:
        pattern_id = str(banned.get("id", "unknown_pattern"))
        pattern_text = str(banned.get("pattern", ""))
        scopes = _as_list(banned.get("scopes"))
        if not pattern_text or not scopes:
            errors.append(f"[policy] banned pattern {pattern_id} missing pattern/scopes")
            continue

        flags = re.IGNORECASE if bool(banned.get("case_insensitive", False)) else 0
        matcher = re.compile(pattern_text, flags=flags) if bool(banned.get("regex", False)) else None

        for scope in scopes:
            file_path = root / scope
            if not file_path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {pattern_id})")
                continue
            if _is_allowlisted(allowlist, pattern_id, scope):
                continue
            text = file_path.read_text(encoding="utf-8")
            hit = bool(matcher.search(text)) if matcher is not None else (pattern_text in text)
            if hit:
                errors.append(f"[banned-pattern] {scope}: matched `{pattern_text}` ({pattern_id})")

    required_markers = list(policy.get("required_doc_markers", []))
    for req in required_markers:
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
            text = path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(f"[missing-marker] {scope}: missing `{marker}` ({req_id})")

    partition_policy = dict(policy.get("metric_partition_policy", {}))
    matching_metrics = set(_as_list(partition_policy.get("matching_metrics")))
    holdout_metrics = set(_as_list(partition_policy.get("holdout_evaluation_metrics")))
    max_overlap = int(partition_policy.get("max_metric_overlap", 0))
    overlap = sorted(matching_metrics & holdout_metrics)
    if len(overlap) > max_overlap:
        errors.append(
            "[metric-overlap] policy overlap exceeds max: "
            f"{len(overlap)} > {max_overlap} ({', '.join(overlap)})"
        )

    normalization_policy = dict(policy.get("normalization_policy", {}))
    allowed_modes = set(_as_list(normalization_policy.get("allowed_modes")))

    artifact_policy = dict(policy.get("artifact_policy", {}))
    artifact_specs = list(artifact_policy.get("tracked_artifacts", []))
    for spec in artifact_specs:
        rel_path = str(spec.get("path", ""))
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

        for key in _as_list(spec.get("required_result_keys")):
            if key not in results:
                errors.append(f"[artifact-field] {rel_path}: missing top-level results key `{key}`")

        comp_source: Dict[str, Any]
        if isinstance(results.get("comparability"), dict):
            comp_source = dict(results["comparability"])
        else:
            comp_source = dict(results)

        allowed_statuses = set(_as_list(spec.get("allowed_statuses")))
        if allowed_statuses and "status" in comp_source:
            status_value = str(comp_source.get("status"))
            if status_value not in allowed_statuses:
                errors.append(
                    f"[artifact-status] {rel_path}: status `{status_value}` "
                    f"not in allowed_statuses={sorted(allowed_statuses)}"
                )
        else:
            status_value = str(comp_source.get("status"))

        status_policy = dict(spec.get("status_policy", {}))
        blocked_status = str(status_policy.get("blocked_status", "")).strip()
        if blocked_status and status_value == blocked_status:
            allowed_block_reasons = set(
                _as_list(status_policy.get("allowed_block_reason_codes"))
            )
            reason_code = str(comp_source.get("reason_code", ""))
            if allowed_block_reasons and reason_code not in allowed_block_reasons:
                errors.append(
                    "[artifact-block-reason] "
                    f"{rel_path}: blocked reason_code `{reason_code}` "
                    f"not in allowed set {sorted(allowed_block_reasons)}"
                )

            for key in _as_list(status_policy.get("required_block_fields")):
                if key not in comp_source:
                    errors.append(
                        f"[artifact-block-field] {rel_path}: missing blocked-state key `{key}`"
                    )

            data_availability_reason_codes = set(
                _as_list(status_policy.get("data_availability_reason_codes"))
            )
            expected_scope = str(
                status_policy.get("data_availability_expected_scope", "")
            ).strip()
            if (
                expected_scope
                and reason_code in data_availability_reason_codes
                and str(comp_source.get("evidence_scope")) != expected_scope
            ):
                errors.append(
                    "[artifact-block-scope] "
                    f"{rel_path}: evidence_scope `{comp_source.get('evidence_scope')}` "
                    f"must be `{expected_scope}` when reason_code={reason_code}"
                )

        for key in _as_list(spec.get("required_comparability_keys")):
            if key not in comp_source:
                errors.append(
                    f"[artifact-field] {rel_path}: missing comparability key `{key}`"
                )

        artifact_matching = set(_as_list(comp_source.get("matching_metrics")))
        artifact_holdout = set(_as_list(comp_source.get("holdout_evaluation_metrics")))
        artifact_overlap = sorted(artifact_matching & artifact_holdout)
        if "metric_overlap" in comp_source:
            declared_overlap = sorted(_as_list(comp_source.get("metric_overlap")))
            if declared_overlap != artifact_overlap:
                errors.append(
                    "[artifact-overlap] "
                    f"{rel_path}: metric_overlap mismatch (declared={declared_overlap}, computed={artifact_overlap})"
                )
        leakage_detected = bool(comp_source.get("leakage_detected", False))
        if leakage_detected != (len(artifact_overlap) > 0):
            errors.append(
                "[artifact-leakage] "
                f"{rel_path}: leakage_detected={leakage_detected} inconsistent with overlap={artifact_overlap}"
            )

        if allowed_modes and "normalization_mode" in comp_source:
            mode_value = str(comp_source.get("normalization_mode"))
            if mode_value not in allowed_modes:
                errors.append(
                    f"[artifact-normalization] {rel_path}: normalization_mode `{mode_value}` not allowed"
                )

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-H3 control comparability policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to control-comparability policy JSON.",
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
        help="Enforcement mode. release mode requires tracked artifacts.",
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
        print(f"[FAIL] control-comparability policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] control-comparability policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
