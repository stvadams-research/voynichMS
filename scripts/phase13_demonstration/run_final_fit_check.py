#!/usr/bin/env python3
"""
Final Fit Score: Real vs Mechanical
A final check to see how much of the Voynich 'Identity' 
the physical model accounts for.
"""

import sys
import json
from pathlib import Path
from collections import Counter
import math

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter
from phase12_mechanical.volvelle_simulator import VolvelleSimulator

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = Path("results/data/phase13_demonstration/final_fit_check.json")

def calculate_entropy(tokens):
    if not tokens: return 0
    counts = Counter(tokens)
    total = len(tokens)
    return -sum((c/total) * math.log2(c/total) for c in counts.values() if c > 0)

def main():
    print("Running Final Mechanical Fit-Score...")
    
    # 1. Real Baseline
    store = MetadataStore(DB_PATH)
    real_lines = get_lines_from_store(store, "voynich_real")
    real_tokens = [t for l in real_lines for t in l]
    real_entropy = calculate_entropy(real_tokens)
    
    # 2. Reconstructed Engine
    # We use the top 100 words as our reconstructed palette
    vocab = [v[0] for v in Counter(real_tokens).most_common(100)]
    simulator = VolvelleSimulator(vocab, seed=42)
    syn_lines = simulator.generate_corpus(num_lines=5000, line_length=6)
    syn_tokens = [t for l in syn_lines for t in l]
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
        print("\nCONCLUSION: The physical model is SUFFICIENT to explain the manuscript's structure.")
    else:
        print("\nCONCLUSION: The physical model is PARTIAL. More rings or a larger palette are required for 100% fit.")

if __name__ == "__main__":
    main()
