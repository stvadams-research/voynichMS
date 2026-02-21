#!/usr/bin/env python3
# ruff: noqa: E402
"""
Bounded Kolmogorov proxy check (compression-based).

Uses lossless compression as an approximation to algorithmic complexity and
compares observed corpora against shuffled-token null baselines.
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
from phase4_inference.projection_diagnostics.kolmogorov_proxy import (  # noqa: E402
    KolmogorovProxyAnalyzer,
    KolmogorovProxyConfig,
)

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Kolmogorov complexity proxy checks.")
    parser.add_argument("--token-limit", type=int, default=120000)
    parser.add_argument("--permutations", type=int, default=30)
    parser.add_argument("--codecs", type=str, default="zlib,lzma")
    parser.add_argument("--output-name", type=str, default="kolmogorov_proxy_check.json")
    return parser.parse_args()


def run_experiment(args: argparse.Namespace) -> None:
    codec_list = tuple(c.strip() for c in args.codecs.split(",") if c.strip())
    console.print(
        Panel.fit(
            "[bold blue]Bounded Kolmogorov Proxy Check[/bold blue]\n"
            f"Compression codecs={codec_list}, permutations={args.permutations}",
            border_style="blue",
        )
    )

    with active_run(config={"command": "run_kolmogorov_proxy_check_phase4", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        datasets = {
            "voynich_real": "Voynich (Real)",
            "latin_classic": "Latin (Semantic)",
            "self_citation": "Self-Citation",
            "table_grille": "Table-Grille",
            "mechanical_reuse": "Mechanical Reuse",
            "shuffled_global": "Shuffled (Global)",
        }

        dataset_tokens: dict[str, list[str]] = {}
        for dataset_id, label in datasets.items():
            tokens, _ = get_tokens_and_boundaries(store, dataset_id)
            dataset_tokens[dataset_id] = tokens
            console.print(f"Loaded {label}: {len(tokens)} tokens")

        config = KolmogorovProxyConfig(
            token_limit=args.token_limit,
            permutations=args.permutations,
            random_state=42,
            codecs=codec_list,
        )
        results = KolmogorovProxyAnalyzer(config).analyze(dataset_tokens)
        results["dataset_labels"] = datasets

        for codec in codec_list:
            table = Table(title=f"Kolmogorov Proxy vs Shuffled Null ({codec})")
            table.add_column("Dataset", style="cyan")
            table.add_column("Bits/Token", justify="right")
            table.add_column("Delta Bytes", justify="right")
            table.add_column("p(low)", justify="right")

            for dataset_id, label in datasets.items():
                row = results["datasets"].get(dataset_id, {})
                if row.get("status") != "ok":
                    table.add_row(label, "n/a", "n/a", "n/a")
                    continue
                cr = row["codec_results"][codec]
                table.add_row(
                    label,
                    f"{cr['observed_bits_per_token']:.3f}",
                    f"{cr['delta_bytes_vs_perm_mean']:.1f}",
                    f"{cr['p_low_bytes']:.4f}",
                )
            console.print(table)

        output_dir = Path("results/data/phase4_inference")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / args.output_name)
        store.save_run(run)


if __name__ == "__main__":
    run_experiment(parse_args())

