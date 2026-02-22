#!/usr/bin/env python3
"""
MASTER REPLICATION SCRIPT
Project: Voynich Manuscript Assumption-Resistant Foundation

Runs the project lifecycle from raw data through publication synthesis.
Phase orchestration is sourced from configs/project/phase_manifest.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = PROJECT_ROOT / "configs/project/phase_manifest.json"
VERIFY_SCRIPT = PROJECT_ROOT / "scripts/phase0_data/verify_external_assets.py"
PUBLICATION_SCRIPT = PROJECT_ROOT / "scripts/support_preparation/generate_publication.py"
RELEASE_SCOPE = "release"
EXPLORATORY_SCOPE = "exploratory"


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing phase manifest: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    phases = payload.get("phases")
    if not isinstance(phases, list) or len(phases) == 0:
        raise ValueError("Phase manifest must define a non-empty 'phases' list.")

    required = {"phase_id", "canonical_slug", "aliases", "release_scope", "replicate_entry"}
    ordered: list[dict[str, Any]] = []
    for entry in phases:
        if not isinstance(entry, dict):
            raise ValueError("Each manifest phase entry must be an object.")
        missing = sorted(required - set(entry.keys()))
        if missing:
            raise ValueError(
                f"Manifest phase entry missing required keys {missing}: {entry!r}"
            )
        ordered.append(entry)

    return sorted(ordered, key=lambda item: int(item["phase_id"]))


def _selected_phases(
    phases: list[dict[str, Any]], *, include_exploratory: bool
) -> list[dict[str, Any]]:
    allowed_scopes = {RELEASE_SCOPE}
    if include_exploratory:
        allowed_scopes.add(EXPLORATORY_SCOPE)

    selected = [phase for phase in phases if str(phase["release_scope"]) in allowed_scopes]
    if not selected:
        raise ValueError("No phases selected from manifest for requested scope.")
    return selected


def _run_command(command: list[str]) -> int:
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    return int(result.returncode)


def run_phase(phase: dict[str, Any]) -> bool:
    phase_id = phase["phase_id"]
    slug = phase["canonical_slug"]
    scope = phase["release_scope"]
    entry = PROJECT_ROOT / str(phase["replicate_entry"])

    print(f"\n{'='*60}")
    print(f" STARTING PHASE {phase_id}: {slug} [{scope}]")
    print(f"{'='*60}")

    if not entry.exists():
        print(f"Error: Replication entrypoint not found for phase {phase_id}: {entry}")
        return False

    start_time = time.time()
    returncode = _run_command([sys.executable, str(entry)])
    elapsed = time.time() - start_time

    if returncode == 0:
        print(f"\n[OK] Phase {phase_id} completed in {elapsed:.1f}s")
        return True

    print(f"\n[FAIL] Phase {phase_id} failed (exit={returncode}).")
    return False


def _verify_assets() -> None:
    print(f"\n{'='*60}")
    print(" VERIFYING EXTERNAL ASSETS (PHASE 0)")
    print(f"{'='*60}")

    if not VERIFY_SCRIPT.exists():
        raise FileNotFoundError(f"Verification script not found: {VERIFY_SCRIPT}")

    if _run_command([sys.executable, str(VERIFY_SCRIPT)]) != 0:
        raise RuntimeError(
            "Master replication aborted: asset verification failed. "
            "Run scripts/phase0_data/download_external_data.py."
        )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run manifest-driven master replication for VoynichMS phases."
    )
    parser.add_argument(
        "--include-exploratory",
        action="store_true",
        help="Include exploratory phases (currently 18-19) in addition to release phases.",
    )
    parser.add_argument(
        "--manifest",
        default=str(MANIFEST_PATH),
        help=f"Path to phase manifest (default: {MANIFEST_PATH}).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    manifest_path = Path(args.manifest)
    phases = _load_manifest(manifest_path)
    selected = _selected_phases(phases, include_exploratory=args.include_exploratory)

    release_count = sum(1 for item in selected if item["release_scope"] == RELEASE_SCOPE)
    exploratory_count = sum(1 for item in selected if item["release_scope"] == EXPLORATORY_SCOPE)

    print("!!! Voynich Project: MANIFEST-DRIVEN MASTER REPLICATION !!!")
    print(f"Starting at: {time.ctime()}")
    print(f"Manifest: {manifest_path}")
    print(
        "Selected phases: "
        f"{len(selected)} (release={release_count}, exploratory={exploratory_count})"
    )

    _verify_assets()

    for phase in selected:
        if not run_phase(phase):
            print("\n!!! Master Replication Aborted due to Phase Failure !!!")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(" GENERATING FINAL COMPREHENSIVE RESEARCH SUMMARY")
    print(f"{'='*60}")

    if _run_command([sys.executable, str(PUBLICATION_SCRIPT)]) != 0:
        print("\n[WARN] Publication generation returned non-zero exit code.")

    print("\n" + "#" * 60)
    print("!!! MASTER REPLICATION SUCCESSFUL !!!")
    print(
        f"{release_count} release-canonical phases completed"
        + (
            f"; {exploratory_count} exploratory phases included."
            if exploratory_count
            else "."
        )
    )
    print("Phase reports available under: results/publication/")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
