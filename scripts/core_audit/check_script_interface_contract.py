#!/usr/bin/env python3
"""Validate tiered CLI interface contract for user-facing scripts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONTRACT_PATH = PROJECT_ROOT / "configs/project/script_interface_tiers.json"
USER_FACING_TIER = "tier1_user_facing"
INVALID_FLAG = "--__voynich_invalid_flag__"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check script interface tiers and user-facing CLI contract."
    )
    parser.add_argument(
        "--contract",
        default=str(DEFAULT_CONTRACT_PATH),
        help=f"Path to script interface contract JSON (default: {DEFAULT_CONTRACT_PATH}).",
    )
    parser.add_argument(
        "--python-bin",
        default=sys.executable,
        help="Python executable used to invoke scripts.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=20.0,
        help="Per-command timeout for CLI probes.",
    )
    return parser.parse_args()


def _run_command(command: list[str], timeout_seconds: float) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return 124, f"timeout after {timeout_seconds}s"
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    return int(completed.returncode), output


def _load_contract(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Contract payload must be a JSON object.")
    return payload


def main() -> int:
    args = _parse_args()
    contract_path = Path(args.contract)
    if not contract_path.exists():
        print(f"[FAIL] Script interface contract not found: {contract_path}")
        return 1

    try:
        payload = _load_contract(contract_path)
    except Exception as exc:
        print(f"[FAIL] Could not load script interface contract: {exc}")
        return 1

    tiers = payload.get("tiers")
    scripts = payload.get("scripts")
    if not isinstance(tiers, dict) or USER_FACING_TIER not in tiers:
        print(f"[FAIL] Contract must define {USER_FACING_TIER!r} in tiers.")
        return 1
    if not isinstance(scripts, list) or not scripts:
        print("[FAIL] Contract must define a non-empty scripts list.")
        return 1

    errors: list[str] = []
    tier_names = set(tiers.keys())
    seen_paths: set[str] = set()
    user_checked = 0

    for index, raw in enumerate(scripts):
        label = f"scripts[{index}]"
        if not isinstance(raw, dict):
            errors.append(f"[schema] {label} must be an object.")
            continue

        rel_path = raw.get("path")
        tier = raw.get("tier")
        expected_flags = raw.get("expected_flags", [])
        required_args = raw.get("required_args", [])

        if not isinstance(rel_path, str) or not rel_path.strip():
            errors.append(f"[schema] {label} missing non-empty path.")
            continue
        rel_path = rel_path.strip()

        if rel_path in seen_paths:
            errors.append(f"[schema] duplicate script path in contract: {rel_path}")
            continue
        seen_paths.add(rel_path)

        if tier not in tier_names:
            errors.append(
                f"[schema] {label} tier={tier!r} not found in tiers section."
            )
            continue

        script_path = PROJECT_ROOT / rel_path
        if not script_path.exists() or not script_path.is_file():
            errors.append(f"[path] script not found: {rel_path}")
            continue

        if not isinstance(expected_flags, list) or not all(
            isinstance(flag, str) for flag in expected_flags
        ):
            errors.append(f"[schema] {label} expected_flags must be list[str].")
            continue
        if not isinstance(required_args, list) or not all(
            isinstance(arg, str) for arg in required_args
        ):
            errors.append(f"[schema] {label} required_args must be list[str].")
            continue

        if tier != USER_FACING_TIER:
            continue

        user_checked += 1
        script_text = script_path.read_text(encoding="utf-8")
        if not expected_flags:
            errors.append(
                f"[tier1] {rel_path} must declare at least one explicit CLI flag."
            )
            continue

        for flag in expected_flags:
            if not flag.startswith("--"):
                errors.append(f"[tier1] {rel_path} has non-long flag entry: {flag!r}")
            if flag not in script_text:
                errors.append(
                    f"[tier1] {rel_path} missing expected CLI flag marker {flag!r}."
                )

        code, output = _run_command(
            [args.python_bin, str(script_path), "--help"],
            timeout_seconds=args.timeout_seconds,
        )
        if code != 0:
            errors.append(
                f"[tier1-help] {rel_path} --help exited {code}; output={output[:240]!r}"
            )

        code, output = _run_command(
            [args.python_bin, str(script_path), INVALID_FLAG],
            timeout_seconds=args.timeout_seconds,
        )
        if code == 0:
            errors.append(
                f"[tier1-invalid] {rel_path} accepted invalid arg {INVALID_FLAG!r}; "
                "expected non-zero exit."
            )
        known_error_markers = (
            "unrecognized arguments",
            "invalid choice",
            "the following arguments are required",
        )
        if not any(marker in output for marker in known_error_markers):
            errors.append(
                f"[tier1-invalid] {rel_path} invalid-arg output missing argparse diagnostics."
            )

        if required_args:
            code, output = _run_command(
                [args.python_bin, str(script_path)],
                timeout_seconds=args.timeout_seconds,
            )
            if code == 0:
                errors.append(
                    f"[tier1-required] {rel_path} should fail without required args."
                )
            for required_arg in required_args:
                if required_arg not in output:
                    errors.append(
                        f"[tier1-required] {rel_path} missing required-arg marker "
                        f"{required_arg!r} in failure output."
                    )

    if user_checked == 0:
        errors.append("[contract] no tier1_user_facing scripts were checked.")

    if errors:
        print("[FAIL] Script interface contract checks failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(
        "[OK] Script interface contract checks passed "
        f"(scripts={len(scripts)}, tier1_checked={user_checked})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
