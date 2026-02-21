#!/usr/bin/env python3
"""Phase 12F: Skeptic's Gate (Shuffle Control)."""

import sys
import random
from pathlib import Path
from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase12_mechanical.slip_detection import MechanicalSlipDetector

DB_PATH = "sqlite:///data/voynich.db"
console = Console()

def main():
    console.print("[bold yellow]Skeptic's Gate: Running Shuffle Control Test...[/bold yellow]")
    
    store = MetadataStore(DB_PATH)
    lines = get_lines_from_store(store, "voynich_real")
    
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
    
    if ratio > 2.0:
        console.print("\n[bold green]VERIFIED:[/bold green] The slips are a real signal linked to vertical line proximity.")
    else:
        console.print("\n[bold red]FALSE POSITIVE:[/bold red] The slips are likely random coincidences.")

if __name__ == "__main__":
    main()
