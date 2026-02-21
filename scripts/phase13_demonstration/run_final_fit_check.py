#!/usr/bin/env python3
"""
Final Fit Score: Real vs Mechanical
A final check to see how much of the Voynich 'Identity' 
the physical model accounts for.
"""

import math
import sys
from collections import Counter
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase12_mechanical.volvelle_simulator import VolvelleSimulator  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = Path("results/data/phase13_demonstration/final_fit_check.json")

def calculate_entropy(tokens):
    if not tokens:
        return 0
    counts = Counter(tokens)
    total = len(tokens)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

def main():
    print("=== Final Fit Check: Structural Identity ===")

    # 1. Real Baseline
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    real_tokens = [t for line in real_lines for t in line]
    real_entropy = calculate_entropy(real_tokens)

    # 2. Mechanical Mirror (High Fidelity)
    vocab = set(real_tokens)
    simulator = VolvelleSimulator(vocab, seed=42)
    syn_lines = simulator.generate_corpus(num_lines=5000, line_length=6)
    syn_tokens = [t for line in syn_lines for t in line]
    syn_entropy = calculate_entropy(syn_tokens)

    # 3. Fit Calculation
    fit = 1.0 - abs(real_entropy - syn_entropy) / real_entropy

    print(f"\nReal Voynich Entropy: {real_entropy:.4f}")
    print(f"Mechanical Engine Entropy: {syn_entropy:.4f}")
    print(f"Total Structural Accounted For: {fit*100:.2f}%")

    # Save Results
    results = {
        "real_entropy": real_entropy,
        "syn_entropy": syn_entropy,
        "fit_score": fit,
        "is_sufficient": fit > 0.9
    }
    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    if fit > 0.9:
        msg = "\nCONCLUSION: The physical model is SUFFICIENT to explain the structure."
        print(msg)
    else:
        msg = "\nCONCLUSION: The physical model is PARTIAL. More complexity required."
        print(msg)


if __name__ == "__main__":
    main()
