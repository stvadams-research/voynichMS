#!/usr/bin/env python3
"""
Corpus Builder for Phase 4

Generates and registers all required matched corpora:
- latin_classic (Semantic)
- self_citation (Non-semantic structured)
- table_grille (Non-semantic structured)
- mechanical_reuse (Non-semantic structured)
- shuffled_global (Negative control)
"""

import sys
from pathlib import Path
import random
import re

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.panel import Panel

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore
from foundation.controls.self_citation import SelfCitationGenerator
from foundation.controls.table_grille import TableGrilleGenerator
from foundation.controls.mechanical_reuse import MechanicalReuseGenerator

console = Console()
DB_PATH = "sqlite:///data/voynich.db"
LATIN_FILE = Path("data/inference/latin_corpus.txt")
SOURCE_ID = "corpus_gen"


def _ensure_transcription_source(store, source_id: str = SOURCE_ID) -> None:
    """Ensure synthetic corpus ingestion source metadata exists."""
    store.add_transcription_source(
        source_id,
        name="Corpus Generator",
        citation="scripts/inference/build_corpora.py",
    )

def build_latin_corpus(store, target_count):
    console.print(f"\n[bold yellow]Building Latin Corpus ({target_count} tokens)[/bold yellow]")
    if not LATIN_FILE.exists():
        console.print("[red]Error: latin_corpus.txt not found.[/red]")
        return
        
    with open(LATIN_FILE, "r") as f:
        text = f.read()
        
    # Simple tokenization
    tokens = re.findall(r'\b\w+\b', text.lower())
    console.print(f"  Source tokens: {len(tokens)}")
    
    # Match length
    if len(tokens) < target_count:
        # Repeat if too short
        full_tokens = (tokens * (target_count // len(tokens) + 1))[:target_count]
    else:
        full_tokens = tokens[:target_count]
        
    # Ingest
    # Use MechanicalReuseGenerator's _ingest_tokens helper (or similar)
    # Actually, I'll just implement a helper here.
    _ingest_tokens(store, "latin_classic", full_tokens, "semantic_latin")

def build_shuffled_control(store, source_id, target_id):
    console.print(f"\n[bold yellow]Building Shuffled Control: {target_id}[/bold yellow]")
    session = store.Session()
    try:
        from foundation.storage.metadata import TranscriptionTokenRecord, TranscriptionLineRecord, PageRecord
        tokens = (
            session.query(TranscriptionTokenRecord.content)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == source_id)
            .all()
        )
        token_list = [t[0] for t in tokens]
        rng = random.Random(42)
        rng.shuffle(token_list)
        
        _ingest_tokens(store, target_id, token_list, "negative_control_shuffled")
    finally:
        session.close()

def _ingest_tokens(store, dataset_id, tokens, type_label):
    from foundation.core.id_factory import DeterministicIDFactory
    id_factory = DeterministicIDFactory(seed=42)
    
    _ensure_transcription_source(store, SOURCE_ID)
    store.add_dataset(dataset_id, type_label)
    
    tokens_per_page = 1000

    for p_idx, start in enumerate(range(0, len(tokens), tokens_per_page)):
        end = start + tokens_per_page
        page_tokens = tokens[start:end]
        if not page_tokens:
            continue

        page_id = f"{dataset_id}_p{p_idx}"
        store.add_page(page_id, dataset_id, "synthetic", f"hash_{page_id}", 1000, 1500)

        trans_line_id = id_factory.next_uuid(f"line:{page_id}")
        store.add_transcription_line(trans_line_id, SOURCE_ID, page_id, 0, " ".join(page_tokens))

        for w_idx, token in enumerate(page_tokens):
            token_id = id_factory.next_uuid(f"token:{trans_line_id}:{w_idx}")
            store.add_transcription_token(token_id, trans_line_id, w_idx, token)

    console.print(f"  [green]Registered {len(tokens)} tokens in {dataset_id}[/green]")

def main():
    console.print(Panel.fit(
        "[bold blue]Phase 4 Corpus Builder[/bold blue]\n"
        "Assembling the Inference Admissibility Benchmark Suite",
        border_style="blue"
    ))

    with active_run(config={"command": "build_phase_4_corpora", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        target_tokens = 230000
        
        # 1. Semantic Baseline
        build_latin_corpus(store, target_tokens)
        
        # 2. Non-Semantic Structured
        console.print("\n[bold yellow]Building Self-Citation Corpus[/bold yellow]")
        sc_gen = SelfCitationGenerator(store)
        sc_gen.generate("voynich_real", "self_citation", params={"target_tokens": target_tokens})
        
        console.print("\n[bold yellow]Building Table-Grille Corpus[/bold yellow]")
        tg_gen = TableGrilleGenerator(store)
        tg_gen.generate("voynich_real", "table_grille", params={"target_tokens": target_tokens})
        
        console.print("\n[bold yellow]Building Mechanical Reuse Corpus[/bold yellow]")
        mr_gen = MechanicalReuseGenerator(store)
        mr_gen.generate("voynich_real", "mechanical_reuse", params={"target_tokens": target_tokens})
        
        # 3. Negative Controls
        build_shuffled_control(store, "voynich_real", "shuffled_global")
        
        # 4. Verify Manifest
        console.print("\n[bold green]Corpus Suite Assembly Complete.[/bold green]")
        store.save_run(run)

if __name__ == "__main__":
    main()
