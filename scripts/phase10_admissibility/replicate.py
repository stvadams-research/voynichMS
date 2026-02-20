#!/usr/bin/env python3
"""
Replication Script: Phase 10 (Adversarial Admissibility Retest)
Purpose: Tests six methods (F-K) designed to defeat the Phase 4.5 closure.
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
    print("=== Replicating Phase 10: Adversarial Admissibility Retest ===")

    # Stage 1: Methods H (typology), J (steganographic), K (residual gap)
    run_command("python3 scripts/phase10_admissibility/run_stage1_hjk.py --seed 42")

    # Stage 1B: J/K replication across multiple seeds
    run_command(
        "python3 scripts/phase10_admissibility/run_stage1b_jk_replication.py"
        " --seeds 42,77,101"
    )

    # Stage 2: Methods G (illustration features), I (cross-linguistic typology)
    run_command("python3 scripts/phase10_admissibility/run_stage2_gi.py --seed 42")

    # Stage 3: Method F (generation vs encoding hypothesis)
    run_command("python3 scripts/phase10_admissibility/run_stage3_f.py --seed 42")

    # Stage 4: Synthesis (aggregates stage 1-3 outcomes)
    run_command("python3 scripts/phase10_admissibility/run_stage4_synthesis.py")

    # Stage 5: High-ROI confirmatory runs
    run_command("python3 scripts/phase10_admissibility/run_stage5_high_roi.py")

    # Stage 5B: Method K targeted adjudication
    run_command("python3 scripts/phase10_admissibility/run_stage5b_k_adjudication.py")

    print("\n[SUCCESS] Phase 10 Replication Complete.")
    print("  Results: results/reports/phase10_admissibility/")
    print("  Data:    results/data/phase10_admissibility/")


if __name__ == "__main__":
    main()
