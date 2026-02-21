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

import argparse
import random
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console  # noqa: E402
from rich.panel import Panel  # noqa: E402
from rich.table import Table  # noqa: E402

from phase1_foundation.config import DEFAULT_SEED  # noqa: E402
from phase1_foundation.core.id_factory import DeterministicIDFactory  # noqa: E402
from phase1_foundation.core.provenance import ProvenanceWriter  # noqa: E402
from phase1_foundation.metrics.library import RepetitionRate  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore  # noqa: E402
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator  # noqa: E402

console = Console()
DEFAULT_DB_URL = "sqlite:///data/voynich.db"
GRAMMAR_PATH = Path("data/derived/voynich_grammar.json")

def run_test_a(
    seed: int = DEFAULT_SEED,
    output_path: str = "core_status/phase3_synthesis/TEST_A_RESULTS.json",
    db_url: str = DEFAULT_DB_URL,
):
    console.print(Panel.fit(
        "[bold blue]Phase 3.3.2: Test A - Maximal Mechanical Reuse[/bold blue]\n"
        "One-shot falsification of the repetition gap",
        border_style="blue"
    ))

    if not GRAMMAR_PATH.exists():
        console.print("[bold red]Error: Grammar file not found. Run Step 3.2.2 first.[/bold red]")
        return

    with active_run(
        config={
            "command": "test_a_mechanical_reuse",
            "seed": seed,
            "db_url": db_url,
        }
    ) as run:
        store = MetadataStore(db_url)
        store.add_transcription_source("synthetic", "Synthetic Generator")
        id_factory = DeterministicIDFactory(seed=seed)
        generator = GrammarBasedGenerator(GRAMMAR_PATH, seed=seed)

        pool_sizes = [10, 20, 30]
        results = {}

        for size in pool_sizes:
            console.print(f"\n[bold yellow]Testing Pool Size: {size}[/bold yellow]")
            dataset_id = f"test_a_pool_{size}_s{seed}"
            store.add_dataset(dataset_id, "generated")

            # Generate 5 pages per pool size for one-shot test
            num_pages = 5

            session = store.Session()
            try:
                for p_idx in range(num_pages):
                    page_id = f"syn_reuse_{seed}_{size}_{p_idx}"
                    store.add_page(page_id, dataset_id, "placeholder.jpg", f"hash_{size}_{p_idx}", 1000, 1500)

                    # 1. Generate the pool for this page
                    # Deterministic pool per page based on seed + page_id
                    page_rng = random.Random(f"pool_{seed}_{size}_{page_id}")
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
        ProvenanceWriter.save_results(results, output_path)

        store.save_run(run)

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run deterministic Test A phase3_synthesis check.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Seed for deterministic generation.")
    parser.add_argument(
        "--output",
        type=str,
        default="core_status/phase3_synthesis/TEST_A_RESULTS.json",
        help="Path to output JSON results file.",
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=DEFAULT_DB_URL,
        help="SQLAlchemy URL for metadata database.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_test_a(seed=args.seed, output_path=args.output, db_url=args.db_url)
