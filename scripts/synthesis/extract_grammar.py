#!/usr/bin/env python3
"""
Step 3.2.2: Automated Grammar Extraction

Reverse-engineers the structural rules of Voynichese by analyzing
glyph transition and positional probabilities from the database.

Outputs: data/derived/voynich_grammar.json
"""

import sys
from pathlib import Path
import json
from collections import defaultdict, Counter

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from rich.panel import Panel

from foundation.storage.metadata import (
    MetadataStore,
    WordRecord,
    GlyphCandidateRecord,
    GlyphAlignmentRecord
)
from foundation.runs.manager import active_run

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = Path("data/derived/voynich_grammar.json")

def extract_grammar(dataset_id: str = "voynich_real"):
    store = MetadataStore(DB_PATH)
    session = store.Session()
    
    # Rules storage
    transitions = defaultdict(Counter)
    positions = defaultdict(Counter) # {symbol: {pos_type: count}}
    word_lengths = Counter()
    
    try:
        # Get all words for the dataset
        from foundation.storage.metadata import PageRecord, LineRecord
        words = (
            session.query(WordRecord)
            .join(LineRecord, WordRecord.line_id == LineRecord.id)
            .join(PageRecord, LineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .all()
        )
        
        console.print(f"Processing {len(words)} words...")
        
        with Progress() as progress:
            task = progress.add_task("Extracting rules...", total=len(words))
            
            for word in words:
                # Get glyphs for this word in order
                glyphs = (
                    session.query(GlyphAlignmentRecord.symbol)
                    .join(GlyphCandidateRecord, GlyphAlignmentRecord.glyph_id == GlyphCandidateRecord.id)
                    .filter(GlyphCandidateRecord.word_id == word.id)
                    .order_by(GlyphCandidateRecord.glyph_index)
                    .all()
                )
                
                symbols = [g[0] for g in glyphs if g[0]]
                if not symbols:
                    progress.update(task, advance=1)
                    continue
                
                word_lengths[len(symbols)] += 1
                
                # Track transitions
                # Add pseudo-symbols for start/end
                sequence = ["<START>"] + symbols + ["<END>"]
                
                for i in range(len(sequence) - 1):
                    current = sequence[i]
                    next_sym = sequence[i+1]
                    transitions[current][next_sym] += 1
                
                # Track positions
                for i, sym in enumerate(symbols):
                    if i == 0:
                        pos = "start"
                    elif i == len(symbols) - 1:
                        pos = "end"
                    else:
                        pos = "mid"
                    positions[sym][pos] += 1
                
                progress.update(task, advance=1)
                
        # 2. Normalize probabilities
        grammar = {
            "transitions": {},
            "positions": {},
            "word_lengths": {},
            "metadata": {
                "dataset": dataset_id,
                "total_words": len(words),
                "unique_symbols": len(positions)
            }
        }
        
        for current, next_counts in transitions.items():
            total = sum(next_counts.values())
            grammar["transitions"][current] = {
                sym: count / total for sym, count in next_counts.items()
            }
            
        for sym, pos_counts in positions.items():
            total = sum(pos_counts.values())
            grammar["positions"][sym] = {
                pos: count / total for pos, count in pos_counts.items()
            }
            
        total_len_counts = sum(word_lengths.values())
        grammar["word_lengths"] = {
            str(length): count / total_len_counts for length, count in word_lengths.items()
        }
        
        # 3. Save to file
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, "w") as f:
            json.dump(grammar, f, indent=2)
            
        console.print(f"\n[bold green]Grammar extraction complete.[/bold green]")
        console.print(f"Rules saved to: {OUTPUT_PATH}")
        
        # Display summary table for key glyphs
        table = Table(title="Top Transition Rules (P > 0.5)")
        table.add_column("Symbol", style="cyan")
        table.add_column("Next Symbol", style="green")
        table.add_column("Probability", justify="right")
        
        for sym in ["q", "o", "y", "i", "h", "e"]:
            if sym in grammar["transitions"]:
                for next_sym, prob in grammar["transitions"][sym].items():
                    if prob > 0.5:
                        table.add_row(sym, next_sym, f"{prob:.2%}")
        
        console.print(table)
        
    finally:
        session.close()

def main():
    console.print(Panel.fit(
        "[bold blue]Phase 3.2.2: Automated Grammar Extraction[/bold blue]\n"
        "Reverse-engineering glyph sequences",
        border_style="blue"
    ))
    
    with active_run(config={"command": "extract_grammar", "seed": 42}) as run:
        extract_grammar("voynich_real")

if __name__ == "__main__":
    main()
