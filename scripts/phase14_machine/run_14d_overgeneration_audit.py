#!/usr/bin/env python3
"""Phase 14D: Overgeneration Audit.

Measures the 'Unattested Form Rate' (UFR) to ensure the lattice is a narrow 
gate, not a permissive nonsense generator.
"""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table
from collections import Counter

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.storage.metadata import MetadataStore
from phase14_machine.high_fidelity_emulator import HighFidelityVolvelle

DB_PATH = "sqlite:///data/voynich.db"
PALETTE_PATH = project_root / "results/data/phase14_machine/full_palette_grid.json"
OUTPUT_PATH = project_root / "results/data/phase14_machine/overgeneration_audit.json"
console = Console()

def main():
    console.print("[bold magenta]Phase 14D: Overgeneration Audit (The Narrow Gate Test)[/bold magenta]")
    
    if not PALETTE_PATH.exists():
        console.print(f"[red]Error: {PALETTE_PATH} not found.[/red]")
        return

    # 1. Load Solved Palette
    with open(PALETTE_PATH, "r") as f:
        p_data = json.load(f)
    results = p_data.get("results", p_data)
    lattice_map = results.get("lattice_map", {})
    window_contents = results.get("window_contents", {})
    
    # 2. Setup Emulator
    emulator = HighFidelityVolvelle(lattice_map, window_contents, seed=42)
    
    # 3. Load Real Vocabulary
    store = MetadataStore(DB_PATH)
    real_lines = load_canonical_lines(store)
    real_vocab = set(t for l in real_lines for t in l)
    console.print(f"Real Vocabulary Size: [bold]{len(real_vocab)}[/bold]")
    
    # 4. Generate Large Synthetic Corpus
    num_lines = 100000
    console.print(f"Generating {num_lines} synthetic lines...")
    syn_lines = emulator.generate_mirror_corpus(num_lines)
    syn_tokens = [t for l in syn_lines for t in l]
    syn_vocab = set(syn_tokens)
    
    # 5. Analyze Overgeneration
    unattested = syn_vocab - real_vocab
    ufr = len(unattested) / len(syn_vocab) if syn_vocab else 0
    
    # 5.1 Trigram Analysis (The Sequential Overgeneration)
    def get_trigrams(lines):
        return set(tuple(line[i:i+3]) for line in lines for i in range(len(line) - 2))
    
    real_trigrams = get_trigrams(real_lines)
    syn_trigrams = get_trigrams(syn_lines)
    unattested_trigrams = syn_trigrams - real_trigrams
    tufr = len(unattested_trigrams) / len(syn_trigrams) if syn_trigrams else 0
    
    # Top unattested forms
    counts = Counter(syn_tokens)
    top_unattested = sorted([(w, counts[w]) for w in unattested], key=lambda x: x[1], reverse=True)[:20]
    
    # 6. Save and Report
    results = {
        "num_real_tokens": len(real_vocab),
        "num_syn_tokens": len(syn_vocab),
        "num_unattested_forms": len(unattested),
        "unattested_form_rate": ufr,
        "num_real_trigrams": len(real_trigrams),
        "num_syn_trigrams": len(syn_trigrams),
        "num_unattested_trigrams": len(unattested_trigrams),
        "trigram_unattested_rate": tufr,
        "top_unattested": top_unattested
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print("\n[green]Success! Overgeneration audit complete.[/green]")
    console.print(f"Unattested Word Rate (UWR): [bold]{ufr*100:.2f}%[/bold]")
    console.print(f"Unattested Trigram Rate (UTR): [bold blue]{tufr*100:.2f}%[/bold blue]")
    
    table = Table(title="Top Unattested Forms (Overgeneration)")
    table.add_column("Word", style="cyan")
    table.add_column("Frequency", justify="right")
    
    for word, count in top_unattested:
        table.add_row(word, str(count))
    console.print(table)
    
    if ufr < 0.05:
        console.print("\n[bold green]PASS:[/bold green] The lattice is sufficiently restrictive.")
    else:
        console.print("\n[bold yellow]WARNING:[/bold yellow] High overgeneration rate detected.")

if __name__ == "__main__":
    main()
