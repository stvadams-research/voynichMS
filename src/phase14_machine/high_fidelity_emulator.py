"""
High-Fidelity Voynich Engine (Phase 14)

A full-scale mechanical emulator using a Lattice-Modulated Window system.
"""

from typing import List, Dict, Any, Optional
import random
import numpy as np

class HighFidelityVolvelle:
    """
    Simulates the full-scale production tool using a word-to-window lattice.
    """
    def __init__(self, lattice_map: Dict[str, int], window_contents: Dict[int, List[str]], seed: Optional[int] = None):
        self.rng = random.Random(seed)
        self.lattice_map = lattice_map # word -> window_id
        self.window_contents = {int(k): v for k, v in window_contents.items()}
        self.num_windows = len(self.window_contents)
        self.mask_state = 0
        
        # Scribe Agent Profiles (Final Calibration)
        self.scribe_profiles = {
            "Hand 1": {"drift": 15, "suffix_weights": {"dy": 12.0, "in": 4.0, "y": 8.0, "m": 3.0}},
            "Hand 2": {"drift": 25, "suffix_weights": {"in": 20.0, "dy": 2.0, "m": 10.0, "y": 5.0}}
        }
        self.current_scribe = "Hand 1"

    def set_scribe(self, hand: str):
        if hand in self.scribe_profiles:
            self.current_scribe = hand

    def set_mask(self, state: int):
        self.mask_state = state % 12

    def generate_token(self, window_idx: int) -> str:
        profile = self.scribe_profiles[self.current_scribe]
        # Modulate window index by mask state
        modulated_idx = (window_idx + self.mask_state) % self.num_windows
        col = self.window_contents.get(modulated_idx, self.window_contents[0])
        
        # Scribe Drift (Human Choice within the physical window)
        candidates = []
        for _ in range(15):
            # We pick a random slot in the window, mimicking eye-movement
            idx = self.rng.randint(0, len(col) - 1)
            word = col[idx]
            weight = 1.0
            for s, w in profile['suffix_weights'].items():
                if word.endswith(s): weight += w
            candidates.append((word, weight))
            
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        return self.rng.choices(words, weights=weights, k=1)[0]

    def generate_line(self, length: int) -> List[str]:
        line = []
        # Initial window (random)
        current_window = self.rng.randint(0, self.num_windows - 1)
        
        for p in range(length):
            word = self.generate_token(current_window)
            line.append(word)
            # The word chosen determines the NEXT window (The Lattice Rule)
            current_window = self.lattice_map.get(word, (current_window + 1) % self.num_windows)
            
        return line

    def generate_mirror_corpus(self, num_lines: int) -> List[List[str]]:
        corpus = []
        for i in range(num_lines):
            if i % 5000 == 0:
                self.set_scribe("Hand 1" if self.current_scribe == "Hand 2" else "Hand 2")
            if i % 20 == 0:
                self.set_mask(self.rng.randint(0, 11))
            corpus.append(self.generate_line(length=random.randint(4, 10)))
        return corpus
