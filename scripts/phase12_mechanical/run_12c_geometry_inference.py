#!/usr/bin/env python3
"""Phase 12C: Geometry Inference."""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.provenance import ProvenanceWriter
from phase12_mechanical.geometry_inference import GeometryInferrer

INPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/geometry_inference.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12C: Geometry Inference[/bold blue]")
    
    if not Path(INPUT_PATH).exists():
        console.print(f"[red]Error: {INPUT_PATH} not found. Run 12a first.[/red]")
        return

    with open(INPUT_PATH) as f:
        data = json.load(f)
    slips = data.get("results", data).get("slips", [])
    
    inferrer = GeometryInferrer()
    results = inferrer.analyze_slip_geometry(slips)
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Analysis complete. Geometry inference saved.[/green]")
    
    # Summary Table: Positions
    table = Table(title="Slip Frequency by Token Position")
    table.add_column("Position", justify="right")
    table.add_column("Count", justify="right", style="bold cyan")
    
    # Sort positions
    pos_data = sorted(results["positional_distribution"].items())
    for pos, count in pos_data[:15]:
        table.add_row(str(pos), str(count))
    console.print(table)
    
    console.print(f"\nMean Slip Position: {results['mean_slip_position']:.2f}")
    console.print(f"Mean Word Length: {results['mean_word_length']:.2f}")

if __name__ == "__main__":
    main()
