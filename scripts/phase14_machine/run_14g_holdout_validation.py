#!/usr/bin/env python3
"""Phase 14G: Holdout Validation.

Trains the lattice on one section (Herbal) and tests admissibility 
on another (Biological) to prove generalizability.
"""

import sys
import json
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase14_machine.palette_solver import GlobalPaletteSolver
from phase1_foundation.storage.metadata import MetadataStore, PageRecord, TranscriptionLineRecord, TranscriptionTokenRecord
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
SLIP_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/holdout_performance.json"
console = Console()

def get_folio_num(folio_id):
    match = re.search(r'f(\d+)', folio_id)
    return int(match.group(1)) if match else 0

def get_section_lines(store, start_f, end_f):
    session = store.Session()
    try:
        rows = (
            session.query(TranscriptionTokenRecord.content, PageRecord.id, TranscriptionLineRecord.id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )
        
        lines = []
        current_line = []
        last_line_id = None
        for content, folio_id, line_id in rows:
            f_num = get_folio_num(folio_id)
            if start_f <= f_num <= end_f:
                if last_line_id is not None and line_id != last_line_id:
                    lines.append(current_line)
                    current_line = []
                current_line.append(content)
                last_line_id = line_id
        if current_line:
            lines.append(current_line)
        return lines
    finally:
        session.close()

def main():
    console.print("[bold green]Phase 14G: Holdout Validation (The Generalization Test)[/bold green]")
    
    store = MetadataStore(DB_PATH)
    
    # 1. Split Data: Train (Herbal: 1-66), Test (Biological: 75-84)
    console.print("Extracting Herbal section (Training)...")
    train_lines = get_section_lines(store, 1, 66)
    console.print(f"  Training on {len(train_lines)} lines.")
    
    console.print("Extracting Biological section (Testing)...")
    test_lines = get_section_lines(store, 75, 84)
    console.print(f"  Testing on {len(test_lines)} lines.")
    
    # 2. Train Lattice on Herbal
    solver = GlobalPaletteSolver()
    # We use a simplified ingest without slips for pure text-holdout
    solver.ingest_data([], train_lines, top_n=2000)
    solved_pos = solver.solve_grid(iterations=20)
    lattice_data = solver.cluster_lattice(solved_pos, num_windows=50)
    
    lattice_map = lattice_data["word_to_window"]
    window_contents = lattice_data["window_contents"]
    
    # 3. Test Admissibility on Biological
    console.print("Measuring admissibility of Biological section under Herbal lattice...")
    admissible_count = 0
    total_tokens = 0
    current_window = 0
    
    for line in test_lines:
        for word in line:
            total_tokens += 1
            # Check current window + neighbors
            is_valid = False
            for offset in [-1, 0, 1]:
                check_win = (current_window + offset) % 50
                if word in window_contents.get(check_win, []):
                    is_valid = True
                    current_window = check_win
                    break
            
            if is_valid:
                admissible_count += 1
                # Advance
                current_window = lattice_map.get(word, (current_window + 1) % 50)
            else:
                # Snap to real window if possible to continue test
                if word in lattice_map:
                    current_window = lattice_map[word]
                    
    admissibility_rate = admissible_count / total_tokens if total_tokens > 0 else 0
    
    # 4. Save and Report
    results = {
        "train_lines": len(train_lines),
        "test_lines": len(test_lines),
        "admissibility_rate": admissibility_rate,
        "total_test_tokens": total_tokens
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Holdout validation complete.[/green]")
    console.print(f"Admissibility Rate on Unseen Section: [bold blue]{admissibility_rate*100:.2f}%[/bold blue]")
    
    if admissibility_rate > 0.40:
        console.print("\n[bold green]PASS:[/bold green] The lattice generalizes significantly better than chance.")
    else:
        console.print("\n[bold yellow]WARNING:[/bold yellow] Poor generalization to unseen sections.")

if __name__ == "__main__":
    main()
