#!/usr/bin/env python3
"""Phase 16C: Layout Projection.

Tests whether the sequential transitions in the manuscript minimize 
physical travel distance in a 2D Grid vs. a Circular Volvelle layout.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase16_physical_grounding.layout import LayoutAnalyzer  # noqa: E402

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
TRACE_PATH = project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical_grounding/layout_projection.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 16C: Layout Projection (Geometric Optimization)[/bold cyan]")

    if not PALETTE_PATH.exists() or not TRACE_PATH.exists():
        console.print(f"[red]Error: Palette or Trace data missing at {PALETTE_PATH} or {TRACE_PATH}.[/red]")
        return

    # 1. Load Data
    with open(TRACE_PATH) as f:
        choices = json.load(f)["results"]["choices"]
    window_ids = [c['window_id'] for c in choices]

    # 2. Test Geometries
    analyzer = LayoutAnalyzer(num_windows=50)
    analysis = analyzer.analyze_transitions(window_ids, limit=10000)
    
    # 3. Random Baseline
    avg_rand_grid = analyzer.calculate_random_baseline(num_samples=1000, seed=42)
    
    avg_grid = analysis["avg_grid_dist"]
    avg_circle = analysis["avg_circle_dist"]

    # 4. Save and Report
    results = {
        "avg_grid_dist": avg_grid,
        "avg_circle_dist": avg_circle,
        "random_baseline_grid": avg_rand_grid,
        "grid_efficiency": (avg_rand_grid - avg_grid) / avg_rand_grid if avg_rand_grid > 0 else 0.0
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print("\n[green]Success! Geometric analysis complete.[/green]")
    console.print(f"Average Grid Travel: [bold]{avg_grid:.2f} units[/bold]")
    console.print(f"Average Circular Travel: [bold]{avg_circle:.2f} units[/bold]")
    eff_pct = results['grid_efficiency'] * 100
    console.print(
        f"Grid Layout Efficiency: [bold green]{eff_pct:.2f}% "
        f"improvement over random[/bold green]"
    )

    if results['grid_efficiency'] > 0.10:
        console.print(
            "\n[bold green]VERIFIED:[/bold green] The lattice transitions "
            "are physically optimized for a 2D Grid/Grille layout."
        )
    else:
        console.print(
            "\n[bold yellow]CONDITION:[/bold yellow] No strong physical "
            "optimization found for these specific geometries."
        )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_16c_layout_projection"}):
        main()
