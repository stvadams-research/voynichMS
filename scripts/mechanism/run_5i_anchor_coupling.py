#!/usr/bin/env python3
"""
Phase 5H: Proximity-Conditioned Consistency

Tests if text anchored to illustrations is more or less consistent than 
unanchored text.
"""

import sys
from pathlib import Path
import json
from collections import defaultdict

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from foundation.core.provenance import ProvenanceWriter
from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, AnchorRecord, WordRecord, TranscriptionTokenRecord
from mechanism.large_object.collision_testing import PathCollisionTester

console = Console()
DB_PATH = "sqlite:///data/voynich.db"

def get_anchored_word_ids(store):
    session = store.Session()
    try:
        # Get word IDs that are sources of an anchor
        anchors = session.query(AnchorRecord.source_id).filter(AnchorRecord.source_type == 'word').all()
        return {a[0] for a in anchors}
    finally:
        session.close()

def get_tokens_and_anchor_status(store):
    session = store.Session()
    try:
        from foundation.storage.metadata import PageRecord, LineRecord, WordAlignmentRecord
        
        # We need tokens and their anchor status
        anchored_ids = get_anchored_word_ids(store)
        
        results = (
            session.query(TranscriptionTokenRecord.content, WordRecord.id)
            .join(WordAlignmentRecord, TranscriptionTokenRecord.id == WordAlignmentRecord.token_id)
            .join(WordRecord, WordAlignmentRecord.word_id == WordRecord.id)
            .all()
        )
        
        anchored_tokens = []
        unanchored_tokens = []
        
        for content, word_id in results:
            if word_id in anchored_ids:
                anchored_tokens.append(content)
            else:
                unanchored_tokens.append(content)
                
        return anchored_tokens, unanchored_tokens
    finally:
        session.close()

def run_anchor_coupling():
    console.print(Panel.fit(
        "[bold blue]Phase 5H: Proximity-Conditioned Consistency[/bold blue]\n"
        "Testing if illustration proximity affects mechanism determinism",
        border_style="blue"
    ))

    with active_run(config={"command": "run_5h_anchor_coupling", "seed": 42}) as run:
        store = MetadataStore(DB_PATH)
        coll_tester = PathCollisionTester(context_len=2)
        
        # 1. Fetch Data
        console.print("\n[bold yellow]Step 1: Partitioning Tokens by Anchor Status[/bold yellow]")
        anchored, unanchored = get_tokens_and_anchor_status(store)
        
        console.print(f"  Anchored tokens: {len(anchored)}")
        console.print(f"  Unanchored tokens: {len(unanchored)}")
        
        # 2. Analyze
        anchored_res = coll_tester.calculate_successor_consistency([anchored])
        unanchored_res = coll_tester.calculate_successor_consistency([unanchored])
        
        # 3. Report
        table = Table(title="Illustration Coupling Signatures")
        table.add_column("Token Group", style="cyan")
        table.add_column("Successor Consistency", justify="right")
        table.add_column("Sample Size (Bigrams)", justify="right")

        table.add_row(
            "Anchored (Proximity)", 
            f"{anchored_res['mean_consistency']:.4f}", 
            str(anchored_res['num_recurring_contexts'])
        )
        table.add_row(
            "Unanchored (Block)", 
            f"{unanchored_res['mean_consistency']:.4f}", 
            str(unanchored_res['num_recurring_contexts'])
        )
        
        console.print(table)
        
        # Save results
        results = {
            "anchored": anchored_res,
            "unanchored": unanchored_res
        }
        
        output_dir = Path("results/mechanism")
        output_dir.mkdir(parents=True, exist_ok=True)
        ProvenanceWriter.save_results(results, output_dir / "anchor_coupling.json")
            
        store.save_run(run)

if __name__ == "__main__":
    run_anchor_coupling()
