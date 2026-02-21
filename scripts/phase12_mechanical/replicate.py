#!/usr/bin/env python3
"""
Replication Script: Phase 12 (Mechanical Reconstruction)
Purpose: Automates vertical slip detection and physical columnar grid inference.
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
    print("=== Replicating Phase 12: Mechanical Reconstruction ===")
    
    # 1. Detection
    run_command("python3 scripts/phase12_mechanical/run_12a_slip_detection.py")
    
    # 2. Inference
    run_command("python3 scripts/phase12_mechanical/run_12b_cluster_analysis.py")
    run_command("python3 scripts/phase12_mechanical/run_12c_geometry_inference.py")
    
    # 3. Validation
    run_command("python3 scripts/phase12_mechanical/run_12e_prototype_validation.py")
    
    # 4. Synthesis
    run_command("python3 scripts/phase12_mechanical/run_12i_blueprint_synthesis.py")

    # 5. Generate Word Report
    print("\n>> Generating Phase 12 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 12")

    print("\n[SUCCESS] Phase 12 Replication Complete.")

if __name__ == "__main__":
    main()
