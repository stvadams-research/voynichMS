#!/usr/bin/env python3
"""
Replication Script: Phase 13 (Demonstration)
Purpose: Generates the evidence gallery and exports data for interactive visualization.
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
    print("=== Replicating Phase 13: Demonstration ===")
    
    # 1. Evidence Gallery
    run_command("python3 scripts/phase13_demonstration/generate_evidence_gallery.py")
    
    # 2. Fit Check
    run_command("python3 scripts/phase13_demonstration/run_final_fit_check.py")
    
    # 3. Viz Export
    run_command("python3 scripts/phase13_demonstration/export_slip_viz.py")

    # 4. Generate Word Report
    print("\n>> Generating Phase 13 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 13")

    print("\n[SUCCESS] Phase 13 Replication Complete.")

if __name__ == "__main__":
    main()
