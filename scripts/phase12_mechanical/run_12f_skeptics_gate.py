#!/usr/bin/env python3
"""Phase 12F: Skeptic's Gate (Shuffle Control)."""

import random
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase12_mechanical.slip_detection import MechanicalSlipDetector  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = Path("results/data/phase12_mechanical/skeptics_gate.json")
console = Console()

def main():
    console.print("[bold yellow]Skeptic's Gate: Running Shuffle Control Test...[/bold yellow]")

    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)

    # Baseline
    detector = MechanicalSlipDetector(min_transition_count=2)
    detector.build_model(lines)

    # Test 1: Real Order
    real_slips = detector.detect_slips(lines)
    count_real = len(real_slips)

    # Test 2: Shuffled Order
    shuffled_lines = list(lines)
    random.seed(42)
    random.shuffle(shuffled_lines)
    shuffled_slips = detector.detect_slips(shuffled_lines)
    count_shuffled = len(shuffled_slips)

    console.print(f"\nReal Order Slips: [bold green]{count_real}[/bold green]")
    console.print(f"Shuffled Order Slips: [bold red]{count_shuffled}[/bold red]")

    ratio = count_real / count_shuffled if count_shuffled > 0 else count_real
    console.print(f"Signal-to-Noise Ratio: [bold cyan]{ratio:.2f}x[/bold cyan]")

    # Save Results
    results = {
        "count_real": count_real,
        "count_shuffled": count_shuffled,
        "ratio": ratio,
        "verified": ratio > 2.0
    }
    ProvenanceWriter.save_results(results, OUTPUT_PATH)

    if ratio > 2.0:
        msg = "\n[bold green]VERIFIED:[/bold green] Slips linked to vertical line proximity."
        console.print(msg)
    else:
        msg = "\n[bold red]FALSE POSITIVE:[/bold red] Slips are likely random coincidences."
        console.print(msg)


if __name__ == "__main__":
    main()
