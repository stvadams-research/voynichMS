#!/usr/bin/env python3
"""
Phase 5E Pilot: Large-Object Traversal

Benchmarks Voynich (Real) against a Large-Grid traversal simulator 
using path collision (successor consistency) phase2_analysis.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase5_mechanism.large_object.collision_testing import PathCollisionTester
from phase5_mechanism.large_object.simulators import LargeGridSimulator

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5E Pilot: Large-Object Traversal")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5e(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5E: Large-Object Traversal Pilot[/bold blue]\n"
        "Testing for path collision signatures (Successor Consistency)",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5e_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        tester = PathCollisionTester(context_len=2)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        
        # Generator: Large 50x50 Grid
        sim = LargeGridSimulator(GRAMMAR_PATH, rows=50, cols=50, seed=seed)
        sim_lines = sim.generate_corpus(num_lines=2000, line_len=8)
        
        # 2. Run Collision Tests
        console.print("\n[bold yellow]Step 2: Measuring Path Stiffness[/bold yellow]")
        
        real_coll = tester.calculate_successor_consistency(real_lines[:5000])
        sim_coll = tester.calculate_successor_consistency(sim_lines)
        
        # 3. Report
        table = Table(title="Phase 5E Pilot: Path Collision Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Mean Successor Consistency", justify="right")
        table.add_column("Sample Size (Bigrams)", justify="right")
        table.add_column("Interpretation", style="dim")

        table.add_row(
            "Voynich (Real)", 
            f"{real_coll['mean_consistency']:.4f}", 
            str(real_coll['num_recurring_contexts']),
            "Ground Truth"
        )
        table.add_row(
            "Large Grid (Syn)", 
            f"{sim_coll['mean_consistency']:.4f}", 
            str(sim_coll['num_recurring_contexts']),
            "Rigid Traversal"
        )
        
        console.print(table)
        
        # Save results
        results = {
            "real": real_coll,
            "sim": sim_coll
        }
        
        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/large_object")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5e_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5e(seed=args.seed, output_dir=args.output_dir)
