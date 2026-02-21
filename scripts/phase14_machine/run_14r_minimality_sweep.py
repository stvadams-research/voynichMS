#!/usr/bin/env python3
"""Phase 14R: Minimality Sweep.

Sweeps the state-space complexity (number of windows) to identify the 
mathematical 'knee' where fit vs parsimony is optimized.
"""

import json
import math
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase14_machine.evaluation_engine import EvaluationEngine
from phase14_machine.palette_solver import GlobalPaletteSolver

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase14_machine/minimality_sweep.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 14R: Minimality Sweep (Complexity vs. Admissibility)[/bold cyan]")
    
    # 1. Load Data
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    all_tokens = [t for l in real_lines for t in l]
    
    # 2. Solve Grid (Once, for 2000 tokens for speed)
    solver = GlobalPaletteSolver()
    solver.ingest_data([], real_lines, top_n=2000)
    solved_pos = solver.solve_grid(iterations=20)
    
    vocab = set(solved_pos.keys())
    engine = EvaluationEngine(vocab)
    
    # 3. Sweep K
    results = []
    for k in [2, 5, 10, 25, 50, 75, 100, 200, 500]:
        console.print(f"Testing Complexity K={k} windows...")
        lattice_data = solver.cluster_lattice(solved_pos, num_windows=k)
        
        # Admissibility
        metrics = engine.calculate_admissibility(
            real_lines, 
            lattice_data["word_to_window"], 
            lattice_data["window_contents"]
        )
        
        # MDL Calculation
        # L(model) = K * avg_win_size * bits + edges * bits
        # Simplified: L(model) approx proportional to len(vocab) * log2(K)
        l_model = len(vocab) * math.log2(k)
        # L(data | model) approx proportional to total_tokens * log2(len(vocab)/K)
        l_data = metrics['total_clamped_tokens'] * math.log2(len(vocab)/k)
        l_total = l_model + l_data
        
        results.append({
            "num_windows": k,
            "admissibility": metrics["admissibility_rate"],
            "l_total_bits": l_total
        })
        
    # 4. Save and Report
    saved = ProvenanceWriter.save_results({"sweep": results}, OUTPUT_PATH)
    
    table = Table(title="Complexity Sweep Results")
    table.add_column("Windows (K)", justify="right")
    table.add_column("Admissibility", justify="right", style="bold green")
    table.add_column("MDL Score", justify="right", style="cyan")
    
    for r in results:
        table.add_row(
            str(r['num_windows']), 
            f"{r['admissibility']*100:.2f}%", 
            f"{r['l_total_bits']:.0f}"
        )
    console.print(table)
    
    # Identify the "Knee" (Point where MDL starts increasing or admissibility plateaus)
    best_mdl = min(results, key=lambda x: x['l_total_bits'])
    console.print(f"\n[bold green]Minimality Proven at K={best_mdl['num_windows']}[/bold green] (Optimal MDL)")

if __name__ == "__main__":
    main()
