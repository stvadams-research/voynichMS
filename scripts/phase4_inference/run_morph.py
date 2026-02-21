#!/usr/bin/env python3
"""
Method E Runner: Unsupervised Morphology Induction

Benchmarks real vs. semantic vs. synthetic vs. shuffled text.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import (
    MetadataStore,
    TranscriptionLineRecord,
    TranscriptionTokenRecord,
)
from phase4_inference.morph_induction.analyzer import MorphologyAnalyzer

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
    parser = argparse.ArgumentParser(description="Method E: Morphology Induction Analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_experiment(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Method E: Morphology Induction Analysis[/bold blue]\n"
        "Testing for morphological consistency signatures",
        border_style="blue"
    ))

    with active_run(config={"command": "run_morph_phase4", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = MorphologyAnalyzer()
        
        datasets = {
            "Voynich (Real)": "voynich_real",
            "Latin (Semantic)": "latin_classic",
            "Self-Citation": "self_citation",
            "Table-Grille": "table_grille",
            "Mechanical Reuse": "mechanical_reuse",
            "Shuffled (Global)": "shuffled_global"
        }
        
        results = {}
        
        table = Table(title="Morphology Consistency Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Unique Words", justify="right")
        table.add_column("Consistency Score", justify="right")
        table.add_column("Top Suffixes")

        for label, dataset_id in datasets.items():
            console.print(f"Analyzing: {label}...")
            tokens = get_tokens(store, dataset_id)
            
            if not tokens: continue
                
            res = analyzer.analyze(tokens)
            results[dataset_id] = res
            
            suffix_str = ", ".join([s for s, c in res['top_suffixes'][:3]])
            table.add_row(
                label,
                str(res['num_unique_words']),
                f"{res['morph_consistency']:.4f}",
                suffix_str
            )
            
        console.print(table)
        
        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase4_inference")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "morph_results.json")

        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_experiment(seed=args.seed, output_dir=args.output_dir)
