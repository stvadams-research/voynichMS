from abc import ABC, abstractmethod
import random
import numpy as np
from typing import List

class RegionEncoder(ABC):
    @abstractmethod
    def encode(self, image_path: str, bbox: dict) -> bytes:
        pass

class DummyEncoder(RegionEncoder):
    """
    Returns a random vector as a dummy embedding.
    """
    def __init__(self, dim: int = 128):
        self.dim = dim

    def encode(self, image_path: str, bbox: dict) -> bytes:
        # Generate random vector
        vec = np.random.rand(self.dim).astype(np.float32)
        return vec.tobytes()
