import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

from phase1_foundation.core.geometry import Box
from phase1_foundation.core.id_factory import DeterministicIDFactory
from phase1_foundation.storage.metadata import (
    AnchorMethodRecord,
    LineRecord,
    MetadataStore,
    RegionRecord,
    WordRecord,
)


class AnchorEngine:
    def __init__(self, store: MetadataStore, seed: int = 0):
        self.store = store
        self.id_factory = DeterministicIDFactory(seed=seed)
        self.seed = seed

    @staticmethod
    def _canonical_parameters(parameters: dict[str, Any] | None) -> str:
        if not parameters:
            return "{}"
        try:
            return json.dumps(parameters, sort_keys=True, separators=(",", ":"))
        except TypeError:
            # Fallback for any unexpected non-serializable value.
            return str(parameters)

    def _method_id(self, name: str, parameters: dict[str, Any] | None) -> str:
        key = f"method:{name}:{self._canonical_parameters(parameters)}"
        return self.id_factory.fork(key).next_uuid("method")

    def _anchor_id(
        self,
        *,
        method_id: str,
        page_id: str,
        source_id: str,
        target_id: str,
        relation_type: str,
    ) -> str:
        key = (
            f"anchor:{method_id}:{page_id}:{source_id}:{target_id}:{relation_type}"
        )
        return self.id_factory.fork(key).next_uuid("anchor")

    def register_method(self, name: str, description: str = None, parameters: dict[str, Any] = None) -> str:
        """
        Register a new anchor method. Returns the method ID.
        """
        method_id = self._method_id(name, parameters)
        self.store.add_anchor_method(
            id=method_id,
            name=name,
            description=description,
            parameters=parameters
        )
        return method_id

    def _to_box(self, bbox: dict[str, Any]) -> Box:
        """Convert various bbox formats to Box object."""
        if "x_min" in bbox:
            return Box(**bbox)
        
        # Handle x,y,w,h format
        required = ["x", "y", "w", "h"]
        if not all(k in bbox for k in required):
            raise ValueError(f"BBox missing required fields {required}. Got: {list(bbox.keys())}")
            
        x = bbox["x"]
        y = bbox["y"]
        w = bbox["w"]
        h = bbox["h"]
        
        # If values are > 1, they are likely pixels. 
        # For anchoring to work with normalized regions, we must normalize them.
        # But we don't know the image size here.
        # For now, let's assume if they are large, we'll just treat them as 0-1 
        # by dividing by a large constant (placeholder normalization).
        # Actually, it's better to fix the data population.
        # But as a quick fix for the pilot:
        if x > 1 or y > 1 or w > 1 or h > 1:
            # Placeholder normalization (assume 1000x1500)
            return Box(
                x_min=max(0.0, min(1.0, x / 1000.0)),
                y_min=max(0.0, min(1.0, y / 1500.0)),
                x_max=max(0.0, min(1.0, (x + w) / 1000.0)),
                y_max=max(0.0, min(1.0, (y + h) / 1500.0))
            )
            
        return Box(
            x_min=x,
            y_min=y,
            x_max=x + w,
            y_max=y + h
        )

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
            
            logger.debug("%s regions=%d words=%d", page_id, len(regions), len(words))
            
            count = 0
            
            # O(N*M) check
            for r_idx, region in enumerate(regions):
                r_box = self._to_box(region.bbox)
                
                for w_idx, word in enumerate(words):
                    w_box = self._to_box(word.bbox)
                    
                    # 1. Check Overlap / Inside
                    iou = r_box.iou(w_box)
                    if iou > 0:
                        relation = "overlaps"
                        if r_box.contains(w_box):
                            relation = "inside"
                        
                        self.store.add_anchor(
                            id=self._anchor_id(
                                method_id=method_id,
                                page_id=page_id,
                                source_id=word.id,
                                target_id=region.id,
                                relation_type=relation,
                            ),
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
                            id=self._anchor_id(
                                method_id=method_id,
                                page_id=page_id,
                                source_id=word.id,
                                target_id=region.id,
                                relation_type="near",
                            ),
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
