#!/usr/bin/env python3
"""Phase 16A: Ergonomic Costing.

Calculates the 'Physical Effort Score' for every word in the vocabulary 
based on sub-glyph stroke complexity.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase16_physical_grounding.ergonomics import ErgonomicCostAnalyzer  # noqa: E402

STROKE_PATH = project_root / "results/data/phase11_stroke/stroke_features.json"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical_grounding/word_ergonomic_costs.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 16A: Ergonomic Costing (The Physical Hand)[/bold magenta]")

    if not STROKE_PATH.exists() or not PALETTE_PATH.exists():
        console.print(f"[red]Error: Missing Phase 11 or Phase 14 data artifacts at {STROKE_PATH} or {PALETTE_PATH}.[/red]")
        return

    # 1. Load Stroke Features
    with open(STROKE_PATH) as f:
        stroke_data = json.load(f)["results"]
    token_features = stroke_data["token_type_features"]

    # 2. Load Palette (Target Vocabulary)
    with open(PALETTE_PATH) as f:
        p_data = json.load(f)["results"]
    lattice_map = p_data["lattice_map"]

    # 3. Assign Costs
    analyzer = ErgonomicCostAnalyzer(token_features)
    costs, missing_count = analyzer.batch_process(lattice_map.keys())

    # 4. Save and Report
    results = {
        "num_words": len(costs),
        "num_matched": len(costs) - missing_count,
        "avg_cost": sum(costs.values()) / len(costs) if costs else 0,
        "word_costs": costs
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print(f"\n[green]Success! Physical costs assigned to {len(costs)} words.[/green]")
    console.print(f"Average Effort Score: [bold]{results['avg_cost']:.2f}[/bold]")
    console.print(f"Matched from Stroke Data: [bold]{results['num_matched']}[/bold]")

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_16a_ergonomic_costing"}):
        main()
