#!/usr/bin/env python3
"""Phase 14A: Global Palette Solver."""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase14_machine.palette_solver import GlobalPaletteSolver

DB_PATH = "sqlite:///data/voynich.db"
SLIPS_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
console = Console()

import argparse


def main():
    parser = argparse.ArgumentParser(description="Run Phase 14A: Global Palette Solver.")
    parser.add_argument("--full", action="store_true", help="Solve for the full 8,000+ token vocabulary.")
    args = parser.parse_args()

    console.print("[bold magenta]Phase 14A: Global Palette Solver (High-Fidelity Grid)[/bold magenta]")
    
    if not SLIPS_PATH.exists():
        console.print(f"[red]Error: {SLIPS_PATH} not found. Run 12a first.[/red]")
        return

    # 1. Load Data
    with open(SLIPS_PATH) as f:
        slips_data = json.load(f)
    slips = slips_data.get("results", slips_data).get("slips", [])
    
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
            
    console.print(f"Loaded [bold cyan]{len(lines)}[/bold cyan] canonical lines from Zandbergen-Landini.")
    
    # 2. Solve Palette
    solver = GlobalPaletteSolver()
    # Use top 2000 by default, or None if --full is provided
    top_n = None if args.full else 2000
    solver.ingest_data(slips, lines, top_n=top_n)
    
    pos_coords = solver.solve_grid(iterations=50 if args.full else 30)
    lattice_data = solver.cluster_lattice(pos_coords, num_windows=50)

    # 2b. Spectral reordering: renumber windows for optimal sequential access
    reordered = solver.reorder_windows(
        lattice_data["word_to_window"],
        lattice_data["window_contents"],
        lines,
    )

    # 3. Save High-Fidelity Blueprint
    results = {
        "num_tokens_mapped": len(pos_coords),
        "is_full_vocabulary": args.full,
        "lattice_map": reordered["word_to_window"],
        "window_contents": reordered["window_contents"],
        "raw_coordinates": {w: list(c) for w, c in pos_coords.items()}
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Success! Palette grid saved to:[/green] {saved['latest_path']}")
    console.print(f"Total tokens mapped: [bold cyan]{len(pos_coords)}[/bold cyan]")

if __name__ == "__main__":
    main()
