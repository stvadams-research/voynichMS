#!/usr/bin/env python3
"""Check runner-level provenance contract compliance (SK-C2.2)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_POLICY_PATH = PROJECT_ROOT / "configs/audit/provenance_runner_contract.json"


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing policy file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Policy must be JSON object: {path}")
    return payload


def _as_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _resolve_run_scripts(root: Path, run_glob: str) -> List[Path]:
    return sorted(p for p in root.glob(run_glob) if p.is_file())


def run_checks(policy: Dict[str, Any], *, root: Path, mode: str) -> List[str]:
    errors: List[str] = []

    run_glob = str(policy.get("run_glob", "scripts/**/run_*.py"))
    direct_required_symbol = str(policy.get("direct_required_symbol", "ProvenanceWriter"))
    display_only = set(_as_list(policy.get("display_only_exemptions")))
    delegated = {
        str(k): _as_dict(v)
        for k, v in _as_dict(policy.get("delegated_provenance")).items()
    }

    run_files = _resolve_run_scripts(root, run_glob)
    if not run_files:
        errors.append(f"[policy] no runner files matched run_glob={run_glob!r}")
        return errors

    run_relpaths = {p.relative_to(root).as_posix() for p in run_files}

    for rel in sorted(display_only):
        path = root / rel
        if not path.exists():
            errors.append(f"[policy] display-only exemption path missing: {rel}")
        if rel in delegated:
            errors.append(f"[policy] path declared as both display-only and delegated: {rel}")

    for rel, spec in sorted(delegated.items()):
        path = root / rel
        if not path.exists():
            errors.append(f"[policy] delegated runner path missing: {rel}")
            continue

        module_rel = str(spec.get("module_path", "")).strip()
        if not module_rel:
            errors.append(f"[policy] delegated runner missing module_path: {rel}")
        elif not (root / module_rel).exists():
            errors.append(
                f"[policy] delegated module missing for {rel}: {module_rel}"
            )

        if rel not in run_relpaths:
            errors.append(
                f"[policy] delegated entry does not match run_glob/run_*.py set: {rel}"
            )

    for rel in sorted(display_only):
        if rel not in run_relpaths and (root / rel).exists():
            errors.append(
                f"[policy] display-only entry does not match run_glob/run_*.py set: {rel}"
            )

    for script_path in run_files:
        rel = script_path.relative_to(root).as_posix()
        script_text = script_path.read_text(encoding="utf-8")

        if rel in display_only:
            continue

        if rel in delegated:
            spec = delegated[rel]
            modes = set(_as_list(spec.get("modes")))
            if modes and mode not in modes:
                errors.append(
                    f"[delegated-mode] {rel}: delegation not approved for mode={mode}"
                )

            for marker in _as_list(spec.get("required_script_markers")):
                if marker not in script_text:
                    errors.append(
                        f"[delegated-script-marker] {rel}: missing marker `{marker}`"
                    )

            module_rel = str(spec.get("module_path", "")).strip()
            if module_rel:
                module_path = root / module_rel
                if module_path.exists():
                    module_text = module_path.read_text(encoding="utf-8")
                    required_symbol = str(
                        spec.get("module_required_symbol", direct_required_symbol)
                    )
                    if required_symbol not in module_text:
                        errors.append(
                            f"[delegated-module-symbol] {rel}: delegated module "
                            f"`{module_rel}` missing `{required_symbol}`"
                        )
            continue

        if direct_required_symbol not in script_text:
            errors.append(
                f"[missing-direct-provenance] {rel}: missing `{direct_required_symbol}` and "
                "not declared as display-only or delegated"
            )

    return sorted(errors)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check provenance runner contract policy compliance."
    )
    parser.add_argument(
        "--policy-path",
        default=str(DEFAULT_POLICY_PATH),
        help="Path to provenance runner contract policy JSON.",
    )
    parser.add_argument(
        "--root",
        default=str(PROJECT_ROOT),
        help="Repository root for resolving policy paths.",
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
        policy = _read_json(policy_path)
    except Exception as exc:
        print(f"[FAIL] could not read provenance runner policy: {exc}")
        return 1

    errors = run_checks(policy, root=root, mode=args.mode)
    if errors:
        print(f"[FAIL] provenance runner contract violations (mode={args.mode}):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"[OK] provenance runner contract checks passed (mode={args.mode}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
