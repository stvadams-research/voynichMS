#!/usr/bin/env python3
"""Validate project phase manifest and top-level phase naming consistency."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = PROJECT_ROOT / "configs/project/phase_manifest.json"
DEFAULT_CLAIM_MAP = PROJECT_ROOT / "governance/claim_artifact_map.md"
TOP_LEVEL_DOCS = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "replicateResults.md",
    PROJECT_ROOT / "governance/runbook.md",
    PROJECT_ROOT / "STATUS.md",
    PROJECT_ROOT / "governance/RELEASE_SCOPE.md",
]
PHASE_TOKEN_RE = re.compile(r"\bphase\d+_[a-z0-9_]+\b")
PHASE_HEADER_RE = re.compile(r"^##\s+Phase\s+(\d+)", re.IGNORECASE)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate phase manifest schema, entrypoints, and doc naming."
    )
    parser.add_argument(
        "--manifest",
        default=str(DEFAULT_MANIFEST),
        help=f"Path to phase manifest (default: {DEFAULT_MANIFEST}).",
    )
    parser.add_argument(
        "--claim-map",
        default=str(DEFAULT_CLAIM_MAP),
        help=f"Path to claim-artifact map (default: {DEFAULT_CLAIM_MAP}).",
    )
    return parser.parse_args()


def _validate_manifest_schema(payload: dict[str, Any], manifest_path: Path) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    phases = payload.get("phases")
    if not isinstance(phases, list) or not phases:
        return [f"[schema] {manifest_path}: 'phases' must be a non-empty list."], []

    required = {"phase_id", "canonical_slug", "aliases", "release_scope", "replicate_entry"}
    known_scopes = {"release", "exploratory"}
    seen_ids: set[int] = set()
    seen_tokens: dict[str, str] = {}
    normalized: list[dict[str, Any]] = []

    for idx, raw in enumerate(phases):
        label = f"{manifest_path} phases[{idx}]"
        if not isinstance(raw, dict):
            errors.append(f"[schema] {label}: entry must be an object.")
            continue
        missing = sorted(required - set(raw))
        if missing:
            errors.append(f"[schema] {label}: missing keys {missing}.")
            continue

        phase_id = raw["phase_id"]
        canonical_slug = raw["canonical_slug"]
        aliases = raw["aliases"]
        release_scope = raw["release_scope"]
        replicate_entry = raw["replicate_entry"]

        if not isinstance(phase_id, int) or phase_id <= 0:
            errors.append(f"[schema] {label}: phase_id must be a positive integer.")
            continue
        if phase_id in seen_ids:
            errors.append(f"[schema] {label}: duplicate phase_id={phase_id}.")
            continue
        seen_ids.add(phase_id)

        if not isinstance(canonical_slug, str) or not PHASE_TOKEN_RE.fullmatch(canonical_slug):
            errors.append(
                f"[schema] {label}: canonical_slug must match 'phase<id>_<slug>' pattern."
            )
            continue

        if not isinstance(aliases, list) or not all(isinstance(item, str) for item in aliases):
            errors.append(f"[schema] {label}: aliases must be a list[str].")
            continue
        bad_aliases = [item for item in aliases if not PHASE_TOKEN_RE.fullmatch(item)]
        if bad_aliases:
            errors.append(f"[schema] {label}: invalid alias values {bad_aliases!r}.")
            continue

        if not isinstance(release_scope, str) or release_scope not in known_scopes:
            errors.append(
                f"[schema] {label}: release_scope must be one of {sorted(known_scopes)}."
            )
            continue

        if not isinstance(replicate_entry, str) or not replicate_entry.strip():
            errors.append(f"[schema] {label}: replicate_entry must be a non-empty string.")
            continue

        entry_path = PROJECT_ROOT / replicate_entry
        if not entry_path.exists():
            errors.append(
                f"[entrypoint] phase {phase_id} ({canonical_slug}) missing replicate_entry: {replicate_entry}"
            )
        elif not entry_path.is_file():
            errors.append(
                f"[entrypoint] phase {phase_id} ({canonical_slug}) replicate_entry is not a file: "
                f"{replicate_entry}"
            )

        for token in [canonical_slug, *aliases]:
            if token in seen_tokens:
                errors.append(
                    f"[schema] phase slug token {token!r} reused by both "
                    f"{seen_tokens[token]} and phase {phase_id}."
                )
            else:
                seen_tokens[token] = f"phase {phase_id} ({canonical_slug})"

        normalized.append(
            {
                "phase_id": phase_id,
                "canonical_slug": canonical_slug,
                "aliases": aliases,
                "release_scope": release_scope,
                "replicate_entry": replicate_entry,
            }
        )

    if normalized:
        ids = sorted(item["phase_id"] for item in normalized)
        expected = list(range(min(ids), max(ids) + 1))
        if ids != expected:
            errors.append(
                f"[schema] manifest phase_ids must be contiguous; found {ids}, expected {expected}."
            )

    return errors, sorted(normalized, key=lambda item: item["phase_id"])


def _extract_claim_phase_ids(claim_map_path: Path) -> set[int]:
    required: set[int] = set()
    if not claim_map_path.exists():
        return required
    for line in claim_map_path.read_text(encoding="utf-8").splitlines():
        match = PHASE_HEADER_RE.match(line.strip())
        if match:
            required.add(int(match.group(1)))
    return required


def _check_claim_phase_coverage(
    phases: list[dict[str, Any]], claim_map_path: Path
) -> list[str]:
    errors: list[str] = []
    claim_phase_ids = _extract_claim_phase_ids(claim_map_path)
    if not claim_phase_ids:
        return errors

    manifest_phase_ids = {item["phase_id"] for item in phases}
    missing = sorted(claim_phase_ids - manifest_phase_ids)
    if missing:
        errors.append(
            f"[claim-map] {claim_map_path}: claim-bearing phases missing from manifest: {missing}"
        )
    return errors


def _check_top_level_docs(phases: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    known_tokens = {
        token
        for phase in phases
        for token in [phase["canonical_slug"], *phase["aliases"]]
    }
    declared_aliases = {alias for phase in phases for alias in phase["aliases"]}

    for doc_path in TOP_LEVEL_DOCS:
        if not doc_path.exists():
            errors.append(f"[doc] missing top-level doc: {doc_path}")
            continue
        text = doc_path.read_text(encoding="utf-8")
        used_tokens = set(PHASE_TOKEN_RE.findall(text))
        unknown = sorted(
            token for token in (used_tokens - known_tokens) if not token.startswith("phase0_")
        )
        if unknown:
            errors.append(
                f"[doc] {doc_path.relative_to(PROJECT_ROOT)} uses undocumented phase tokens: {unknown}"
            )

    release_scope_doc = PROJECT_ROOT / "governance/RELEASE_SCOPE.md"
    if release_scope_doc.exists():
        release_text = release_scope_doc.read_text(encoding="utf-8")
        for alias in sorted(declared_aliases):
            if alias not in release_text:
                errors.append(
                    "[doc] governance/RELEASE_SCOPE.md must document alias mapping for "
                    f"{alias!r}."
                )

    return errors


def main() -> int:
    args = _parse_args()
    manifest_path = Path(args.manifest)
    claim_map_path = Path(args.claim_map)

    if not manifest_path.exists():
        print(f"[FAIL] Missing phase manifest: {manifest_path}")
        return 1

    payload = _load_json(manifest_path)
    errors, phases = _validate_manifest_schema(payload, manifest_path)
    errors.extend(_check_claim_phase_coverage(phases, claim_map_path))
    errors.extend(_check_top_level_docs(phases))

    if errors:
        print("[FAIL] Phase manifest checks failed:")
        for item in errors:
            print(f"  - {item}")
        return 1

    release_count = sum(1 for phase in phases if phase["release_scope"] == "release")
    exploratory_count = sum(1 for phase in phases if phase["release_scope"] == "exploratory")
    alias_count = sum(len(phase["aliases"]) for phase in phases)
    print(
        "[OK] Phase manifest checks passed "
        f"(phases={len(phases)}, release={release_count}, "
        f"exploratory={exploratory_count}, aliases={alias_count})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
