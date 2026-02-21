#!/usr/bin/env python3
"""
Replication Script: Phase 15 (Instrumented Choice & Rule Extraction)
Purpose: Traces within-window selection decisions and extracts scribal bias rules.
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
    print("=== Replicating Phase 15: Instrumented Choice & Rule Extraction ===")

    # 1. Trace Instrumentation (choice stream)
    run_command("python3 scripts/phase15_rule_extraction/run_15a_trace_instrumentation.py")

    # 2. Rule Extraction
    run_command("python3 scripts/phase15_rule_extraction/run_15b_extract_rules.py")

    # 3. Bias and Compressibility
    run_command("python3 scripts/phase15_rule_extraction/run_15c_bias_and_compressibility.py")

    # 4. Selection Drivers
    run_command("python3 scripts/phase15_rule_extraction/run_15d_selection_drivers.py")

    print("\n[SUCCESS] Phase 15 Replication Complete.")


if __name__ == "__main__":
    main()
