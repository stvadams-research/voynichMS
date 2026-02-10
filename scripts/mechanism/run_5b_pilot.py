#!/usr/bin/env python3
"""
Phase 5B Pilot: Constraint Geometry

Benchmarks Voynich (Real) against Pool and Table models using dimensionality 
and reset analysis.
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

from foundation.core.queries import get_tokens_and_boundaries
from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from mechanism.generators.pool_generator import PoolGenerator
from mechanism.generators.constraint_geometry.table_variants import GeometricTableGenerator
from mechanism.constraint_geometry.latent_state import LatentStateAnalyzer
from mechanism.constraint_geometry.locality_resets import LocalityResetAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def run_pilot_5b():
    console.print(Panel.fit(
        "[bold blue]Phase 5B: Constraint Geometry Pilot[/bold blue]\n"
        "Measuring latent state dimensionality and reset behavior",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5b_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Preparing Data[/bold yellow]")
        real_tokens, real_boundaries = get_tokens_and_boundaries(store, "voynich_real")
        
        # Generator A: Pool (Size 25)
        pool_gen = PoolGenerator(GRAMMAR_PATH, pool_size=25, seed=42)
        pool_tokens = pool_gen.generate(10000)
        
        # Generator B: Table (10x10 Snake)
        table_gen = GeometricTableGenerator(GRAMMAR_PATH, rows=10, cols=10, seed=42)
        table_tokens = table_gen.generate(10000, walk_type="snake")
        
        # 2. Run Geometry Tests
        console.print("\n[bold yellow]Step 2: Running Geometry Tests[/bold yellow]")
        dim_analyzer = LatentStateAnalyzer(top_n=500)
        reset_analyzer = LocalityResetAnalyzer(min_freq=5)
        
        # A. Latent Dimensionality
        real_dim = dim_analyzer.estimate_dimensionality(real_tokens[:10000])
        pool_dim = dim_analyzer.estimate_dimensionality(pool_tokens)
        table_dim = dim_analyzer.estimate_dimensionality(table_tokens)
        
        # B. Reset Behavior (using 72 token 'dummy' boundaries for syn)
        syn_boundaries = list(range(71, 10000, 72))
        real_reset = reset_analyzer.analyze_resets(real_tokens[:10000], real_boundaries)
        pool_reset = reset_analyzer.analyze_resets(pool_tokens, syn_boundaries)
        table_reset = reset_analyzer.analyze_resets(table_tokens, syn_boundaries)
        
        # 3. Report
        table = Table(title="Phase 5B Pilot: Constraint Topology Benchmark")
        table.add_column("Dataset", style="cyan")
        table.add_column("Effective Rank (Dim)", justify="right")
        table.add_column("Reset Score", justify="right")
        table.add_column("Interpretation", style="dim")

        table.add_row(
            "Voynich (Real)", 
            str(real_dim['effective_rank_90']), 
            f"{real_reset['reset_score']:.4f}",
            "Ground Truth"
        )
        table.add_row(
            "Pool-Reuse (Syn)", 
            str(pool_dim['effective_rank_90']), 
            f"{pool_reset['reset_score']:.4f}",
            "Stochastic / High-Dim"
        )
        table.add_row(
            "Geometric Table (Syn)", 
            str(table_dim['effective_rank_90']), 
            f"{table_reset['reset_score']:.4f}",
            "Structural / Low-Dim"
        )
        
        console.print(table)
        
        # Save results
        results = {
            "real": {"dim": real_dim, "reset": real_reset},
            "pool": {"dim": pool_dim, "reset": pool_reset},
            "table": {"dim": table_dim, "reset": table_reset}
        }
        
        output_dir = Path("results/mechanism/constraint_geometry")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "pilot_5b_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5b()
