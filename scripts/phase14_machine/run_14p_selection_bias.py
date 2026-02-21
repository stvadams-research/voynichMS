#!/usr/bin/env python3
"""Phase 14P: Selection Bias Analysis.

Measures the entropy of the 'choice stream' (word indices within windows)
to prove non-random selection bias.
"""

import json
import math
import sys
from collections import Counter
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/selection_bias.json"
console = Console()

def calculate_entropy(data):
    if not data:
        return 0.0
    counts = Counter(data)
    total = len(data)
    return -sum((c/total) * math.log2(c/total) for c in counts.values())

def main():
    console.print("[bold magenta]Phase 14P: Selection Bias Analysis[/bold magenta]")

    if not PALETTE_PATH.exists():
        console.print("[red]Error: Palette grid not found.[/red]")
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

    # 3. Extract Choice Stream (Indices)
    choice_stream = []
    current_window = 0
    total_clamped = 0

    for line in real_lines:
        for word in line:
            if word not in lattice_map:
                continue
            total_clamped += 1

            # Find which window word belongs to
            target_win = lattice_map[word]

            # Check if it's in the neighborhood of current state (Admissible)
            found = False
            for offset in [-1, 0, 1]:
                check_win = (current_window + offset) % num_wins
                if word in window_contents.get(check_win, []):
                    # Admissible! Record its index in THIS window
                    idx = window_contents[check_win].index(word)
                    choice_stream.append(idx)
                    current_window = check_win # Update state
                    found = True
                    break

            if not found:
                # Inadmissible transition - snap to real window but don't record choice
                current_window = target_win
            else:
                # Advance window based on lattice
                current_window = lattice_map.get(word, (current_window + 1) % num_wins)

    # 4. Analyze Entropy
    real_entropy = calculate_entropy(choice_stream)

    # Theoretical maximum entropy (Uniform choice per window)
    # We sum the log2(size of the window) for every choice actually made
    baseline_entropy_sum = 0
    current_window = 0
    for line in real_lines:
        for word in line:
            if word not in lattice_map:
                continue
            target_win = lattice_map[word]
            found = False
            for offset in [-1, 0, 1]:
                check_win = (current_window + offset) % num_wins
                if word in window_contents.get(check_win, []):
                    baseline_entropy_sum += math.log2(len(window_contents[check_win]))
                    current_window = check_win
                    found = True
                    break
            if not found:
                current_window = target_win
            else:
                current_window = lattice_map.get(word, (current_window + 1) % num_wins)

    uniform_entropy = baseline_entropy_sum / len(choice_stream) if choice_stream else 0

    # 5. Save and Report
    results = {
        "admissible_choices": len(choice_stream),
        "real_choice_entropy": real_entropy,
        "uniform_random_entropy": uniform_entropy,
        "entropy_reduction": (
            (uniform_entropy - real_entropy) / uniform_entropy
            if uniform_entropy > 0 else 0
        )
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    console.print("\n[green]Success! Selection bias analysis complete.[/green]")
    console.print(f"  Real Choice Entropy: [bold]{real_entropy:.4f} bits/word[/bold]")
    console.print(f"  Uniform Random Baseline: [bold]{uniform_entropy:.4f} bits/word[/bold]")
    ent_red_pct = results['entropy_reduction'] * 100
    console.print(
        f"  Selection Bias Efficiency: "
        f"[bold green]{ent_red_pct:.2f}% improvement[/bold green]"
    )

    if results['entropy_reduction'] > 0.10:
        console.print(
            "\n[bold green]PASS:[/bold green] "
            "Word selection is significantly non-random."
        )
    else:
        console.print(
            "\n[bold yellow]WARNING:[/bold yellow] "
            "Low selection bias detected. Choices are near-uniform."
        )

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_14p_selection_bias"}):
        main()
