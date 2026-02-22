#!/usr/bin/env python3
"""
Replication Script: Phase 19 (Alignment Evaluation)
Purpose: Evaluate Phase 18 generators against held-out folios and report gains.
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
    print("=== Replicating Phase 19: Alignment Evaluation ===")

    run_command("scripts/phase19_alignment/build_folio_match_benchmark.py")
    run_command("scripts/phase19_alignment/run_19a_line_conditioned_decoder.py")
    run_command("scripts/phase19_alignment/run_19b_retrieval_edit.py")
    run_command("scripts/phase19_alignment/run_19c_alignment_eval.py")

    print("\n[SUCCESS] Phase 19 Replication Complete.")


if __name__ == "__main__":
    main()
