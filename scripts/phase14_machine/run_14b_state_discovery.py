#!/usr/bin/env python3
"""Phase 14B: State-Space Discovery."""

import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase14_machine.state_discovery import StateSpaceSolver  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase14_machine/state_space_discovery.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 14B: State-Space Discovery (The Mask Profiles)[/bold magenta]")

    # 1. Load Data
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)

    # 2. Build and Cluster Transition Profiles
    solver = StateSpaceSolver()
    console.print("Building sliding-window transition vectors...")
    vectors = solver.build_transition_vectors(lines)

    console.print(f"Clustering {len(vectors)} profiles into 3 states...")
    results = solver.solve_states(vectors, num_states=3)

    # 3. Save
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Success! State-space profiles saved to:[/green] {saved['latest_path']}")

    # Summary of State Persistence
    from collections import Counter
    counts = Counter(results['labels'])

    table = Table(title="Mechanical State Distribution")
    table.add_column("State ID", style="cyan")
    table.add_column("Window Count", justify="right")
    table.add_column("Persistence %", justify="right", style="bold green")

    total = sum(counts.values())
    for sid, count in counts.items():
        table.add_row(str(sid), str(count), f"{(count/total)*100:.1f}%")
    console.print(table)

if __name__ == "__main__":
    main()
