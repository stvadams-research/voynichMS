#!/usr/bin/env python3
"""Phase 15A: Trace Instrumentation.

Traces the real manuscript through the Voynich Engine and logs the choice 
context for every admissible transition.
"""

import json
import sys
from pathlib import Path

from rich.console import Console

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase15_rule_extraction/choice_stream_trace.json"
console = Console()

def main():
    console.print(
        "[bold cyan]Phase 15A: Trace Instrumentation (The Scribe's Decisions)[/bold cyan]"
    )

    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: Palette grid not found at {PALETTE_PATH}[/red]")
        return

    # 1. Load Model
    with open(PALETTE_PATH) as f:
        data = json.load(f)["results"]
    lattice_map = data["lattice_map"]
    window_contents = data["window_contents"]

    # 2. Setup Instrumented Emulator
    emulator = HighFidelityVolvelle(lattice_map, window_contents, log_choices=True)

    # 3. Load Real Manuscript
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    console.print(f"Tracing {len(real_lines)} lines...")

    # 4. Perform Trace
    emulator.trace_lines(real_lines)

    # 5. Save and Report
    log = emulator.choice_log
    console.print(f"\n[green]Success! Logged {len(log)} scribal decisions.[/green]")

    results = {
        "num_decisions": len(log),
        "choices": log
    }

    ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"Artifact saved to: [bold]{OUTPUT_PATH}[/bold]")

if __name__ == "__main__":
    with active_run(config={"seed": 42, "command": "run_15a_trace_instrumentation"}):
        main()
