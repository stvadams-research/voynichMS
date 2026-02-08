#!/usr/bin/env python3
"""
Generates geometric anchors for the entire voynich_real dataset.
"""

import sys
from pathlib import Path
import argparse

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from foundation.runs.manager import active_run
from foundation.storage.metadata import MetadataStore, PageRecord
from foundation.anchors.engine import AnchorEngine

DB_PATH = "sqlite:///data/voynich.db"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.1)
    args = parser.parse_args()

    with active_run(config={"command": "generate_all_anchors", "seed": 42, "threshold": args.threshold}) as run:
        store = MetadataStore(DB_PATH)
        engine = AnchorEngine(store, seed=42)
        
        # 1. Register method
        method_id = engine.register_method(
            name="geometric_v1", 
            description="Default geometric overlap and proximity",
            parameters={"distance_threshold": args.threshold}
        )
        
        # 2. Get all pages
        session = store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id="voynich_real").all()
            print(f"Generating anchors for {len(pages)} pages...")
            
            total_anchors = 0
            for page in pages:
                count = engine.compute_page_anchors(page.id, method_id, run.run_id)
                total_anchors += count
                if count > 0:
                    print(f"  {page.id}: {count} anchors")
            
            print(f"\nDone. Total anchors: {total_anchors}")
            store.save_run(run)
        finally:
            session.close()

if __name__ == "__main__":
    main()
