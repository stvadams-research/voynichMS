#!/usr/bin/env python3
"""Phase 14M: Refined MDL Showdown.

Proves parsimony by comparing Lattice L(total) against an equal-budget 
Markov baseline.
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase14_machine.evaluation_engine import EvaluationEngine

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/refined_mdl_stats.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 14M: Refined MDL Showdown[/bold cyan]")
    
    # 1. Load Data
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    all_tokens = [t for l in real_lines for t in l]
    
    # 2. Load Lattice
    with open(PALETTE_PATH) as f:
        p_data = json.load(f)
    model_data = p_data.get("results", p_data)
    lattice_map = model_data.get("lattice_map", {})
    window_contents = model_data.get("window_contents", {})
    
    vocab = set(lattice_map.keys())
    engine = EvaluationEngine(vocab)
    
    # 3. Calculate Lattice MDL
    # Params: Map (7755) + Window Contents (7755) = 15510 params
    lattice_params = len(lattice_map) + sum(len(v) for v in window_contents.values())
    lattice_mdl = engine.calculate_mdl_bits(all_tokens, lattice_params)
    
    # 4. Construct Equal-Budget Markov Baseline
    # We allow the Markov model EXACTLY lattice_params parameter entries.
    # We calculate the residual entropy of the Markov-O1 model.
    markov_mdl = engine.calculate_mdl_bits(all_tokens, lattice_params, is_markov=True)
    
    # 5. Save and Report
    results = {
        "lattice": lattice_mdl,
        "markov_equal_budget": markov_mdl,
        "is_parsimonious": lattice_mdl['l_total'] < markov_mdl['l_total']
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    table = Table(title="Refined MDL Comparison (Bits)")
    table.add_column("Model", style="cyan")
    table.add_column("L(model)", justify="right")
    table.add_column("L(data|model)", justify="right")
    table.add_column("L(total)", justify="right", style="bold green")
    
    table.add_row("Lattice", f"{lattice_mdl['l_model']:.0f}", f"{lattice_mdl['l_data_given_model']:.0f}", f"{lattice_mdl['l_total']:.0f}")
    table.add_row("Markov (Equal Budget)", f"{markov_mdl['l_model']:.0f}", f"{markov_mdl['l_data_given_model']:.0f}", f"{markov_mdl['l_total']:.0f}")
    
    console.print(table)

if __name__ == "__main__":
    main()
