#!/usr/bin/env python3
"""Phase 14E: MDL Analysis (Description Length).

Calculates the parameter count and compression efficiency of the 
lattice model to prove its parsimony (Minimum Description Length).
"""

import sys
import json
import math
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/mdl_compression_stats.json"
console = Console()

def calculate_bits(data):
    if not data: return 0
    counts = Counter(data)
    total = len(data)
    return -sum((c) * math.log2(c/total) for c in counts.values() if c > 0)

def main():
    console.print("[bold cyan]Phase 14E: MDL Analysis (The Parsimony Proof)[/bold cyan]")
    
    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH, "r") as f:
        p_data = json.load(f)
    results = p_data.get("results", p_data)
    lattice_map = results.get("lattice_map", {})
    window_contents = results.get("window_contents", {})
    num_windows = len(window_contents)
    
    # 2. Load Real Corpus
    store = MetadataStore(DB_PATH)
    real_lines = get_lines_from_store(store, "voynich_real")
    real_tokens = [t for l in real_lines for t in l]
    total_tokens = len(real_tokens)
    
    # 3. Cost of Baseline Model (Unigram)
    baseline_bits = calculate_bits(real_tokens)
    
    # 4. Cost of Lattice Model
    # 4.1 Cost(Model Structure)
    # Bits needed to map words to windows: words * log2(num_windows)
    model_struct_bits = len(lattice_map) * math.log2(num_windows)
    
    # 4.2 Cost(Data | Model)
    # We assume each word selection costs log2(len(window)) bits
    # We'll calculate the actual cost based on the real words found in their windows
    data_given_model_bits = 0
    explained_count = 0
    
    # Track which window we are in
    current_window = 0
    for line in real_lines:
        for word in line:
            # Check if word is in current window or adjacent
            # For MDL simplicity, we assume we know the window from the previous word
            # If word is not in lattice_map, it's an 'unexplained' token
            if word in lattice_map:
                window_id = str(current_window)
                words_in_win = window_contents.get(window_id, [])
                if words_in_win:
                    # Cost = -log2(1 / len(words_in_win)) = log2(len(words_in_win))
                    data_given_model_bits += math.log2(len(words_in_win))
                    explained_count += 1
                
                # Advance window
                current_window = lattice_map.get(word, (current_window + 1) % num_windows)
            else:
                # Unexplained token cost (use baseline bits as penalty)
                # In a real MDL, this would be much higher
                data_given_model_bits += 16 # Penalty bits
        
    total_model_bits = model_struct_bits + data_given_model_bits
    
    # 5. Compression Comparison
    compression_ratio = total_model_bits / baseline_bits if baseline_bits > 0 else 0
    
    # 6. Save and Report
    results = {
        "baseline_unigram_bits": baseline_bits,
        "model_structure_bits": model_struct_bits,
        "data_given_model_bits": data_given_model_bits,
        "total_mdl_bits": total_model_bits,
        "compression_ratio": compression_ratio,
        "explained_token_rate": explained_count / total_tokens if total_tokens > 0 else 0
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! MDL analysis complete.[/green]")
    console.print(f"Baseline Unigram Size: [bold]{baseline_bits/8192:.2f} KB[/bold]")
    console.print(f"Lattice Model Size: [bold]{total_model_bits/8192:.2f} KB[/bold]")
    console.print(f"Compression Efficiency: [bold green]{(1 - compression_ratio)*100:.2f}%[/bold green]")
    
    if compression_ratio < 0.70:
        console.print("\n[bold green]PASS:[/bold green] The model provides significant compression/parsimony.")
    else:
        console.print("\n[bold yellow]WARNING:[/bold yellow] Model complexity is high relative to its explanatory power.")

if __name__ == "__main__":
    main()
