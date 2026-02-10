#!/usr/bin/env python3
"""
Method D Runner: Language ID under Flexible Transforms

Tests if flexible transformations can produce high-confidence 
language matches for non-semantic data.
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
from foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from foundation.config import DEFAULT_SEED
from foundation.core.provenance import ProvenanceWriter
from inference.lang_id_transforms.analyzer import LanguageIDAnalyzer

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_text(store, dataset_id):
    session = store.Session()
    try:
        from foundation.storage.metadata import PageRecord
        tokens = (
            session.query(TranscriptionTokenRecord.content)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == dataset_id)
            .all()
        )
        return " ".join([t[0] for t in tokens])
    finally:
        session.close()

def run_experiment():
    console.print(Panel.fit(
        "[bold blue]Method D: Language ID under Flexible Transforms[/bold blue]\n"
        "Testing for false positive language matches via multiple comparisons",
        border_style="blue"
    ))

    with active_run(config={"command": "run_lang_id_phase4", "seed": DEFAULT_SEED}) as run:
        store = MetadataStore(DB_PATH)
        analyzer = LanguageIDAnalyzer()
        seed = int(run.config.get("seed", DEFAULT_SEED))
        rng = random.Random(seed)
        
        # 1. Build Language Profiles
        console.print("Building language profiles...")
        for lang, path in [("latin", "data/inference/latin_corpus.txt"), ("english", "data/inference/english.txt"), ("german", "data/inference/german.txt")]:
            if Path(path).exists():
                with open(path, "r") as f:
                    analyzer.build_profile(lang, f.read())
            else:
                console.print(f"  [red]Warning: {path} not found.[/red]")

        # 2. Define Flexible Transforms (Dummy set for simulation)
        # In real decipherment claims, people try many vowel mappings etc.
        transforms = [
            {}, # Identity
            {'q': 'qu', 'o': 'a', 'y': 'e'}, # Vowel shift
            {'ch': 'c', 'sh': 's', 'ii': 'i'}, # Digraph collapse
            {'a': 'e', 'e': 'i', 'i': 'o', 'o': 'u', 'u': 'a'}, # Rot-vowel
        ]
        # Add some random mappings to simulate large search space
        for _ in range(10):
            random_map = {c: rng.choice('aeiou') for c in 'aeiouy'}
            transforms.append(random_map)

        datasets = {
            "Voynich (Real)": "voynich_real",
            "Shuffled (Global)": "shuffled_global",
            "Mechanical Reuse": "mechanical_reuse"
        }
        
        results = {}
        
        table = Table(title="Language ID Confidence (Best Match)")
        table.add_column("Dataset", style="cyan")
        table.add_column("Target: Latin", justify="right")
        table.add_column("Target: English", justify="right")

        for label, dataset_id in datasets.items():
            console.print(f"Analyzing: {label}...")
            text = get_text(store, dataset_id)
            
            if not text: continue
            
            latin_score, _ = analyzer.find_best_transform(text, "latin", transforms)
            english_score, _ = analyzer.find_best_transform(text, "english", transforms)
            
            results[dataset_id] = {
                "latin": latin_score,
                "english": english_score
            }
            
            table.add_row(
                label,
                f"{latin_score:.4f}",
                f"{english_score:.4f}"
            )
            
        console.print(table)
        
        # Save results
        output_dir = Path("results/phase_4")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "lang_id_results.json")
            
        store.save_run(run)

if __name__ == "__main__":
    run_experiment()
