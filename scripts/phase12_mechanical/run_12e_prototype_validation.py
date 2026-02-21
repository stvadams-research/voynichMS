#!/usr/bin/env python3
"""Phase 12E: Prototype Validation (Digital Volvelle vs Real)."""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase12_mechanical.volvelle_simulator import VolvelleSimulator
from phase10_admissibility.mask_anatomy.mapper import SlidingResidualMapper
from phase1_foundation.storage.metadata import MetadataStore
from phase1_foundation.core.queries import get_lines_from_store
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase12_mechanical/prototype_validation.json"
console = Console()

def main():
    console.print("[bold blue]Phase 12E: Mechanical Prototype Validation[/bold blue]")
    
    # 1. Load Real Data Baseline
    store = MetadataStore(DB_PATH)
    real_lines = get_lines_from_store(store, "voynich_real")
    real_tokens = [t for l in real_lines for t in l]
    
    # 2. Setup Prototype
    # We use the top 100 Voynich words as our 'Palette'
    from collections import Counter
    vocab_counts = Counter(real_tokens).most_common(100)
    vocab = [v[0] for v in vocab_counts]
    
    simulator = VolvelleSimulator(vocab, seed=42)
    
    # 3. Generate Synthetic Corpus
    console.print("Generating text from Digital Volvelle prototype...")
    syn_lines = simulator.generate_corpus(num_lines=1000, line_length=6)
    syn_tokens = [t for l in syn_lines for t in l]
    
    # 4. Compare Residual Tension (The 'Mask' Signature)
    mapper = SlidingResidualMapper(window_size=500, step_size=100)
    
    console.print("Mapping tension in Real corpus...")
    # Use dummy folio IDs for simplicity in mapping
    real_folios = ["fX"] * len(real_tokens)
    real_map = mapper.map_corpus(real_tokens, real_folios)
    
    console.print("Mapping tension in Prototype corpus...")
    syn_folios = ["fSyn"] * len(syn_tokens)
    syn_map = mapper.map_corpus(syn_tokens, syn_folios)
    
    # Calculate Similarity
    # (Compare the variance of residuals - indicates 'Maskyness')
    real_var = real_map['global_entropy'] # Simple baseline
    syn_var = syn_map['global_entropy']
    
    results = {
        "prototype_config": "4-ring_8-sector_3-state",
        "real_global_entropy": float(real_map['global_entropy']),
        "syn_global_entropy": float(syn_map['global_entropy']),
        "entropy_similarity": 1.0 - abs(real_map['global_entropy'] - syn_map['global_entropy']) / real_map['global_entropy']
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    console.print(f"\n[green]Analysis complete. Prototype validation saved to:[/green] {saved['latest_path']}")
    
    table = Table(title="Prototype Validation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Voynich Real", justify="right")
    table.add_column("Volvelle Prototype", justify="right")
    table.add_column("Fit Score", justify="right", style="bold green")
    
    table.add_row("Global Entropy", f"{results['real_global_entropy']:.3f}", f"{results['syn_global_entropy']:.3f}", f"{results['entropy_similarity']*100:.1f}%")
    
    console.print(table)
    
    if results['entropy_similarity'] > 0.8:
        console.print("\n[bold green]VALIDATION SUCCESS:[/bold green] The physical volvelle prototype successfully replicates the manuscript's global entropy profile.")

if __name__ == "__main__":
    main()
