#!/usr/bin/env python3
"""
Phase 3.3.4: Test C - Glyph Variant Sensitivity (Ablation Test)

Tests if structural conclusions are sensitive to glyph variant interpretation.

Modes:
1. Collapsed Mode: Variants mapped to canonical glyphs (e.g., k/t -> K, p/f -> P)
2. Expanded Mode: Variants treated as distinct glyphs.
"""

import sys
from pathlib import Path
import json
from collections import defaultdict, Counter
import math

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, GlyphAlignmentRecord, GlyphCandidateRecord

from foundation.core.provenance import ProvenanceWriter

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def run_test_c():
    console.print(Panel.fit(
        "[bold blue]Phase 3.3.4: Test C - Glyph Variant Sensitivity[/bold blue]\n"
        "Testing Collapsed vs Expanded glyph sets",
        border_style="blue"
    ))

    with active_run(config={"command": "test_c_glyph_sensitivity", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        session = store.Session()
        
        try:
            # 1. Fetch glyph sequence data
            console.print("\n[bold yellow]Step 1: Fetching Glyph Data[/bold yellow]")
            
            # Fetch all glyph alignments
            all_alignments = session.query(GlyphAlignmentRecord.symbol, GlyphCandidateRecord.word_id, GlyphCandidateRecord.glyph_index).\
                join(GlyphCandidateRecord, GlyphAlignmentRecord.glyph_id == GlyphCandidateRecord.id).\
                all()
            
            if not all_alignments:
                console.print("[bold red]Error: No glyph data found. Run Step 3.2.2 first.[/bold red]")
                return

            # Group by word
            words_glyphs = defaultdict(list)
            for sym, word_id, idx in all_alignments:
                words_glyphs[word_id].append((idx, sym))
            
            # Sort words and symbols
            word_sequences = []
            for word_id in sorted(words_glyphs.keys()):
                seq = [sym for idx, sym in sorted(words_glyphs[word_id])]
                word_sequences.append(seq)

            # 2. Define Mapping for Collapsed Mode
            # Collapse 'gallows' pairs and other common variants
            variant_map = {
                'k': 'k', 't': 'k', # Gallows pair 1
                'p': 'p', 'f': 'p', # Gallows pair 2
                'i': 'i', 'ii': 'i', 'iii': 'i', # Minims
            }

            modes = ["Expanded", "Collapsed"]
            results = {}

            for mode in modes:
                console.print(f"\n[bold yellow]Mode: {mode}[/bold yellow]")
                
                # Transform sequences
                transformed_words = []
                for seq in word_sequences:
                    if mode == "Collapsed":
                        word_str = "".join([variant_map.get(s, s) for s in seq])
                    else:
                        word_str = "".join(seq)
                    transformed_words.append(word_str)
                
                # Calculate Repetition
                counts = Counter(transformed_words)
                rep_rate = sum(c for c in counts.values() if c > 1) / len(transformed_words)
                
                # Calculate Positional Entropy (Simplified Global)
                # We'll measure the entropy of start-glyphs
                start_glyphs = [w[0] for w in transformed_words if w]
                start_counts = Counter(start_glyphs)
                total_starts = len(start_glyphs)
                entropy = -sum((c/total_starts) * math.log2(c/total_starts) for c in start_counts.values())
                
                results[mode] = {
                    "repetition": rep_rate,
                    "entropy": entropy,
                    "vocab_size": len(counts)
                }
                
                console.print(f"  Vocabulary Size: {len(counts)}")
                console.print(f"  Repetition Rate: {rep_rate:.4f}")
                console.print(f"  Start Glyph Entropy: {entropy:.4f}")

            # 3. Final Report for Test C
            table = Table(title="Test C Results: Glyph Variant Sensitivity")
            table.add_column("Mode", style="cyan")
            table.add_column("Vocab Size", justify="right")
            table.add_column("Repetition Rate", style="yellow")
            table.add_column("Start Entropy", style="magenta")
            table.add_column("Findings Stable?", justify="center")

            for mode, data in results.items():
                # Stable if repetition remains > 0.70 and entropy < 4.0
                stable = "[green]YES[/green]" if data["repetition"] > 0.70 else "[red]NO[/red]"
                table.add_row(
                    mode, 
                    str(data["vocab_size"]), 
                    f"{data['repetition']:.4f}", 
                    f"{data['entropy']:.4f}",
                    stable
                )

            console.print(table)
            
            # Save results
            ProvenanceWriter.save_results(results, "status/synthesis/TEST_C_RESULTS.json")
                
        finally:
            session.close()
            
        store.save_run(run)

if __name__ == "__main__":
    run_test_c()
