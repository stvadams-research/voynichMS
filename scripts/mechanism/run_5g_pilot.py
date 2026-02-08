#!/usr/bin/env python3
"""
Phase 5G Pilot: Topology Collapse

Benchmarks Voynich (Real) against four topology simulators using 
overlap, coverage, and convergence signatures.
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
from mechanism.topology_collapse.simulators import (
    GridTopologySimulator, LayeredTableSimulator, DAGTopologySimulator, LatticeTopologySimulator
)
from mechanism.topology_collapse.signatures import TopologySignatureAnalyzer

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

def run_pilot_5g():
    console.print(Panel.fit(
        "[bold blue]Phase 5G: Topology Collapse Pilot[/bold blue]\n"
        "Testing non-equivalence of large-object topologies",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5g_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = TopologySignatureAnalyzer(prefix_len=2)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines(store, "voynich_real")
        
        sims = {
            "Grid (60x60)": GridTopologySimulator(GRAMMAR_PATH),
            "Layered Table": LayeredTableSimulator(GRAMMAR_PATH),
            "DAG (Stratified)": DAGTopologySimulator(GRAMMAR_PATH),
            "Lattice (Implicit)": LatticeTopologySimulator(GRAMMAR_PATH)
        }
        
        corpus_data = {"Voynich (Real)": real_lines[:5000]}
        for label, sim in sims.items():
            corpus_data[label] = sim.generate_corpus(num_lines=2000, line_len=8)
            
        # 2. Run Geometry Tests
        console.print("\n[bold yellow]Step 2: Running Topology Signatures[/bold yellow]")
        
        table = Table(title="Phase 5G Pilot: Topology Signature Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Collision Rate", justify="right")
        table.add_column("Gini (Skew)", justify="right")
        table.add_column("Convergence", justify="right")
        table.add_column("Status", justify="center")

        results = {}
        for label, lines in corpus_data.items():
            overlap = analyzer.analyze_overlap(lines)
            coverage = analyzer.analyze_coverage(lines)
            convergence = analyzer.analyze_convergence(lines)
            
            results[label] = {
                "overlap": overlap,
                "coverage": coverage,
                "convergence": convergence
            }
            
            status = "TARGET" if "Voynich" in label else ""
            table.add_row(
                label,
                f"{overlap['collision_rate']:.4f}",
                f"{coverage['gini_coefficient']:.4f}",
                f"{convergence['avg_successor_convergence']:.4f}",
                status
            )
            
        console.print(table)
        
        # Save results
        output_dir = Path("results/mechanism/topology_collapse")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "pilot_5g_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5g()
