#!/usr/bin/env python3
"""Phase 12G: Physical Adjacency Mapping."""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase12_mechanical.jigsaw_solver import JigsawAdjacencyMapper
from phase1_foundation.core.provenance import ProvenanceWriter

INPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/physical_adjacency.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12G: Physical Adjacency Mapping (The Jigsaw Solver)[/bold blue]")
    
    if not Path(INPUT_PATH).exists():
        console.print(f"[red]Error: {INPUT_PATH} not found.[/red]")
        return

    with open(INPUT_PATH, "r") as f:
        data = json.load(f)
    slips = data.get("results", data).get("slips", [])
    
    mapper = JigsawAdjacencyMapper()
    results = mapper.build_adjacency_graph(slips)
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Physical adjacency map saved to:[/green] {saved['latest_path']}")
    
    # Table 1: Most Connected Physical Anchors
    table_nodes = Table(title="Top Physical Anchors (Most Connected Words on Tool)")
    table_nodes.add_column("Word", style="cyan")
    table_nodes.add_column("Connectivity", justify="right", style="bold green")
    for node, score in results["top_physical_anchors"][:15]:
        table_nodes.add_row(node, f"{score:.3f}")
    console.print(table_nodes)
    
    # Table 2: Frequent Adjacencies
    table_edges = Table(title="Frequent Physical Adjacencies (Neighbors on Tool)")
    table_edges.add_column("Pair", style="cyan")
    table_edges.add_column("Frequency", justify="right", style="bold yellow")
    for item in results["frequent_adjacencies"][:15]:
        pair_str = f"{item['pair'][0]} <--> {item['pair'][1]}"
        table_edges.add_row(pair_str, str(item['count']))
    console.print(table_edges)

if __name__ == "__main__":
    main()
