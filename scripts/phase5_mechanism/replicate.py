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

    # 1. Mechanism Pilot (iterative collapse baseline)
    run_command("python3 scripts/phase5_mechanism/run_pilot.py")

    # 2. Mechanism signature pilots (5b-5k)
    run_command("python3 scripts/phase5_mechanism/run_5b_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5c_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5d_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5e_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5f_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5g_pilot.py")   # Topology assessment
    run_command("python3 scripts/phase5_mechanism/run_5j_pilot.py")
    run_command("python3 scripts/phase5_mechanism/run_5k_pilot.py")   # Parsimony collapse (key kill-step)

    # 3. Anchor generation, coverage audit, and coupling test
    run_command(
        "python3 scripts/phase5_mechanism/generate_all_anchors.py"
        " --dataset-id voynich_real --method-name geometric_v1 --threshold 0.10"
    )
    run_command("python3 scripts/phase5_mechanism/audit_anchor_coverage.py")
    run_command("python3 scripts/phase5_mechanism/run_5i_anchor_coupling.py")

    # 4. Supplementary 5i analyses
    run_command("python3 scripts/phase5_mechanism/run_5i_lattice_overlap.py")
    run_command("python3 scripts/phase5_mechanism/run_5i_sectional_profiling.py")

    # 5. Section categorization and region generation
    run_command("python3 scripts/phase5_mechanism/categorize_sections.py")
    run_command("python3 scripts/phase5_mechanism/generate_all_regions.py")

    # 6. Generate Word Report
    print("\n>> Generating Phase 5 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 5")

    print("\n[SUCCESS] Phase 5 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
