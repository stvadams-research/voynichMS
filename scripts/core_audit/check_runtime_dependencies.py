#!/usr/bin/env python3
"""
Runtime dependency preflight check.

Fails fast when critical runtime imports are missing so long-running CI or
replication commands do not fail deep into execution.
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys

REQUIRED_IMPORTS: list[tuple[str, str]] = [
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("sklearn", "scikit-learn"),
    ("networkx", "networkx"),
    ("Levenshtein", "python-Levenshtein"),
    ("pydantic", "pydantic"),
    ("sqlalchemy", "SQLAlchemy"),
    ("PIL", "Pillow"),
    ("cv2", "opencv-python"),
    ("yaml", "PyYAML"),
    ("rich", "rich"),
    ("typer", "typer"),
]


def _check_imports() -> list[tuple[str, str, str]]:
    missing: list[tuple[str, str, str]] = []
    for module_name, package_name in REQUIRED_IMPORTS:
        try:
            importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - preflight should catch all import errors
            missing.append((module_name, package_name, f"{type(exc).__name__}: {exc}"))
    return missing


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check critical runtime Python imports.")
    parser.add_argument(
        "--mode",
        choices=["ci", "verify", "release", "manual"],
        default="manual",
        help="Context label used in output messages.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    missing = _check_imports()

    if not missing:
        print(
            f"[OK] Runtime dependency preflight passed for mode={args.mode} "
            f"({len(REQUIRED_IMPORTS)} imports validated)."
        )
        return 0

    print(f"[FAIL] Runtime dependency preflight failed for mode={args.mode}.")
    print("Missing or broken imports:")
    for module_name, package_name, err in missing:
        print(f"  - import {module_name!r} (package {package_name!r}): {err}")

    if not os.environ.get("VIRTUAL_ENV"):
        print("\nNote: no active virtual environment detected (VIRTUAL_ENV is unset).")

    missing_packages = sorted({package_name for _, package_name, _ in missing})
    print("\nRemediation:")
    print("  1) Exact reproduction environment:")
    print("     pip install -r requirements-lock.txt")
    print("  2) Compatible environment:")
    print("     pip install -r requirements.txt")
    print("  3) Minimal install for currently missing packages:")
    print(f"     pip install {' '.join(missing_packages)}")
    print(f"  4) Python executable used for this check: {sys.executable}")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
