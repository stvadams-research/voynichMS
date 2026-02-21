#!/usr/bin/env python3
"""Phase 16A: Ergonomic Costing.

Calculates the 'Physical Effort Score' for every word in the vocabulary 
based on sub-glyph stroke complexity.
"""

import json
import re
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
STROKE_PATH = project_root / "results/data/phase11_stroke/stroke_features.json"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase16_physical/word_ergonomic_costs.json"
sys.path.insert(0, str(project_root / "src"))
from phase1_foundation.runs.manager import active_run  # noqa: E402

console = Console()

def clean_token(t):
    # Remove metadata like <!00:00>, <%> etc
    t = re.sub(r'<!.*?>', '', t)
    t = re.sub(r'<.*?>', '', t)
    t = re.sub(r'[,\.;]', '', t)
    return t.strip()

def main():
    console.print("[bold magenta]Phase 16A: Ergonomic Costing (The Physical Hand)[/bold magenta]")
    
    if not STROKE_PATH.exists() or not PALETTE_PATH.exists():
        console.print("[red]Error: Missing Phase 11 or Phase 14 data artifacts.[/red]")
        return

    # 1. Load Stroke Features
    with open(STROKE_PATH) as f:
        stroke_data = json.load(f)["results"]
    
    token_features = stroke_data["token_type_features"]
    
    # Map cleaned token -> mean stroke count
    # mean_profile index 5 is 'stroke_count'
    word_to_strokes = {}
    for raw_t, feats in token_features.items():
        clean = clean_token(raw_t)
        if not clean:
            continue
        word_to_strokes[clean] = feats["mean_profile"][5]

    # 2. Load Palette (Target Vocabulary)
    with open(PALETTE_PATH) as f:
        p_data = json.load(f)["results"]
    lattice_map = p_data["lattice_map"]
    
    # 3. Assign Costs
    costs = {}
    missing_count = 0
    
    for word in lattice_map:
        if word in word_to_strokes:
            # Base cost: strokes per glyph * word length
            # Actually mean_profile is already aggregate per token in Phase 11?
            # Let's check aggregate_profile index 5
            base_cost = word_to_strokes[word]
            # Complexity bonus for gallows/descenders
            # Index 0: gallows, Index 3: descender
            gallows = token_features.get(word, {}).get("mean_profile", [0]*6)[0]
            descenders = token_features.get(word, {}).get("mean_profile", [0]*6)[3]
            
            # Total Effort = Strokes + (2.0 * gallows) + (1.5 * descenders)
            costs[word] = float(base_cost + (2.0 * gallows) + (1.5 * descenders))
        else:
            # Estimation for missing tokens: length * avg stroke count (1.5)
            costs[word] = float(len(word) * 1.5)
            missing_count += 1
            
    # 4. Save and Report
    results = {
        "num_words": len(costs),
        "num_matched": len(costs) - missing_count,
        "avg_cost": sum(costs.values()) / len(costs) if costs else 0,
        "word_costs": costs
    }
    
    from phase1_foundation.core.provenance import ProvenanceWriter
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    console.print(f"\n[green]Success! Physical costs assigned to {len(costs)} words.[/green]")
    console.print(f"Average Effort Score: [bold]{results['avg_cost']:.2f}[/bold]")
    console.print(f"Matched from Stroke Data: [bold]{results['num_matched']}[/bold]")

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_16a_ergonomic_costing"}):
        main()
