#!/usr/bin/env python3
"""
Phase 5G Pilot: Topology Collapse

Benchmarks Voynich (Real) against four topology simulators using 
overlap, coverage, and convergence signatures.
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
from phase5_mechanism.topology_collapse.signatures import TopologySignatureAnalyzer
from phase5_mechanism.topology_collapse.simulators import (
    DAGTopologySimulator,
    GridTopologySimulator,
    LatticeTopologySimulator,
    LayeredTableSimulator,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5G Pilot: Topology Collapse")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5g(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5G: Topology Collapse Pilot[/bold blue]\n"
        "Testing non-equivalence of large-object topologies",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5g_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = TopologySignatureAnalyzer(prefix_len=2)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        
        sims = {
            "Grid (60x60)": GridTopologySimulator(GRAMMAR_PATH, seed=seed),
            "Layered Table": LayeredTableSimulator(GRAMMAR_PATH, seed=seed),
            "DAG (Stratified)": DAGTopologySimulator(GRAMMAR_PATH, seed=seed),
            "Lattice (Implicit)": LatticeTopologySimulator(GRAMMAR_PATH, seed=seed)
        }
        
        corpus_data = {"Voynich (Real)": real_lines[:5000]}
        for label, sim in sims.items():
            corpus_data[label] = sim.generate_corpus(num_lines=2000, line_len=8)
            
        # 2. Run Geometry Tests
        console.print("\n[bold yellow]Step 2: Running Topology Signatures[/bold yellow]")
        
        table = Table(title="Phase 5G Pilot: Topology Signature Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Collision Rate", justify="right")
        table.add_column("Gini (Skew)", justify="right")
        table.add_column("Convergence", justify="right")
        table.add_column("Status", justify="center")

        results = {}
        for label, lines in corpus_data.items():
            overlap = analyzer.analyze_overlap(lines)
            coverage = analyzer.analyze_coverage(lines)
            convergence = analyzer.analyze_convergence(lines)
            
            results[label] = {
                "overlap": overlap,
                "coverage": coverage,
                "convergence": convergence
            }
            
            status = "TARGET" if "Voynich" in label else ""
            table.add_row(
                label,
                f"{overlap['collision_rate']:.4f}",
                f"{coverage['gini_coefficient']:.4f}",
                f"{convergence['avg_successor_convergence']:.4f}",
                status
            )
            
        console.print(table)
        
        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/topology_collapse")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5g_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5g(seed=args.seed, output_dir=args.output_dir)
