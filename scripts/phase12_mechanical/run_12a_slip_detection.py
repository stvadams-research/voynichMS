#!/usr/bin/env python3
"""Phase 12A: Mechanical Slip Detection."""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase12_mechanical.slip_detection import MechanicalSlipDetector

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12A: Mechanical Slip Detection[/bold blue]")
    
    if not Path("data/voynich.db").exists():
        console.print("[red]Error: data/voynich.db not found.[/red]")
        return

    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    
    detector = MechanicalSlipDetector(min_transition_count=2)
    
    console.print(f"Building empirical lattice from {len(lines)} lines...")
    detector.build_model(lines)
    
    console.print("Scanning for vertical offsets...")
    slips = detector.detect_slips(lines)
    
    # Save results
    final_output = {
        "total_lines_scanned": len(lines),
        "total_slips_detected": len(slips),
        "slips": slips
    }
    
    saved = ProvenanceWriter.save_results(final_output, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Detected {len(slips)} potential mechanical slips.[/green]")
    console.print(f"Results saved to: {saved['latest_path']}")
    
    # Summary Table
    if slips:
        table = Table(title="Sample Mechanical Slips (Top 20)")
        table.add_column("Line", justify="right")
        table.add_column("Pos", justify="right")
        table.add_column("Word", style="cyan")
        table.add_column("Actual Context", style="dim")
        table.add_column("Vertical Context", style="bold green")
        
        for s in slips[:20]:
            table.add_row(
                str(s['line_index']),
                str(s['token_index']),
                s['word'],
                f"{s['actual_context'][0]} @ {s['actual_context'][1]}",
                f"{s['vertical_context'][0]} @ {s['vertical_context'][1]}"
            )
        console.print(table)

if __name__ == "__main__":
    main()
