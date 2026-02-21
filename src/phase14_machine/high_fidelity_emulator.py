"""
High-Fidelity Voynich Engine (Phase 14)

A full-scale mechanical emulator using the solved 2000-token palette 
and the discovered 3-state state-space.
"""

from typing import List, Dict, Any, Optional
import random
import numpy as np

class HighFidelityVolvelle:
    """
    Simulates the full-scale production tool.
    """
    def __init__(self, full_grid: Dict[int, List[str]], seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.columns = full_grid
        self.num_cols = len(full_grid)
        self.mask_state = 0
        
        # Suffix Mapping for Biased Drift
        self.suffix_weights = {"dy": 5.0, "in": 4.0, "y": 3.0, "m": 2.0}

    def generate_token(self, column_idx: int, position: int) -> str:
        # Physical Rule: Slot selection is biased by position and mask
        col = self.columns.get(column_idx, self.columns[1])
        base_offset = (position + self.mask_state) % len(col)
        
        # Suffix-Biased Drift (Task 7.2):
        # We sample 5 candidates from the drift window and pick the one 
        # with the most 'Voynich-typical' suffix.
        candidates = []
        for _ in range(5):
            drift = self.rng.randint(-15, 15)
            idx = (base_offset + drift) % len(col)
            word = col[idx]
            # Weight by suffix
            weight = 1.0
            for s, w in self.suffix_weights.items():
                if word.endswith(s):
                    weight += w
            candidates.append((word, weight))
            
        # Weighted selection
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        return self.rng.choices(words, weights=weights, k=1)[0]

    def set_mask(self, state: int):
        self.mask_state = state % 12 # 12 discrete settings

    def generate_line(self, length: int) -> List[str]:
        line = []
        for p in range(length):
            # Complex Ring Mapping: 
            # Modulate column selection by position AND current mask
            col_idx = ((p + self.mask_state) % self.num_cols) + 1
            line.append(self.generate_token(col_idx, p))
        return line

    def generate_mirror_corpus(self, num_lines: int) -> List[List[str]]:
        corpus = []
        for i in range(num_lines):
            # Dynamic Masking: Scribe shifts setting every few lines
            if i % 20 == 0:
                self.set_mask(self.rng.randint(0, 11))
                
            corpus.append(self.generate_line(length=random.randint(4, 10)))
        return corpus
