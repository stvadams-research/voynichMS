#!/usr/bin/env python3
"""Phase 14S: Sectional Invariance Audit.

Tests if the mechanical lattice is text-intrinsic by comparing 
admissibility on the original corpus vs. a line-shuffled corpus.
"""

import sys
import json
import random
from pathlib import Path
from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase14_machine.evaluation_engine import EvaluationEngine
from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/sectional_invariance.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 14S: Sectional Invariance Audit[/bold cyan]")
    
    # 1. Load Model
    with open(PALETTE_PATH, "r") as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}
    
    # 2. Load Real Lines
    store = MetadataStore(DB_PATH)
    lines_original = get_lines_from_store(store, "voynich_real")
    
    # 3. Create Shuffled Lines
    lines_shuffled = list(lines_original)
    random.seed(42)
    random.shuffle(lines_shuffled)
    
    # 4. Measure Admissibility
    engine = EvaluationEngine(set(lattice_map.keys()))
    
    res_orig = engine.calculate_admissibility(lines_original, lattice_map, window_contents, fuzzy_suffix=True)
    res_shuf = engine.calculate_admissibility(lines_shuffled, lattice_map, window_contents, fuzzy_suffix=True)
    
    # 5. Report
    console.print(f"\nOriginal Admissibility: [bold green]{res_orig['admissibility_rate']*100:.2f}%[/bold green]")
    console.print(f"Shuffled Admissibility: [bold blue]{res_shuf['admissibility_rate']*100:.2f}%[/bold blue]")
    
    # Save Results
    results = {
        "original_admissibility": res_orig['admissibility_rate'],
        "shuffled_admissibility": res_shuf['admissibility_rate'],
        "invariant": abs(res_orig['admissibility_rate'] - res_shuf['admissibility_rate']) < 0.05
    }
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    diff = abs(res_orig['admissibility_rate'] - res_shuf['admissibility_rate'])
    if diff < 0.05:
        console.print("\n[bold green]PASS:[/bold green] The lattice is text-intrinsic. (Invariant to sectional shuffling)")
    else:
        console.print("\n[bold yellow]CONDITION:[/bold yellow] The lattice is partially section-dependent.")

if __name__ == "__main__":
    main()
