#!/usr/bin/env python3
# ruff: noqa: E402
"""
Bounded order-constraint check runner (Phase 4).

Compares transition-order metrics to shuffled baselines.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.core.queries import get_tokens_and_boundaries  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase4_inference.projection_diagnostics.order_constraints import (  # noqa: E402
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run order-constraint permutation checks.")
    parser.add_argument("--token-limit", type=int, default=120000)
    parser.add_argument("--vocab-limit", type=int, default=500)
    parser.add_argument("--permutations", type=int, default=50)
    parser.add_argument(
        "--output-name",
        type=str,
        default="order_constraints_check.json",
        help="Output filename written under results/data/phase4_inference/",
    )
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Bounded Order-Constraint Check[/bold blue]\n"
            "Bigram/trigram entropy and bigram mutual information vs shuffled baselines",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_order_constraints_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        config = OrderConstraintConfig(
            token_limit=args.token_limit,
            vocab_limit=args.vocab_limit,
            permutations=args.permutations,
            random_state=42,
        )
        analyzer = OrderConstraintAnalyzer(config=config)

        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
        }

        dataset_tokens = {}
        for dataset_id, label in datasets.items():
            tokens, _ = get_tokens_and_boundaries(store, dataset_id)
            console.print(f"Loaded {label}: {len(tokens)} tokens")
            dataset_tokens[dataset_id] = tokens

        results = analyzer.analyze(dataset_tokens)
        results["dataset_labels"] = datasets

        table = Table(title="Order Constraint vs Shuffle Baseline")
        table.add_column("Dataset", style="cyan")
        table.add_column("H2 delta", justify="right")
        table.add_column("H2 p(low)", justify="right")
        table.add_column("H3 delta", justify="right")
        table.add_column("H3 p(low)", justify="right")
        table.add_column("MI2 delta", justify="right")
        table.add_column("MI2 p(high)", justify="right")

        for dataset_id, label in datasets.items():
            row = results["datasets"].get(dataset_id, {})
            if row.get("status") != "ok":
                table.add_row(label, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a")
                continue

            m = row["metrics"]
            h2 = m["bigram_cond_entropy"]
            h3 = m["trigram_cond_entropy"]
            mi2 = m["bigram_mutual_information"]
            table.add_row(
                label,
                f"{h2['delta']:.4f}",
                f"{h2['p_directional']:.4f}",
                f"{h3['delta']:.4f}",
                f"{h3['p_directional']:.4f}",
                f"{mi2['delta']:.4f}",
                f"{mi2['p_directional']:.4f}",
            )
        console.print(table)

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)

        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())
