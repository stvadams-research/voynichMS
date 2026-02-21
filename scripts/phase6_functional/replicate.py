#!/usr/bin/env python3
"""
Replication Script: Phase 6 (Functional Analysis)
Purpose: Evaluates the system's efficiency, exhaustion, and adversarial robustness.
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
    print("=== Replicating Phase 6: Functional Analysis ===")
    
    # 1. Run Exhaustion Tests
    run_command("python3 scripts/phase6_functional/run_6a_exhaustion.py")
    
    # 2. Run Efficiency Metrics
    run_command("python3 scripts/phase6_functional/run_6b_efficiency.py")
    
    # 3. Run Adversarial Robustness
    run_command("python3 scripts/phase6_functional/run_6c_adversarial.py")

    # 4. Generate Word Report
    print("\n>> Generating Phase 6 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 6")

    print("\n[SUCCESS] Phase 6 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
