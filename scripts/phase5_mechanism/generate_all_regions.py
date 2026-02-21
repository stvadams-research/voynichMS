#!/usr/bin/env python3
"""
Generates geometric regions for the entire voynich_real dataset.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))

from phase1_foundation.regions.dummy import GridProposer  # noqa: E402
from phase1_foundation.runs.manager import active_run  # noqa: E402
from phase1_foundation.storage.metadata import MetadataStore, PageRecord  # noqa: E402

DB_PATH = "sqlite:///data/voynich.db"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=3)
    parser.add_argument("--cols", type=int, default=3)
    parser.add_argument("--padding", type=float, default=0.1)
    args = parser.parse_args()

    with active_run(config={"command": "generate_all_regions", "seed": 42, "rows": args.rows, "cols": args.cols, "padding": args.padding}) as run:
        store = MetadataStore(DB_PATH)
        proposer = GridProposer(rows=args.rows, cols=args.cols, scale="mid", padding=args.padding)

        # 2. Get all pages
        session = store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id="voynich_real").all()
            print(f"Generating regions for {len(pages)} pages...")

            total_regions = 0
            for page in pages:
                regions = proposer.propose_regions(page.id, page.image_path)
                for r in regions:
                    store.add_region(
                        id=f"reg_{page.id}_{total_regions}",
                        page_id=page.id,
                        scale=r.scale,
                        method=r.method,
                        bbox=r.bbox.model_dump(),
                        confidence=r.confidence
                    )
                    total_regions += 1

            print(f"\nDone. Total regions: {total_regions}")
            store.save_run(run)
        finally:
            session.close()

if __name__ == "__main__":
    main()
