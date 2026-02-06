import uuid
from typing import List, Dict, Any
from voynich.storage.metadata import MetadataStore, RegionRecord, WordRecord, LineRecord, AnchorMethodRecord
from voynich.core.geometry import Box, Point

class AnchorEngine:
    def __init__(self, store: MetadataStore):
        self.store = store

    def register_method(self, name: str, description: str = None, parameters: Dict[str, Any] = None) -> str:
        """
        Register a new anchor method. Returns the method ID.
        """
        method_id = str(uuid.uuid4())
        self.store.add_anchor_method(
            id=method_id,
            name=name,
            description=description,
            parameters=parameters
        )
        return method_id

    def compute_page_anchors(self, page_id: str, method_id: str, run_id: str):
        """
        Compute anchors for a page using the specified method.
        """
        session = self.store.Session()
        try:
            # Get method params
            method = session.query(AnchorMethodRecord).filter_by(id=method_id).first()
            if not method:
                raise ValueError(f"Method {method_id} not found")
            
            params = method.parameters or {}
            threshold_dist = params.get("distance_threshold", 0.1)
            
            # Fetch objects
            regions = session.query(RegionRecord).filter_by(page_id=page_id).all()
            words = session.query(WordRecord).join(LineRecord).filter(LineRecord.page_id == page_id).all()
            
            count = 0
            
            # O(N*M) check
            for region in regions:
                r_box = Box(**region.bbox)
                
                for word in words:
                    w_box = Box(**word.bbox)
                    
                    # 1. Check Overlap / Inside
                    iou = r_box.iou(w_box)
                    if iou > 0:
                        relation = "overlaps"
                        if r_box.contains(w_box):
                            relation = "inside"
                        
                        self.store.add_anchor(
                            id=str(uuid.uuid4()),
                            run_id=run_id,
                            page_id=page_id,
                            source_type="word",
                            source_id=word.id,
                            target_type="region",
                            target_id=region.id,
                            relation_type=relation,
                            method_id=method_id,
                            score=iou
                        )
                        count += 1
                        continue # Don't double count as "near" if it overlaps
                    
                    # 2. Check Near (Distance)
                    dist = r_box.distance(w_box)
                    if dist < threshold_dist:
                        self.store.add_anchor(
                            id=str(uuid.uuid4()),
                            run_id=run_id,
                            page_id=page_id,
                            source_type="word",
                            source_id=word.id,
                            target_type="region",
                            target_id=region.id,
                            relation_type="near",
                            method_id=method_id,
                            score=1.0 - dist # Higher score = closer
                        )
                        count += 1
            
            return count
        finally:
            session.close()
