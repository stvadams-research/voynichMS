#!/usr/bin/env python3
"""
Replication Script: Phase 20 (State Machine Codebook Architecture)
Purpose: Reconstructs the physical production device specification from lattice data.
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
    print("=== Replicating Phase 20: State Machine Codebook Architecture ===")

    # 1. Codebook architecture
    run_command("python3 scripts/phase20_state_machine/run_20a_codebook_architecture.py")

    # 2. State merging
    run_command("python3 scripts/phase20_state_machine/run_20b_state_merging.py")

    # 3. Linear devices
    run_command("python3 scripts/phase20_state_machine/run_20c_linear_devices.py")

    # 4. Layout analysis
    run_command("python3 scripts/phase20_state_machine/run_20d_layout_analysis.py")

    # 5. Annotated device
    run_command("python3 scripts/phase20_state_machine/run_20e_annotated_device.py")

    # 6. Hand analysis
    run_command("python3 scripts/phase20_state_machine/run_20f_hand_analysis.py")

    # 7. Merged volvelle characterization
    run_command("python3 scripts/phase20_state_machine/run_20g_merged_volvelle_characterization.py")

    # 8. Production synthesis
    run_command("python3 scripts/phase20_state_machine/run_20h_production_synthesis.py")

    print("\n[SUCCESS] Phase 20 Replication Complete.")

if __name__ == "__main__":
    main()
