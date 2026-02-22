#!/usr/bin/env python3
"""Validate tracked critical/non-critical unreferenced module triage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TIERS_PATH = PROJECT_ROOT / "configs/project/unreferenced_module_tiers.json"

ALLOWED_CLASSIFICATIONS = {"critical_path", "non_critical"}
ALLOWED_STATUSES = {"covered", "deferred", "waived"}
CLOSED_CRITICAL_STATUSES = {"covered", "waived"}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check unreferenced-module triage registry integrity."
    )
    parser.add_argument(
        "--tiers",
        default=str(DEFAULT_TIERS_PATH),
        help=f"Path to unreferenced module tiers JSON (default: {DEFAULT_TIERS_PATH}).",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Triage payload must be a JSON object: {path}")
    return payload


def main() -> int:
    args = _parse_args()
    tiers_path = Path(args.tiers)
    if not tiers_path.exists():
        print(f"[FAIL] Triage config not found: {tiers_path}")
        return 1

    try:
        payload = _load_json(tiers_path)
    except Exception as exc:
        print(f"[FAIL] Could not load triage config: {exc}")
        return 1

    modules = payload.get("modules")
    if not isinstance(modules, list) or not modules:
        print("[FAIL] Triage config must include a non-empty modules list.")
        return 1

    errors: list[str] = []
    seen_paths: set[str] = set()
    critical_total = 0
    closed_critical = 0
    open_critical: list[str] = []
    non_critical_total = 0

    for index, entry in enumerate(modules):
        label = f"modules[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"[schema] {label} must be an object.")
            continue

        rel_path = entry.get("path")
        classification = entry.get("classification")
        status = entry.get("status")
        test_paths = entry.get("test_paths")

        if not isinstance(rel_path, str) or not rel_path.strip():
            errors.append(f"[schema] {label} missing non-empty path.")
            continue
        rel_path = rel_path.strip()

        if rel_path in seen_paths:
            errors.append(f"[schema] duplicate module path in triage: {rel_path}")
            continue
        seen_paths.add(rel_path)

        file_path = PROJECT_ROOT / rel_path
        if not file_path.exists():
            errors.append(f"[path] missing module file: {rel_path}")

        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(
                f"[schema] {label} invalid classification={classification!r}; "
                f"expected one of {sorted(ALLOWED_CLASSIFICATIONS)}."
            )
            continue

        if status not in ALLOWED_STATUSES:
            errors.append(
                f"[schema] {label} invalid status={status!r}; "
                f"expected one of {sorted(ALLOWED_STATUSES)}."
            )
            continue

        if not isinstance(test_paths, list) or not all(
            isinstance(item, str) and item.strip() for item in test_paths
        ):
            errors.append(f"[schema] {label} test_paths must be list[str].")
            continue

        if classification == "critical_path":
            critical_total += 1
            if status in CLOSED_CRITICAL_STATUSES:
                closed_critical += 1
            else:
                open_critical.append(rel_path)

            if status == "covered":
                if not test_paths:
                    errors.append(
                        f"[critical] covered critical module requires test_paths: {rel_path}"
                    )
                for test_rel in test_paths:
                    if not (PROJECT_ROOT / test_rel).exists():
                        errors.append(
                            f"[critical] missing test path for {rel_path}: {test_rel}"
                        )
        else:
            non_critical_total += 1

    if open_critical:
        errors.append(
            "[critical] open critical-path unreferenced modules remain: "
            + ", ".join(open_critical)
        )

    if errors:
        print("[FAIL] Unreferenced-module tier checks failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(
        "[OK] Unreferenced-module tiers validated "
        f"(modules={len(modules)}, critical={critical_total}, "
        f"critical_closed={closed_critical}, critical_open={len(open_critical)}, "
        f"non_critical={non_critical_total})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
