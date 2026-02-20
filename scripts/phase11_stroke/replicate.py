#!/usr/bin/env python3
"""
Replication Script: Phase 11 (Stroke Topology)
Purpose: Sub-glyph structural analysis with fast-kill gate.
"""

import subprocess
import sys


def run_command(cmd):
    print(f"\n>> Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error executing {cmd}")
        sys.exit(1)


def main():
    print("=== Replicating Phase 11: Stroke Topology ===")

    # 1. Extract corpus-wide stroke features
    run_command("python3 scripts/phase11_stroke/run_11a_extract.py")

    # 2. Cluster analysis (Test A — partial rho clustering)
    run_command(
        "python3 scripts/phase11_stroke/run_11b_cluster.py"
        " --seed 42 --permutations 10000"
    )

    # 3. Transition analysis (Test B1 — boundary mutual information)
    run_command(
        "python3 scripts/phase11_stroke/run_11c_transitions.py"
        " --seed 42 --permutations 10000"
    )

    print("\n[SUCCESS] Phase 11 Replication Complete.")
    print("  Results: results/data/phase11_stroke/")


if __name__ == "__main__":
    main()
