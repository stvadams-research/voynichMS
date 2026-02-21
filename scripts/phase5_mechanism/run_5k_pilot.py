#!/usr/bin/env python3
"""
Phase 5K Pilot: Parsimony Collapse and Residual Dependency

Benchmarks Voynich (Real) against Position-Indexed DAG (M1) and 
Implicit Lattice (M2) simulators.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from phase5_mechanism.parsimony.phase2_analysis import ParsimonyAnalyzer  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.queries import get_lines_from_store  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase5_mechanism.parsimony.simulators import (  # noqa: E402
    ImplicitLatticeSimulator,
    PositionIndexedDAGSimulator,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5K Pilot: Parsimony Collapse and Residual Dependency")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5k(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5K: Parsimony Collapse Pilot[/bold blue]\n"
        "Testing: Position-Indexed DAG (M1) vs. Implicit Lattice (M2)",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5k_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = ParsimonyAnalyzer()

        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")

        # Generator Setup
        # We match vocab size to Voynich roughly
        vocab = set(w for l in real_lines for w in l)
        vocab_size = len(vocab)

        sim_m1 = PositionIndexedDAGSimulator(GRAMMAR_PATH, vocab_size=vocab_size, seed=seed)
        m1_lines = sim_m1.generate_corpus(num_lines=5000, line_len=8)

        sim_m2 = ImplicitLatticeSimulator(GRAMMAR_PATH, vocab_size=vocab_size, seed=seed)
        m2_lines = sim_m2.generate_corpus(num_lines=5000, line_len=8)

        datasets = {
            "Voynich (Real)": real_lines[:5000],
            "Pos-Indexed DAG (M1)": m1_lines,
            "Implicit Lattice (M2)": m2_lines
        }

        # 2. Run Parsimony Tests
        console.print("\n[bold yellow]Step 2: Analyzing Node Explosion[/bold yellow]")

        table_par = Table(title="Parsimony Metrics")
        table_par.add_column("Dataset", style="cyan")
        table_par.add_column("Vocab", justify="right")
        table_par.add_column("State Count", justify="right")
        table_par.add_column("Explosion Factor", justify="right")

        results = {}
        for label, lines in datasets.items():
            par_res = analyzer.analyze_node_explosion(lines)
            res_res = analyzer.analyze_residual_dependency(lines)

            results[label] = {
                "parsimony": par_res,
                "residual": res_res
            }

            table_par.add_row(
                label,
                str(par_res['vocab_size']),
                str(par_res['state_count']),
                f"{par_res['explosion_factor']:.2f}x"
            )

        console.print(table_par)

        # 3. Run Residual Tests
        console.print("\n[bold yellow]Step 3: Analyzing Residual Dependency[/bold yellow]")

        table_res = Table(title="Residual Dependency (History)")
        table_res.add_column("Dataset", style="cyan")
        table_res.add_column("H(S|W,P)", justify="right")
        table_res.add_column("H(S|W,P,H)", justify="right")
        table_res.add_column("Reduction (%)", justify="right")

        for label, res in results.items():
            r = res['residual']
            table_res.add_row(
                label,
                f"{r['h_word_pos']:.4f}",
                f"{r['h_word_pos_hist']:.4f}",
                f"{r['rel_reduction']*100:.2f}%"
            )

        console.print(table_res)

        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/parsimony")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5k_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5k(seed=args.seed, output_dir=args.output_dir)
