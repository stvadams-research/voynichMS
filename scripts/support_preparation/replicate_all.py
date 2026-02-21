#!/usr/bin/env python3
"""
MASTER REPLICATION SCRIPT
Project: Voynich Manuscript Assumption-Resistant Foundation

This script runs the entire project lifecycle from raw data to final publication draft.
Covers 17 research phases (Foundation through Physical Synthesis).
"""

import subprocess
import sys
import time
from pathlib import Path


def run_phase(phase_num, phase_path):
    print(f"\n{'='*60}")
    print(f" STARTING PHASE {phase_num}: {phase_path}")
    print(f"{'='*60}")

    script_path = Path(f"scripts/{phase_path}/replicate.py")
    if not script_path.exists():
        print(f"Error: Replication script not found for {phase_path}")
        return False

    start_time = time.time()
    result = subprocess.run(f"python3 {script_path}", shell=True)
    elapsed = time.time() - start_time

    if result.returncode == 0:
        print(f"\n[OK] Phase {phase_num} completed in {elapsed:.1f}s")
        return True
    else:
        print(f"\n[FAIL] Phase {phase_num} failed.")
        return False

def main():
    print("!!! Voynich Project: FULL MASTER REPLICATION (17 PHASES) !!!")
    print(f"Starting at: {time.ctime()}")

    # 0. Asset Verification
    print(f"\n{'='*60}")
    print(" VERIFYING EXTERNAL ASSETS (PHASE 0)")
    print(f"{'='*60}")

    verify_script = Path("scripts/phase0_data/verify_external_assets.py")
    if not verify_script.exists():
        print(f"Error: Verification script not found: {verify_script}")
        sys.exit(1)

    v_result = subprocess.run(f"python3 {verify_script}", shell=True)
    if v_result.returncode != 0:
        print("\n!!! Master Replication Aborted: Asset Verification Failed !!!")
        print("This may indicate missing external data or a script error.")
        print("Please run: python3 scripts/phase0_data/download_external_data.py")
        sys.exit(1)

    phases = [
        (1, "phase1_foundation"),
        (2, "phase2_analysis"),
        (3, "phase3_synthesis"),
        (4, "phase4_inference"),
        (5, "phase5_mechanism"),
        (6, "phase6_functional"),
        (7, "phase7_human"),
        (8, "phase8_comparative"),
        (9, "phase9_conjecture"),
        (10, "phase10_admissibility"),
        (11, "phase11_stroke"),
        (12, "phase12_mechanical"),
        (13, "phase13_demonstration"),
        (14, "phase14_machine"),
        (15, "phase15_rule_extraction"),
        (16, "phase16_physical_grounding"),
        (17, "phase17_finality"),
    ]

    for num, path in phases:
        if not run_phase(num, path):
            print("\n!!! Master Replication Aborted due to Phase Failure !!!")
            sys.exit(1)

    # Final Full Publication Synthesis
    print(f"\n{'='*60}")
    print(" GENERATING FINAL COMPREHENSIVE RESEARCH SUMMARY")
    print(f"{'='*60}")

    # Generate the full master doc (no --phase flag)
    pub_result = subprocess.run(
        "python3 scripts/support_preparation/generate_publication.py", shell=True
    )
    if pub_result.returncode != 0:
        print("\n[WARN] Publication generation returned non-zero exit code.")

    print("\n" + "#"*60)
    print("!!! MASTER REPLICATION SUCCESSFUL !!!")
    print("17 Phase Reports available in: results/publication/")
    print("#"*60 + "\n")

if __name__ == "__main__":
    main()
