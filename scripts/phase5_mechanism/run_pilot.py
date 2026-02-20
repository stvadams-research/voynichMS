#!/usr/bin/env python3
"""
Phase 5 Pilot Benchmark

Benchmarks Voynich (Real) against a matched Pool-Reuse generator 
using the first two signature tests.
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

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from phase5_mechanism.generators.pool_generator import PoolGenerator
from phase5_mechanism.tests.copying_signatures import CopyingSignatureTest
from phase5_mechanism.tests.table_signatures import TableSignatureTest

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

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

def run_pilot():
    console.print(Panel.fit(
        "[bold blue]Phase 5: Identifiability Pilot Benchmark[/bold blue]\n"
        "Testing signature discrimination: Real vs. Pool-Reuse",
        border_style="blue"
    ))

    with active_run(config={"command": "run_pilot_benchmark", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_tokens = get_tokens(store, "voynich_real")
        
        generator = PoolGenerator(GRAMMAR_PATH, pool_size=25, seed=42)
        syn_tokens = generator.generate(target_tokens=10000) # Pilot scale
        
        # 2. Run Signature Tests
        console.print("\n[bold yellow]Step 2: Running Signature Tests[/bold yellow]")
        
        copy_tester = CopyingSignatureTest(window_size=50)
        table_tester = TableSignatureTest(min_freq=5)
        
        # A. Copying Signatures (C5.COPY.1)
        real_copy = copy_tester.calculate_variant_clustering(real_tokens[:10000])
        syn_copy = copy_tester.calculate_variant_clustering(syn_tokens)
        
        # B. Table Signatures (C5.TABLE.1)
        real_table = table_tester.calculate_successor_sharpness(real_tokens[:10000])
        syn_table = table_tester.calculate_successor_sharpness(syn_tokens)
        
        # 3. Report
        table = Table(title="Phase 5 Pilot: Signature Comparison")
        table.add_column("Signature Metric", style="cyan")
        table.add_column("Voynich (Real)", justify="right")
        table.add_column("Pool-Reuse (Syn)", justify="right")
        table.add_column("Discriminated?", justify="center")

        def check_diff(v1, v2, tol=0.1):
            return "[green]YES[/green]" if abs(v1 - v2) > tol else "[red]NO[/red]"

        table.add_row(
            "Variant Clustering (C5.COPY.1)", 
            f"{real_copy['clustering_score']:.4f}", 
            f"{syn_copy['clustering_score']:.4f}",
            check_diff(real_copy['clustering_score'], syn_copy['clustering_score'], 0.05)
        )
        
        table.add_row(
            "Successor Entropy (C5.TABLE.1)", 
            f"{real_table['mean_successor_entropy']:.4f}", 
            f"{syn_table['mean_successor_entropy']:.4f}",
            check_diff(real_table['mean_successor_entropy'], syn_table['mean_successor_entropy'], 0.2)
        )
        
        console.print(table)
        
        # Save Pilot results
        results = {
            "copying": {"real": real_copy, "syn": syn_copy},
            "table": {"real": real_table, "syn": syn_table}
        }
        
        output_dir = Path("results/data/phase5_mechanism")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "pilot_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot()
