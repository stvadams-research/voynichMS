#!/usr/bin/env python3
"""
Replication Script: Phase 16 (Physical Grounding)
Purpose: Tests ergonomic coupling and geometric layout optimization of the engine.
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
    print("=== Replicating Phase 16: Physical Grounding ===")

    # 1. Ergonomic Costing
    run_command("python3 scripts/phase16_physical_grounding/run_16a_ergonomic_costing.py")

    # 2. Effort Correlation
    run_command("python3 scripts/phase16_physical_grounding/run_16b_effort_correlation.py")

    # 3. Layout Projection
    run_command("python3 scripts/phase16_physical_grounding/run_16c_layout_projection.py")

    print("\n[SUCCESS] Phase 16 Replication Complete.")


if __name__ == "__main__":
    main()
