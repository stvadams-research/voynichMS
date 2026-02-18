#!/usr/bin/env python3
# ruff: noqa: E402
"""
Bounded discrimination check runner (Phase 4).

Answers: which matched corpus family is Voynich closest to, under simple
train/test TF-IDF similarity models.
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
from phase1_foundation.core.queries import get_tokens_and_boundaries
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase4_inference.projection_diagnostics.discrimination import (
    DiscriminationCheckAnalyzer,
    DiscriminationCheckConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run bounded discrimination diagnostics.")
    parser.add_argument("--ngram-min", type=int, default=1)
    parser.add_argument("--ngram-max", type=int, default=1)
    parser.add_argument(
        "--output-name",
        type=str,
        default="discrimination_check.json",
        help="Output filename written under results/data/phase4_inference/",
    )
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Bounded Discrimination Check[/bold blue]\n"
            "Nearest corpus analysis for Voynich vs matched controls\n"
            f"TF-IDF ngram_range=({args.ngram_min},{args.ngram_max})",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_discrimination_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        config = DiscriminationCheckConfig(
            window_size=72,
            windows_per_dataset=160,
            max_features=2000,
            ngram_min=args.ngram_min,
            ngram_max=args.ngram_max,
            train_fraction=0.7,
            random_state=42,
            voynich_dataset_id="voynich_real",
        )
        analyzer = DiscriminationCheckAnalyzer(config=config)

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

        coverage_table = Table(title="Bounded Sample Coverage")
        coverage_table.add_column("Dataset", style="cyan")
        coverage_table.add_column("Doc Windows", justify="right")
        for dataset_id, label in datasets.items():
            coverage_table.add_row(label, str(results.get("doc_counts", {}).get(dataset_id, 0)))
        console.print(coverage_table)

        if results.get("status") == "ok":
            metrics = results["models"]
            model_table = Table(title="Model Accuracy (Held-out Windows)")
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Accuracy", justify="right")
            model_table.add_row(
                "Nearest Centroid (cosine)",
                f"{metrics['nearest_centroid']['accuracy']:.4f}",
            )
            model_table.add_row(
                "1-NN (cosine)",
                f"{metrics['knn_1_cosine']['accuracy']:.4f}",
            )
            console.print(model_table)

            v = results["voynich_summary"]
            if v.get("status") == "ok":
                closest_table = Table(title="Voynich Closest Centroid Families")
                closest_table.add_column("Rank", justify="right")
                closest_table.add_column("Dataset", style="cyan")
                closest_table.add_column("Cosine Distance", justify="right")
                for rank, row in enumerate(v["closest_centroids"][:5], start=1):
                    label = datasets.get(row["dataset_id"], row["dataset_id"])
                    closest_table.add_row(str(rank), label, f"{row['cosine_distance']:.4f}")
                console.print(closest_table)

                assign_table = Table(title="Voynich Held-out Assignment Distribution")
                assign_table.add_column("Predicted Family", style="cyan")
                assign_table.add_column("Nearest Centroid", justify="right")
                assign_table.add_column("1-NN", justify="right")
                for dataset_id, label in datasets.items():
                    nc = v["voynich_test_assignment_nearest_centroid"].get(dataset_id, 0.0)
                    knn = v["voynich_test_assignment_knn_1"].get(dataset_id, 0.0)
                    assign_table.add_row(label, f"{nc:.3f}", f"{knn:.3f}")
                console.print(assign_table)

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)

        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())
