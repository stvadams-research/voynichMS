#!/usr/bin/env python3
"""
Phase 5E Pilot: Large-Object Traversal

Benchmarks Voynich (Real) against a Large-Grid traversal simulator 
using path collision (successor consistency) analysis.
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
from mechanism.large_object.simulators import LargeGridSimulator
from mechanism.large_object.collision_testing import PathCollisionTester

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def get_lines(store, dataset_id):
    session = store.Session()
    try:
        from foundation.storage.metadata import PageRecord
        tokens_recs = (
            session.query(TranscriptionTokenRecord.content, TranscriptionTokenRecord.line_id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )
        
        lines = []
        current_line = []
        last_line_id = None
        
        for content, line_id in tokens_recs:
            if last_line_id and line_id != last_line_id:
                lines.append(current_line)
                current_line = []
            current_line.append(content)
            last_line_id = line_id
        if current_line:
            lines.append(current_line)
            
        return lines
    finally:
        session.close()

def run_pilot_5e():
    console.print(Panel.fit(
        "[bold blue]Phase 5E: Large-Object Traversal Pilot[/bold blue]\n"
        "Testing for path collision signatures (Successor Consistency)",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5e_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        tester = PathCollisionTester(context_len=2)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines(store, "voynich_real")
        
        # Generator: Large 50x50 Grid
        sim = LargeGridSimulator(GRAMMAR_PATH, rows=50, cols=50)
        sim_lines = sim.generate_corpus(num_lines=2000, line_len=8)
        
        # 2. Run Collision Tests
        console.print("\n[bold yellow]Step 2: Measuring Path Stiffness[/bold yellow]")
        
        real_coll = tester.calculate_successor_consistency(real_lines[:5000])
        sim_coll = tester.calculate_successor_consistency(sim_lines)
        
        # 3. Report
        table = Table(title="Phase 5E Pilot: Path Collision Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Mean Successor Consistency", justify="right")
        table.add_column("Sample Size (Bigrams)", justify="right")
        table.add_column("Interpretation", style="dim")

        table.add_row(
            "Voynich (Real)", 
            f"{real_coll['mean_consistency']:.4f}", 
            str(real_coll['num_recurring_contexts']),
            "Ground Truth"
        )
        table.add_row(
            "Large Grid (Syn)", 
            f"{sim_coll['mean_consistency']:.4f}", 
            str(sim_coll['num_recurring_contexts']),
            "Rigid Traversal"
        )
        
        console.print(table)
        
        # Save results
        results = {
            "real": real_coll,
            "sim": sim_coll
        }
        
        output_dir = Path("results/mechanism/large_object")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "pilot_5e_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5e()
