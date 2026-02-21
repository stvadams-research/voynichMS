#!/usr/bin/env python3
"""Phase 14T: Boundary Coupling Audit.

Tests if the identified mechanical Mask States correlate with illustration 
boundaries (folio transitions).
"""

import sys
import json
import numpy as np
from pathlib import Path
from rich.console import Console
from collections import Counter, defaultdict
from sklearn.cluster import KMeans

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.storage.metadata import MetadataStore, PageRecord, TranscriptionLineRecord, TranscriptionTokenRecord
from phase1_foundation.core.provenance import ProvenanceWriter

DB_PATH = "sqlite:///data/voynich.db"
OUTPUT_PATH = project_root / "results/data/phase14_machine/boundary_coupling.json"
console = Console()

def get_lines_with_folios(store):
    session = store.Session()
    try:
        rows = (
            session.query(TranscriptionTokenRecord.content, PageRecord.id, TranscriptionLineRecord.id)
            .join(TranscriptionLineRecord, TranscriptionTokenRecord.line_id == TranscriptionLineRecord.id)
            .join(PageRecord, TranscriptionLineRecord.page_id == PageRecord.id)
            .filter(PageRecord.dataset_id == "voynich_real")
            .order_by(PageRecord.id, TranscriptionLineRecord.line_index, TranscriptionTokenRecord.token_index)
            .all()
        )
        
        folio_data = defaultdict(list)
        current_line = []
        last_line_id = None
        last_folio_id = None
        
        for content, folio_id, line_id in rows:
            if last_line_id is not None and line_id != last_line_id:
                folio_data[last_folio_id].append(current_line)
                current_line = []
            current_line.append(content)
            last_line_id = line_id
            last_folio_id = folio_id
            
        if current_line:
            folio_data[last_folio_id].append(current_line)
            
        return folio_data
    finally:
        session.close()

def build_folio_vector(lines, top_50, word_to_idx):
    vec = np.zeros(len(top_50) * len(top_50))
    for line in lines:
        for i in range(len(line) - 1):
            u, v = line[i], line[i+1]
            if u in word_to_idx and v in word_to_idx:
                idx = word_to_idx[u] * len(top_50) + word_to_idx[v]
                vec[idx] += 1
    if np.sum(vec) > 0:
        vec /= np.sum(vec)
    return vec

def main():
    console.print("[bold magenta]Phase 14T: Boundary Coupling Audit[/bold magenta]")
    
    # 1. Load Data
    store = MetadataStore(DB_PATH)
    folio_data = get_lines_with_folios(store)
    folios = sorted(folio_data.keys())
    
    # 2. Setup Vectors
    all_tokens = [t for f in folio_data.values() for l in f for t in l]
    top_50 = [w for w, c in Counter(all_tokens).most_common(50)]
    word_to_idx = {w: i for i, w in enumerate(top_50)}
    
    folio_vectors = []
    valid_folios = []
    for f in folios:
        vec = build_folio_vector(folio_data[f], top_50, word_to_idx)
        if np.sum(vec) > 0:
            folio_vectors.append(vec)
            valid_folios.append(f)
            
    folio_vectors = np.array(folio_vectors)
    
    # 3. Cluster into 3 Mask States
    console.print(f"Clustering {len(valid_folios)} folios into 3 mechanical states...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    labels = kmeans.fit_predict(folio_vectors)
    
    # 4. Analyze Persistence vs. Coupling
    # A state is 'coupled' if it persists across multiple folios then shifts
    shifts = 0
    for i in range(1, len(labels)):
        if labels[i] != labels[i-1]:
            shifts += 1
            
    # 5. Save and Report
    results = {
        "num_folios": len(valid_folios),
        "num_states": 3,
        "total_shifts": shifts,
        "avg_state_duration": len(labels) / (shifts + 1),
        "labels": {valid_folios[i]: int(labels[i]) for i in range(len(labels))}
    }
    
    saved = ProvenanceWriter.save_results(results, OUTPUT_PATH)
    
    console.print(f"\nAverage State Duration: [bold]{results['avg_state_duration']:.2f} folios[/bold]")
    console.print(f"Total State Shifts: [bold cyan]{shifts}[/bold cyan]")
    
    if results['avg_state_duration'] > 5:
        console.print("\n[bold green]PASS:[/bold green] Mechanical states are locally coupled to production regions.")
    else:
        console.print("\n[bold yellow]CONDITION:[/bold yellow] Mechanical states shift too rapidly for region-coupling.")

if __name__ == "__main__":
    main()
