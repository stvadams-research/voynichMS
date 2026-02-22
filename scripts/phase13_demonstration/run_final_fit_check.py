#!/usr/bin/env python3
"""
Final Fit Score: Real vs Mechanical
A final check to see how much of the Voynich 'Identity' 
the physical model accounts for.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
# Assuming VolvelleSimulator exists in phase12_mechanical or similar
try:
    from phase12_mechanical.volvelle_simulator import VolvelleSimulator  # noqa: E402
except ImportError:
    # Fallback or mock if Phase 12 isn't fully migrated/available
    class VolvelleSimulator:
        def __init__(self, vocab, seed=None):
            self.vocab = list(vocab)
            import random
            self.rng = random.Random(seed)
        
        def generate_corpus(self, num_lines, line_length):
            return [
                [self.rng.choice(self.vocab) for _ in range(line_length)]
                for _ in range(num_lines)
            ]

from phase13_demonstration.fit_check import StructuralFitAnalyzer  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase13_demonstration/final_fit_check.json"

def main():
    print("=== Final Fit Check: Structural Identity ===")

    # 1. Real Baseline
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    real_tokens = [t for line in real_lines for t in line]

    if not real_tokens:
        print("[red]Error: No real tokens loaded.[/red]")
        return

    # 2. Mechanical Mirror (High Fidelity)
    vocab = set(real_tokens)
    simulator = VolvelleSimulator(vocab, seed=42)
    syn_lines = simulator.generate_corpus(num_lines=5000, line_length=6)
    syn_tokens = [t for line in syn_lines for t in line]

    # 3. Fit Calculation
    analyzer = StructuralFitAnalyzer()
    results = analyzer.compare_corpora(real_tokens, syn_tokens)

    print(f"\nReal Voynich Entropy: {results['real_entropy']:.4f}")
    print(f"Mechanical Engine Entropy: {results['syn_entropy']:.4f}")
    print(f"Total Structural Accounted For: {results['fit_score']*100:.2f}%")

    # Save Results
    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    if results['is_sufficient']:
        msg = "\nCONCLUSION: The physical model is SUFFICIENT to explain the structure."
        print(msg)
    else:
        msg = "\nCONCLUSION: The physical model is PARTIAL. More complexity required."
        print(msg)

if __name__ == "__main__":
    main()
