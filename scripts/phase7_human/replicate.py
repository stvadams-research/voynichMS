#!/usr/bin/env python3
"""
Replication Script: Phase 7 (Human Factors & Codicology)
Purpose: Analyzes the physical and ergonomic constraints of the manuscript's creation.
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
    print("=== Replicating Phase 7: Human Factors ===")

    # 1. Run Human Factors Analysis
    run_command("python3 scripts/phase7_human/run_7a_human_factors.py")

    # 2. Run Codicological Audit
    run_command("python3 scripts/phase7_human/run_7b_codicology.py")

    # 3. Comparative Scribe Analysis
    run_command("python3 scripts/phase7_human/run_7c_comparative.py")

    # 4. Generate Word Report
    print("\n>> Generating Phase 7 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 7")

    print("\n[SUCCESS] Phase 7 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
