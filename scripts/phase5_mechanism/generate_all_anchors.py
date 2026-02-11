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

from phase1_foundation.runs.manager import active_run
from phase1_foundation.storage.metadata import MetadataStore, PageRecord
from phase1_foundation.anchors.engine import AnchorEngine

DB_PATH = "sqlite:///data/voynich.db"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.1)
    parser.add_argument(
        "--dataset-id",
        default="voynich_real",
        help="Dataset id to process.",
    )
    parser.add_argument(
        "--method-name",
        default="geometric_v1",
        help="Anchor method name.",
    )
    parser.add_argument(
        "--description",
        default="Default geometric overlap and proximity",
        help="Anchor method description.",
    )
    args = parser.parse_args()

    with active_run(
        config={
            "command": "generate_all_anchors",
            "seed": 42,
            "threshold": args.threshold,
            "dataset_id": args.dataset_id,
            "method_name": args.method_name,
        }
    ) as run:
        store = MetadataStore(DB_PATH)
        engine = AnchorEngine(store, seed=42)
        
        # 1. Register method
        method_id = engine.register_method(
            name=args.method_name,
            description=args.description,
            parameters={"distance_threshold": args.threshold}
        )
        
        # 2. Get all pages
        session = store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=args.dataset_id).all()
            print(
                f"Generating anchors for {len(pages)} pages in {args.dataset_id} "
                f"with method {args.method_name} ({method_id})..."
            )
            
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
