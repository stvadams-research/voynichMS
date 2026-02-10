#!/usr/bin/env python3
"""
Historical provenance-uncertainty checker for SK-M4 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_m4_provenance_policy.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _is_allowlisted(allowlist: Sequence[Dict[str, Any]], pattern_id: str, scope: str) -> bool:
    for entry in allowlist:
        if entry.get("pattern_id") == pattern_id and entry.get("scope") == scope:
            return True
    return False


def _rule_applies_to_mode(rule: Mapping[str, Any], mode: str) -> bool:
    modes = set(_as_list(rule.get("modes")))
    return not modes or mode in modes


def _load_results_payload(path: Path) -> Dict[str, Any]:
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
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _run_threshold_checks(
    *,
    policy: Dict[str, Any],
    parsed_artifacts: Dict[str, Dict[str, Any]],
    mode: str,
) -> List[str]:
    errors: List[str] = []
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
        age_hours = (datetime.now(timezone.utc) - generated).total_seconds() / 3600.0
        if age_hours > max_artifact_age_hours:
            errors.append(
                f"[stale-artifact] {artifact_path}: age_hours {age_hours:.2f} > {max_artifact_age_hours}"
            )

    return errors


def _run_contract_coupling_checks(
    *,
    policy: Dict[str, Any],
    parsed_artifacts: Dict[str, Dict[str, Any]],
    root: Path,
) -> List[str]:
    errors: List[str] = []
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

    # Ensure provenance artifact mirrors observed gate-health state for audit clarity.
    if str(provenance.get("contract_health_status", "")) and gate_status:
        if str(provenance.get("contract_health_status")) != gate_status:
            errors.append(
                "[contract-coupling] provenance artifact contract_health_status does not match "
                f"gate artifact status ({provenance.get('contract_health_status')} != {gate_status})"
            )

    return errors


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors: List[str] = []
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

    parsed_artifacts: Dict[str, Dict[str, Any]] = {}
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
