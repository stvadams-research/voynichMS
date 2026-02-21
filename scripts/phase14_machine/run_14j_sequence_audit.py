#!/usr/bin/env python3
"""Phase 14J: Sequence Diversity Audit.

Measures how much of the generated sequence space is 'hallucinated' vs.
attested in the real manuscript.
"""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/sequence_diversity.json"
console = Console()

def get_ngrams(lines, n=3):
    return set(tuple(line[i:i+n]) for line in lines for i in range(len(line) - n + 1))

def main():
    console.print("[bold blue]Phase 14J: Sequence Diversity Audit[/bold blue]")
    
    if not PALETTE_PATH.exists():
        return

    # 1. Load Data
    with open(PALETTE_PATH, "r") as f:
        p_data = json.load(f)
    results = p_data.get("results", p_data)
    
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    
    # 2. Setup Emulator
    emulator = HighFidelityVolvelle(results["lattice_map"], results["window_contents"], seed=42)
    
    # 3. Generate Comparison Corpus
    num_lines = 10000
    console.print(f"Generating {num_lines} synthetic lines for sequence comparison...")
    syn_lines = emulator.generate_mirror_corpus(num_lines)
    
    # 4. N-gram Diversity
    results = {"ngrams": {}}
    for n in [2, 3, 4]:
        real_ng = get_ngrams(real_lines, n)
        syn_ng = get_ngrams(syn_lines, n)
        
        overlap = syn_ng & real_ng
        fpr = 1.0 - (len(overlap) / len(syn_ng)) if syn_ng else 0
        
        results["ngrams"][f"n{n}"] = {
            "real_count": len(real_ng),
            "syn_count": len(syn_ng),
            "overlap_count": len(overlap),
            "false_positive_rate": fpr
        }
        
    # 5. Save and Report
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    table = Table(title="Sequence Overgeneration Audit")
    table.add_column("N-gram", justify="right")
    table.add_column("Real Count", justify="right")
    table.add_column("Syn Count", justify="right")
    table.add_column("Hallucination Rate (FPR)", justify="right", style="bold red")
    
    for n, data in results["ngrams"].items():
        table.add_row(
            n, 
            str(data['real_count']), 
            str(data['syn_count']), 
            f"{data['false_positive_rate']*100:.2f}%"
        )
    console.print(table)
    
    console.print("\n[bold yellow]Interpretation:[/bold yellow] High FPR at N=3+ is expected for a non-semantic generator, as the state space exceeds the available corpus sample size.")

if __name__ == "__main__":
    main()
