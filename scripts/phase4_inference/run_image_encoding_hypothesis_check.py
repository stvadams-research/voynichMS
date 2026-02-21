#!/usr/bin/env python3
# ruff: noqa: E402
"""
Format-agnostic image-encoding hypothesis check.

Builds image-derived symbolic streams from decoded pixel data and compares them
against Voynich and existing controls using the same bounded diagnostics.
"""

import argparse
import sys
from collections import Counter
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
from phase4_inference.projection_diagnostics.discrimination import (  # noqa: E402
    DiscriminationCheckAnalyzer,
    DiscriminationCheckConfig,
)
from phase4_inference.projection_diagnostics.image_stream_controls import (  # noqa: E402
    ImageStreamConfig,
    ImageStreamControlBuilder,
)
from phase4_inference.projection_diagnostics.order_constraints import (  # noqa: E402
    OrderConstraintAnalyzer,
    OrderConstraintConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run format-agnostic image-encoding hypothesis check."
    )
    parser.add_argument("--image-glob", type=str, default="data/raw/scans/jpg/folios_1000/*.jpg")
    parser.add_argument("--max-images", type=int, default=24)
    parser.add_argument("--resize-width", type=int, default=256)
    parser.add_argument("--quant-levels", type=int, default=16)
    parser.add_argument("--target-tokens", type=int, default=230000)
    parser.add_argument("--disc-ngram-min", type=int, default=1)
    parser.add_argument("--disc-ngram-max", type=int, default=2)
    parser.add_argument("--disc-max-features", type=int, default=2000)
    parser.add_argument("--order-token-limit", type=int, default=120000)
    parser.add_argument("--order-vocab-limit", type=int, default=500)
    parser.add_argument("--order-permutations", type=int, default=50)
    parser.add_argument("--output-name", type=str, default="image_encoding_hypothesis_check.json")
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    console.print(
        Panel.fit(
            "[bold blue]Image-Encoding Hypothesis Check[/bold blue]\n"
            "Format-agnostic image->symbol streams vs Voynich diagnostics",
            border_style="blue",
        )
    )

    with active_run(
        config={"command": "run_image_encoding_hypothesis_check_phase4", "seed": 42}
    ) as run:
        store = MetadataStore(DB_PATH)
        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
            "image_raster_q16": "Image Raster Q16",
            "image_snake_q16": "Image Snake Q16",
            "image_gradient_q16": "Image Gradient Q16",
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

        # Fairer substitution test: map image bins onto frequent Voynich tokens.
        top_tokens = [
            token
            for token, _ in Counter(dataset_tokens["voynich_real"]).most_common(
                max(2, args.quant_levels)
            )
        ]

        image_builder = ImageStreamControlBuilder(
            ImageStreamConfig(
                image_glob=args.image_glob,
                max_images=args.max_images,
                resize_width=args.resize_width,
                quant_levels=args.quant_levels,
                target_tokens=args.target_tokens,
                random_state=42,
                symbol_alphabet=tuple(top_tokens),
            )
        )
        image_controls = image_builder.build_controls()
        if image_controls.get("status") != "ok":
            raise RuntimeError(f"Failed to build image controls: {image_controls}")
        controls = image_controls["controls"]
        for key in ("image_raster_q16", "image_snake_q16", "image_gradient_q16"):
            dataset_tokens[key] = controls[key]
            console.print(f"Built {datasets[key]}: {len(controls[key])} tokens")

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
        disc = DiscriminationCheckAnalyzer(disc_cfg).analyze(dataset_tokens)
        disc["dataset_labels"] = datasets

        order_cfg = OrderConstraintConfig(
            token_limit=args.order_token_limit,
            vocab_limit=args.order_vocab_limit,
            permutations=args.order_permutations,
            random_state=42,
        )
        order = OrderConstraintAnalyzer(order_cfg).analyze(dataset_tokens)
        order["dataset_labels"] = datasets

        if disc.get("status") == "ok":
            table = Table(title="Voynich Closest Families (Discrimination)")
            table.add_column("Rank", justify="right")
            table.add_column("Dataset", style="cyan")
            table.add_column("Cosine Distance", justify="right")
            for rank, row in enumerate(disc["voynich_summary"]["closest_centroids"][:8], start=1):
                table.add_row(
                    str(rank),
                    datasets.get(row["dataset_id"], row["dataset_id"]),
                    f"{row['cosine_distance']:.4f}",
                )
            console.print(table)

        order_table = Table(title="Order Constraints: Delta vs Shuffled Baseline")
        order_table.add_column("Dataset", style="cyan")
        order_table.add_column("H2 delta", justify="right")
        order_table.add_column("H3 delta", justify="right")
        order_table.add_column("MI2 delta", justify="right")
        for dataset_id in datasets:
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

        results = {
            "status": "ok",
            "image_controls": image_controls,
            "discrimination": disc,
            "order_constraints": order,
        }

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())
