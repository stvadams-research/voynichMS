from typing import List
from foundation.storage.metadata import MetadataStore, RegionRecord, RegionEdgeRecord
from foundation.core.geometry import Box
import logging
logger = logging.getLogger(__name__)

class GraphBuilder:
    def __init__(self, store: MetadataStore):
        self.store = store

    def build_graph(self, page_id: str):
        """
        Build relationships between all regions on a page.
        """
        session = self.store.Session()
        try:
            # Fetch all regions for the page
            regions = session.query(RegionRecord).filter_by(page_id=page_id).all()
            
            # Compare all pairs (O(N^2) - okay for Level 2B scale)
            for i, r1 in enumerate(regions):
                b1 = Box(**r1.bbox)
                for j, r2 in enumerate(regions):
                    if i == j:
                        continue
                    
                    b2 = Box(**r2.bbox)
                    
                    # Contains
                    # Check if b1 contains b2
                    # Simple check: b2 inside b1
                    if (b2.x_min >= b1.x_min and b2.x_max <= b1.x_max and
                        b2.y_min >= b1.y_min and b2.y_max <= b1.y_max):
                        self.store.add_region_edge(r1.id, r2.id, "contains", 1.0)
                        self.store.add_region_edge(r2.id, r1.id, "contained_by", 1.0)
                    
                    # Overlaps
                    iou = b1.iou(b2)
                    if iou > 0:
                        self.store.add_region_edge(r1.id, r2.id, "overlaps", iou)
                    
                    # Near (simple distance check between centers)
                    # Not implementing full distance logic here to save space, 
                    # but would go here.
            
            session.commit()
        finally:
            session.close()
