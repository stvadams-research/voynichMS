#!/usr/bin/env python3
"""
Comparative-uncertainty policy checker for SK-M2 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m2_comparative_uncertainty_policy.json"


def _read_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _is_allowlisted(allowlist: Sequence[dict[str, Any]], pattern_id: str, scope: str) -> bool:
    for entry in allowlist:
        if entry.get("pattern_id") == pattern_id and entry.get("scope") == scope:
            return True
    return False


def _load_results_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return payload["results"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


def run_checks(policy: dict[str, Any], *, root: Path, mode: str) -> list[str]:
    errors: list[str] = []
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
        required_fields_present = False
        if isinstance(metric_validity, dict):
            required_fields_present = metric_validity.get("required_fields_present") is True
            if not required_fields_present:
                errors.append(
                    f"[artifact-validity] {rel_path}: metric_validity.required_fields_present must be true"
                )
            if mode == "release" and metric_validity.get("sufficient_iterations") is not True:
                errors.append(
                    f"[artifact-validity] {rel_path}: release mode requires sufficient_iterations=true"
                )

        m2_4_policy = dict(policy.get("m2_4_policy", {}))
        if m2_4_policy:
            lane = str(results.get("m2_4_closure_lane", "")).strip()
            required_lane_by_status = dict(m2_4_policy.get("required_lane_by_status", {}))
            expected_lane = str(required_lane_by_status.get(status_value, "")).strip()
            inconclusive_missing_lane = str(
                m2_4_policy.get("inconclusive_lane_when_fields_missing", "")
            ).strip()

            if status_value == "INCONCLUSIVE_UNCERTAINTY":
                if required_fields_present and expected_lane and lane != expected_lane:
                    errors.append(
                        f"[artifact-lane] {rel_path}: status `{status_value}` requires lane "
                        f"`{expected_lane}` (observed `{lane}`)"
                    )
                if (
                    not required_fields_present
                    and inconclusive_missing_lane
                    and lane != inconclusive_missing_lane
                ):
                    errors.append(
                        f"[artifact-lane] {rel_path}: incomplete INCONCLUSIVE_UNCERTAINTY "
                        f"requires lane `{inconclusive_missing_lane}` (observed `{lane}`)"
                    )
            elif expected_lane and lane != expected_lane:
                errors.append(
                    f"[artifact-lane] {rel_path}: status `{status_value}` requires lane "
                    f"`{expected_lane}` (observed `{lane}`)"
                )

            required_trigger_lanes = set(
                _as_list(m2_4_policy.get("require_reopen_triggers_for_lanes"))
            )
            if lane in required_trigger_lanes:
                triggers = results.get("m2_4_reopen_triggers")
                if not isinstance(triggers, list) or not any(
                    isinstance(item, str) and item.strip() for item in triggers
                ):
                    errors.append(
                        f"[artifact-lane] {rel_path}: lane `{lane}` requires non-empty "
                        "m2_4_reopen_triggers list"
                    )

            required_residual_lanes = set(
                _as_list(m2_4_policy.get("require_residual_reason_for_lanes"))
            )
            if lane in required_residual_lanes:
                residual_reason = str(results.get("m2_4_residual_reason", "")).strip()
                if not residual_reason:
                    errors.append(
                        f"[artifact-lane] {rel_path}: lane `{lane}` requires non-empty "
                        "m2_4_residual_reason"
                    )

            if status_value == "INCONCLUSIVE_UNCERTAINTY":
                fragility = results.get("fragility_diagnostics")
                if isinstance(fragility, dict):
                    dominant_signal = str(
                        fragility.get("dominant_fragility_signal", "")
                    ).strip()
                    if dominant_signal and dominant_signal != reason_code:
                        errors.append(
                            f"[artifact-fragility] {rel_path}: dominant_fragility_signal "
                            f"`{dominant_signal}` does not match reason_code `{reason_code}`"
                        )

        m2_5_policy = dict(policy.get("m2_5_policy", {}))
        if m2_5_policy:
            m2_5_lane = str(results.get("m2_5_closure_lane", "")).strip()
            allowed_lanes = set(_as_list(m2_5_policy.get("allowed_lanes")))
            if allowed_lanes and m2_5_lane not in allowed_lanes:
                errors.append(
                    f"[artifact-lane] {rel_path}: m2_5_closure_lane `{m2_5_lane}` not in "
                    f"{sorted(allowed_lanes)}"
                )

            required_lane_by_status = dict(m2_5_policy.get("required_lane_by_status", {}))
            expected_lane = str(required_lane_by_status.get(status_value, "")).strip()
            inconclusive_missing_lane = str(
                m2_5_policy.get("inconclusive_lane_when_fields_missing", "")
            ).strip()
            if status_value == "INCONCLUSIVE_UNCERTAINTY":
                if required_fields_present and expected_lane and m2_5_lane != expected_lane:
                    errors.append(
                        f"[artifact-lane] {rel_path}: status `{status_value}` requires "
                        f"m2_5_closure_lane `{expected_lane}` (observed `{m2_5_lane}`)"
                    )
                if (
                    not required_fields_present
                    and inconclusive_missing_lane
                    and m2_5_lane != inconclusive_missing_lane
                ):
                    errors.append(
                        f"[artifact-lane] {rel_path}: incomplete INCONCLUSIVE_UNCERTAINTY "
                        f"requires m2_5_closure_lane `{inconclusive_missing_lane}` "
                        f"(observed `{m2_5_lane}`)"
                    )
            elif expected_lane and m2_5_lane != expected_lane:
                errors.append(
                    f"[artifact-lane] {rel_path}: status `{status_value}` requires "
                    f"m2_5_closure_lane `{expected_lane}` (observed `{m2_5_lane}`)"
                )

            required_trigger_lanes = set(
                _as_list(m2_5_policy.get("require_reopen_triggers_for_lanes"))
            )
            if m2_5_lane in required_trigger_lanes:
                triggers = results.get("m2_5_reopen_triggers")
                if not isinstance(triggers, list) or not any(
                    isinstance(item, str) and item.strip() for item in triggers
                ):
                    errors.append(
                        f"[artifact-lane] {rel_path}: lane `{m2_5_lane}` requires non-empty "
                        "m2_5_reopen_triggers list"
                    )

            required_residual_lanes = set(
                _as_list(m2_5_policy.get("require_residual_reason_for_lanes"))
            )
            if m2_5_lane in required_residual_lanes:
                residual_reason = str(results.get("m2_5_residual_reason", "")).strip()
                if not residual_reason:
                    errors.append(
                        f"[artifact-lane] {rel_path}: lane `{m2_5_lane}` requires non-empty "
                        "m2_5_residual_reason"
                    )

        guard_policy = dict(policy.get("non_blocking_h3_irrecoverability_guard", {}))
        if bool(guard_policy.get("enabled")):
            blocked_lane = str(
                m2_5_policy.get("blocked_lane", "M2_5_BLOCKED")
                if m2_5_policy
                else "M2_5_BLOCKED"
            )
            m2_5_lane = str(results.get("m2_5_closure_lane", "")).strip()
            residual_text = str(results.get("m2_5_residual_reason", "")).lower()
            reason_text = str(results.get("reason_code", "")).lower()
            combined_text = f"{residual_text} {reason_text}"
            linkage = results.get("m2_5_data_availability_linkage")
            if not isinstance(linkage, dict):
                errors.append(
                    "[artifact-m2_5] m2_5_data_availability_linkage must be an object"
                )
                linkage = {}

            blocking_claimed = _as_bool(linkage.get("missing_folio_blocking_claimed"))
            objective_failure = _as_bool(
                linkage.get("objective_comparative_validity_failure")
            )
            if blocking_claimed is None:
                errors.append(
                    "[artifact-m2_5] m2_5_data_availability_linkage."
                    "missing_folio_blocking_claimed must be boolean"
                )
            if objective_failure is None:
                errors.append(
                    "[artifact-m2_5] m2_5_data_availability_linkage."
                    "objective_comparative_validity_failure must be boolean"
                )
                objective_failure = False

            if blocking_claimed and not objective_failure:
                errors.append(
                    "[artifact-m2_5] missing-folio blocking claim requires "
                    "objective_comparative_validity_failure=true"
                )

            if (
                bool(guard_policy.get("require_objective_linkage_for_blocked_lane"))
                and m2_5_lane == blocked_lane
                and not objective_failure
            ):
                errors.append(
                    "[artifact-m2_5] blocked lane requires objective phase8_comparative "
                    "validity linkage for missing-folio/data-availability objections"
                )

            forbidden = [
                s.lower()
                for s in _as_list(
                    guard_policy.get("forbidden_non_blocked_residual_keywords")
                )
            ]
            if (
                bool(guard_policy.get("disallow_folio_block_terms_for_non_blocked_lane"))
                and m2_5_lane != blocked_lane
            ):
                for keyword in forbidden:
                    if keyword and keyword in combined_text:
                        errors.append(
                            "[artifact-m2_5] non-blocked lane contains blocked residual "
                            f"keyword `{keyword}` without objective linkage"
                        )

            blocked_keywords = [
                s.lower()
                for s in _as_list(guard_policy.get("blocked_residual_keywords"))
            ]
            if m2_5_lane == blocked_lane and blocked_keywords:
                if not any(keyword and keyword in combined_text for keyword in blocked_keywords):
                    errors.append(
                        "[artifact-m2_5] blocked lane residual/reason should include one of "
                        f"{blocked_keywords}"
                    )

        matrix_policy = dict(policy.get("registered_confidence_matrix", {}))
        run_profiles = matrix_policy.get("run_profiles")
        parameters = results.get("parameters")
        if isinstance(run_profiles, dict) and isinstance(parameters, dict):
            run_profile = str(parameters.get("run_profile", "")).strip()
            iterations = _as_float(parameters.get("iterations"))
            if not run_profile:
                errors.append(
                    f"[artifact-parameters] {rel_path}: parameters.run_profile is required"
                )
            elif run_profile != "custom":
                if run_profile not in run_profiles:
                    errors.append(
                        f"[artifact-parameters] {rel_path}: run_profile `{run_profile}` "
                        f"not registered in run_profiles={sorted(run_profiles.keys())}"
                    )
                expected_iterations = _as_float(run_profiles.get(run_profile))
                if (
                    expected_iterations is not None
                    and iterations is not None
                    and int(iterations) != int(expected_iterations)
                ):
                    errors.append(
                        f"[artifact-parameters] {rel_path}: run_profile `{run_profile}` "
                        f"requires iterations={int(expected_iterations)} "
                        f"(observed={iterations})"
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
    parser = argparse.ArgumentParser(description="Check SK-M2 phase8_comparative-uncertainty policy.")
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
        print(f"[FAIL] phase8_comparative-uncertainty policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] phase8_comparative-uncertainty policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
