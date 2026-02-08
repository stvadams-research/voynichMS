#!/usr/bin/env python3
"""
Phase 3.3.2: Test A - Maximal Mechanical Reuse (One-Shot Falsification)

Tests if glyph-level grammar plus bounded token pools suffice to produce 
Voynich-level repetition (0.90).

Mechanism:
- Glyph-level grammar fixed from Phase 3.2
- Token pools defined exogenously per page (Sizes: 10, 20, 30)
- Tokens generated once per page, then reused blindly
- No novelty penalties or scoring
"""

import sys
from pathlib import Path
import json
import random

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from foundation.core.id_factory import DeterministicIDFactory
from synthesis.generators.grammar_based import GrammarBasedGenerator
from foundation.metrics.library import RepetitionRate

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def run_test_a():
    console.print(Panel.fit(
        "[bold blue]Phase 3.3.2: Test A - Maximal Mechanical Reuse[/bold blue]\n"
        "One-shot falsification of the repetition gap",
        border_style="blue"
    ))

    if not GRAMMAR_PATH.exists():
        console.print("[bold red]Error: Grammar file not found. Run Step 3.2.2 first.[/bold red]")
        return

    with active_run(config={"command": "test_a_mechanical_reuse", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        id_factory = DeterministicIDFactory(seed=42)
        generator = GrammarBasedGenerator(GRAMMAR_PATH)
        
        pool_sizes = [10, 20, 30]
        results = {}

        for size in pool_sizes:
            console.print(f"\n[bold yellow]Testing Pool Size: {size}[/bold yellow]")
            dataset_id = f"test_a_pool_{size}"
            store.add_dataset(dataset_id, "generated")
            
            # Generate 5 pages per pool size for one-shot test
            num_pages = 5
            
            session = store.Session()
            try:
                for p_idx in range(num_pages):
                    page_id = f"syn_reuse_{size}_{p_idx}"
                    store.add_page(page_id, dataset_id, "placeholder.jpg", f"hash_{size}_{p_idx}", 1000, 1500)
                    
                    # 1. Generate the pool for this page
                    # Deterministic pool per page based on seed + page_id
                    page_rng = random.Random(f"pool_{size}_{page_id}")
                    token_pool = [generator.generate_word() for _ in range(size)]
                    
                    # 2. Fill the page (blindly reuse from pool)
                    # Use typical pharmaceutical layout: 4 jars, 6 lines each, 3 words per line = 72 words
                    words_per_page = 72
                    page_tokens = [page_rng.choice(token_pool) for _ in range(words_per_page)]
                    
                    # 3. Ingest into DB
                    # (Simplified ingestion: one block/line for the whole page)
                    line_id = id_factory.next_uuid(f"line:{page_id}")
                    store.add_line(line_id, page_id, 0, {"x":0,"y":0,"w":0,"h":0}, 1.0)
                    
                    trans_line_id = id_factory.next_uuid(f"trans_line:{page_id}")
                    store.add_transcription_line(trans_line_id, "synthetic", page_id, 0, " ".join(page_tokens))
                    
                    for w_idx, token in enumerate(page_tokens):
                        token_id = id_factory.next_uuid(f"trans_token:{trans_line_id}:{w_idx}")
                        store.add_transcription_token(token_id, trans_line_id, w_idx, token)
                
                session.commit()
            finally:
                session.close()
            
            # 4. Measure Repetition
            rep_metric = RepetitionRate(store)
            rep_val = rep_metric.calculate(dataset_id)[0].value
            results[size] = rep_val
            console.print(f"  Repetition Rate: {rep_val:.4f}")

        # 5. Final Report for Test A
        table = Table(title="Test A Results: Repetition vs Pool Size")
        table.add_column("Pool Size", style="cyan")
        table.add_column("Repetition Rate", style="yellow")
        table.add_column("Target (0.90)", style="green")
        table.add_column("H1 Support?", justify="center")

        target = 0.90
        for size, val in results.items():
            h1_support = "[green]YES[/green]" if val >= target else "[red]NO[/red]"
            table.add_row(str(size), f"{val:.4f}", f"{target:.2f}", h1_support)

        console.print(table)
        
        # Save results
        with open("status/synthesis/TEST_A_RESULTS.json", "w") as f:
            json.dump(results, f, indent=2)
            
        store.save_run(run)

if __name__ == "__main__":
    run_test_a()
