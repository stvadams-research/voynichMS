#!/usr/bin/env python3
"""
Claim-boundary policy checker for SK-H2 public-language guardrails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/skeptic/sk_h2_claim_language_policy.json"


def _read_policy(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Policy file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _is_allowlisted(
    allowlist: Sequence[Dict[str, Any]], pattern_id: str, scope: str
) -> bool:
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


def _gate_health_state(
    policy: Dict[str, Any], *, root: Path, mode: str
) -> tuple[Dict[str, Any], Dict[str, Any], str, List[str]]:
    errors: List[str] = []
    gate_policy = dict(policy.get("gate_health_policy", {}))
    if not gate_policy:
        return gate_policy, {}, "", errors

    required_modes = set(_as_list(gate_policy.get("required_in_modes")))
    if required_modes and mode not in required_modes:
        return gate_policy, {}, "", errors

    rel_path = str(gate_policy.get("artifact_path", "")).strip()
    if not rel_path:
        errors.append("[policy] gate_health_policy missing artifact_path")
        return gate_policy, {}, "", errors

    path = root / rel_path
    if not path.exists():
        errors.append(f"[missing-artifact] gate-health artifact missing: {rel_path}")
        return gate_policy, {}, "", errors

    try:
        results = _load_results_payload(path)
    except Exception as exc:
        errors.append(f"[artifact-parse] {rel_path}: {exc}")
        return gate_policy, {}, "", errors

    for key in _as_list(gate_policy.get("required_result_keys")):
        if key not in results:
            errors.append(f"[artifact-field] {rel_path}: missing result key `{key}`")

    status = str(results.get("status", "")).strip()
    allowed_statuses = set(_as_list(gate_policy.get("allowed_statuses")))
    if allowed_statuses and status not in allowed_statuses:
        errors.append(
            f"[artifact-status] {rel_path}: status `{status}` not in {sorted(allowed_statuses)}"
        )
    return gate_policy, results, status, errors


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str = "ci") -> List[str]:
    errors: List[str] = []
    allowlist = list(policy.get("allowlist", []))

    banned_patterns = list(policy.get("banned_patterns", []))
    for banned in banned_patterns:
        if not _rule_applies_to_mode(banned, mode):
            continue
        pattern_id = str(banned.get("id", "unknown_pattern"))
        pattern_text = str(banned.get("pattern", ""))
        scopes = _as_list(banned.get("scopes"))
        if not pattern_text or not scopes:
            errors.append(f"[policy] banned pattern {pattern_id} is missing pattern/scopes")
            continue
        matcher = (
            re.compile(
                pattern_text,
                flags=re.IGNORECASE if bool(banned.get("case_insensitive", False)) else 0,
            )
            if bool(banned.get("regex", False))
            else None
        )

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
                errors.append(
                    f"[banned-pattern] {scope}: matched `{pattern_text}` ({pattern_id})"
                )

    required_markers = list(policy.get("required_markers", []))
    for req in required_markers:
        if not _rule_applies_to_mode(req, mode):
            continue
        req_id = str(req.get("id", "unknown_requirement"))
        scopes = _as_list(req.get("scopes"))
        markers = _as_list(req.get("markers"))
        if not scopes or not markers:
            errors.append(f"[policy] required marker rule {req_id} is missing scopes/markers")
            continue
        for scope in scopes:
            file_path = root / scope
            if not file_path.exists():
                errors.append(f"[missing-file] {scope} (referenced by {req_id})")
                continue
            text = file_path.read_text(encoding="utf-8")
            for marker in markers:
                if marker not in text:
                    errors.append(
                        f"[missing-marker] {scope}: missing `{marker}` ({req_id})"
                    )

    gate_policy, _, gate_status, gate_errors = _gate_health_state(policy, root=root, mode=mode)
    errors.extend(gate_errors)
    degraded_statuses = set(_as_list(gate_policy.get("degraded_statuses")))
    gate_is_degraded = bool(gate_status and gate_status in degraded_statuses)

    if gate_is_degraded:
        for req in list(gate_policy.get("degraded_required_markers", [])):
            if not isinstance(req, dict) or not _rule_applies_to_mode(req, mode):
                continue
            req_id = str(req.get("id", "gate_degraded_required_marker"))
            scopes = _as_list(req.get("scopes"))
            markers = _as_list(req.get("markers"))
            if not scopes or not markers:
                errors.append(
                    f"[policy] gate degraded marker rule {req_id} missing scopes/markers"
                )
                continue
            for scope in scopes:
                file_path = root / scope
                if not file_path.exists():
                    errors.append(f"[missing-file] {scope} (referenced by {req_id})")
                    continue
                text = file_path.read_text(encoding="utf-8")
                for marker in markers:
                    if marker not in text:
                        errors.append(
                            f"[missing-gate-marker] {scope}: missing `{marker}` ({req_id})"
                        )

        for banned in list(gate_policy.get("degraded_banned_patterns", [])):
            if not isinstance(banned, dict) or not _rule_applies_to_mode(banned, mode):
                continue
            pattern_id = str(banned.get("id", "gate_degraded_banned_pattern"))
            pattern_text = str(banned.get("pattern", ""))
            scopes = _as_list(banned.get("scopes"))
            if not pattern_text or not scopes:
                errors.append(
                    f"[policy] gate degraded banned pattern {pattern_id} missing pattern/scopes"
                )
                continue
            matcher = (
                re.compile(
                    pattern_text,
                    flags=re.IGNORECASE
                    if bool(banned.get("case_insensitive", False))
                    else 0,
                )
                if bool(banned.get("regex", False))
                else None
            )
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
                    errors.append(
                        f"[gate-degraded-banned-pattern] {scope}: matched `{pattern_text}` ({pattern_id})"
                    )

    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check SK-H2 claim-boundary policy.")
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to claim-language policy JSON.",
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
        print(f"[FAIL] claim-boundary policy violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] claim-boundary policy checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
