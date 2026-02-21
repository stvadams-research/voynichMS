#!/usr/bin/env python3
"""Phase 14I: Ablation Study.

Tests model performance (Admissibility / MDL) as a function of 
lattice complexity (number of windows).
"""

import sys
import json
import math
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase14_machine.palette_solver import GlobalPaletteSolver
from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase14_machine/ablation_results.json"
console = Console()

def calculate_mdl(total_tokens, vocab_bits, num_windows, lattice_map, window_contents):
    # Param bits: words in lattice_map * log2(num_windows)
    param_bits = len(lattice_map) * math.log2(num_windows)
    
    # Data bits: we assume the unigram entropy within the window
    # Simplified: total_tokens * log2(avg_window_size)
    avg_win_size = len(lattice_map) / num_windows
    data_bits = total_tokens * math.log2(avg_win_size)
    
    return param_bits + data_bits

def main():
    console.print("[bold yellow]Phase 14I: Ablation Study (Complexity vs Fit)[/bold yellow]")
    
    # 1. Load Data
    store = MetadataStore(DB_PATH)
    real_lines = get_lines_from_store(store, "voynich_real")
    all_tokens = [t for l in real_lines for t in l]
    total_tokens = len(all_tokens)
    
    # 2. Solve Grid (Once)
    solver = GlobalPaletteSolver()
    solver.ingest_data([], real_lines, top_n=2000)
    solved_pos = solver.solve_grid(iterations=20)
    
    # 3. Test different Window counts
    results = []
    for k in [10, 20, 50, 100, 200]:
        console.print(f"Testing K={k} windows...")
        lattice_data = solver.cluster_lattice(solved_pos, num_windows=k)
        
        mdl = calculate_mdl(
            total_tokens, 
            0, # vocab_bits handled by baseline
            k, 
            lattice_data["word_to_window"], 
            lattice_data["window_contents"]
        )
        
        results.append({
            "num_windows": k,
            "mdl_bits": mdl,
            "bpt": mdl / total_tokens
        })
        
    # 4. Save and Report
    saved = ProvenanceWriter.save_results({"ablation": results}, OUTPUT_PATH)
    
    table = Table(title="Lattice Complexity Ablation")
    table.add_column("Windows (K)", justify="right")
    table.add_column("MDL Bits", justify="right")
    table.add_column("BPT", justify="right", style="bold green")
    
    for r in results:
        table.add_row(str(r['num_windows']), f"{r['mdl_bits']:.0f}", f"{r['bpt']:.4f}")
    console.print(table)
    
    # Identify optimal K (the knee)
    best = min(results, key=lambda x: x['mdl_bits'])
    console.print(f"\n[bold green]Optimal Complexity Found:[/bold green] K={best['num_windows']} windows (BPT={best['bpt']:.4f})")

if __name__ == "__main__":
    main()
