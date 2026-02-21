#!/usr/bin/env python3
"""
Replication Script: Phase 17 (Finality)
Purpose: Generates physical blueprints and performs the final bandwidth audit.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    print(f"\n>> Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error executing {cmd}")
        sys.exit(1)

def main():
    print("=== Replicating Phase 17: Finality & Synthesis ===")
    
    # 1. Blueprints
    run_command("python3 scripts/phase17_finality/run_17a_generate_blueprints.py")
    
    # 2. Bandwidth
    run_command("python3 scripts/phase17_finality/run_17b_bandwidth_audit.py")

    # 3. Generate Word Report
    print("\n>> Generating Phase 17 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 17")

    print("\n[SUCCESS] Phase 17 Replication Complete.")

if __name__ == "__main__":
    main()
