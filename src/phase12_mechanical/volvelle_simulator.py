"""
Voynich Volvelle Simulator (Mechanical Prototype)

Simulates the production of text via a physical combinatorial device 
(rotating wheel / volvelle) rather than a statistical lattice.
"""

from typing import List, Dict, Any, Optional
import random
import numpy as np

class VolvelleSimulator:
    """
    A 3-state mechanical simulator.
    Components:
    - Rings: The physical constraint slots.
    - Palette: The words assigned to slots.
    - State: The rotation of the rings (The Mask).
    """
    def __init__(self, vocab: List[str], seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.vocab = vocab
        # Physical Layout: 4 rings, each with 8 sectors (32 slots total)
        self.rings = []
        for _ in range(4):
            ring = self.vocab[:8]
            self.rng.shuffle(ring)
            self.rings.append(ring)
            # Remove used vocab
            self.vocab = self.vocab[8:]
            
        self.mask_state = 0 # 0, 1, or 2

    def rotate(self, state: int):
        """Sets the 'thematic key' / mask."""
        self.mask_state = state % 3

    def generate_token(self, ring_idx: int, position: int) -> str:
        """
        Picks a token from a ring based on position and current mask rotation.
        """
        ring = self.rings[ring_idx % 4]
        # The 'Physical' rule: Index is modulated by (position + mask)
        idx = (position + self.mask_state) % len(ring)
        return ring[idx]

    def generate_line(self, length: int) -> List[str]:
        line = []
        for p in range(length):
            # Select ring based on simple alternating logic
            ring_idx = p % 4
            token = self.generate_token(ring_idx, p)
            line.append(token)
        return line

    def generate_corpus(self, num_lines: int, line_length: int = 6) -> List[List[str]]:
        corpus = []
        for i in range(num_lines):
            # Periodically shift the mask (simulating thematic sections)
            if i % 50 == 0:
                self.rotate(self.rng.randint(0, 2))
            corpus.append(self.generate_line(line_length))
        return corpus
