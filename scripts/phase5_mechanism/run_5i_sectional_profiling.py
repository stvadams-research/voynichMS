#!/usr/bin/env python3
"""
Phase 5H: Sectional Profiling

Maps Lattice Dimensionality and Successor Consistency across major sections.
"""

import sys
from pathlib import Path
import json
from collections import defaultdict

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root)) # For scripts.phase5_mechanism

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from phase1_foundation.core.provenance import ProvenanceWriter
from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, TranscriptionTokenRecord, TranscriptionLineRecord
from phase5_mechanism.constraint_geometry.latent_state import LatentStateAnalyzer
from phase5_mechanism.large_object.collision_testing import PathCollisionTester
from scripts.phase5_mechanism.categorize_sections import get_section

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

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

def run_sectional_profiling():
    console.print(Panel.fit(
        "[bold blue]Phase 5H: Sectional Profiling[/bold blue]\n"
        "Mapping phase5_mechanism stability across manuscript sections",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5h_sectional_profiling", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        dim_analyzer = LatentStateAnalyzer(top_n=500)
        coll_tester = PathCollisionTester(context_len=2)
        
        # 1. Fetch Data
        console.print("\n[bold yellow]Step 1: Fetching Tokens by Section[/bold yellow]")
        section_map = get_tokens_by_section(store)
        
        # 2. Analyze Sections
        table = Table(title="Sectional Mechanism Profiles")
        table.add_column("Section", style="cyan")
        table.add_column("Tokens", justify="right")
        table.add_column("Effective Rank (Dim)", justify="right")
        table.add_column("Successor Consistency", justify="right")

        results = {}
        for sec in sorted(section_map.keys()):
            if sec == "unknown": continue
            
            tokens = section_map[sec]
            if len(tokens) < 1000: continue
            
            # Dimensionality
            dim_res = dim_analyzer.estimate_dimensionality(tokens)
            rank = dim_res.get('effective_rank_90', 0)
            
            # Consistency (we need lines for the tester, so I'll approximate with windows)
            # Refactoring PathCollisionTester to handle raw list
            coll_res = coll_tester.calculate_successor_consistency([tokens])
            cons = coll_res.get('mean_consistency', 0.0)
            
            results[sec] = {"rank": rank, "consistency": cons, "token_count": len(tokens)}
            
            table.add_row(
                sec.capitalize(),
                str(len(tokens)),
                str(rank),
                f"{cons:.4f}"
            )
            
        console.print(table)
        
        # Save results
        output_dir = Path("results/data/phase5_mechanism")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "sectional_profiles.json")
            
        store.save_run(run)

if __name__ == "__main__":
    run_sectional_profiling()
