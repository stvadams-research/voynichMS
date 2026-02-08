#!/usr/bin/env python3
"""
Method B Runner: Network and Multi-Feature Analysis

Benchmarks real vs. semantic vs. synthetic vs. shuffled text.
"""

import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from inference.network_features.analyzer import NetworkAnalyzer

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
        "[bold blue]Method B: Network Feature Analysis[/bold blue]\n"
        "Testing for language-like network topology signatures",
        border_style="blue"
    ))

    with active_run(config={"command": "run_network_phase4", "seed": 42}) as run:
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
        output_dir = Path("results/phase_4")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "network_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_experiment()
