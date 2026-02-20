#!/usr/bin/env python3
"""
Replication Script: Phase 4 (Inference Admissibility)
Purpose: Evaluates whether common decipherment methods can distinguish noise from meaning.
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
    print("=== Replicating Phase 4: Inference Admissibility ===")

    # 1. Build reference corpora
    run_command("python3 scripts/phase4_inference/build_corpora.py")

    # 2. Core methods (A-E)
    run_command("python3 scripts/phase4_inference/run_lang_id.py")        # Method D
    run_command("python3 scripts/phase4_inference/run_montemurro.py")     # Method A
    run_command("python3 scripts/phase4_inference/run_network.py")        # Method B
    run_command("python3 scripts/phase4_inference/run_morph.py")          # Method E
    run_command("python3 scripts/phase4_inference/run_topics.py")         # Method C

    # 3. Supplementary hypothesis checks
    run_command("python3 scripts/phase4_inference/run_boundary_persistence_holdout_check.py")
    run_command("python3 scripts/phase4_inference/run_boundary_persistence_sweep.py")
    run_command("python3 scripts/phase4_inference/run_boundary_persistence_section_holdout_check.py")
    run_command("python3 scripts/phase4_inference/run_line_reset_markov_check.py")
    run_command("python3 scripts/phase4_inference/run_line_reset_backoff_check.py")
    run_command("python3 scripts/phase4_inference/run_order_constraints_check.py")
    run_command("python3 scripts/phase4_inference/run_ncd_matrix_check.py")
    run_command("python3 scripts/phase4_inference/run_projection_bounded.py")
    run_command("python3 scripts/phase4_inference/run_discrimination_check.py")
    run_command("python3 scripts/phase4_inference/run_kolmogorov_proxy_check.py")
    run_command("python3 scripts/phase4_inference/run_image_encoding_hypothesis_check.py")
    run_command("python3 scripts/phase4_inference/run_music_hypothesis_check.py")
    run_command("python3 scripts/phase4_inference/run_reference_42_check.py")

    # 4. Generate Visuals
    print("\n>> Generating Inference Visuals...")
    run_command(
        "python3 -m support_visualization.cli.main inference lang-id"
        " results/data/phase4_inference/lang_id_results.json"
    )

    # 5. Generate Word Report
    print("\n>> Generating Phase 4 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 4")

    print("\n[SUCCESS] Phase 4 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
