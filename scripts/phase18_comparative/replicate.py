#!/usr/bin/env python3
"""
Replication Script: Phase 18 (Comparative Signature Program)
Purpose: Build structural signatures and cross-manuscript discrimination outputs.
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_command(*parts: str) -> None:
    command = [sys.executable, *parts]
    print(f"\n>> Executing: {' '.join(command)}")
    result = subprocess.run(command, cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Error executing {' '.join(parts)} (exit={result.returncode})")


def main() -> None:
    print("=== Replicating Phase 18: Comparative Signature Program ===")

    run_command("scripts/phase18_generate/build_page_generation_assets.py")
    run_command("scripts/phase18_comparative/run_18a_signature_battery.py")
    run_command("scripts/phase18_comparative/run_18b_corpus_ingestion.py")
    run_command("scripts/phase18_comparative/run_18c_comparative_analysis.py")

    print("\n[SUCCESS] Phase 18 Replication Complete.")


if __name__ == "__main__":
    main()
