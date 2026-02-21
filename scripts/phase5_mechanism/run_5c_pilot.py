#!/usr/bin/env python3
"""
Phase 5C Pilot: Workflow Reconstruction

Benchmarks Voynich (Real) against Independent and Coupled pool simulators
using line-level parameter phase4_inference.
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
from phase5_mechanism.workflow.parameter_inference import WorkflowParameterInferrer  # noqa: E402
from phase5_mechanism.workflow.simulators import (  # noqa: E402
    LineScopedPoolSimulator,
    WeaklyCoupledPoolSimulator,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5C Pilot: Workflow Reconstruction")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5c(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5C: Workflow Reconstruction Pilot[/bold blue]\n"
        "Testing sufficiency of line-conditioned generators",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5c_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        inferrer = WorkflowParameterInferrer()

        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Inferring Parameters from Real Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        real_dist = inferrer.aggregate_distributions(real_lines[:1000]) # Pilot scale

        # 2. Run Simulators
        console.print("\n[bold yellow]Step 2: Executing Workflow Simulators[/bold yellow]")

        # Family 1: Independent Pool
        sim1 = LineScopedPoolSimulator(GRAMMAR_PATH, mean_pool_size=12.0, seed=seed)
        sim1_lines = sim1.generate_corpus(num_lines=500, line_len=8)
        sim1_dist = inferrer.aggregate_distributions(sim1_lines)

        # Family 2: Weakly Coupled Pool
        sim2 = WeaklyCoupledPoolSimulator(GRAMMAR_PATH, reservoir_size=50, drift_rate=0.1, seed=seed)
        sim2_lines = sim2.generate_corpus(num_lines=500, line_len=8)
        sim2_dist = inferrer.aggregate_distributions(sim2_lines)

        # 3. Report
        table = Table(title="Phase 5C Pilot: Workflow Sufficiency Benchmark")
        table.add_column("Workflow Model", style="cyan")
        table.add_column("Mean TTR", justify="right")
        table.add_column("Mean Entropy", justify="right")
        table.add_column("Matches Real?", justify="center")

        def check_match(val, target, tol=0.1):
            return "[green]YES[/green]" if abs(val - target) < tol else "[red]NO[/red]"

        table.add_row(
            "Voynich (Real)",
            f"{real_dist['mean_ttr']:.4f}",
            f"{real_dist['mean_entropy']:.4f}",
            "TARGET"
        )
        table.add_row(
            "Independent Pool (F1)",
            f"{sim1_dist['mean_ttr']:.4f}",
            f"{sim1_dist['mean_entropy']:.4f}",
            check_match(sim1_dist['mean_ttr'], real_dist['mean_ttr'], 0.05)
        )
        table.add_row(
            "Coupled Pool (F2)",
            f"{sim2_dist['mean_ttr']:.4f}",
            f"{sim2_dist['mean_entropy']:.4f}",
            check_match(sim2_dist['mean_ttr'], real_dist['mean_ttr'], 0.05)
        )

        console.print(table)

        # Save Pilot results
        results = {
            "real": real_dist,
            "sim1_independent": sim1_dist,
            "sim2_coupled": sim2_dist
        }

        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/workflow")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5c_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5c(seed=args.seed, output_dir=args.output_dir)
