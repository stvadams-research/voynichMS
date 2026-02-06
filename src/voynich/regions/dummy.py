from typing import List
import random
from voynich.regions.interface import RegionProposer, ProposedRegion
from voynich.core.geometry import Box

class GridProposer(RegionProposer):
    """
    Proposes regions by dividing the page into a grid.
    Useful for mid/large scale testing.
    """
    def __init__(self, rows: int = 3, cols: int = 3, scale: str = "large"):
        self.rows = rows
        self.cols = cols
        self.scale = scale

    def propose_regions(self, page_id: str, image_path: str) -> List[ProposedRegion]:
        regions = []
        w_step = 1.0 / self.cols
        h_step = 1.0 / self.rows
        
        for r in range(self.rows):
            for c in range(self.cols):
                bbox = Box(
                    x_min=c * w_step,
                    y_min=r * h_step,
                    x_max=(c + 1) * w_step,
                    y_max=(r + 1) * h_step
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
    def __init__(self, count: int = 20, scale: str = "primitive"):
        self.count = count
        self.scale = scale

    def propose_regions(self, page_id: str, image_path: str) -> List[ProposedRegion]:
        regions = []
        for _ in range(self.count):
            # Random center
            cx = random.uniform(0.1, 0.9)
            cy = random.uniform(0.1, 0.9)
            # Random size
            w = random.uniform(0.01, 0.05)
            h = random.uniform(0.01, 0.05)
            
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
                confidence=random.uniform(0.5, 0.9)
            ))
        return regions
