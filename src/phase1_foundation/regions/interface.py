import logging
from abc import ABC, abstractmethod

from pydantic import BaseModel

from phase1_foundation.core.geometry import Box

logger = logging.getLogger(__name__)

class ProposedRegion(BaseModel):
    bbox: Box
    scale: str # primitive, mid, large
    method: str
    features: dict | None = None
    confidence: float = 1.0

class RegionProposer(ABC):
    @abstractmethod
    def propose_regions(self, page_id: str, image_path: str) -> list[ProposedRegion]:
        pass
