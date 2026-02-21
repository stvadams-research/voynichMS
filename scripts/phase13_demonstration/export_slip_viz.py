#!/usr/bin/env python3
"""
Task 1.1: Export Slip Viz Data

Merges detected mechanical slips with their full line contexts 
for interactive visualization.
"""

import json
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from phase1_foundation.core.data_loading import load_canonical_lines
from phase1_foundation.storage.metadata import MetadataStore

DB_PATH = "sqlite:///data/voynich.db"
INPUT_PATH = project_root / "results/data/phase12_mechanical/slip_detection_results.json"
OUTPUT_DIR = project_root / "results/data/phase13_demonstration"
OUTPUT_FILE = OUTPUT_DIR / "slip_viz_data.json"

def main():
    print("Exporting data for Slip Explorer...")
    
    if not INPUT_PATH.exists():
        print(f"Error: {INPUT_PATH} not found. Run Phase 12A first.")
        return

    # 1. Load Slips
    with open(INPUT_PATH) as f:
        data = json.load(f)
    slips = data.get("results", data).get("slips", [])
    
    # 2. Load Full Corpus for Context
    store = MetadataStore(DB_PATH)
    lines = load_canonical_lines(store)
    
    # 3. Enrich Slips
    enriched_slips = []
    for s in slips:
        line_idx = s['line_index']
        token_idx = s['token_index']
        
        if line_idx >= len(lines) or line_idx < 1:
            continue
            
        curr_line = lines[line_idx]
        prev_line = lines[line_idx - 1]
        
        enriched_slips.append({
            "line_no": line_idx,
            "token_pos": token_idx,
            "word": s['word'],
            "current_line": curr_line,
            "previous_line": prev_line,
            "type": s['type']
        })
        
    # 4. Save
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump({"slips": enriched_slips}, f, indent=2)
        
    print(f"Exported {len(enriched_slips)} enriched slips to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
