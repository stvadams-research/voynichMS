from typing import List, Optional
import random
from phase1_foundation.regions.interface import RegionProposer, ProposedRegion
from phase1_foundation.core.geometry import Box
import logging
logger = logging.getLogger(__name__)

class GridProposer(RegionProposer):
    """
    Proposes regions by dividing the page into a grid.
    Useful for mid/large scale testing.
    """
    def __init__(self, rows: int = 3, cols: int = 3, scale: str = "large", padding: float = 0.1):
        self.rows = rows
        self.cols = cols
        self.scale = scale
        self.padding = padding

    def propose_regions(self, page_id: str, image_path: str) -> List[ProposedRegion]:
        regions = []
        w_step = 1.0 / self.cols
        h_step = 1.0 / self.rows
        
        for r in range(self.rows):
            for c in range(self.cols):
                # Calculate padded box
                x_min = c * w_step + (w_step * self.padding)
                y_min = r * h_step + (h_step * self.padding)
                x_max = (c + 1) * w_step - (w_step * self.padding)
                y_max = (r + 1) * h_step - (h_step * self.padding)
                
                bbox = Box(
                    x_min=x_min,
                    y_min=y_min,
                    x_max=x_max,
                    y_max=y_max
                )
                regions.append(ProposedRegion(
                    bbox=bbox,
                    scale=self.scale,
                    method="grid",
                    confidence=1.0
                ))
        return regions

class RandomBlobProposer(RegionProposer):
    """
    Proposes random small regions.
    Useful for primitive scale testing.
    """
    def __init__(self, count: int = 20, scale: str = "primitive", seed: Optional[int] = 42):
        self.count = count
        self.scale = scale
        self.seed = seed

    def propose_regions(self, page_id: str, image_path: str) -> List[ProposedRegion]:
        regions = []
        # Intentional controller bypass: this dummy proposer is used for synthetic
        # region stubs and keeps deterministic randomness fully local.
        rng = random.Random(self.seed)
        
        for _ in range(self.count):
            # Random center
            cx = rng.uniform(0.1, 0.9)
            cy = rng.uniform(0.1, 0.9)
            # Random size
            w = rng.uniform(0.01, 0.05)
            h = rng.uniform(0.01, 0.05)
            
            bbox = Box(
                x_min=max(0, cx - w/2),
                y_min=max(0, cy - h/2),
                x_max=min(1, cx + w/2),
                y_max=min(1, cy + h/2)
            )
            regions.append(ProposedRegion(
                bbox=bbox,
                scale=self.scale,
                method="random_blob",
                confidence=rng.uniform(0.5, 0.9)
            ))
        return regions
