#!/usr/bin/env python3
"""
Replication Script: Phase 1 (Foundation)
Purpose: Establishes the digital ledger, ingests raw scans, and verifies data integrity.
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
    print("=== Replicating Phase 1: Foundation ===")
    
    # 1. Initialize and Verify Database
    run_command("python3 scripts/phase1_foundation/acceptance_test.py")
    
    # 2. Populate standard datasets
    run_command("python3 scripts/phase1_foundation/populate_database.py")
    
    # 3. Verify Ledger Determinism
    run_command("python3 scripts/phase1_foundation/run_destructive_audit.py")

    # 4. Generate Visuals
    print("\n>> Generating Foundation Visuals...")
    run_command("support_visualization foundation token-frequency voynich_real")
    run_command("support_visualization foundation repetition-rate voynich_real")

    # 5. Generate Word Report
    print("\n>> Generating Phase 1 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 1")

    print("\n[SUCCESS] Phase 1 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
