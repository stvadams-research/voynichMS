#!/usr/bin/env python3
"""Phase 14O: Logic Export.

Exports the Lattice Map and Window Contents to flat CSV files for 
independent (non-Python) implementation.
"""

import sys
import json
import csv
from pathlib import Path
from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
EXPORT_DIR = project_root / "results/data/phase14_machine/export"
console = Console()

def main():
    console.print("[bold yellow]Phase 14O: Exporting Machine Logic to CSV[/bold yellow]")
    
    if not PALETTE_PATH.exists():
        return

    # 1. Load Model
    with open(PALETTE_PATH, "r") as f:
        data = json.load(f)["results"]
    
    lattice_map = data["lattice_map"]
    window_contents = data["window_contents"]
    
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Export Lattice Map (Word -> Window)
    lattice_csv = EXPORT_DIR / "lattice_map.csv"
    with open(lattice_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["word", "target_window"])
        for word, win_id in sorted(lattice_map.items()):
            writer.writerow([word, win_id])
            
    # 3. Export Window Contents (Window -> Word List)
    contents_csv = EXPORT_DIR / "window_contents.csv"
    with open(contents_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["window_id", "word"])
        for win_id, words in sorted(window_contents.items(), key=lambda x: int(x[0])):
            for word in words:
                writer.writerow([win_id, word])
                
    console.print(f"\n[green]Success! Logic exported to:[/green] {EXPORT_DIR}")

if __name__ == "__main__":
    main()
