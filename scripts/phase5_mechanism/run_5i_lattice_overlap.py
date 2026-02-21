#!/usr/bin/env python3
"""
Phase 5I: Lattice Overlap Analysis

Checks for shared path fragments (long n-grams) across major sections 
to determine if they traverse the same underlying object.
"""

import argparse
import sys
from pathlib import Path
import json
from collections import defaultdict, Counter

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from scripts.phase5_mechanism.categorize_sections import get_section

console = Console()
DB_PATH = "sqlite:///data/voynich.db"


def _parse_args():
    parser = argparse.ArgumentParser(description="Phase 5I: Lattice Overlap Analysis")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Override output directory")
    return parser.parse_args()


def get_tokens_by_section(store):
    session = store.Session()
    try:
        from phase1_foundation.storage.metadata import PageRecord
        tokens_recs = (
            session.query(TranscriptionTokenRecord.content, PageRecord.id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .all()
        )
        
        section_tokens = defaultdict(list)
        for content, page_id in tokens_recs:
            sec = get_section(page_id)
            section_tokens[sec].append(content)
            
        return section_tokens
    finally:
        session.close()

def get_ngrams(tokens, n=3):
    return set(tuple(tokens[i:i+n]) for i in range(len(tokens)-n+1))

def run_lattice_overlap(seed: int = 42, output_dir: str | None = None):
    console.print(Panel.fit(
        "[bold blue]Phase 5I: Lattice Overlap Analysis[/bold blue]\n"
        "Testing for shared path fragments across sections",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5i_lattice_overlap", "seed": seed}) as run:
        store = MetadataStore(DB_PATH)
        
        # 1. Fetch Data
        console.print("\n[bold yellow]Step 1: Fetching Tokens by Section[/bold yellow]")
        section_map = get_tokens_by_section(store)
        
        # 2. Extract N-grams (Trigrams)
        console.print("\n[bold yellow]Step 2: Extracting Trigrams[/bold yellow]")
        section_ngrams = {}
        for sec, tokens in section_map.items():
            if sec == "unknown" or len(tokens) < 1000: continue
            section_ngrams[sec] = get_ngrams(tokens, n=3)
            
        # 3. Compare
        table = Table(title="Lattice Fragment Overlap (Trigrams)")
        table.add_column("Section Pair", style="cyan")
        table.add_column("Common Fragments", justify="right")
        table.add_column("Jaccard Similarity", justify="right")

        sections = sorted(section_ngrams.keys())
        results = []
        for i in range(len(sections)):
            for j in range(i + 1, len(sections)):
                s1, s2 = sections[i], sections[j]
                n1, n2 = section_ngrams[s1], section_ngrams[s2]
                
                common = n1.intersection(n2)
                union = n1.union(n2)
                jaccard = len(common) / len(union) if union else 0
                
                table.add_row(
                    f"{s1.capitalize()} / {s2.capitalize()}",
                    str(len(common)),
                    f"{jaccard:.4f}"
                )
                results.append({"pair": (s1, s2), "common": len(common), "jaccard": jaccard})
                
        console.print(table)
        
        # Save results
        out = Path(output_dir) if output_dir else Path("results/data/phase5_mechanism")
        out.mkdir(parents=True, exist_ok=True)
        # JSON doesn't like tuple values, so normalize pair fields.
        serializable_results = [
            {"s1": r["pair"][0], "s2": r["pair"][1], "common": r["common"], "jaccard": r["jaccard"]}
            for r in results
        ]
        ProvenanceWriter.save_results(serializable_results, out / "lattice_overlap.json")
            
        store.save_run(run)

if __name__ == "__main__":
    args = _parse_args()
    run_lattice_overlap(seed=args.seed, output_dir=args.output_dir)
