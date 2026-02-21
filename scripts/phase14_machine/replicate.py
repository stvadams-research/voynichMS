#!/usr/bin/env python3
"""
Replication Script: Phase 14 (Voynich Engine)
Purpose: Automates the full-scale machine reconstruction and formal verification.
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    print(f"\n>> Executing: {cmd}")
    # Fix: Ensure we use the virtualenv python
    if cmd.startswith("python3"):
        cmd = cmd.replace("python3", "./.venv/bin/python3")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"Error executing {cmd}")
        sys.exit(1)

def main():
    print("=== Replicating Phase 14: Voynich Engine ===")
    
    # 1. Reconstruction
    run_command("python3 scripts/phase14_machine/run_14a_palette_solver.py")
    run_command("python3 scripts/phase14_machine/run_14b_state_discovery.py")
    
    # 2. Validation
    run_command("python3 scripts/phase14_machine/run_14c_mirror_corpus.py")
    run_command("python3 scripts/phase14_machine/run_14d_overgeneration_audit.py")
    run_command("python3 scripts/phase14_machine/run_14e_mdl_analysis.py")
    run_command("python3 scripts/phase14_machine/run_14f_noise_register.py")
    run_command("python3 scripts/phase14_machine/run_14g_holdout_validation.py")
    run_command("python3 scripts/phase14_machine/run_14h_baseline_showdown.py")
    run_command("python3 scripts/phase14_machine/run_14i_ablation_study.py")
    run_command("python3 scripts/phase14_machine/run_14j_sequence_audit.py")
    run_command("python3 scripts/phase14_machine/run_14k_failure_viz.py")
    
    # 3. Canonical Evaluation
    run_command("python3 scripts/phase14_machine/run_14l_canonical_metrics.py")
    run_command("python3 scripts/phase14_machine/run_14m_refined_mdl.py")
    run_command("python3 scripts/phase14_machine/run_14n_chance_calibration.py")
    
    # 4. Logic Export
    run_command("python3 scripts/phase14_machine/run_14o_export_logic.py")

    # 5. Generate Word Report
    print("\n>> Generating Phase 14 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 14")

    print("\n[SUCCESS] Phase 14 Replication Complete.")

if __name__ == "__main__":
    main()
