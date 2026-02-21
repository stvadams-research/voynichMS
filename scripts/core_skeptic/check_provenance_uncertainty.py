#!/usr/bin/env python3
"""
Historical provenance-uncertainty checker for SK-M4 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m4_provenance_policy.json"


def _read_policy(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _is_allowlisted(allowlist: Sequence[dict[str, Any]], pattern_id: str, scope: str) -> bool:
    for entry in allowlist:
        if entry.get("pattern_id") == pattern_id and entry.get("scope") == scope:
            return True
    return False


def _rule_applies_to_mode(rule: Mapping[str, Any], mode: str) -> bool:
    modes = set(_as_list(rule.get("modes")))
    return not modes or mode in modes


def _load_results_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and isinstance(payload.get("results"), dict):
        return payload["results"]
    if isinstance(payload, dict):
        return payload
    raise ValueError(f"Artifact payload at {path} must be a JSON object")


def _parse_iso_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def _run_threshold_checks(
    *,
    policy: dict[str, Any],
    parsed_artifacts: dict[str, dict[str, Any]],
    mode: str,
) -> list[str]:
    errors: list[str] = []
    threshold_policy = dict(policy.get("threshold_policy", {}))
    if not threshold_policy:
        return errors

    artifact_path = str(threshold_policy.get("artifact_path", "")).strip()
    if not artifact_path and parsed_artifacts:
        artifact_path = next(iter(parsed_artifacts.keys()))
    if not artifact_path:
        errors.append("[policy] threshold_policy is set but no artifact path is available")
        return errors

    artifact = parsed_artifacts.get(artifact_path)
    if artifact is None:
        errors.append(f"[missing-artifact] threshold policy artifact missing: {artifact_path}")
        return errors

    orphaned_ratio_max = float(threshold_policy.get("orphaned_ratio_max", 1.0))
    orphaned_count_max = int(threshold_policy.get("orphaned_count_max", 10**9))
    running_count_max = int(threshold_policy.get("running_count_max", 0))
    missing_manifests_max = int(threshold_policy.get("missing_manifests_max", 0))
    max_artifact_age_hours = int(threshold_policy.get("max_artifact_age_hours", 168))

    orphaned_ratio = float(artifact.get("orphaned_ratio", 0.0))
    orphaned_rows = int(artifact.get("orphaned_rows", 0))
    running_rows = int(artifact.get("running_rows", 0))
    missing_manifests = int(artifact.get("missing_manifests", 0))

    if orphaned_ratio > orphaned_ratio_max:
        errors.append(
            f"[threshold] {artifact_path}: orphaned_ratio {orphaned_ratio:.6f} > {orphaned_ratio_max:.6f}"
        )
    if orphaned_rows > orphaned_count_max:
        errors.append(
            f"[threshold] {artifact_path}: orphaned_rows {orphaned_rows} > {orphaned_count_max}"
        )
    if running_rows > running_count_max:
        errors.append(
            f"[threshold] {artifact_path}: running_rows {running_rows} > {running_count_max}"
        )
    if missing_manifests > missing_manifests_max:
        errors.append(
            f"[threshold] {artifact_path}: missing_manifests {missing_manifests} > {missing_manifests_max}"
        )

    if artifact.get("threshold_policy_pass") is not True:
        errors.append(
            f"[threshold] {artifact_path}: threshold_policy_pass must be true for mode={mode}"
        )

    generated = _parse_iso_timestamp(artifact.get("generated_utc"))
    if generated is None:
        errors.append(f"[artifact-field] {artifact_path}: generated_utc must be ISO8601")
    else:
        age_hours = (datetime.now(UTC) - generated).total_seconds() / 3600.0
        if age_hours > max_artifact_age_hours:
            errors.append(
                f"[stale-artifact] {artifact_path}: age_hours {age_hours:.2f} > {max_artifact_age_hours}"
            )

    sync_artifact_path = str(threshold_policy.get("sync_artifact_path", "")).strip()
    max_sync_artifact_age_hours = int(
        threshold_policy.get("max_sync_artifact_age_hours", max_artifact_age_hours)
    )
    if sync_artifact_path:
        sync_artifact = parsed_artifacts.get(sync_artifact_path)
        if sync_artifact is None:
            errors.append(f"[missing-artifact] threshold policy sync artifact missing: {sync_artifact_path}")
        else:
            sync_generated = _parse_iso_timestamp(sync_artifact.get("generated_utc"))
            if sync_generated is None:
                errors.append(
                    f"[artifact-field] {sync_artifact_path}: generated_utc must be ISO8601"
                )
            else:
                sync_age_hours = (datetime.now(UTC) - sync_generated).total_seconds() / 3600.0
                if sync_age_hours > max_sync_artifact_age_hours:
                    errors.append(
                        f"[stale-artifact] {sync_artifact_path}: age_hours {sync_age_hours:.2f} "
                        f"> {max_sync_artifact_age_hours}"
                    )

    return errors


def _run_contract_coupling_checks(
    *,
    policy: dict[str, Any],
    parsed_artifacts: dict[str, dict[str, Any]],
    root: Path,
) -> list[str]:
    errors: list[str] = []
    coupling = dict(policy.get("contract_coupling_policy", {}))
    if not coupling:
        return errors

    provenance_path = str(coupling.get("provenance_artifact_path", "")).strip()
    gate_path = str(coupling.get("gate_health_artifact_path", "")).strip()
    if not provenance_path:
        errors.append("[policy] contract_coupling_policy missing provenance_artifact_path")
        return errors
    if not gate_path:
        errors.append("[policy] contract_coupling_policy missing gate_health_artifact_path")
        return errors

    provenance = parsed_artifacts.get(provenance_path)
    if provenance is None:
        file_path = root / provenance_path
        if not file_path.exists():
            errors.append(f"[missing-artifact] contract coupling provenance artifact missing: {provenance_path}")
            return errors
        try:
            provenance = _load_results_payload(file_path)
            parsed_artifacts[provenance_path] = provenance
        except Exception as exc:
            errors.append(f"[artifact-parse] {provenance_path}: {exc}")
            return errors

    gate = parsed_artifacts.get(gate_path)
    if gate is None:
        file_path = root / gate_path
        if not file_path.exists():
            if bool(coupling.get("fail_when_gate_health_missing", False)):
                errors.append(f"[missing-artifact] contract coupling gate-health artifact missing: {gate_path}")
            return errors
        try:
            gate = _load_results_payload(file_path)
            parsed_artifacts[gate_path] = gate
        except Exception as exc:
            errors.append(f"[artifact-parse] {gate_path}: {exc}")
            return errors

    gate_status = str(gate.get("status", ""))
    provenance_status = str(provenance.get("status", ""))
    degraded_gate_statuses = set(_as_list(coupling.get("degraded_gate_statuses")))
    disallow_when_degraded = set(
        _as_list(coupling.get("disallow_provenance_statuses_when_gate_degraded"))
    )
    require_reason_codes = set(
        _as_list(coupling.get("require_contract_reason_codes_when_gate_degraded"))
    )
    required_m4_5_lanes = set(_as_list(coupling.get("require_m4_5_lanes_when_gate_degraded")))
    required_m4_4_lanes = set(_as_list(coupling.get("require_m4_4_lanes_when_gate_degraded")))

    if gate_status in degraded_gate_statuses:
        if provenance_status in disallow_when_degraded:
            errors.append(
                f"[contract-coupling] gate status `{gate_status}` disallows provenance status `{provenance_status}`"
            )
        if bool(coupling.get("require_contract_coupling_pass", False)):
            if provenance.get("contract_coupling_pass") is not True:
                errors.append(
                    "[contract-coupling] provenance artifact must set contract_coupling_pass=true "
                    "under degraded gate state"
                )
        actual_reason_codes = set(_as_list(provenance.get("contract_reason_codes")))
        missing_reason_codes = sorted(require_reason_codes - actual_reason_codes)
        if missing_reason_codes:
            errors.append(
                "[contract-coupling] provenance artifact missing required contract reason codes "
                f"under degraded gate state: {missing_reason_codes}"
            )
        required_lanes = required_m4_5_lanes or required_m4_4_lanes
        if required_lanes:
            lane = str(provenance.get("m4_5_historical_lane") or provenance.get("m4_4_historical_lane") or "")
            if lane not in required_lanes:
                errors.append(
                    "[contract-coupling] degraded gate state requires provenance lane in "
                    f"{sorted(required_lanes)} (observed `{lane}`)"
                )

    # Ensure provenance artifact mirrors observed gate-health state for core_audit clarity.
    if str(provenance.get("contract_health_status", "")) and gate_status:
        if str(provenance.get("contract_health_status")) != gate_status:
            errors.append(
                "[contract-coupling] provenance artifact contract_health_status does not match "
                f"gate artifact status ({provenance.get('contract_health_status')} != {gate_status})"
            )

    return errors


def _run_m4_5_lane_checks(
    *,
    policy: dict[str, Any],
    parsed_artifacts: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    m4_policy = dict(policy.get("m4_5_policy", {}))
    key_prefix = "m4_5"
    lane_key = "m4_5_historical_lane"
    residual_reason_key = "m4_5_residual_reason"
    reopen_conditions_key = "m4_5_reopen_conditions"
    if not m4_policy:
        m4_policy = dict(policy.get("m4_4_policy", {}))
        key_prefix = "m4_4"
        lane_key = "m4_4_historical_lane"
        residual_reason_key = "m4_4_residual_reason"
        reopen_conditions_key = "m4_4_reopen_conditions"

    if not m4_policy:
        return errors

    threshold_policy = dict(policy.get("threshold_policy", {}))
    provenance_path = str(threshold_policy.get("artifact_path", "")).strip()
    sync_path = str(threshold_policy.get("sync_artifact_path", "")).strip()
    if not provenance_path or provenance_path not in parsed_artifacts:
        errors.append(f"[{key_prefix}-lane] provenance artifact unavailable for lane checks.")
        return errors
    if not sync_path or sync_path not in parsed_artifacts:
        errors.append(f"[{key_prefix}-lane] sync artifact unavailable for lane checks.")
        return errors

    provenance = parsed_artifacts[provenance_path]
    sync = parsed_artifacts[sync_path]

    status = str(provenance.get("status", ""))
    lane = str(provenance.get(lane_key) or provenance.get("m4_4_historical_lane") or "")
    recoverability_class = str(provenance.get("recoverability_class", ""))

    required_lane_by_status = dict(m4_policy.get("required_lane_by_provenance_status", {}))
    bounded_classes = set(_as_list(m4_policy.get("bounded_recoverability_classes")))
    bounded_lane_name = str(m4_policy.get("bounded_lane_name", "M4_5_BOUNDED"))
    inconclusive_lane_name = str(m4_policy.get("inconclusive_lane_name", "M4_5_INCONCLUSIVE"))
    blocked_lane_name = str(m4_policy.get("blocked_lane_name", "M4_5_BLOCKED"))

    if status == "PROVENANCE_QUALIFIED" and recoverability_class in bounded_classes:
        expected_lane = bounded_lane_name
    else:
        expected_lane = str(required_lane_by_status.get(status, "")).strip()
        if status not in required_lane_by_status and status.startswith("INCONCLUSIVE"):
            expected_lane = inconclusive_lane_name

    if expected_lane and lane != expected_lane:
        errors.append(
            f"[{key_prefix}-lane] {provenance_path}: status `{status}` with recoverability "
            f"`{recoverability_class}` requires lane `{expected_lane}` (observed `{lane}`)"
        )

    if lane == bounded_lane_name and recoverability_class not in bounded_classes:
        errors.append(
            f"[{key_prefix}-lane] {provenance_path}: lane `{bounded_lane_name}` requires recoverability "
            f"class in {sorted(bounded_classes)} (observed `{recoverability_class}`)"
        )

    required_reopen_lanes = set(_as_list(m4_policy.get("require_reopen_conditions_for_lanes")))
    if lane in required_reopen_lanes:
        reopen_conditions = provenance.get(reopen_conditions_key) or provenance.get("m4_4_reopen_conditions")
        if not isinstance(reopen_conditions, list) or not any(
            isinstance(item, str) and item.strip() for item in reopen_conditions
        ):
            errors.append(
                f"[{key_prefix}-lane] {provenance_path}: lane `{lane}` requires non-empty "
                f"{reopen_conditions_key} list"
            )

    required_residual_reason_lanes = set(_as_list(m4_policy.get("require_residual_reason_for_lanes")))
    if lane in required_residual_reason_lanes:
        residual_reason = provenance.get(residual_reason_key) or provenance.get("m4_4_residual_reason")
        if not isinstance(residual_reason, str) or not residual_reason.strip():
            errors.append(
                f"[{key_prefix}-lane] {provenance_path}: lane `{lane}` requires non-empty "
                f"{residual_reason_key}"
            )

    missing_folio_guard = dict(m4_policy.get("missing_folio_non_blocking_guard", {}))
    if missing_folio_guard:
        linkage_key = str(
            missing_folio_guard.get("linkage_key", "m4_5_data_availability_linkage")
        )
        linkage = provenance.get(linkage_key, {})
        if not isinstance(linkage, dict):
            errors.append(
                f"[{key_prefix}-lane] {provenance_path}: `{linkage_key}` must be an object"
            )
        else:
            required_bool_keys = _as_list(missing_folio_guard.get("required_boolean_keys"))
            for bool_key in required_bool_keys:
                if not isinstance(linkage.get(bool_key), bool):
                    errors.append(
                        f"[{key_prefix}-lane] {provenance_path}: `{linkage_key}.{bool_key}` must be boolean"
                    )
            missing_folio_blocking_claimed = linkage.get("missing_folio_blocking_claimed")
            objective_incompleteness = linkage.get("objective_provenance_contract_incompleteness")
            approved_irrecoverable = linkage.get("approved_irrecoverable_loss_classification")
            if (
                missing_folio_guard.get(
                    "require_objective_linkage_when_missing_folio_blocking_claimed", False
                )
                and missing_folio_blocking_claimed is True
                and objective_incompleteness is not True
            ):
                errors.append(
                    f"[{key_prefix}-lane] {provenance_path}: folio-based blocking claim requires "
                    "objective provenance-contract incompleteness linkage"
                )
            if (
                missing_folio_guard.get(
                    "disallow_blocking_when_approved_irrecoverable_loss_without_objective_linkage",
                    False,
                )
                and missing_folio_blocking_claimed is True
                and approved_irrecoverable is True
                and objective_incompleteness is not True
            ):
                errors.append(
                    f"[{key_prefix}-lane] {provenance_path}: approved irrecoverable-loss folio claim "
                    "cannot block SK-M4 without objective provenance-contract incompleteness"
                )
            if (
                lane == blocked_lane_name
                and missing_folio_blocking_claimed is True
                and objective_incompleteness is not True
            ):
                errors.append(
                    f"[{key_prefix}-lane] {provenance_path}: blocked lane requires objective linkage "
                    "when folio-based blocking is claimed"
                )

    # Cross-artifact parity checks.
    if str(sync.get("provenance_status", "")) and str(sync.get("provenance_status")) != status:
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: provenance_status `{sync.get('provenance_status')}` "
            f"!= health status `{status}`"
        )
    if (
        str(sync.get("provenance_reason_code", ""))
        and str(sync.get("provenance_reason_code")) != str(provenance.get("reason_code", ""))
    ):
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: provenance_reason_code `{sync.get('provenance_reason_code')}` "
            f"!= health reason_code `{provenance.get('reason_code')}`"
        )
    if (
        str(sync.get("provenance_health_lane", ""))
        and str(sync.get("provenance_health_lane")) != lane
    ):
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: provenance_health_lane `{sync.get('provenance_health_lane')}` "
            f"!= health lane `{lane}`"
        )
    sync_lane_explicit = sync.get("provenance_health_m4_5_lane")
    if key_prefix == "m4_5" and str(sync_lane_explicit or "") and str(sync_lane_explicit) != lane:
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: provenance_health_m4_5_lane `{sync_lane_explicit}` "
            f"!= health lane `{lane}`"
        )
    sync_residual_explicit = sync.get("provenance_health_m4_5_residual_reason")
    residual_reason = provenance.get(residual_reason_key) or provenance.get("m4_4_residual_reason")
    if (
        key_prefix == "m4_5"
        and str(sync_residual_explicit or "")
        and str(sync_residual_explicit) != str(residual_reason)
    ):
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: provenance_health_m4_5_residual_reason "
            f"`{sync_residual_explicit}` != health residual reason `{residual_reason}`"
        )

    health_orphaned_rows = provenance.get("orphaned_rows")
    sync_health_orphaned_rows = sync.get("health_orphaned_rows")
    if (
        isinstance(sync_health_orphaned_rows, int)
        and isinstance(health_orphaned_rows, int)
        and sync_health_orphaned_rows != health_orphaned_rows
    ):
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: health_orphaned_rows `{sync_health_orphaned_rows}` "
            f"!= provenance orphaned_rows `{health_orphaned_rows}`"
        )

    if str(sync.get("status", "")) == "IN_SYNC" and sync.get("drift_detected") is True:
        errors.append(
            f"[{key_prefix}-parity] {sync_path}: status=IN_SYNC is incompatible with drift_detected=true"
        )
    if sync.get("drift_detected") is False and isinstance(sync.get("drift_by_status"), dict):
        non_zero = {
            k: v
            for k, v in sync.get("drift_by_status", {}).items()
            if isinstance(v, int) and v != 0
        }
        if non_zero:
            errors.append(
                f"[{key_prefix}-parity] {sync_path}: drift_detected=false but non-zero drift entries exist: {non_zero}"
            )

    return errors


def run_checks(policy: dict[str, Any], *, root: Path, mode: str) -> list[str]:
    errors: list[str] = []
    allowlist = list(policy.get("allowlist", []))

    for scope in _as_list(policy.get("tracked_files")):
        if not (root / scope).exists():
            errors.append(f"[missing-file] tracked file missing: {scope}")

    for banned in list(policy.get("banned_patterns", [])):
        if not _rule_applies_to_mode(banned, mode):
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

    for req in list(policy.get("required_markers", [])):
        if not _rule_applies_to_mode(req, mode):
            continue

        req_id = str(req.get("id", "unknown_requirement"))
        scopes = _as_list(req.get("scopes"))
        markers = _as_list(req.get("markers"))
        if not scopes or not markers:
            errors.append(f"[policy] required marker rule {req_id} missing scopes/markers")
            continue

        for scope in scopes:
            file_path = root / scope
            if not file_path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {req_id})")
                continue
            text = file_path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(f"[missing-marker] {scope}: missing `{marker}` ({req_id})")

    parsed_artifacts: dict[str, dict[str, Any]] = {}
    artifact_policy = dict(policy.get("artifact_policy", {}))
    for spec in list(artifact_policy.get("tracked_artifacts", [])):
        rel_path = str(spec.get("path", "")).strip()
        required_in_modes = set(_as_list(spec.get("required_in_modes")))
        required = mode in required_in_modes
        if not rel_path:
            errors.append("[policy] artifact policy entry missing `path`")
            continue

        file_path = root / rel_path
        if not file_path.exists():
            if required:
                errors.append(f"[missing-artifact] required in mode={mode}: {rel_path}")
            continue

        try:
            results = _load_results_payload(file_path)
        except Exception as exc:
            errors.append(f"[artifact-parse] {rel_path}: {exc}")
            continue

        parsed_artifacts[rel_path] = results

        for key in _as_list(spec.get("required_result_keys")):
            if key not in results:
                errors.append(f"[artifact-field] {rel_path}: missing result key `{key}`")

        allowed_statuses = set(_as_list(spec.get("allowed_statuses")))
        status_value = str(results.get("status"))
        if allowed_statuses and status_value not in allowed_statuses:
            errors.append(
                f"[artifact-status] {rel_path}: status `{status_value}` not in {sorted(allowed_statuses)}"
            )

    errors.extend(_run_threshold_checks(policy=policy, parsed_artifacts=parsed_artifacts, mode=mode))
    errors.extend(
        _run_contract_coupling_checks(
            policy=policy,
            parsed_artifacts=parsed_artifacts,
            root=root,
        )
    )
    errors.extend(
        _run_m4_5_lane_checks(
            policy=policy,
            parsed_artifacts=parsed_artifacts,
        )
    )
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-M4 historical provenance uncertainty policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to SK-M4 policy JSON.",
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
        print(f"[FAIL] provenance uncertainty policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] provenance uncertainty policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
