#!/usr/bin/env python3
"""
Method B Runner: Network and Multi-Feature Analysis

Benchmarks real vs. semantic vs. synthetic vs. shuffled text.
"""

import argparse
import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from phase1_foundation.core.provenance import ProvenanceWriter
from phase4_inference.network_features.analyzer import NetworkAnalyzer

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
    parser = argparse.ArgumentParser(description="Method B: Network Feature Analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_experiment(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Method B: Network Feature Analysis[/bold blue]\n"
        "Testing for language-like network topology signatures",
        border_style="blue"
    ))

    with active_run(config={"command": "run_network_phase4", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = NetworkAnalyzer(max_tokens=15000) # Balanced for scale/speed
        
        datasets = {
            "Voynich (Real)": "voynich_real",
            "Latin (Semantic)": "latin_classic",
            "Self-Citation": "self_citation",
            "Table-Grille": "table_grille",
            "Mechanical Reuse": "mechanical_reuse",
            "Shuffled (Global)": "shuffled_global"
        }
        
        results = {}
        
        table = Table(title="Network Features Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Clustering", justify="right")
        table.add_column("Assortativity", justify="right")
        table.add_column("Zipf Alpha", justify="right")
        table.add_column("TTR", justify="right")

        for label, dataset_id in datasets.items():
            console.print(f"Analyzing: {label}...")
            tokens = get_tokens(store, dataset_id)
            
            if not tokens:
                continue
                
            res = analyzer.analyze(tokens)
            results[dataset_id] = res
            
            table.add_row(
                label,
                f"{res['avg_clustering']:.4f}",
                f"{res['assortativity']:.4f}",
                f"{res['zipf_alpha']:.4f}",
                f"{res['ttr']:.4f}"
            )
            
        console.print(table)
        
        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase4_inference")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "network_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_experiment(seed=args.seed, output_dir=args.output_dir)
