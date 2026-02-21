#!/usr/bin/env python3
"""Phase 12I: Blueprint Synthesis (Physical Tool Map)."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase12_mechanical.jigsaw_solver import BlueprintSynthesizer

INPUT_PATH = project_root / "results/data/phase12_mechanical/columnar_reconstruction.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/physical_blueprint.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12I: Blueprint Synthesis (The Voynich Engine Blueprint)[/bold blue]")
    
    if not Path(INPUT_PATH).exists():
        console.print(f"[red]Error: {INPUT_PATH} not found.[/red]")
        return

    with open(INPUT_PATH) as f:
        data = json.load(f)
    columns = data.get("results", data)
    
    # Convert keys back to int
    columns = {int(k): v for k, v in columns.items()}
    
    synthesizer = BlueprintSynthesizer()
    blueprint = synthesizer.synthesize_blueprint(columns, max_rows=10)
    
    saved = ProvenanceWriter.save_results({"blueprint": blueprint}, OUTPUT_PATH)
    console.print(f"\n[green]Blueprint synthesized and saved to:[/green] {saved['latest_path']}")
    
    # Display the Blueprint
    table = Table(title="The Voynich Engine: Conjectured Physical Layout")
    for i in range(1, 11): # First 10 positions
        table.add_column(f"Pos {i}", style="cyan")
        
    for row in blueprint:
        table.add_row(*row[:10])
        
    console.print(table)

if __name__ == "__main__":
    main()
