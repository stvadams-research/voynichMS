#!/usr/bin/env python3
"""Phase 14S: Sectional Invariance Audit.

Tests if the mechanical lattice is text-intrinsic by comparing 
admissibility on the original corpus vs. a line-shuffled corpus.
"""

import json
import random
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase14_machine.evaluation_engine import EvaluationEngine  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/sectional_invariance.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 14S: Sectional Invariance Audit[/bold cyan]")

    # 1. Load Model
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = {int(k): v for k, v in data["window_contents"].items()}

    # 2. Load Real Lines
    store = MetadataStore(DB_PATH)
    lines_original = load_canonical_lines(store)

    # 3. Create Shuffled Lines
    lines_shuffled = list(lines_original)
    random.seed(42)
    random.shuffle(lines_shuffled)

    # 4. Measure Admissibility
    engine = EvaluationEngine(set(lattice_map.keys()))

    res_orig = engine.calculate_admissibility(
        lines_original, lattice_map, window_contents, fuzzy_suffix=True
    )
    res_shuf = engine.calculate_admissibility(
        lines_shuffled, lattice_map, window_contents, fuzzy_suffix=True
    )

    # 5. Report
    orig_rate = res_orig['admissibility_rate']
    shuf_rate = res_shuf['admissibility_rate']
    console.print(f"\nOriginal Admissibility: [bold green]{orig_rate*100:.2f}%[/bold green]")
    console.print(f"Shuffled Admissibility: [bold blue]{shuf_rate*100:.2f}%[/bold blue]")

    # Save Results
    results = {
        "original_admissibility": orig_rate,
        "shuffled_admissibility": shuf_rate,
        "invariant": abs(orig_rate - shuf_rate) < 0.05
    }
    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    diff = abs(orig_rate - shuf_rate)
    if diff < 0.05:
        msg = "\n[bold green]PASS:[/bold green] Lattice is text-intrinsic (Shuffle invariant)."
        console.print(msg)
    else:
        msg = "\n[bold yellow]CONDITION:[/bold yellow] Lattice is partially section-dependent."
        console.print(msg)


if __name__ == "__main__":
    main()
