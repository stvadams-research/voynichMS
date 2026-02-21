#!/usr/bin/env python3
"""
Replication Script: Phase 2 (Analysis & Admissibility)
Purpose: Tests structural admissibility and formal exclusion of linguistic models.
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
    print("=== Replicating Phase 2: Analysis & Admissibility ===")
    
    # 1. Run Admissibility Mapping (Classes 1-4)
    for i in range(1, 5):
        run_command(f"python3 scripts/phase2_analysis/run_phase_2_{i}.py")
    
    # 2. Execute Sensitivity Sweep (Robustness Check)
    run_command("python3 scripts/phase2_analysis/run_sensitivity_sweep.py --mode smoke")

    # 3. Generate Visuals
    print("\n>> Generating Analysis Visuals...")
    # Note: Using the core_status path for sweep results
    run_command("python3 -m support_visualization.cli.main analysis sensitivity-sweep core_status/core_audit/sensitivity_sweep.json")

    # 4. Generate Word Report
    print("\n>> Generating Phase 2 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 2")

    print("\n[SUCCESS] Phase 2 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
