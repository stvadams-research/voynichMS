#!/usr/bin/env python3
"""
Comparative-uncertainty policy checker for SK-M2 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_m2_comparative_uncertainty_policy.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors: List[str] = []
    allowlist = list(policy.get("allowlist", []))
    status_reason_codes = dict(policy.get("status_reason_codes", {}))
    thresholds = dict(policy.get("thresholds", {}))

    for scope in _as_list(policy.get("tracked_files")):
        if not (root / scope).exists():
            errors.append(f"[missing-file] tracked file missing: {scope}")

    for banned in list(policy.get("banned_patterns", [])):
        modes = set(_as_list(banned.get("modes")))
        if modes and mode not in modes:
            continue
        pattern_id = str(banned.get("id", "unknown_pattern"))
        pattern_text = str(banned.get("pattern", ""))
        scopes = _as_list(banned.get("scopes"))
        if not pattern_text or not scopes:
            errors.append(f"[policy] banned pattern {pattern_id} missing pattern/scopes")
            continue

        flags = re.IGNORECASE if bool(banned.get("case_insensitive", False)) else 0
        matcher = re.compile(pattern_text, flags=flags) if bool(banned.get("regex", False)) else None

        for scope in scopes:
            path = root / scope
            if not path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {pattern_id})")
                continue
            if _is_allowlisted(allowlist, pattern_id, scope):
                continue
            text = path.read_text(encoding="utf-8")
            hit = bool(matcher.search(text)) if matcher is not None else (pattern_text in text)
            if hit:
                errors.append(f"[banned-pattern] {scope}: matched `{pattern_text}` ({pattern_id})")

    for req in list(policy.get("required_markers", [])):
        modes = set(_as_list(req.get("modes")))
        if modes and mode not in modes:
            continue
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

    artifact_policy = dict(policy.get("artifact_policy", {}))
    for spec in list(artifact_policy.get("tracked_artifacts", [])):
        rel_path = str(spec.get("path", ""))
        required_in_modes = set(_as_list(spec.get("required_in_modes")))
        required = mode in required_in_modes
        path = root / rel_path
        if not path.exists():
            if required:
                errors.append(f"[missing-artifact] required in mode={mode}: {rel_path}")
            continue

        try:
            results = _load_results_payload(path)
        except Exception as exc:
            errors.append(f"[artifact-parse] {rel_path}: {exc}")
            continue

        for key in _as_list(spec.get("required_result_keys")):
            if key not in results:
                errors.append(f"[artifact-field] {rel_path}: missing result key `{key}`")

        nested = spec.get("required_nested_result_keys", {})
        if isinstance(nested, dict):
            for parent_key, child_keys in nested.items():
                parent = results.get(str(parent_key))
                if not isinstance(parent, dict):
                    errors.append(
                        f"[artifact-field] {rel_path}: expected object for `{parent_key}`"
                    )
                    continue
                for child_key in _as_list(child_keys):
                    if child_key not in parent:
                        errors.append(
                            f"[artifact-field] {rel_path}: missing nested key "
                            f"`{parent_key}.{child_key}`"
                        )

        allowed_statuses = set(_as_list(spec.get("allowed_statuses")))
        status_value = str(results.get("status"))
        if allowed_statuses and status_value not in allowed_statuses:
            errors.append(
                f"[artifact-status] {rel_path}: status `{status_value}` not in {sorted(allowed_statuses)}"
            )

        reason_code = str(results.get("reason_code", ""))
        allowed_reason_codes = set(_as_list(status_reason_codes.get(status_value)))
        if allowed_reason_codes and reason_code not in allowed_reason_codes:
            errors.append(
                f"[artifact-reason] {rel_path}: reason_code `{reason_code}` not allowed "
                f"for status `{status_value}`"
            )

        metric_validity = results.get("metric_validity")
        if isinstance(metric_validity, dict):
            if metric_validity.get("required_fields_present") is not True:
                errors.append(
                    f"[artifact-validity] {rel_path}: metric_validity.required_fields_present must be true"
                )
            if mode == "release" and metric_validity.get("sufficient_iterations") is not True:
                errors.append(
                    f"[artifact-validity] {rel_path}: release mode requires sufficient_iterations=true"
                )

        nearest_stability = _as_float(results.get("nearest_neighbor_stability"))
        jackknife_stability = _as_float(results.get("jackknife_nearest_neighbor_stability"))
        rank_stability = _as_float(results.get("rank_stability"))
        probability_margin = _as_float(results.get("nearest_neighbor_probability_margin"))
        top2_gap_ci_low = _as_float((results.get("top2_gap") or {}).get("ci95_lower"))

        if status_value == "STABILITY_CONFIRMED":
            checks = [
                (
                    nearest_stability,
                    _as_float(thresholds.get("min_nearest_neighbor_stability_for_confirmed")),
                    "nearest_neighbor_stability",
                ),
                (
                    jackknife_stability,
                    _as_float(thresholds.get("min_jackknife_stability_for_confirmed")),
                    "jackknife_nearest_neighbor_stability",
                ),
                (
                    rank_stability,
                    _as_float(thresholds.get("min_rank_stability_for_confirmed")),
                    "rank_stability",
                ),
                (
                    probability_margin,
                    _as_float(thresholds.get("min_probability_margin_for_confirmed")),
                    "nearest_neighbor_probability_margin",
                ),
                (
                    top2_gap_ci_low,
                    _as_float(thresholds.get("min_top2_gap_ci_lower_for_confirmed")),
                    "top2_gap.ci95_lower",
                ),
            ]
            for observed, floor, metric_name in checks:
                if floor is None:
                    continue
                if observed is None or observed < floor:
                    errors.append(
                        f"[artifact-threshold] {rel_path}: status STABILITY_CONFIRMED requires "
                        f"{metric_name}>={floor:.4f} (observed={observed})"
                    )

        if status_value == "DISTANCE_QUALIFIED":
            checks = [
                (
                    nearest_stability,
                    _as_float(thresholds.get("min_nearest_neighbor_stability_for_qualified")),
                    "nearest_neighbor_stability",
                ),
                (
                    jackknife_stability,
                    _as_float(thresholds.get("min_jackknife_stability_for_qualified")),
                    "jackknife_nearest_neighbor_stability",
                ),
                (
                    rank_stability,
                    _as_float(thresholds.get("min_rank_stability_for_qualified")),
                    "rank_stability",
                ),
            ]
            for observed, floor, metric_name in checks:
                if floor is None:
                    continue
                if observed is None or observed < floor:
                    errors.append(
                        f"[artifact-threshold] {rel_path}: status DISTANCE_QUALIFIED requires "
                        f"{metric_name}>={floor:.4f} (observed={observed})"
                    )

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-M2 comparative-uncertainty policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-M2 policy JSON.",
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
        print(f"[FAIL] comparative-uncertainty policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] comparative-uncertainty policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
