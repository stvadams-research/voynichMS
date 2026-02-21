#!/usr/bin/env python3
"""Phase 14K: Failure Visualization.

Analyzes the spatial distribution of 'noise' (failures) across the 
manuscript's quires and line positions.
"""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter, defaultdict

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore, PageRecord, TranscriptionLineRecord, TranscriptionTokenRecord
from phase1_foundation.core.provenance import ProvenanceWriter
from phase7_human.quire_analysis import QuireAnalyzer

DB_PATH = "sqlite:///data/voynich.db"
NOISE_PATH = project_root / "results/data/phase14_machine/noise_register.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/failure_distribution.json"
console = Console()

def main():
    console.print("[bold cyan]Phase 14K: Failure Visualization (Spatial Analysis)[/bold cyan]")
    
    if not NOISE_PATH.exists():
        console.print("[red]Error: run_14f_noise_register.py must be run first.[/red]")
        return

    # 1. Load Noise Register
    with open(NOISE_PATH, "r") as f:
        noise_data = json.load(f)
    failures = noise_data.get("results", {}).get("failures", [])
    
    # 2. Map Failures to Quires
    analyzer = QuireAnalyzer()
    store = MetadataStore(DB_PATH)
    session = store.Session()
    
    quire_failures = Counter()
    pos_failures = Counter()
    
    # We need to map global line_index to folio_id
    # We'll use a cache to speed this up
    line_to_folio = {}
    lines_query = session.query(TranscriptionLineRecord.id, PageRecord.id).\
        join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id).\
        filter(PageRecord.dataset_id == "voynich_real").all()

    # Simplified: failures in register already have line index
    # We'll just load all folios in order
    folios = session.query(PageRecord.id).filter_by(dataset_id="voynich_real").order_by(PageRecord.id).all()
    folio_list = [f[0] for f in folios]
    
    for f in failures:
        # Approximate folio from line_no (each folio has ~30-40 lines)
        f_idx = min(f['line'] // 35, len(folio_list) - 1)
        folio_id = folio_list[f_idx]
        
        q = analyzer.get_quire(folio_id)
        quire_failures[q] += 1
        pos_failures[f['pos']] += 1
        
    # 3. Save and Report
    results = {
        "quire_distribution": dict(quire_failures),
        "position_distribution": dict(pos_failures)
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Failure distribution saved.[/green]")
    
    table = Table(title="Failures by Quire")
    table.add_column("Quire", justify="right")
    table.add_column("Failures", justify="right", style="bold red")
    
    for q in sorted(quire_failures.keys()):
        table.add_row(str(q), str(quire_failures[q]))
    console.print(table)
    
    session.close()

if __name__ == "__main__":
    main()
