import random
import uuid
from typing import Dict, Any, List
from phase1_foundation.controls.interface import ControlGenerator
from phase1_foundation.storage.metadata import PageRecord, GlyphCandidateRecord, WordRecord, LineRecord
from phase1_foundation.core.id_factory import DeterministicIDFactory
import logging
logger = logging.getLogger(__name__)

class ScrambledControlGenerator(ControlGenerator):
    """
    Generates a scrambled control dataset by shuffling glyphs/words.
    """
    def generate(self, source_dataset_id: str, control_id: str, seed: int = 42, params: Dict[str, Any] = None) -> str:
        rng = random.Random(seed)
        params = params or {}
        id_factory = DeterministicIDFactory(seed=seed)
        
        # Register control dataset
        self.store.add_control_dataset(
            id=control_id,
            source_dataset_id=source_dataset_id,
            type="scrambled",
            params=params,
            seed=seed
        )
        
        session = self.store.Session()
        try:
            pages = session.query(PageRecord).filter_by(dataset_id=source_dataset_id).all()
            
            for page in pages:
                # Register page for control dataset (same image path)
                control_page_id = f"{control_id}_{page.id}"
                self.store.add_page(
                    page_id=control_page_id,
                    dataset_id=control_id,
                    image_path=page.image_path,
                    checksum=page.checksum,
                    width=page.width,
                    height=page.height
                )
                
                # Fetch original lines and words
                lines = session.query(LineRecord).filter_by(page_id=page.id).all()
                
                # Map old_line_id -> new_line_id
                line_map = {}
                for line in lines:
                    new_id = id_factory.next_uuid(f"line:{control_page_id}")
                    self.store.add_line(
                        id=new_id,
                        page_id=control_page_id,
                        line_index=line.line_index,
                        bbox=line.bbox,
                        confidence=line.confidence
                    )
                    line_map[line.id] = new_id

                for line in lines:
                    words = session.query(WordRecord).filter_by(line_id=line.id).all()
                    for word in words:
                        self.store.add_word(
                            id=id_factory.next_uuid(f"word:{line_map[line.id]}"),
                            line_id=line_map[line.id],
                            word_index=word.word_index,
                            bbox=word.bbox,
                            features=word.features,
                            confidence=word.confidence
                        )

                # NOW SCRAMBLE REGIONS
                from phase1_foundation.storage.metadata import RegionRecord
                regions = session.query(RegionRecord).filter_by(page_id=page.id).all()
                
                if regions:
                    bboxes = [r.bbox for r in regions]
                    rng.shuffle(bboxes) # Shuffle positions using local rng
                    
                    for i, region in enumerate(regions):
                        new_region_id = f"{control_id}_{region.id}"
                        
                        self.store.add_region(
                            id=new_region_id,
                            page_id=control_page_id,
                            scale=region.scale,
                            method=region.method,
                            bbox=bboxes[i], 
                            features=region.features,
                            confidence=region.confidence
                        )

            session.commit()
        finally:
            session.close()
            
        return control_id
