#!/usr/bin/env python3
"""
Replication Script: Phase 8 (Comparative Analysis)
Purpose: Measures the proximity of the Voynich structure to known historical and synthetic artifacts.
"""

import subprocess
import sys

def run_command(cmd):
    print(f"
>> Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error executing {cmd}")
        sys.exit(1)

def main():
    print("=== Replicating Phase 8: Comparative Analysis ===")
    
    # 1. Run Proximity and Uncertainty Sweep
    run_command("python3 scripts/phase8_comparative/run_proximity_uncertainty.py --iterations 100")

    # 2. Generate Word Report
    print("
>> Generating Phase 8 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 8")

    print("
[SUCCESS] Phase 8 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
