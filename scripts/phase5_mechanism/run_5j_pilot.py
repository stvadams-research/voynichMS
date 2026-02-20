#!/usr/bin/env python3
"""
Phase 5J Pilot: Dependency Scope and Constraint Locality

Benchmarks Voynich (Real) against Local Transition (H1) and 
Feature-Conditioned (H2) simulators.
"""

import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase5_mechanism.dependency_scope.simulators import LocalTransitionSimulator, FeatureConditionedSimulator
from phase5_mechanism.dependency_scope.phase2_analysis import DependencyScopeAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def run_pilot_5j():
    console.print(Panel.fit(
        "[bold blue]Phase 5J: Dependency Scope Pilot[/bold blue]\n"
        "Testing: Local Transitions (H1) vs. Feature-Conditioned (H2)",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5j_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = DependencyScopeAnalyzer()
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        
        sim_h1 = LocalTransitionSimulator(GRAMMAR_PATH, vocab_size=1000, seed=42)
        h1_lines = sim_h1.generate_corpus(num_lines=2000, line_len=8)
        
        sim_h2 = FeatureConditionedSimulator(GRAMMAR_PATH, vocab_size=1000, seed=42)
        h2_lines = sim_h2.generate_corpus(num_lines=2000, line_len=8)
        
        datasets = {
            "Voynich (Real)": real_lines[:5000],
            "Local Transition (H1)": h1_lines,
            "Feature-Conditioned (H2)": h2_lines
        }
        
        # 2. Run Tests
        console.print("\n[bold yellow]Step 2: Measuring Predictive Lift[/bold yellow]")
        
        table = Table(title="Phase 5J Pilot: Dependency Scope Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("H(S|Node)", justify="right")
        table.add_column("H(S|Node,Feat)", justify="right")
        table.add_column("Predictive Lift (%)", justify="right")
        table.add_column("H(S|Node,Pos)", justify="right")

        results = {}
        for label, lines in datasets.items():
            lift_res = analyzer.analyze_predictive_lift(lines)
            pos_res = analyzer.analyze_equivalence_splitting(lines)
            
            results[label] = {
                "predictive_lift": lift_res,
                "position_lift": pos_res
            }
            
            table.add_row(
                label,
                f"{lift_res['h_node']:.4f}",
                f"{lift_res['h_node_feat']:.4f}",
                f"{lift_res['rel_lift']*100:.2f}%",
                f"{pos_res['h_node_pos']:.4f}"
            )
            
        console.print(table)
        
        # Save results
        output_dir = Path("results/data/phase5_mechanism/dependency_scope")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "pilot_5j_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5j()
