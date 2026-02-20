#!/usr/bin/env python3
"""
Replication Script: Phase 3 (Synthesis & Sufficiency)
Purpose: Tests whether non-semantic generative processes can replicate manuscript metrics.
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
    print("=== Replicating Phase 3: Synthesis & Sufficiency ===")

    # 1. Extract Glyph-level Grammar
    run_command("python3 scripts/phase3_synthesis/extract_grammar.py")

    # 2. Run core synthesis pipeline
    run_command("python3 scripts/phase3_synthesis/run_phase_3.py")

    # 3. Run Baseline Assessment
    run_command("python3 scripts/phase3_synthesis/run_baseline_assessment.py")

    # 4. Tests A, B, C (specific metric verification)
    run_command("python3 scripts/phase3_synthesis/run_test_a.py --seed 42")
    run_command("python3 scripts/phase3_synthesis/run_test_b.py")
    run_command("python3 scripts/phase3_synthesis/run_test_c.py")

    # 5. Indistinguishability (Turing) Test
    run_command("python3 scripts/phase3_synthesis/run_indistinguishability_test.py")

    # 6. Control Matching Audit (produces CONTROL_COMPARABILITY_STATUS.json)
    run_command("python3 scripts/phase3_synthesis/run_control_matching_audit.py")

    # 7. Generate Visuals
    print("\n>> Generating Synthesis Visuals...")
    run_command(
        "python3 -m support_visualization.cli.main synthesis gap-analysis"
        " core_status/phase3_synthesis/BASELINE_GAP_ANALYSIS.json"
    )

    # 8. Generate Word Report
    print("\n>> Generating Phase 3 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 3")

    print("\n[SUCCESS] Phase 3 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
