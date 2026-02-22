#!/usr/bin/env python3
"""Enforce threshold-rationale registry coverage and drift checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = PROJECT_ROOT / "configs/project/threshold_registry.json"
DEFAULT_RATIONALE = PROJECT_ROOT / "governance/THRESHOLDS_RATIONALE.md"
SCAN_ROOTS = [PROJECT_ROOT / "src", PROJECT_ROOT / "scripts"]

RATIONAL_SECTION_HEADER = "## Source-Code Hardcoded Constants"
KEYWORD_RE = re.compile(
    r"\b("
    r"threshold|cutoff|tolerance|alpha|confidence|percentile|quantile|"
    r"z[_a-z]*|p_value|significance|pass_rate|min_[a-z0-9_]+|max_[a-z0-9_]+"
    r")\b",
    re.IGNORECASE,
)
NUMBER_RE = re.compile(r"(?<![A-Za-z_])[-+]?\d+(?:\.\d+)?")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate threshold-rationale registry and detect new threshold-like "
            "hardcoded constants in source."
        )
    )
    parser.add_argument(
        "--registry",
        default=str(DEFAULT_REGISTRY),
        help=f"Path to threshold registry JSON (default: {DEFAULT_REGISTRY}).",
    )
    parser.add_argument(
        "--rationale",
        default=str(DEFAULT_RATIONALE),
        help=f"Path to THRESHOLDS_RATIONALE markdown (default: {DEFAULT_RATIONALE}).",
    )
    parser.add_argument(
        "--write-baseline",
        action="store_true",
        help="Rewrite baseline_candidates in registry from current source scan.",
    )
    return parser.parse_args()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_rationale_locations(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    locations: list[str] = []

    for raw in lines:
        line = raw.rstrip()
        if line.strip() == RATIONAL_SECTION_HEADER:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        if not line.strip().startswith("|"):
            continue

        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        if cells[0] == "Value" or cells[0].startswith("---"):
            continue

        location = cells[1].strip("` ").strip()
        if location:
            locations.append(location)
    return locations


def _scan_threshold_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel_path = path.relative_to(PROJECT_ROOT).as_posix()
            for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                code = raw.split("#", 1)[0].strip()
                if not code:
                    continue
                if not KEYWORD_RE.search(code):
                    continue
                numbers = NUMBER_RE.findall(code)
                if not numbers:
                    continue

                line_hash = hashlib.sha1(code.encode("utf-8")).hexdigest()[:16]
                candidates.append(
                    {
                        "path": rel_path,
                        "line": lineno,
                        "line_hash": line_hash,
                        "preview": code[:180],
                    }
                )
    return candidates


def _normalize_baseline_entry(entry: dict[str, Any]) -> tuple[str, str] | None:
    path = entry.get("path")
    line_hash = entry.get("line_hash")
    if not isinstance(path, str) or not path.strip():
        return None
    if not isinstance(line_hash, str) or not line_hash.strip():
        return None
    return path.strip(), line_hash.strip()


def _validate_registry(
    registry: dict[str, Any],
    rationale_locations: list[str],
    scanned_candidates: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []

    registered = registry.get("registered_constants")
    if not isinstance(registered, list) or not registered:
        errors.append("[schema] registry must include non-empty registered_constants.")
        registered = []

    baseline = registry.get("baseline_candidates")
    if not isinstance(baseline, list):
        errors.append("[schema] registry must include baseline_candidates list.")
        baseline = []

    rationale_set = set(rationale_locations)
    registered_locations: set[str] = set()

    for item in registered:
        if not isinstance(item, dict):
            errors.append("[schema] registered_constants entries must be objects.")
            continue

        location = item.get("rationale_location")
        path = item.get("path")
        expected_literals = item.get("expected_literals", [])

        if not isinstance(location, str) or not location.strip():
            errors.append("[schema] registered constant missing rationale_location.")
            continue
        location = location.strip()
        registered_locations.add(location)

        if not isinstance(path, str) or not path.strip():
            errors.append(f"[schema] registered constant {location!r} missing path.")
            continue

        file_path = PROJECT_ROOT / path
        if not file_path.exists():
            errors.append(
                f"[registered] rationale location {location!r} points to missing path {path!r}."
            )
            continue

        if not isinstance(expected_literals, list) or not all(
            isinstance(value, str) and value.strip() for value in expected_literals
        ):
            errors.append(
                f"[schema] registered constant {location!r} expected_literals must be list[str]."
            )
            continue

        text = file_path.read_text(encoding="utf-8")
        for literal in expected_literals:
            if literal not in text:
                errors.append(
                    f"[registered] {path!r} missing expected literal {literal!r} "
                    f"for rationale location {location!r}."
                )

    missing_locations = sorted(rationale_set - registered_locations)
    extra_locations = sorted(registered_locations - rationale_set)
    if missing_locations:
        errors.append(
            "[rationale] registry missing rationale locations: "
            + ", ".join(repr(item) for item in missing_locations)
        )
    if extra_locations:
        errors.append(
            "[rationale] registry contains rationale locations not in markdown table: "
            + ", ".join(repr(item) for item in extra_locations)
        )

    baseline_keys: set[tuple[str, str]] = set()
    for entry in baseline:
        if not isinstance(entry, dict):
            errors.append("[schema] baseline_candidates entries must be objects.")
            continue
        norm = _normalize_baseline_entry(entry)
        if norm is None:
            errors.append(f"[schema] invalid baseline_candidates entry: {entry!r}.")
            continue
        baseline_keys.add(norm)

    scanned_keys = {(item["path"], item["line_hash"]) for item in scanned_candidates}
    new_candidates = sorted(scanned_keys - baseline_keys)
    removed_candidates = sorted(baseline_keys - scanned_keys)

    if new_candidates:
        errors.append(
            f"[baseline] detected {len(new_candidates)} new threshold-like constants not in registry baseline."
        )
        for path, line_hash in new_candidates[:20]:
            match = next(
                (cand for cand in scanned_candidates if cand["path"] == path and cand["line_hash"] == line_hash),
                None,
            )
            if match is not None:
                errors.append(
                    "  -> "
                    f"{path}:{match['line']} hash={line_hash} code={match['preview']!r}"
                )
            else:
                errors.append(f"  -> {path} hash={line_hash}")

    if removed_candidates:
        notes.append(
            f"[baseline] {len(removed_candidates)} baseline entries no longer present in source."
        )

    notes.append(
        f"[scan] threshold candidates={len(scanned_candidates)}, baseline={len(baseline_keys)}."
    )
    return errors, notes


def _rewrite_baseline(registry_path: Path, registry: dict[str, Any], scanned: list[dict[str, Any]]) -> None:
    baseline = [
        {
            "path": item["path"],
            "line_hash": item["line_hash"],
        }
        for item in sorted(scanned, key=lambda row: (row["path"], row["line"]))
    ]
    registry["baseline_candidates"] = baseline
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    args = _parse_args()
    registry_path = Path(args.registry)
    rationale_path = Path(args.rationale)

    if not registry_path.exists():
        print(f"[FAIL] Missing registry file: {registry_path}")
        return 1
    if not rationale_path.exists():
        print(f"[FAIL] Missing rationale markdown: {rationale_path}")
        return 1

    registry = _load_json(registry_path)
    rationale_locations = _parse_rationale_locations(rationale_path)
    scanned_candidates = _scan_threshold_candidates()

    if args.write_baseline:
        _rewrite_baseline(registry_path, registry, scanned_candidates)
        print(
            "[OK] Rewrote threshold baseline "
            f"({len(scanned_candidates)} candidates) to {registry_path}."
        )
        return 0

    errors, notes = _validate_registry(
        registry=registry,
        rationale_locations=rationale_locations,
        scanned_candidates=scanned_candidates,
    )

    for note in notes:
        print(note)
    if errors:
        print("[FAIL] Threshold registry checks failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(
        "[OK] Threshold registry checks passed "
        f"(rationale_locations={len(rationale_locations)}, "
        f"threshold_candidates={len(scanned_candidates)})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
