#!/usr/bin/env python3
"""
Extract golden reference outputs from the current result artifacts.

Run this after a clean canonical replication to capture known-good values.
Stores canonicalized result payloads (provenance stripped, keys sorted) as
golden fixtures for future regression testing.

Usage:
    python3 scripts/core_audit/extract_golden_outputs.py
"""

import json
import hashlib
from pathlib import Path

GOLDEN_DIR = Path("tests/fixtures/golden")

# Key result artifacts to capture as golden outputs.
# Format: (source_path, golden_name, key_path_or_None)
# key_path: dot-separated path into the JSON to extract, or None for full results payload.
ARTIFACTS = [
    # Phase 4
    ("results/data/phase4_inference/montemurro_results.json", "phase4_montemurro", None),
    ("results/data/phase4_inference/lang_id_results.json", "phase4_lang_id", None),
    ("results/data/phase4_inference/network_results.json", "phase4_network", None),
    # Phase 5
    ("results/data/phase5_mechanism/pilot_results.json", "phase5_pilot", None),
    ("results/data/phase5_mechanism/constraint_geometry/pilot_5b_results.json", "phase5_5b", None),
    ("results/data/phase5_mechanism/workflow/pilot_5c_results.json", "phase5_5c", None),
    ("results/data/phase5_mechanism/large_object/pilot_5e_results.json", "phase5_5e", None),
    ("results/data/phase5_mechanism/topology_collapse/pilot_5g_results.json", "phase5_5g", None),
    ("results/data/phase5_mechanism/parsimony/pilot_5k_results.json", "phase5_5k", None),
    # Phase 6
    ("results/data/phase6_functional/phase_6a/phase_6a_results.json", "phase6_6a", None),
    ("results/data/phase6_functional/phase_6b/phase_6b_results.json", "phase6_6b", None),
    ("results/data/phase6_functional/phase_6c/phase_6c_results.json", "phase6_6c", None),
    # Phase 7
    ("results/data/phase7_human/phase_7a_results.json", "phase7_7a", None),
    # Phase 11
    ("results/data/phase11_stroke/test_a_clustering.json", "phase11_test_a", None),
    ("results/data/phase11_stroke/test_b_transitions.json", "phase11_test_b", None),
]


def extract_results(data: dict) -> dict:
    """Strip provenance, return only the results payload."""
    if "results" in data and "provenance" in data:
        return data["results"]
    return data


def canonicalize(payload: dict) -> str:
    """Produce a canonical JSON string for comparison."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def main() -> None:
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    extracted = 0
    skipped = 0

    for src_path, golden_name, key_path in ARTIFACTS:
        src = Path(src_path)
        if not src.exists():
            print(f"  [SKIP] {src_path} — not found")
            skipped += 1
            continue

        data = json.loads(src.read_text(encoding="utf-8"))
        payload = extract_results(data)

        if key_path:
            for key in key_path.split("."):
                payload = payload[key]

        canonical = canonicalize(payload)
        sha256 = hashlib.sha256(canonical.encode()).hexdigest()

        golden_file = GOLDEN_DIR / f"{golden_name}.json"
        golden_file.write_text(
            json.dumps(payload, sort_keys=True, indent=2, default=str),
            encoding="utf-8",
        )

        hash_file = GOLDEN_DIR / f"{golden_name}.sha256"
        hash_file.write_text(sha256 + "\n", encoding="utf-8")

        print(f"  [OK] {golden_name} — sha256:{sha256[:16]}...")
        extracted += 1

    print(f"\nExtracted {extracted} golden outputs, skipped {skipped}.")
    print(f"Golden files written to {GOLDEN_DIR}/")


if __name__ == "__main__":
    main()
