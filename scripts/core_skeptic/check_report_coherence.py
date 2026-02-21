#!/usr/bin/env python3
"""
Report-coherence policy checker for SK-M3 guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/core_skeptic/sk_m3_report_coherence_policy.json"


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


def _run_method_policy_checks(
    *,
    policy: dict[str, Any],
    parsed_artifacts: dict[str, dict[str, Any]],
    root: Path,
) -> list[str]:
    errors: list[str] = []
    method_policy = dict(policy.get("method_policy", {}))
    if not method_policy:
        return errors

    artifact_path = str(method_policy.get("artifact_path", "")).strip()
    if not artifact_path and parsed_artifacts:
        artifact_path = next(iter(parsed_artifacts.keys()))
    if not artifact_path:
        errors.append("[policy] method_policy is set but no artifact path is available")
        return errors

    if artifact_path not in parsed_artifacts:
        artifact_file = root / artifact_path
        if not artifact_file.exists():
            errors.append(f"[missing-artifact] method policy artifact missing: {artifact_path}")
            return errors
        try:
            parsed_artifacts[artifact_path] = _load_results_payload(artifact_file)
        except Exception as exc:
            errors.append(f"[artifact-parse] {artifact_path}: {exc}")
            return errors

    payload = parsed_artifacts[artifact_path]
    methods = payload.get("methods")
    if not isinstance(methods, list):
        errors.append(f"[artifact-field] {artifact_path}: missing list field `methods`")
        return errors

    method_by_id: dict[str, dict[str, Any]] = {}
    for row in methods:
        if isinstance(row, dict):
            method_id = str(row.get("id", "")).strip()
            if method_id:
                method_by_id[method_id] = row

    required_method_ids = _as_list(method_policy.get("required_method_ids"))
    required_execution_status = str(method_policy.get("required_execution_status", "")).strip()
    required_determination = str(method_policy.get("required_determination", "")).strip()

    for method_id in required_method_ids:
        row = method_by_id.get(method_id)
        if row is None:
            errors.append(f"[artifact-method] {artifact_path}: missing method id `{method_id}`")
            continue
        if required_execution_status:
            actual = str(row.get("execution_status", ""))
            if actual != required_execution_status:
                errors.append(
                    f"[artifact-method] {artifact_path}: method `{method_id}` "
                    f"execution_status `{actual}` != `{required_execution_status}`"
                )
        if required_determination:
            actual = str(row.get("determination", ""))
            if actual != required_determination:
                errors.append(
                    f"[artifact-method] {artifact_path}: method `{method_id}` "
                    f"determination `{actual}` != `{required_determination}`"
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

    errors.extend(_run_method_policy_checks(policy=policy, parsed_artifacts=parsed_artifacts, root=root))
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-M3 report coherence policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to report coherence policy JSON.",
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
        print(f"[FAIL] report coherence policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] report coherence policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
