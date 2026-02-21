#!/usr/bin/env python3
"""Phase 14Q: Residual Analysis (The 35%).

Categorizes inadmissible transitions to determine if they are pure noise 
or 'Extended Drift' (Mechanical error).
"""

import json
import sys
from collections import Counter
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/residual_analysis.json"
console = Console()

def main():
    msg_title = "[bold yellow]Phase 14Q: Residual Analysis (Spatial Mapping of Error)[/bold yellow]"
    console.print(msg_title)
    
    if not PALETTE_PATH.exists():
        return

    # 1. Load Model
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}
    num_wins = len(window_contents)
    
    # 2. Load Real Data
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    
    # 3. Analyze Residuals
    categories = Counter()
    current_window = 0
    total_clamped = 0
    
    for line in real_lines:
        for word in line:
            if word not in lattice_map:
                continue
            total_clamped += 1
            
            # Distance search
            found_dist = None
            # Search up to distance 10
            for dist in range(0, 11):
                for direction in [1, -1]:
                    check_win = (current_window + (dist * direction)) % num_wins
                    if word in window_contents.get(check_win, []):
                        found_dist = dist
                        break
                if found_dist is not None:
                    break
            
            if found_dist is None:
                categories["Extreme Jump (>10)"] += 1
                current_window = lattice_map[word]
            elif found_dist <= 1:
                categories["Admissible (Dist 0-1)"] += 1
                current_window = lattice_map.get(word, (current_window + 1) % num_wins)
            elif found_dist <= 3:
                categories["Extended Drift (Dist 2-3)"] += 1
                current_window = lattice_map.get(word, (current_window + 1) % num_wins)
            else:
                categories["Mechanical Slip (Dist 4-10)"] += 1
                current_window = lattice_map.get(word, (current_window + 1) % num_wins)

    # 4. Save and Report
    ext_rate = categories["Admissible (Dist 0-1)"] + categories["Extended Drift (Dist 2-3)"]
    ext_admissibility = ext_rate / total_clamped
    results = {
        "total_clamped": total_clamped,
        "categories": dict(categories),
        "extended_admissibility_rate": ext_admissibility
    }
    
    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    table = Table(title="Transition Category Distribution")
    table.add_column("Category", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percent", justify="right", style="bold green")
    
    for cat, count in categories.items():
        table.add_row(cat, str(count), f"{(count/total_clamped)*100:.2f}%")
    console.print(table)
    
    msg_out = (
        f"\n[bold green]Extended Admissibility (Drift <= 3):[/bold green] "
        f"{ext_admissibility*100:.2f}%"
    )
    console.print(msg_out)

if __name__ == "__main__":
    main()
