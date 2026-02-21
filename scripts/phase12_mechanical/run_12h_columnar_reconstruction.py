#!/usr/bin/env python3
"""Phase 12H: Columnar Reconstruction (Physical Stack Mapping)."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase12_mechanical.jigsaw_solver import ColumnarReconstructor

INPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/columnar_reconstruction.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12H: Columnar Reconstruction (Mapping the Physical Stacks)[/bold blue]")
    
    if not Path(INPUT_PATH).exists():
        console.print(f"[red]Error: {INPUT_PATH} not found.[/red]")
        return

    with open(INPUT_PATH) as f:
        data = json.load(f)
    slips = data.get("results", data).get("slips", [])
    
    reconstructor = ColumnarReconstructor()
    results = reconstructor.reconstruct_columns(slips)
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Physical stacks saved to:[/green] {saved['latest_path']}")
    
    # Summary Table: The Physical Grid (Positions 1-5 are most data-rich)
    table = Table(title="Reconstructed Physical Tool (Top Words per Position Window)")
    table.add_column("Pos 1", style="cyan")
    table.add_column("Pos 2", style="cyan")
    table.add_column("Pos 3", style="cyan")
    table.add_column("Pos 4", style="cyan")
    table.add_column("Pos 5", style="cyan")
    
    # We'll take the top 10 from each of the first 5 columns
    rows = []
    for i in range(10):
        row = []
        for pos in range(1, 6):
            stack = results.get(pos, [])
            if i < len(stack):
                row.append(f"{stack[i][0]} ({stack[i][1]})")
            else:
                row.append("-")
        rows.append(row)
        
    for r in rows:
        table.add_row(*r)
    console.print(table)

if __name__ == "__main__":
    main()
