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
    
    # 2. Run Language ID False Positive Test
    run_command("python3 scripts/phase4_inference/run_lang_id.py")
    
    # 3. Run Information Theoretic (Montemurro) Test
    run_command("python3 scripts/phase4_inference/run_montemurro.py")
    
    # 4. Run Network Feature Analysis
    run_command("python3 scripts/phase4_inference/run_network.py")

    # 5. Generate Visuals
    print("\n>> Generating Inference Visuals...")
    run_command("support_visualization inference lang-id results/data/phase4_inference/lang_id_results.json")

    # 6. Generate Word Report
    print("\n>> Generating Phase 4 Word Report...")
    run_command("python3 scripts/support_preparation/generate_publication.py --phase 4")

    print("\n[SUCCESS] Phase 4 Replication Complete. Reports saved to results/publication/")

if __name__ == "__main__":
    main()
