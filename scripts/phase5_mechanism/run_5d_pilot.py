#!/usr/bin/env python3
"""
Phase 5D Pilot: Deterministic Line Grammar

Benchmarks Voynich (Real) against a Deterministic Slot simulator
using successor entropy profiling.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore
from phase5_mechanism.deterministic_grammar.boundary_detection import SlotBoundaryDetector
from phase5_mechanism.deterministic_grammar.simulators import DeterministicSlotSimulator

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5D Pilot: Deterministic Line Grammar")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def run_pilot_5d(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5D: Deterministic Grammar Pilot[/bold blue]\n"
        "Testing sufficiency of rigid slot-filling models",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5d_pilot", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        detector = SlotBoundaryDetector(max_pos=6)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Detecting Boundaries in Real Data[/bold yellow]")
        real_lines = get_lines_from_store(store, "voynich_real")
        real_profile = detector.calculate_successor_sharpness(real_lines[:2000])
        
        # 2. Run Simulator
        console.print("\n[bold yellow]Step 2: Executing Deterministic Simulator[/bold yellow]")
        sim = DeterministicSlotSimulator(GRAMMAR_PATH, num_slots=6, seed=seed)
        sim_lines = sim.generate_corpus(num_lines=1000)
        sim_profile = detector.calculate_successor_sharpness(sim_lines)
        
        # 3. Report
        table = Table(title="Phase 5D Pilot: Successor Entropy Profile (Sharpness)")
        table.add_column("Word Position", style="cyan")
        table.add_column("Voynich (Real)", justify="right")
        table.add_column("Slot-Sim (Syn)", justify="right")
        table.add_column("Matches?", justify="center")

        def check_match(val, target, tol=0.5):
            return "[green]YES[/green]" if abs(val - target) < tol else "[red]NO[/red]"

        for i in range(len(real_profile)):
            sim_val = sim_profile[i] if i < len(sim_profile) else 0.0
            table.add_row(
                f"Slot {i+1}", 
                f"{real_profile[i]:.4f}", 
                f"{sim_val:.4f}",
                check_match(sim_val, real_profile[i], 1.0)
            )
        
        console.print(table)
        
        # Save Pilot results
        results = {
            "real_profile": real_profile,
            "sim_profile": sim_profile
        }
        
        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism/deterministic_grammar")
        out.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, out / "pilot_5d_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_pilot_5d(seed=args.seed, output_dir=args.output_dir)
