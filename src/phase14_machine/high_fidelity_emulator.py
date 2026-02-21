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
    
    Attributes:
        lattice_map: Mapping from word to its predicted next window ID.
        window_contents: Mapping from window ID to the list of words in that window.
        num_windows: The total number of discrete windows in the physical model.
        mask_state: The current rotation/shift of the mask disc (0-11).
        current_scribe: The profile of the scribe agent (Hand 1 or Hand 2).
    """
    def __init__(self, 
                 lattice_map: Dict[str, int], 
                 window_contents: Dict[int, List[str]], 
                 seed: Optional[int] = None) -> None:
        """
        Initializes the emulator with a solved lattice and window set.
        
        Args:
            lattice_map: Mapping from token to next window index.
            window_contents: Mapping from window index to token list.
            seed: Optional seed for reproducibility.
        """
        self.rng = random.Random(seed)
        self.lattice_map = lattice_map 
        # Ensure window indices are integers for modulo math
        self.window_contents = {int(k): v for k, v in window_contents.items()}
        self.num_windows = len(self.window_contents)
        self.mask_state = 0
        
        # Scribe Agent Profiles (Based on Phase 7/14 calibration)
        self.scribe_profiles = {
            "Hand 1": {"drift": 15, "suffix_weights": {"dy": 12.0, "in": 4.0, "y": 8.0, "m": 3.0}},
            "Hand 2": {"drift": 25, "suffix_weights": {"in": 20.0, "dy": 2.0, "m": 10.0, "y": 5.0}}
        }
        self.current_scribe = "Hand 1"

    def set_scribe(self, hand: str) -> None:
        """Sets the active scribe profile."""
        if hand in self.scribe_profiles:
            self.current_scribe = hand

    def set_mask(self, state: int) -> None:
        """Sets the current mask rotation state (0 to 11)."""
        self.mask_state = state % 12

    def generate_token(self, window_idx: int, prev_word: Optional[str] = None) -> str:
        """
        Generates a single token from a given window, applying scribe biases.
        
        Args:
            window_idx: The base window index to select from.
            prev_word: The previously generated word (for repetition bias).
            
        Returns:
            A single generated token string.
        """
        profile = self.scribe_profiles[self.current_scribe]
        # The mask rotates the exposed windows relative to the base lattice
        modulated_idx = (window_idx + self.mask_state) % self.num_windows
        col = self.window_contents.get(modulated_idx, self.window_contents.get(0, []))
        
        if not col:
            return "???"
            
        candidates = []
        # Simulate the scribe scanning the window for 'attractive' candidates
        # We sample 20 random tokens from the window and weight them by bias
        for _ in range(20):
            idx = self.rng.randint(0, len(col) - 1)
            word = col[idx]
            
            # 1. Base Suffix Bias (Physical ergonomics of certain strokes)
            weight = 1.0
            for s, w in profile['suffix_weights'].items():
                if word.endswith(s): 
                    weight += w
            
            # 2. Repetition Echo (Phase 14.3):
            # Scribes are biased toward echoing character patterns from the 
            # previous word (Physical stroke-rhythm).
            if prev_word:
                # Simple character-set overlap as proxy for stroke-rhythm similarity
                overlap = len(set(word) & set(prev_word))
                weight += (overlap * 2.0)
                
            candidates.append((word, weight))
            
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        return self.rng.choices(words, weights=weights, k=1)[0]

    def generate_line(self, length: int) -> List[str]:
        """
        Generates a full line of synthetic Voynichese.
        
        Args:
            length: The number of tokens to generate.
            
        Returns:
            A list of token strings.
        """
        line = []
        # Lines usually start from a stable reset point or random entry
        current_window = self.rng.randint(0, self.num_windows - 1)
        prev_word = None
        
        for p in range(length):
            word = self.generate_token(current_window, prev_word=prev_word)
            line.append(word)
            # Lattice advances the machine state to the next window
            current_window = self.lattice_map.get(word, (current_window + 1) % self.num_windows)
            prev_word = word
            
        return line

    def generate_mirror_corpus(self, num_lines: int) -> List[List[str]]:
        """
        Generates a large-scale synthetic corpus mirroring the manuscript.
        
        Args:
            num_lines: Total lines to generate.
            
        Returns:
            A list of lines, each being a list of tokens.
        """
        corpus = []
        for i in range(num_lines):
            # Simulate section-level scribe shifts
            if i % 5000 == 0:
                self.set_scribe("Hand 1" if self.current_scribe == "Hand 2" else "Hand 2")
            # Simulate frequent mask rotations (settings)
            if i % 20 == 0:
                self.set_mask(self.rng.randint(0, 11))
            corpus.append(self.generate_line(length=random.randint(4, 10)))
        return corpus
