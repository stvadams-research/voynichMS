#!/usr/bin/env python3
"""
Method A Runner: Information Clustering (Montemurro style)

Benchmarks real vs. semantic vs. synthetic vs. shuffled text.
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
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import (  # noqa: E402
    MetadataStore,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase4_inference.info_clustering.analyzer import MontemurroAnalyzer  # noqa: E402

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_tokens(store, dataset_id):
    session = store.Session()
    try:
        from phase1_foundation.storage.metadata import PageRecord
        tokens = (
            session.query(TranscriptionTokenRecord.content)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .all()
        )
        return [t[0] for t in tokens]
    finally:
        session.close()

def _parse_args():
    parser = argparse.ArgumentParser(description="Method A: Information Clustering Analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_experiment(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Method A: Information Clustering Analysis[/bold blue]\n"
        "Testing for topical structure signatures across Phase 4 Corpora",
        border_style="blue"
    ))

    with active_run(config={"command": "run_montemurro_phase4", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = MontemurroAnalyzer(num_sections=20)

        datasets = {
            "Voynich (Real)": "voynich_real",
            "Latin (Semantic)": "latin_classic",
            "Self-Citation": "self_citation",
            "Table-Grille": "table_grille",
            "Mechanical Reuse": "mechanical_reuse",
            "Shuffled (Global)": "shuffled_global"
        }

        results = {}

        table = Table(title="Information Clustering Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("Avg Info (bits)", justify="right")
        table.add_column("Max Info (bits)", justify="right")
        table.add_column("Keywords (>1bit)", justify="right")

        for label, dataset_id in datasets.items():
            console.print(f"Analyzing: {label}...")
            tokens = get_tokens(store, dataset_id)

            if not tokens:
                console.print(f"  [red]Warning: No tokens found for {dataset_id}[/red]")
                continue

            res = analyzer.calculate_information(tokens)
            metrics = analyzer.get_summary_metrics(res)

            results[dataset_id] = {
                "metrics": metrics,
                "top_keywords": res['top_keywords'][:20]
            }

            table.add_row(
                label,
                str(len(tokens)),
                f"{metrics['avg_info']:.4f}",
                f"{metrics['max_info']:.4f}",
                str(metrics['num_keywords'])
            )

        console.print(table)

        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase4_inference")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "montemurro_phase4_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_experiment(seed=args.seed, output_dir=args.output_dir)
