#!/usr/bin/env python3
"""Phase 14F: Noise Register.

Identifies and categorizes every token the model cannot explain.
"""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter, defaultdict

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
SLIP_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/noise_register.json"
console = Console()

def main():
    console.print("[bold yellow]Phase 14F: Noise Register (The Failure Audit)[/bold yellow]")
    
    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH, "r") as f:
        p_data = json.load(f)
    results = p_data.get("results", p_data)
    lattice_map = results.get("lattice_map", {})
    window_contents = results.get("window_contents", {})
    
    # 2. Load Known Slips
    slips_by_pos = {}
    if SLIP_PATH.exists():
        with open(SLIP_PATH, "r") as f:
            slip_data = json.load(f)
        for s in slip_data.get("results", {}).get("slips", []):
            slips_by_pos[(s['line_index'], s['token_index'])] = s['type']
    
    # 3. Load Real Corpus
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    
    # 4. Audit Failures
    register = []
    current_window = 0
    failure_counts = Counter()
    
    for l_idx, line in enumerate(real_lines):
        # We assume the first word of each line 'resets' the window or we follow from previous
        # For simplicity, let's track the window across lines if they are sequential
        for t_idx, word in enumerate(line):
            is_valid = False
            # Check current window + neighbors (+/- 1 for scribe drift)
            for offset in [-1, 0, 1]:
                check_win = str((current_window + offset) % len(window_contents))
                if word in window_contents.get(check_win, []):
                    is_valid = True
                    current_window = int(check_win)
                    break
            
            if not is_valid:
                # Failure detected
                slip_type = slips_by_pos.get((l_idx, t_idx), "Unknown Noise")
                register.append({
                    "line": l_idx,
                    "pos": t_idx,
                    "word": word,
                    "category": slip_type,
                    "predicted_window": current_window
                })
                failure_counts[slip_type] += 1
                
                # In case of failure, we 'snap' to the word's real window if possible
                if word in lattice_map:
                    current_window = lattice_map[word]
            else:
                # Move to next window
                current_window = lattice_map.get(word, (current_window + 1) % len(window_contents))
                
    # 5. Save and Report
    total_tokens = sum(len(l) for l in real_lines)
    results = {
        "total_tokens": total_tokens,
        "total_failures": len(register),
        "failure_rate": len(register) / total_tokens if total_tokens > 0 else 0,
        "categories": dict(failure_counts),
        "failures": register[:1000] # Cap for JSON size
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Noise register compiled.[/green]")
    console.print(f"Total Failure Rate: [bold]{(len(register)/total_tokens)*100:.2f}%[/bold]")
    
    table = Table(title="Failure Categorization")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    
    for cat, count in failure_counts.items():
        table.add_row(cat, str(count))
    console.print(table)

if __name__ == "__main__":
    main()
