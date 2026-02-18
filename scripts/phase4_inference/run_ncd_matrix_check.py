#!/usr/bin/env python3
# ruff: noqa: E402
"""
Bounded NCD matrix check with bootstrap rank confidence.

Uses zlib-based NCD across matched corpora plus line-reset Markov control.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.queries import get_lines_from_store, get_tokens_and_boundaries
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase4_inference.projection_diagnostics.line_reset_markov import (
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.ncd import NCDAnalyzer, NCDConfig

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run NCD matrix and bootstrap rank checks.")
    parser.add_argument("--token-limit", type=int, default=80000)
    parser.add_argument("--bootstraps", type=int, default=60)
    parser.add_argument("--block-size", type=int, default=512)
    parser.add_argument("--target-tokens", type=int, default=230000)
    parser.add_argument("--output-name", type=str, default="ncd_matrix_check.json")
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Bounded NCD Matrix Check[/bold blue]\n"
            "zlib-NCD across corpora + bootstrap rank confidence",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_ncd_matrix_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
            "line_reset_markov": "Line-Reset Markov (Generated)",
        }

        dataset_tokens: dict[str, list[str]] = {}
        for dataset_id in (
            "voynich_real",
            "latin_classic",
            "self_citation",
            "table_grille",
            "mechanical_reuse",
            "shuffled_global",
        ):
            tokens, _ = get_tokens_and_boundaries(store, dataset_id)
            dataset_tokens[dataset_id] = tokens
            console.print(f"Loaded {datasets[dataset_id]}: {len(tokens)} tokens")

        lines = get_lines_from_store(store, "voynich_real")
        generator = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=42))
        generator.fit(lines)
        generated = generator.generate(target_tokens=args.target_tokens)
        dataset_tokens["line_reset_markov"] = generated["tokens"]  # type: ignore[index]
        console.print(
            "Generated Line-Reset Markov corpus: "
            f"{len(generated['tokens'])} tokens in {len(generated['lines'])} lines"
        )

        config = NCDConfig(
            token_limit=args.token_limit,
            bootstraps=args.bootstraps,
            block_size=args.block_size,
            random_state=42,
            focus_dataset_id="voynich_real",
        )
        results = NCDAnalyzer(config).analyze(dataset_tokens)
        results["dataset_labels"] = datasets
        results["generator_fit_stats"] = generator.fit_stats()

        if results.get("status") == "ok":
            focus = results["focus_dataset_id"]
            summ = results["focus_bootstrap_summary"]
            ranked = sorted(summ.items(), key=lambda kv: kv[1]["point_ncd"])

            table = Table(title="Voynich NCD Ranking (Lower is Closer)")
            table.add_column("Rank", justify="right")
            table.add_column("Dataset", style="cyan")
            table.add_column("Point NCD", justify="right")
            table.add_column("CI95", justify="right")
            table.add_column("P(Closest)", justify="right")
            table.add_column("Mean Rank", justify="right")

            for i, (dataset_id, row) in enumerate(ranked, start=1):
                label = datasets.get(dataset_id, dataset_id)
                ci = f"[{row['bootstrap_ci95_low_ncd']:.4f}, {row['bootstrap_ci95_high_ncd']:.4f}]"
                table.add_row(
                    str(i),
                    label,
                    f"{row['point_ncd']:.4f}",
                    ci,
                    f"{row['closest_probability']:.3f}",
                    f"{row['rank_mean']:.2f}",
                )
            console.print(table)

            size_table = Table(title="Point Compressed Sizes (zlib)")
            size_table.add_column("Dataset", style="cyan")
            size_table.add_column("Compressed Bytes", justify="right")
            for dataset_id, size in results["point_compressed_sizes"].items():
                size_table.add_row(datasets.get(dataset_id, dataset_id), str(size))
            console.print(size_table)

            _ = focus  # readability marker for retained focus output

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())

