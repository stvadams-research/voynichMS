import logging
from abc import ABC, abstractmethod

import numpy as np

logger = logging.getLogger(__name__)

class RegionEncoder(ABC):
    @abstractmethod
    def encode(self, image_path: str, bbox: dict) -> bytes:
        pass

class DummyEncoder(RegionEncoder):
    """
    Returns a random vector as a dummy embedding.
    """
    def __init__(self, dim: int = 128, seed: int | None = 42):
        self.dim = dim
        self.seed = seed

    def encode(self, image_path: str, bbox: dict) -> bytes:
        # Generate deterministic random vector using local RandomState
        rs = np.random.RandomState(self.seed)
        vec = rs.rand(self.dim).astype(np.float32)
        return vec.tobytes()
