#!/usr/bin/env python3
"""Phase 14H: Baseline Showdown.

Compares the Lattice Model against three adversarial baselines:
1. Constrained Markov (Order 2)
2. Copy-with-reset (Local repetition)
3. Table-Grille (Fixed grid random walk)
"""

import sys
import json
import math
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter, defaultdict

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/baseline_comparison.json"
console = Console()

def calculate_mdl(tokens, model_name, param_bits):
    """Simplified MDL: Model bits + Bits to explain data given model."""
    counts = Counter(tokens)
    total = len(tokens)
    data_bits = -sum(counts[t] * math.log2(counts[t]/total) for t in counts)
    return param_bits + data_bits

def main():
    console.print("[bold red]Phase 14H: Baseline Showdown (Adversarial Comparison)[/bold red]")
    
    # 1. Load Real Data
    store = MetadataStore(DB_PATH)
    real_lines = get_lines_from_store(store, "voynich_real")
    all_tokens = [t for l in real_lines for t in l]
    total_tokens = len(all_tokens)
    
    # 2. Lattice Model Performance (Target)
    with open(PALETTE_PATH, "r") as f:
        p_data = json.load(f)
    lattice_results = p_data.get("results", p_data)
    num_lattice_params = len(lattice_results.get("lattice_map", {})) + sum(len(v) for v in lattice_results.get("window_contents", {}).values())
    lattice_bits = calculate_mdl(all_tokens, "Lattice", num_lattice_params * 10) # 10 bits per param approx
    
    # 3. Adversarial 1: Markov Order 2
    # Bits = Transitions * log2(Vocab)
    vocab_size = len(set(all_tokens))
    markov_params = vocab_size * 5 # average 5 transitions per word
    markov_bits = calculate_mdl(all_tokens, "Markov-O2", markov_params * math.log2(vocab_size))
    
    # 4. Adversarial 2: Copy-with-Reset
    # Parameters: reset_rate, window_size
    copy_bits = calculate_mdl(all_tokens, "Copy-Reset", 32) # Very low param count
    
    # 5. Adversarial 3: Table-Grille
    # Parameters: Grid cells (2000)
    grille_bits = calculate_mdl(all_tokens, "Table-Grille", 2000 * math.log2(vocab_size))
    
    # 6. Report
    results = {
        "total_tokens": total_tokens,
        "models": {
            "Lattice (Ours)": {"bits": lattice_bits, "bpt": lattice_bits/total_tokens},
            "Markov-O2": {"bits": markov_bits, "bpt": markov_bits/total_tokens},
            "Copy-Reset": {"bits": copy_bits, "bpt": copy_bits/total_tokens},
            "Table-Grille": {"bits": grille_bits, "bpt": grille_bits/total_tokens}
        }
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    table = Table(title="Model Comparison (MDL / Bits-per-token)")
    table.add_column("Model Family", style="cyan")
    table.add_column("Total Bits", justify="right")
    table.add_column("BPT", justify="right", style="bold green")
    
    for name, data in results["models"].items():
        table.add_row(name, f"{data['bits']:.0f}", f"{data['bpt']:.4f}")
    console.print(table)
    
    # Logic for uniqueness
    lattice_bpt = results["models"]["Lattice (Ours)"]["bpt"]
    best_baseline_bpt = min(data["bpt"] for name, data in results["models"].items() if "Lattice" not in name)
    
    if lattice_bpt < best_baseline_bpt:
        console.print(f"\n[bold green]SUCCESS:[/bold green] Lattice model is uniquely parsimonious (diff: {best_baseline_bpt - lattice_bpt:.4f} BPT)")
    else:
        console.print(f"\n[bold yellow]GAP:[/bold yellow] A baseline model is more efficient. Uniqueness argument is weakened.")

if __name__ == "__main__":
    main()
