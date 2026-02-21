#!/usr/bin/env python3
"""Phase 16C: Layout Projection.

Tests whether the sequential transitions in the manuscript minimize 
physical travel distance in a 2D Grid vs. a Circular Volvelle layout.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.runs.manager import active_run  # noqa: E402

PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
TRACE_PATH = project_root / "results/data/phase15_selection/choice_stream_trace.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical/layout_projection.json"
console = Console()

def get_grid_coords(win_id, cols=10):
    row = win_id // cols
    col = win_id % cols
    return (float(col), float(row))

def get_circle_coords(win_id, num_wins=50, radius=10):
    angle = (2 * math.pi * win_id) / num_wins
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    return (x, y)

def dist(p1, p2):
    return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

def main():
    console.print("[bold cyan]Phase 16C: Layout Projection (Geometric Optimization)[/bold cyan]")
    
    if not PALETTE_PATH.exists() or not TRACE_PATH.exists():
        return

    # 1. Load Data
    with open(TRACE_PATH) as f:
        choices = json.load(f)["results"]["choices"]
    
    # 2. Test Geometries
    grid_total_dist = 0
    circle_total_dist = 0
    num_transitions = 0
    
    for i in range(1, len(choices)):
        w1 = choices[i-1]['window_id']
        w2 = choices[i]['window_id']
        
        # Grid Distance (10x5)
        grid_total_dist += dist(get_grid_coords(w1), get_grid_coords(w2))
        
        # Circular Distance
        circle_total_dist += dist(get_circle_coords(w1), get_circle_coords(w2))
        
        num_transitions += 1
        if num_transitions > 10000:
            break  # Sample for speed

    # 3. Random Baseline (seeded for reproducibility)
    rng = np.random.default_rng(seed=42)
    rand_grid_dist = 0
    for _ in range(1000):
        w1 = rng.integers(0, 50)
        w2 = rng.integers(0, 50)
        rand_grid_dist += dist(get_grid_coords(w1), get_grid_coords(w2))
    avg_rand_grid = rand_grid_dist / 1000
    
    avg_grid = grid_total_dist / num_transitions
    avg_circle = circle_total_dist / num_transitions
    
    # 4. Save and Report
    results = {
        "avg_grid_dist": avg_grid,
        "avg_circle_dist": avg_circle,
        "random_baseline_grid": avg_rand_grid,
        "grid_efficiency": (avg_rand_grid - avg_grid) / avg_rand_grid
    }
    
    from phase1_foundation.core.provenance import ProvenanceWriter
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
