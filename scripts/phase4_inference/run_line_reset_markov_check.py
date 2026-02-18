#!/usr/bin/env python3
# ruff: noqa: E402
"""
Generate a stronger non-semantic control and evaluate it.

Control:
- line-reset Markov generator fit on Voynich line statistics

Evaluations:
- discrimination check (default ngrams 1-2)
- order-constraint check
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
from phase4_inference.projection_diagnostics.line_reset_markov import (
    LineResetMarkovConfig,
    LineResetMarkovGenerator,
)
from phase4_inference.projection_diagnostics.order_constraints import (
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run line-reset Markov control checks.")
    parser.add_argument("--output-name", default="line_reset_markov_check.json")
    parser.add_argument("--target-tokens", type=int, default=230000)
    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=50)
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Line-Reset Markov Control Check[/bold blue]\n"
            "Generate stronger non-semantic control and benchmark against Voynich",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_line_reset_markov_check_phase4", "seed": 42}) as run:
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

        # Load base corpora from DB.
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

        # Fit/generate stronger control from real Voynich lines.
        voynich_lines = get_lines_from_store(store, "voynich_real")
        generator = LineResetMarkovGenerator(LineResetMarkovConfig(random_state=42))
        generator.fit(voynich_lines)

        target_tokens = args.target_tokens
        if target_tokens <= 0:
            target_tokens = len(dataset_tokens["voynich_real"])
        generated = generator.generate(target_tokens=target_tokens)
        dataset_tokens["line_reset_markov"] = generated["tokens"]  # type: ignore[index]
        console.print(
            "Generated Line-Reset Markov corpus: "
            f"{len(generated['tokens'])} tokens in {len(generated['lines'])} lines"
        )

        # Run discrimination check with order-aware ngrams.
        disc_cfg = DiscriminationCheckConfig(
            window_size=72,
            windows_per_dataset=160,
            max_features=args.disc_max_features,
            ngram_min=args.disc_ngram_min,
            ngram_max=args.disc_ngram_max,
            train_fraction=0.7,
            random_state=42,
            voynich_dataset_id="voynich_real",
        )
        disc_result = DiscriminationCheckAnalyzer(disc_cfg).analyze(dataset_tokens)
        disc_result["dataset_labels"] = datasets

        # Run order-constraint check.
        order_cfg = OrderConstraintConfig(
            token_limit=args.order_token_limit,
            vocab_limit=args.order_vocab_limit,
            permutations=args.order_permutations,
            random_state=42,
        )
        order_result = OrderConstraintAnalyzer(order_cfg).analyze(dataset_tokens)
        order_result["dataset_labels"] = datasets

        summary_table = Table(title="Key Comparison: Voynich vs Line-Reset Markov")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Voynich", justify="right")
        summary_table.add_column("Line-Reset Markov", justify="right")

        v_assign = disc_result["voynich_summary"]["voynich_test_assignment_knn_1"]
        summary_table.add_row(
            "Voynich 1-NN self-assignment",
            f"{v_assign.get('voynich_real', 0.0):.3f}",
            "n/a",
        )
        v_close = disc_result["voynich_summary"]["closest_centroids"]
        top_close = v_close[0]["dataset_id"] if v_close else "n/a"
        summary_table.add_row("Voynich closest centroid family", top_close, "n/a")

        order_ds = order_result["datasets"]
        v_h2 = order_ds["voynich_real"]["metrics"]["bigram_cond_entropy"]["delta"]
        l_h2 = order_ds["line_reset_markov"]["metrics"]["bigram_cond_entropy"]["delta"]
        v_h3 = order_ds["voynich_real"]["metrics"]["trigram_cond_entropy"]["delta"]
        l_h3 = order_ds["line_reset_markov"]["metrics"]["trigram_cond_entropy"]["delta"]
        v_mi = order_ds["voynich_real"]["metrics"]["bigram_mutual_information"]["delta"]
        l_mi = order_ds["line_reset_markov"]["metrics"]["bigram_mutual_information"]["delta"]
        summary_table.add_row("H2 delta vs shuffle", f"{v_h2:.4f}", f"{l_h2:.4f}")
        summary_table.add_row("H3 delta vs shuffle", f"{v_h3:.4f}", f"{l_h3:.4f}")
        summary_table.add_row("MI2 delta vs shuffle", f"{v_mi:.4f}", f"{l_mi:.4f}")
        console.print(summary_table)

        results = {
            "status": "ok",
            "generator": {
                "type": "line_reset_markov",
                "fit_stats": generator.fit_stats(),
                "target_tokens": int(target_tokens),
                "generated_tokens": int(len(generated["tokens"])),
                "generated_lines": int(len(generated["lines"])),
            },
            "discrimination": disc_result,
            "order_constraints": order_result,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())

