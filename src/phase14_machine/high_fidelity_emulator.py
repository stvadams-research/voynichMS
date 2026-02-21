"""
High-Fidelity Voynich Engine (Phase 14)

A full-scale mechanical emulator using a Lattice-Modulated Window system.
"""

import random
from typing import Any


class HighFidelityVolvelle:
    """
    Simulates the full-scale production tool using a word-to-window lattice.
    
    Attributes:
        lattice_map: Mapping from word to its predicted next window ID.
        window_contents: Mapping from window ID to the list of words in that window.
        num_windows: The total number of discrete windows in the physical model.
        mask_state: The current rotation/shift of the mask disc (0 to num_windows-1).
        current_scribe: The profile of the scribe agent (Hand 1 or Hand 2).
    """
    def __init__(self, 
                 lattice_map: dict[str, int], 
                 window_contents: dict[int, list[str]], 
                 seed: int | None = None,
                 log_choices: bool = False) -> None:
        """
        Initializes the emulator with a solved lattice and window set.
        
        Args:
            lattice_map: Mapping from token to next window index.
            window_contents: Mapping from window index to token list.
            seed: Optional seed for reproducibility.
            log_choices: If True, records the context of every generated token.
        """
        self.rng = random.Random(seed)
        self.lattice_map = lattice_map 
        # Ensure window indices are integers for modulo math
        self.window_contents = {int(k): v for k, v in window_contents.items()}
        self.num_windows = len(self.window_contents)
        self.mask_state = 0
        self.log_choices = log_choices
        self.choice_log: list[dict[str, Any]] = []
        
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
        """Sets the current mask rotation state (0 to num_windows-1)."""
        self.mask_state = state % self.num_windows

    def generate_token(self, window_idx: int, prev_word: str | None = None, pos: int = 0) -> str:
        """
        Generates a single token from a given window, applying scribe biases.
        
        Args:
            window_idx: The base window index to select from.
            prev_word: The previously generated word (for repetition bias).
            pos: Current word index in line.
            
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
        for _ in range(20):
            idx = self.rng.randint(0, len(col) - 1)
            word = col[idx]
            
            # 1. Base Suffix Bias
            weight = 1.0
            for s, w in profile['suffix_weights'].items():
                if word.endswith(s): 
                    weight += w
            
            # 2. Repetition Echo
            if prev_word:
                overlap = len(set(word) & set(prev_word))
                weight += (overlap * 2.0)
                
            candidates.append((word, weight, idx))
            
        words = [c[0] for c in candidates]
        weights = [c[1] for c in candidates]
        chosen_word = self.rng.choices(words, weights=weights, k=1)[0]
        
        if self.log_choices:
            # Find the original index of the chosen word in the window
            chosen_orig_idx = col.index(chosen_word)
            self.choice_log.append({
                "window_id": modulated_idx,
                "candidates_count": len(col),
                "chosen_word": chosen_word,
                "chosen_index": chosen_orig_idx,
                "token_pos": pos,
                "prev_word": prev_word,
                "mask_state": self.mask_state,
                "scribe": self.current_scribe
            })
            
        return chosen_word

    def generate_line(self, length: int) -> list[str]:
        """
        Generates a full line of synthetic Voynichese.
        
        Args:
            length: The number of tokens to generate.
            
        Returns:
            A list of token strings.
        """
        line = []
        current_window = self.rng.randint(0, self.num_windows - 1)
        prev_word = None
        
        for p in range(length):
            word = self.generate_token(current_window, prev_word=prev_word, pos=p)
            line.append(word)
            current_window = self.lattice_map.get(word, (current_window + 1) % self.num_windows)
            prev_word = word
            
        return line

    def generate_mirror_corpus(self, num_lines: int) -> list[list[str]]:
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
            # Simulate frequent mask rotations (full-range disc rotation)
            if i % 20 == 0:
                self.set_mask(self.rng.randint(0, self.num_windows - 1))
            corpus.append(self.generate_line(length=self.rng.randint(4, 10)))
        return corpus

    def trace_lines(self, lines: list[list[str]]) -> None:
        """
        Traces the real manuscript lines through the lattice and logs 
        the choice context for every admissible token.
        
        Args:
            lines: List of manuscript lines (tokenized).
        """
        current_window = 0
        prev_word = None
        
        for l_idx, line in enumerate(lines):
            for p_idx, word in enumerate(line):
                # 1. Check if word is known
                if word not in self.lattice_map:
                    # Snapping logic
                    continue
                
                # 2. Check Admissibility
                found_win = None
                for offset in [-1, 0, 1]:
                    check_win = (current_window + offset) % self.num_windows
                    col = self.window_contents.get(check_win, [])
                    if word in col:
                        found_win = check_win
                        break
                
                if found_win is not None:
                    # Log the choice
                    chosen_orig_idx = self.window_contents[found_win].index(word)
                    self.choice_log.append({
                        "type": "real_trace",
                        "line_no": l_idx,
                        "token_pos": p_idx,
                        "window_id": found_win,
                        "candidates_count": len(self.window_contents[found_win]),
                        "chosen_word": word,
                        "chosen_index": chosen_orig_idx,
                        "prev_word": prev_word
                    })

                # Advance machine to next predicted window
                current_window = self.lattice_map.get(word, (current_window + 1) % self.num_windows)
                prev_word = word
