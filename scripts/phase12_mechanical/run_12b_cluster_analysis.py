#!/usr/bin/env python3
"""Phase 12B: Mechanical Slip Cluster Analysis."""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase12_mechanical.cluster_analysis import SlipClusterAnalyzer
from phase1_foundation.core.provenance import ProvenanceWriter

INPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/slip_clusters.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12B: Mechanical Slip Cluster Analysis[/bold blue]")
    
    if not INPUT_PATH.exists():
        console.print(f"[red]Error: {INPUT_PATH} not found. Run 12a first.[/red]")
        return

    with open(INPUT_PATH, "r") as f:
        data = json.load(f)
    
    # Unwrap provenance if needed
    slips = data.get("results", data).get("slips", [])
    
    analyzer = SlipClusterAnalyzer(window_size=10)
    cluster_results = analyzer.analyze_clusters(slips)
    
    saved = ProvenanceWriter.save_results(cluster_results, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Identified {cluster_results.get('num_clusters', 0)} misalignment events.[/green]")
    
    if cluster_results.get("clusters"):
        table = Table(title="Detected Misalignment Clusters (Sustained Slips)")
        table.add_column("Start Line", justify="right")
        table.add_column("End Line", justify="right")
        table.add_column("Affected Lines", justify="right")
        table.add_column("Total Slips", justify="right", style="bold red")
        table.add_column("Slip Density", justify="right")
        
        for c in cluster_results["clusters"][:20]:
            table.add_row(
                str(c['start_line']),
                str(c['end_line']),
                str(c['num_affected_lines']),
                str(c['total_slips']),
                f"{c['density']:.3f}"
            )
        console.print(table)

if __name__ == "__main__":
    main()
