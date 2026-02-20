#!/usr/bin/env python3
"""
Compare current result artifacts against golden reference outputs.

Golden files are created by extract_golden_outputs.py and stored in
tests/fixtures/golden/. This script checks that current outputs match
within documented tolerances.

Usage:
    python3 scripts/core_audit/check_golden_outputs.py
    python3 scripts/core_audit/check_golden_outputs.py --tolerance 1e-6

Exit codes:
    0 = all golden outputs match
    1 = one or more mismatches detected
    2 = no golden outputs found (run extract_golden_outputs.py first)
"""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

GOLDEN_DIR = Path("tests/fixtures/golden")

# Same artifact list as extract_golden_outputs.py
ARTIFACTS = [
    ("results/data/phase4_inference/montemurro_results.json", "phase4_montemurro"),
    ("results/data/phase4_inference/lang_id_results.json", "phase4_lang_id"),
    ("results/data/phase4_inference/network_results.json", "phase4_network"),
    ("results/data/phase5_mechanism/pilot_results.json", "phase5_pilot"),
    ("results/data/phase5_mechanism/constraint_geometry/pilot_5b_results.json", "phase5_5b"),
    ("results/data/phase5_mechanism/workflow/pilot_5c_results.json", "phase5_5c"),
    ("results/data/phase5_mechanism/large_object/pilot_5e_results.json", "phase5_5e"),
    ("results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json", "phase5_5g"),
    ("results/data/phase5_mechanism/parsimony/pilot_5k_results.json", "phase5_5k"),
    ("results/data/phase6_functional/phase_6a/phase_6a_results.json", "phase6_6a"),
    ("results/data/phase6_functional/phase_6b/phase_6b_results.json", "phase6_6b"),
    ("results/data/phase6_functional/phase_6c/phase_6c_results.json", "phase6_6c"),
    ("results/data/phase7_human/phase_7a_results.json", "phase7_7a"),
    ("results/data/phase11_stroke/test_a_clustering.json", "phase11_test_a"),
    ("results/data/phase11_stroke/test_b_transitions.json", "phase11_test_b"),
]


def extract_results(data: dict) -> dict:
    if "results" in data and "provenance" in data:
        return data["results"]
    return data


def canonicalize(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def values_close(a, b, tol: float) -> bool:
    """Check if two values are close, handling nested structures."""
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(values_close(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        return all(values_close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if math.isnan(a) and math.isnan(b):
            return True
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


def main() -> None:
    parser = argparse.ArgumentParser(description="Check golden reference outputs.")
    parser.add_argument(
        "--tolerance", type=float, default=1e-10,
        help="Relative tolerance for floating-point comparison (default: 1e-10).",
    )
    parser.add_argument(
        "--hash-only", action="store_true",
        help="Only check SHA-256 hashes (exact match, no tolerance).",
    )
    args = parser.parse_args()

    golden_files = list(GOLDEN_DIR.glob("*.json"))
    if not golden_files:
        print(f"No golden outputs found in {GOLDEN_DIR}/.")
        print("Run extract_golden_outputs.py after a canonical replication first.")
        sys.exit(2)

    passed = 0
    failed = 0
    skipped = 0

    for src_path, golden_name in ARTIFACTS:
        golden_file = GOLDEN_DIR / f"{golden_name}.json"
        hash_file = GOLDEN_DIR / f"{golden_name}.sha256"
        src = Path(src_path)

        if not golden_file.exists():
            print(f"  [SKIP] {golden_name} — no golden file")
            skipped += 1
            continue

        if not src.exists():
            print(f"  [SKIP] {golden_name} — source {src_path} not found")
            skipped += 1
            continue

        golden_data = json.loads(golden_file.read_text(encoding="utf-8"))
        current_data = json.loads(src.read_text(encoding="utf-8"))
        current_payload = extract_results(current_data)

        if args.hash_only or hash_file.exists():
            current_canonical = canonicalize(current_payload)
            current_hash = hashlib.sha256(current_canonical.encode()).hexdigest()

            if hash_file.exists():
                expected_hash = hash_file.read_text(encoding="utf-8").strip()
                if current_hash == expected_hash:
                    print(f"  [OK] {golden_name} — hash match")
                    passed += 1
                    continue
                elif args.hash_only:
                    print(f"  [FAIL] {golden_name} — hash mismatch")
                    print(f"         expected: {expected_hash[:32]}...")
                    print(f"         got:      {current_hash[:32]}...")
                    failed += 1
                    continue
                # Fall through to tolerance check

        if values_close(current_payload, golden_data, args.tolerance):
            print(f"  [OK] {golden_name} — values match (tol={args.tolerance})")
            passed += 1
        else:
            print(f"  [FAIL] {golden_name} — values differ beyond tolerance {args.tolerance}")
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed, {skipped} skipped.")

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
