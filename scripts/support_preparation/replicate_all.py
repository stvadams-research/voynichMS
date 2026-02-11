#!/usr/bin/env python3
"""
MASTER REPLICATION SCRIPT
Project: Voynich Manuscript Assumption-Resistant Foundation

This script runs the entire project lifecycle from raw data to final publication draft.
Covers all 9 research phases (Foundation through Conjecture).
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
    phases = [
        (1, "phase1_foundation"),
        (2, "phase2_analysis"),
        (3, "phase3_synthesis"),
        (4, "phase4_inference"),
        (5, "phase5_mechanism"),
        (6, "phase6_functional"),
        (7, "phase7_human"),
        (8, "phase8_comparative"),
        (9, "phase9_conjecture")
    ]
    
    print("!!! Voynich Project: FULL MASTER REPLICATION (9 PHASES) !!!")
    print(f"Starting at: {time.ctime()}")
    
    for num, path in phases:
        if not run_phase(num, path):
            print("\n!!! Master Replication Aborted due to Phase Failure !!!")
            sys.exit(1)
            
    # Final Full Publication Synthesis
    print(f"\n{'='*60}")
    print(" GENERATING FINAL COMPREHENSIVE RESEARCH SUMMARY")
    print(f"{'='*60}")
    
    # Generate the full master doc (no --phase flag)
    subprocess.run("python3 scripts/support_preparation/generate_publication.py", shell=True)
    # Also generate the master markdown
    subprocess.run("python3 scripts/support_preparation/assemble_draft.py", shell=True)
    
    print("\n" + "#"*60)
    print("!!! MASTER REPLICATION SUCCESSFUL !!!")
    print(f"9 Phase Reports and Master Draft available in: results/publication/")
    print("#"*60 + "\n")

if __name__ == "__main__":
    main()
