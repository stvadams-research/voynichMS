#!/usr/bin/env python3
"""Validate governance/claim_artifact_map.md artifact paths and JSON key paths."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CLAIM_MAP = PROJECT_ROOT / "governance/claim_artifact_map.md"
CLAIM_ID_RE = re.compile(r"^\d+[a-z]?$")
BACKTICK_RE = re.compile(r"`([^`]+)`")


@dataclass
class ClaimRow:
    claim_id: str
    output_cell: str
    key_cell: str
    source_line: int


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate claim artifact paths and JSON key-path mappings."
    )
    parser.add_argument(
        "--claim-map",
        default=str(DEFAULT_CLAIM_MAP),
        help=f"Path to claim map markdown (default: {DEFAULT_CLAIM_MAP}).",
    )
    return parser.parse_args()


def _parse_claim_rows(path: Path) -> list[ClaimRow]:
    rows: list[ClaimRow] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = _split_markdown_cells(stripped)
        if len(cells) < 7:
            continue
        claim_id = cells[0]
        if not CLAIM_ID_RE.fullmatch(claim_id):
            continue
        rows.append(
            ClaimRow(
                claim_id=claim_id,
                output_cell=cells[4],
                key_cell=cells[5],
                source_line=lineno,
            )
        )
    return rows


def _split_markdown_cells(row: str) -> list[str]:
    """Split markdown table row on unescaped pipes."""
    body = row.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []

    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "|" and (i == 0 or body[i - 1] != "\\"):
            cells.append("".join(current).replace("\\|", "|").strip())
            current = []
        else:
            current.append(ch)
        i += 1

    cells.append("".join(current).replace("\\|", "|").strip())
    return cells


def _extract_paths(cell: str) -> list[str]:
    matches = [item.strip() for item in BACKTICK_RE.findall(cell) if item.strip()]
    if matches:
        return matches
    raw = cell.strip()
    if not raw:
        return []
    if "/" in raw or raw.endswith(".json") or raw.endswith(".md"):
        return [raw]
    return []


def _extract_key_paths(cell: str) -> list[str]:
    matches = [item.strip() for item in BACKTICK_RE.findall(cell) if item.strip()]
    if matches:
        return matches
    if cell.strip() in {"—", "-", ""}:
        return []
    parts = [part.strip() for part in cell.split(",") if part.strip()]
    return parts


def _split_key_path(path: str) -> list[str]:
    segments: list[str] = []
    for raw in path.split("."):
        if not raw:
            continue
        # Decompose bracket indices: "per_window[18]" → ["per_window", "18"]
        while "[" in raw:
            bracket_start = raw.index("[")
            bracket_end = raw.index("]", bracket_start)
            prefix = raw[:bracket_start]
            index = raw[bracket_start + 1 : bracket_end]
            if prefix:
                segments.append(prefix)
            segments.append(index)
            raw = raw[bracket_end + 1 :]
        if raw:
            segments.append(raw)
    return segments


def _json_key_exists(payload: Any, key_path: str) -> bool:
    segments = _split_key_path(key_path)
    if not segments:
        return False

    nodes: list[Any] = [payload]
    for segment in segments:
        next_nodes: list[Any] = []
        if segment == "*":
            for node in nodes:
                if isinstance(node, dict):
                    next_nodes.extend(node.values())
                elif isinstance(node, list):
                    next_nodes.extend(node)
        else:
            for node in nodes:
                if isinstance(node, dict):
                    if segment in node:
                        next_nodes.append(node[segment])
                elif isinstance(node, list) and segment.isdigit():
                    idx = int(segment)
                    if 0 <= idx < len(node):
                        next_nodes.append(node[idx])
        if not next_nodes:
            return False
        nodes = next_nodes
    return True


def main() -> int:
    args = _parse_args()
    claim_map_path = Path(args.claim_map)
    if not claim_map_path.exists():
        print(f"[FAIL] Claim map not found: {claim_map_path}")
        return 1

    rows = _parse_claim_rows(claim_map_path)
    if not rows:
        print(f"[FAIL] No claim rows parsed from {claim_map_path}")
        return 1

    errors: list[str] = []
    json_cache: dict[Path, Any] = {}
    checked_files: set[Path] = set()
    checked_key_paths = 0

    for row in rows:
        output_paths = _extract_paths(row.output_cell)
        if len(output_paths) != 1:
            errors.append(
                f"[row {row.claim_id}] line {row.source_line}: output file must contain exactly one path "
                f"(found {len(output_paths)} in {row.output_cell!r})."
            )
            continue

        rel_path = output_paths[0]
        artifact_path = PROJECT_ROOT / rel_path
        checked_files.add(artifact_path)
        if not artifact_path.exists():
            errors.append(
                f"[row {row.claim_id}] line {row.source_line}: missing artifact path {rel_path!r}."
            )
            continue

        if artifact_path.suffix.lower() != ".json":
            # Markdown/text artifacts are path-checked only.
            continue

        key_paths = _extract_key_paths(row.key_cell)
        if not key_paths:
            errors.append(
                f"[row {row.claim_id}] line {row.source_line}: JSON artifact requires key path; "
                f"found {row.key_cell!r}."
            )
            continue

        payload = json_cache.get(artifact_path)
        if payload is None:
            try:
                payload = json.loads(artifact_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(
                    f"[row {row.claim_id}] line {row.source_line}: invalid JSON in {rel_path!r}: {exc}."
                )
                continue
            json_cache[artifact_path] = payload

        for key_path in key_paths:
            checked_key_paths += 1
            if not _json_key_exists(payload, key_path):
                errors.append(
                    f"[row {row.claim_id}] line {row.source_line}: missing key path {key_path!r} "
                    f"in {rel_path!r}."
                )

    if errors:
        print("[FAIL] Claim artifact map validation failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    print(
        "[OK] Claim artifact map validation passed "
        f"(rows={len(rows)}, files_checked={len(checked_files)}, json_keys_checked={checked_key_paths})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
