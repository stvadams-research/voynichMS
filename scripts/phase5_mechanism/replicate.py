#!/usr/bin/env python3
"""
Replication Script: Phase 5 (Mechanism Identification)
Purpose: Identifies the specific mechanical process class that generated the text.
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
    print("=== Replicating Phase 5: Mechanism Identification ===")
    
    # 1. Run the Mechanism Pilot (Iterative Collapse)
    run_command("python3 scripts/phase5_mechanism/run_pilot.py")
    
    # 2. Test External Anchoring (Illustration Coupling)
    run_command("python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py")
    
    # 3. Final Topology Assessment
    run_command("python3 scripts/phase5_mechanism/run_5g_pilot.py")

    # 4. Generate Word Report
    print("\n>> Generating Phase 5 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 5")

    print("\n[SUCCESS] Phase 5 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
