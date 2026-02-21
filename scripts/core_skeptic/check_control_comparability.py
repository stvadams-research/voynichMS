#!/usr/bin/env python3
"""
Control-comparability policy checker for SK-H3 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_h3_control_comparability_policy.json"


def _read_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _as_dict(value: Any) -> dict[str, Any]:
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
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _load_artifact_bundle(path: Path) -> dict[str, Any]:
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


def run_checks(policy: dict[str, Any], *, root: Path, mode: str) -> list[str]:
    errors: list[str] = []
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
    available_subset_policy = _as_dict(policy.get("available_subset_policy"))
    allowed_subset_statuses = set(_as_list(available_subset_policy.get("allowed_statuses")))
    allowed_subset_reason_codes = set(_as_list(available_subset_policy.get("allowed_reason_codes")))
    underpowered_reason_code = str(
        available_subset_policy.get("underpowered_reason_code", "AVAILABLE_SUBSET_UNDERPOWERED")
    )
    required_diagnostic_keys = _as_list(available_subset_policy.get("required_diagnostic_keys"))
    required_reproducibility_keys = _as_list(
        available_subset_policy.get("required_reproducibility_keys")
    )
    subset_thresholds = _as_dict(available_subset_policy.get("thresholds"))

    artifact_policy = dict(policy.get("artifact_policy", {}))
    parsed_artifacts: dict[str, dict[str, Any]] = {}
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
            bundle = _load_artifact_bundle(artifact_path)
        except Exception as exc:
            errors.append(f"[artifact-parse] {rel_path}: {exc}")
            continue

        parsed_artifacts[rel_path] = bundle
        results = _as_dict(bundle.get("results"))

        for key in _as_list(spec.get("required_result_keys")):
            if key not in results:
                errors.append(f"[artifact-field] {rel_path}: missing top-level results key `{key}`")

        comp_source: dict[str, Any]
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

        subset_status = str(comp_source.get("available_subset_status", ""))
        subset_reason = str(comp_source.get("available_subset_reason_code", ""))
        if allowed_subset_statuses and subset_status:
            if subset_status not in allowed_subset_statuses:
                errors.append(
                    "[available-subset-status] "
                    f"{rel_path}: available_subset_status `{subset_status}` "
                    f"not in allowed set {sorted(allowed_subset_statuses)}"
                )
        if allowed_subset_reason_codes and subset_reason:
            if subset_reason not in allowed_subset_reason_codes:
                errors.append(
                    "[available-subset-reason] "
                    f"{rel_path}: available_subset_reason_code `{subset_reason}` "
                    f"not in allowed set {sorted(allowed_subset_reason_codes)}"
                )

        if "available_subset_status" in comp_source:
            diagnostics = _as_dict(comp_source.get("available_subset_diagnostics"))
            reproducibility = _as_dict(comp_source.get("available_subset_reproducibility"))
            confidence = str(comp_source.get("available_subset_confidence", ""))

            for key in required_diagnostic_keys:
                if key not in diagnostics:
                    errors.append(
                        f"[available-subset-diagnostics] {rel_path}: missing diagnostic key `{key}`"
                    )

            for key in required_reproducibility_keys:
                if key not in reproducibility:
                    errors.append(
                        f"[available-subset-repro] {rel_path}: missing reproducibility key `{key}`"
                    )

            diag_thresholds = _as_dict(diagnostics.get("thresholds"))
            for key, expected in subset_thresholds.items():
                if key not in diag_thresholds:
                    errors.append(
                        f"[available-subset-thresholds] {rel_path}: missing threshold key `{key}`"
                    )
                    continue
                if _to_float(diag_thresholds.get(key), 0.0) != _to_float(expected, 0.0):
                    errors.append(
                        "[available-subset-thresholds] "
                        f"{rel_path}: threshold `{key}` mismatch "
                        f"(declared={diag_thresholds.get(key)!r}, expected={expected!r})"
                    )

            passes_thresholds = diagnostics.get("passes_thresholds")
            if not isinstance(passes_thresholds, bool):
                errors.append(
                    f"[available-subset-diagnostics] {rel_path}: `passes_thresholds` must be boolean"
                )
            else:
                if passes_thresholds and subset_reason == underpowered_reason_code:
                    errors.append(
                        "[available-subset-transition] "
                        f"{rel_path}: underpowered reason_code set despite passing thresholds"
                    )
                if (not passes_thresholds) and subset_reason != underpowered_reason_code:
                    errors.append(
                        "[available-subset-transition] "
                        f"{rel_path}: expected reason_code={underpowered_reason_code} when thresholds fail"
                    )
                if (not passes_thresholds) and subset_status != "INCONCLUSIVE_DATA_LIMITED":
                    errors.append(
                        "[available-subset-transition] "
                        f"{rel_path}: status must be INCONCLUSIVE_DATA_LIMITED when thresholds fail"
                    )

            preflight_only = reproducibility.get("preflight_only")
            if preflight_only is True and subset_status == "COMPARABLE_CONFIRMED":
                errors.append(
                    "[available-subset-transition] "
                    f"{rel_path}: preflight_only runs cannot declare COMPARABLE_CONFIRMED"
                )

            diag_card_count = _to_int(diagnostics.get("control_card_count"), -1)
            repro_card_count = _to_int(reproducibility.get("control_card_count"), -1)
            if diag_card_count != repro_card_count:
                errors.append(
                    "[available-subset-consistency] "
                    f"{rel_path}: control_card_count mismatch between diagnostics and reproducibility"
                )

            repro_paths = _as_list(reproducibility.get("control_card_paths"))
            if repro_card_count >= 0 and len(repro_paths) != repro_card_count:
                errors.append(
                    "[available-subset-consistency] "
                    f"{rel_path}: control_card_paths count {len(repro_paths)} "
                    f"does not match control_card_count={repro_card_count}"
                )

            if confidence not in {"QUALIFIED", "UNDERPOWERED", "BLOCKED"}:
                errors.append(
                    f"[available-subset-confidence] {rel_path}: invalid confidence value `{confidence}`"
                )

            evidence_scope = str(comp_source.get("evidence_scope", ""))
            full_data_closure_eligible = comp_source.get("full_data_closure_eligible")
            if evidence_scope == "available_subset" and full_data_closure_eligible is not False:
                errors.append(
                    "[available-subset-entitlement] "
                    f"{rel_path}: evidence_scope=available_subset requires full_data_closure_eligible=false"
                )
            if _as_list(comp_source.get("missing_pages")) and full_data_closure_eligible is not False:
                errors.append(
                    "[available-subset-entitlement] "
                    f"{rel_path}: missing_pages present but full_data_closure_eligible is not false"
                )

    comparability_bundle = _as_dict(parsed_artifacts.get("core_status/phase3_synthesis/CONTROL_COMPARABILITY_STATUS.json"))
    availability_bundle = _as_dict(
        parsed_artifacts.get("core_status/phase3_synthesis/CONTROL_COMPARABILITY_DATA_AVAILABILITY.json")
    )
    if comparability_bundle and availability_bundle:
        comp = _as_dict(comparability_bundle.get("results"))
        avail = _as_dict(availability_bundle.get("results"))
        for field in (
            "evidence_scope",
            "full_data_closure_eligible",
            "missing_count",
            "approved_lost_pages_policy_version",
            "approved_lost_pages_source_note_path",
            "irrecoverability",
            "full_data_feasibility",
            "full_data_closure_terminal_reason",
            "full_data_closure_reopen_conditions",
            "h3_4_closure_lane",
            "h3_5_closure_lane",
            "h3_5_residual_reason",
            "h3_5_reopen_conditions",
        ):
            if comp.get(field) != avail.get(field):
                errors.append(
                    "[cross-artifact] comparability/data-availability mismatch "
                    f"for `{field}` (comparability={comp.get(field)!r}, availability={avail.get(field)!r})"
                )

        feasibility_policy = _as_dict(policy.get("feasibility_policy"))
        allowed_feasibility = set(
            _as_list(feasibility_policy.get("allowed_full_data_feasibility"))
        )
        declared_feasibility = str(comp.get("full_data_feasibility", ""))
        if allowed_feasibility and declared_feasibility not in allowed_feasibility:
            errors.append(
                "[artifact-feasibility] invalid full_data_feasibility "
                f"`{declared_feasibility}` not in {sorted(allowed_feasibility)}"
            )
        if not str(comp.get("full_data_closure_terminal_reason", "")).strip():
            errors.append("[artifact-feasibility] full_data_closure_terminal_reason is required")
        if not _as_list(comp.get("full_data_closure_reopen_conditions")):
            errors.append(
                "[artifact-feasibility] full_data_closure_reopen_conditions must be non-empty"
            )
        h3_5_policy = _as_dict(policy.get("h3_5_policy"))
        if h3_5_policy:
            for field in _as_list(h3_5_policy.get("required_fields")):
                if field not in comp:
                    errors.append(f"[artifact-h3_5] missing comparability field `{field}`")
                if field not in avail:
                    errors.append(f"[artifact-h3_5] missing availability field `{field}`")

            h3_5_aligned_lane = str(h3_5_policy.get("aligned_lane", "H3_5_ALIGNED"))
            h3_5_terminal_lane = str(
                h3_5_policy.get("terminal_qualified_lane", "H3_5_TERMINAL_QUALIFIED")
            )
            h3_5_blocked_lane = str(h3_5_policy.get("blocked_lane", "H3_5_BLOCKED"))
            h3_5_inconclusive_lane = str(
                h3_5_policy.get("inconclusive_lane", "H3_5_INCONCLUSIVE")
            )

            status = str(comp.get("status", ""))
            reason_code = str(comp.get("reason_code", ""))
            evidence_scope = str(comp.get("evidence_scope", ""))
            full_data_closure_eligible = comp.get("full_data_closure_eligible")
            full_data_feasibility = str(comp.get("full_data_feasibility", ""))
            missing_count = _to_int(comp.get("missing_count"), 0)

            if (
                full_data_feasibility == "feasible"
                and missing_count == 0
                and status in {"COMPARABLE_CONFIRMED", "COMPARABLE_QUALIFIED"}
                and evidence_scope == "full_dataset"
                and full_data_closure_eligible is True
            ):
                expected_h3_5_lane = h3_5_aligned_lane
            elif (
                full_data_feasibility == "irrecoverable"
                and missing_count > 0
                and status == "NON_COMPARABLE_BLOCKED"
                and reason_code == "DATA_AVAILABILITY"
                and evidence_scope == "available_subset"
                and full_data_closure_eligible is False
            ):
                expected_h3_5_lane = h3_5_terminal_lane
            elif status == "INCONCLUSIVE_DATA_LIMITED":
                expected_h3_5_lane = h3_5_inconclusive_lane
            else:
                expected_h3_5_lane = h3_5_blocked_lane

            declared_h3_5_lane = str(comp.get("h3_5_closure_lane", ""))
            if declared_h3_5_lane and declared_h3_5_lane != expected_h3_5_lane:
                errors.append(
                    "[artifact-h3_5] h3_5_closure_lane mismatch "
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
                ) or _as_list(comp.get("full_data_closure_reopen_conditions"))
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

            declared_h3_5_reason = str(comp.get("h3_5_residual_reason", ""))
            if declared_h3_5_reason and declared_h3_5_reason != expected_h3_5_reason:
                errors.append(
                    "[artifact-h3_5] h3_5_residual_reason mismatch "
                    f"(declared={declared_h3_5_reason!r}, expected={expected_h3_5_reason!r})"
                )

            declared_h3_5_reopen = _as_list(comp.get("h3_5_reopen_conditions"))
            if declared_h3_5_reopen and declared_h3_5_reopen != expected_h3_5_reopen:
                errors.append(
                    "[artifact-h3_5] h3_5_reopen_conditions mismatch "
                    f"(declared={declared_h3_5_reopen!r}, expected={expected_h3_5_reopen!r})"
                )

        freshness_policy = _as_dict(policy.get("freshness_policy"))
        require_run_id = bool(freshness_policy.get("require_matching_run_id", False))
        require_timestamps = bool(freshness_policy.get("require_timestamps", False))
        max_skew = _to_int(freshness_policy.get("max_timestamp_skew_seconds"), 600)
        comp_prov = _as_dict(comparability_bundle.get("provenance"))
        avail_prov = _as_dict(availability_bundle.get("provenance"))

        if require_run_id:
            comp_run_id = str(comp_prov.get("run_id", ""))
            avail_run_id = str(avail_prov.get("run_id", ""))
            if (not comp_run_id) or (not avail_run_id):
                errors.append(
                    "[freshness] missing provenance.run_id in comparability/data-availability artifacts"
                )
            elif comp_run_id != avail_run_id:
                errors.append(
                    "[freshness] comparability/data-availability provenance.run_id mismatch "
                    f"(comparability={comp_run_id!r}, availability={avail_run_id!r})"
                )

        if require_timestamps:
            comp_ts = _parse_iso_timestamp(comp_prov.get("timestamp"))
            avail_ts = _parse_iso_timestamp(avail_prov.get("timestamp"))
            if comp_ts is None or avail_ts is None:
                errors.append(
                    "[freshness] missing/invalid provenance.timestamp in comparability/data-availability artifacts"
                )
            else:
                skew_seconds = abs((comp_ts - avail_ts).total_seconds())
                if skew_seconds > max_skew:
                    errors.append(
                        "[freshness] comparability/data-availability provenance timestamp skew "
                        f"{skew_seconds:.1f}s exceeds max {max_skew}s"
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
