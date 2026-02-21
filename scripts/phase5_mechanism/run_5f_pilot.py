#!/usr/bin/env python3
"""
Phase 5F Pilot: Entry-Point Selection

Benchmarks Voynich (Real) against Independent and Locally-Coupled 
entry mechanisms using start-word distribution and adjacency phase2_analysis.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.queries import get_lines_from_store  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase5_mechanism.entry_selection.prefix_analysis import EntryPointAnalyzer  # noqa: E402
from phase5_mechanism.entry_selection.simulators import EntryMechanismSimulator  # noqa: E402

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5F Pilot: Entry-Point Selection")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5f(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5F: Entry-Point Selection Pilot[/bold blue]\n"
        "Testing selection rules: Uniform vs. Locally Coupled",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5f_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = EntryPointAnalyzer()

        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Analyzing Real Start-Words[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        real_dist = analyzer.calculate_start_distribution(real_lines)
        real_coup = analyzer.calculate_adjacency_coupling(real_lines)

        # 2. Run Simulators
        console.print("\n[bold yellow]Step 2: Executing Entry Simulators[/bold yellow]")
        sim = EntryMechanismSimulator(GRAMMAR_PATH, vocab_size=500, seed=seed)

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

        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/entry_selection")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5f_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5f(seed=args.seed, output_dir=args.output_dir)
