#!/usr/bin/env python3
# ruff: noqa: E402
"""
Bounded latent-space check runner (Phase 4).

Runs PCA + t-SNE + optional UMAP projections as descriptive diagnostics and
scores separability against permutation baselines.
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
from phase4_inference.projection_diagnostics.analyzer import (  # noqa: E402
    ProjectionDiagnosticsAnalyzer,
    ProjectionDiagnosticsConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def _parse_args():
    parser = argparse.ArgumentParser(description="Bounded Projection Check")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_experiment(seed: int = 42, output_dir: str | None = None) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Bounded Projection Check[/bold blue]\n"
            "PCA / t-SNE / optional UMAP with permutation baselines",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_projection_bounded_phase4", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        config = ProjectionDiagnosticsConfig(
            window_size=72,
            windows_per_dataset=160,
            max_features=2000,
            tsne_perplexity=30,
            permutations=100,
            random_state=seed,
        )
        analyzer = ProjectionDiagnosticsAnalyzer(config=config)

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

        sample_table = Table(title="Bounded Sample Coverage")
        sample_table.add_column("Dataset", style="cyan")
        sample_table.add_column("Doc Windows", justify="right")
        for dataset_id, label in datasets.items():
            sample_table.add_row(label, str(results["doc_counts"].get(dataset_id, 0)))
        console.print(sample_table)

        metric_table = Table(title="Projection Diagnostic Scores")
        metric_table.add_column("Method", style="cyan")
        metric_table.add_column("Observed", justify="right")
        metric_table.add_column("Perm Mean", justify="right")
        metric_table.add_column("z", justify="right")
        metric_table.add_column("p(perm>=obs)", justify="right")

        for method_name, method_result in results["methods"].items():
            if method_result.get("status") != "ok":
                metric_table.add_row(method_name, "n/a", "n/a", "n/a", "n/a")
                continue

            z_score = method_result.get("z_score")
            metric_table.add_row(
                method_name,
                f"{method_result['observed_silhouette']:.4f}",
                f"{method_result['perm_mean']:.4f}",
                f"{z_score:.2f}" if z_score is not None else "n/a",
                f"{method_result['p_ge_obs']:.4f}",
            )
        console.print(metric_table)

        out = Path(output_dir) if output_dir else Path("results/data/phase4_inference")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "projection_bounded_check.json")

        store.save_run(run)


if __name__ == "__main__":
    args = _parse_args()
    run_experiment(seed=args.seed, output_dir=args.output_dir)
