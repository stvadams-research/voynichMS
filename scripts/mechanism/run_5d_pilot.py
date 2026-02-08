#!/usr/bin/env python3
"""
Phase 5D Pilot: Deterministic Line Grammar

Benchmarks Voynich (Real) against a Deterministic Slot simulator
using successor entropy profiling.
"""

import sys
from pathlib import Path
import json

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from mechanism.deterministic_grammar.simulators import DeterministicSlotSimulator
from mechanism.deterministic_grammar.boundary_detection import SlotBoundaryDetector

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def get_lines(store, dataset_id):
    session = store.Session()
    try:
        from foundation.storage.metadata import PageRecord
        tokens_recs = (
            session.query(TranscriptionTokenRecord.content, TranscriptionTokenRecord.line_id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )
        
        lines = []
        current_line = []
        last_line_id = None
        
        for content, line_id in tokens_recs:
            if last_line_id and line_id != last_line_id:
                lines.append(current_line)
                current_line = []
            current_line.append(content)
            last_line_id = line_id
        if current_line:
            lines.append(current_line)
            
        return lines
    finally:
        session.close()

def run_pilot_5d():
    console.print(Panel.fit(
        "[bold blue]Phase 5D: Deterministic Grammar Pilot[/bold blue]\n"
        "Testing sufficiency of rigid slot-filling models",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5d_pilot", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        detector = SlotBoundaryDetector(max_pos=6)
        
        # 1. Setup Data
        console.print("\n[bold yellow]Step 1: Detecting Boundaries in Real Data[/bold yellow]")
        real_lines = get_lines(store, "voynich_real")
        real_profile = detector.calculate_successor_sharpness(real_lines[:2000])
        
        # 2. Run Simulator
        console.print("\n[bold yellow]Step 2: Executing Deterministic Simulator[/bold yellow]")
        sim = DeterministicSlotSimulator(GRAMMAR_PATH, num_slots=6)
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
        
        output_dir = Path("results/mechanism/deterministic_grammar")
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_dir / "pilot_5d_results.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_pilot_5d()
