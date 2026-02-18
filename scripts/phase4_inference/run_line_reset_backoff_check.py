#!/usr/bin/env python3
# ruff: noqa: E402
"""
Hybrid line-reset backoff benchmark.

Compares:
- line_reset_markov (baseline)
- line_reset_backoff (new hybrid)

against Voynich and existing controls using bounded diagnostics.
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
from phase4_inference.projection_diagnostics.discrimination import (
    DiscriminationCheckAnalyzer,
    DiscriminationCheckConfig,
)
from phase4_inference.projection_diagnostics.line_reset_backoff import (
    LineResetBackoffConfig,
    LineResetBackoffGenerator,
)
from phase4_inference.projection_diagnostics.line_reset_markov import (
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.ncd import NCDAnalyzer, NCDConfig
from phase4_inference.projection_diagnostics.order_constraints import (
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run line-reset backoff benchmark checks.")
    parser.add_argument("--target-tokens", type=int, default=230000)
    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=50)
    parser.add_argument("--ncd-token-limit", type=int, default=80000)
    parser.add_argument("--ncd-bootstraps", type=int, default=30)
    parser.add_argument("--ncd-block-size", type=int, default=512)
    parser.add_argument("--output-name", type=str, default="line_reset_backoff_check.json")
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Line-Reset Backoff Check[/bold blue]\n"
            "Comparing baseline Markov vs hybrid higher-order backoff",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_line_reset_backoff_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
            "line_reset_markov": "Line-Reset Markov",
            "line_reset_backoff": "Line-Reset Backoff",
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

        markov = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=42))
        markov.fit(lines)
        m_out = markov.generate(target_tokens=args.target_tokens)
        dataset_tokens["line_reset_markov"] = m_out["tokens"]  # type: ignore[index]
        console.print(
            "Built Line-Reset Markov: "
            f"{len(m_out['tokens'])} tokens in {len(m_out['lines'])} lines"
        )

        backoff = LineResetBackoffGenerator(LineResetBackoffConfig(random_state=42))
        backoff.fit(lines)
        b_out = backoff.generate(target_tokens=args.target_tokens)
        dataset_tokens["line_reset_backoff"] = b_out["tokens"]  # type: ignore[index]
        console.print(
            "Built Line-Reset Backoff: "
            f"{len(b_out['tokens'])} tokens in {len(b_out['lines'])} lines"
        )

        disc = DiscriminationCheckAnalyzer(
            DiscriminationCheckConfig(
                window_size=72,
                windows_per_dataset=160,
                max_features=args.disc_max_features,
                ngram_min=args.disc_ngram_min,
                ngram_max=args.disc_ngram_max,
                train_fraction=0.7,
                random_state=42,
                voynich_dataset_id="voynich_real",
            )
        ).analyze(dataset_tokens)
        disc["dataset_labels"] = datasets

        order = OrderConstraintAnalyzer(
            OrderConstraintConfig(
                token_limit=args.order_token_limit,
                vocab_limit=args.order_vocab_limit,
                permutations=args.order_permutations,
                random_state=42,
            )
        ).analyze(dataset_tokens)
        order["dataset_labels"] = datasets

        ncd = NCDAnalyzer(
            NCDConfig(
                token_limit=args.ncd_token_limit,
                bootstraps=args.ncd_bootstraps,
                block_size=args.ncd_block_size,
                random_state=42,
                focus_dataset_id="voynich_real",
            )
        ).analyze(dataset_tokens)
        ncd["dataset_labels"] = datasets

        if disc.get("status") == "ok":
            closest = Table(title="Voynich Closest Families (Discrimination)")
            closest.add_column("Rank", justify="right")
            closest.add_column("Dataset", style="cyan")
            closest.add_column("Cosine Distance", justify="right")
            for i, row in enumerate(disc["voynich_summary"]["closest_centroids"][:8], start=1):
                closest.add_row(
                    str(i),
                    datasets.get(row["dataset_id"], row["dataset_id"]),
                    f"{row['cosine_distance']:.4f}",
                )
            console.print(closest)

        order_table = Table(title="Order Constraints: Delta vs Shuffled Baseline")
        order_table.add_column("Dataset", style="cyan")
        order_table.add_column("H2 delta", justify="right")
        order_table.add_column("H3 delta", justify="right")
        order_table.add_column("MI2 delta", justify="right")
        for dataset_id in (
            "voynich_real",
            "line_reset_markov",
            "line_reset_backoff",
            "mechanical_reuse",
            "shuffled_global",
        ):
            row = order["datasets"].get(dataset_id, {})
            if row.get("status") != "ok":
                order_table.add_row(datasets[dataset_id], "n/a", "n/a", "n/a")
                continue
            m = row["metrics"]
            order_table.add_row(
                datasets[dataset_id],
                f"{m['bigram_cond_entropy']['delta']:.4f}",
                f"{m['trigram_cond_entropy']['delta']:.4f}",
                f"{m['bigram_mutual_information']['delta']:.4f}",
            )
        console.print(order_table)

        if ncd.get("status") == "ok":
            ncd_table = Table(title="Voynich NCD Ranking (Lower is Closer)")
            ncd_table.add_column("Rank", justify="right")
            ncd_table.add_column("Dataset", style="cyan")
            ncd_table.add_column("Point NCD", justify="right")
            ncd_table.add_column("P(Closest)", justify="right")
            ranked = sorted(
                ncd["focus_bootstrap_summary"].items(),
                key=lambda kv: kv[1]["point_ncd"],
            )
            for i, (dataset_id, row) in enumerate(ranked, start=1):
                ncd_table.add_row(
                    str(i),
                    datasets.get(dataset_id, dataset_id),
                    f"{row['point_ncd']:.4f}",
                    f"{row['closest_probability']:.3f}",
                )
            console.print(ncd_table)

        results = {
            "status": "ok",
            "generators": {
                "line_reset_markov": markov.fit_stats(),
                "line_reset_backoff": backoff.fit_stats(),
            },
            "discrimination": disc,
            "order_constraints": order,
            "ncd": ncd,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())

