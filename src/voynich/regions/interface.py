from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from pydantic import BaseModel
from voynich.core.geometry import Box

class ProposedRegion(BaseModel):
    bbox: Box
    scale: str # primitive, mid, large
    method: str
    features: Optional[Dict] = None
    confidence: float = 1.0

class RegionProposer(ABC):
    @abstractmethod
    def propose_regions(self, page_id: str, image_path: str) -> List[ProposedRegion]:
        pass
