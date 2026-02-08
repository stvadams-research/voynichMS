#!/usr/bin/env python3
"""
Method A Runner: Information Clustering (Montemurro style)

Benchmarks real vs. semantic vs. synthetic vs. shuffled text.
"""

import sys
from pathlib import Path
import json
import random
from collections import Counter

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from inference.info_clustering.analyzer import MontemurroAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_tokens(store, dataset_id):
    session = store.Session()
    try:
        from foundation.storage.metadata import PageRecord
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

def run_experiment():
    console.print(Panel.fit(
        "[bold blue]Method A: Information Clustering Analysis[/bold blue]\n"
        "Testing for topical structure signatures across Phase 4 Corpora",
        border_style="blue"
    ))

    with active_run(config={"command": "run_montemurro_phase4", "seed": 42}) as run:
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
        output_dir = Path("results/phase_4")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "montemurro_phase4_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_experiment()