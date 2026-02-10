#!/usr/bin/env python3
"""
Phase 5F Pilot: Entry-Point Selection

Benchmarks Voynich (Real) against Independent and Locally-Coupled 
entry mechanisms using start-word distribution and adjacency analysis.
"""

import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.core.queries import get_lines_from_store
from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from mechanism.entry_selection.simulators import EntryMechanismSimulator
from mechanism.entry_selection.prefix_analysis import EntryPointAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def run_pilot_5f():
    console.print(Panel.fit(
        "[bold blue]Phase 5F: Entry-Point Selection Pilot[/bold blue]\n"
        "Testing selection rules: Uniform vs. Locally Coupled",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5f_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = EntryPointAnalyzer()
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Analyzing Real Start-Words[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        real_dist = analyzer.calculate_start_distribution(real_lines)
        real_coup = analyzer.calculate_adjacency_coupling(real_lines)
        
        # 2. Run Simulators
        console.print("\n[bold yellow]Step 2: Executing Entry Simulators[/bold yellow]")
        sim = EntryMechanismSimulator(GRAMMAR_PATH, vocab_size=500, seed=42)
        
        # Family 1: Uniform
        syn_uni_lines = sim.generate_uniform_independent(num_lines=2000, line_len=8)
        syn_uni_dist = analyzer.calculate_start_distribution(syn_uni_lines)
        syn_uni_coup = analyzer.calculate_adjacency_coupling(syn_uni_lines)
        
        # Family 2: Coupled
        syn_cpl_lines = sim.generate_locally_coupled(num_lines=2000, line_len=8, coupling=0.8)
        syn_cpl_dist = analyzer.calculate_start_distribution(syn_cpl_lines)
        syn_cpl_coup = analyzer.calculate_adjacency_coupling(syn_cpl_lines)
        
        # 3. Report
        table = Table(title="Phase 5F Pilot: Entry Mechanism Benchmark")
        table.add_column("Entry Mechanism", style="cyan")
        table.add_column("Start Entropy", justify="right")
        table.add_column("Adjacency Coupling", justify="right")
        table.add_column("Matches Real?", justify="center")

        def check_match(val, target, tol=0.05):
            return "[green]YES[/green]" if abs(val - target) < tol else "[red]NO[/red]"

        table.add_row(
            "Voynich (Real)", 
            f"{real_dist['start_entropy']:.4f}", 
            f"{real_coup['coupling_score']:.4f}",
            "TARGET"
        )
        table.add_row(
            "Uniform Independent", 
            f"{syn_uni_dist['start_entropy']:.4f}", 
            f"{syn_uni_coup['coupling_score']:.4f}",
            check_match(syn_uni_coup['coupling_score'], real_coup['coupling_score'], 0.01)
        )
        table.add_row(
            "Locally Coupled", 
            f"{syn_cpl_dist['start_entropy']:.4f}", 
            f"{syn_cpl_coup['coupling_score']:.4f}",
            check_match(syn_cpl_coup['coupling_score'], real_coup['coupling_score'], 0.01)
        )
        
        console.print(table)
        
        # Save results
        results = {
            "real": {"dist": real_dist, "coup": real_coup},
            "uniform": {"dist": syn_uni_dist, "coup": syn_uni_coup},
            "coupled": {"dist": syn_cpl_dist, "coup": syn_cpl_coup}
        }
        
        output_dir = Path("results/mechanism/entry_selection")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "pilot_5f_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5f()
