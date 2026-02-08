"""
Large Object Simulators

Implements traversal models for grids and DAGs.
"""

import random
from typing import List, Dict, Any, Tuple
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class LargeGridSimulator:
    """
    Family 1: A large M x N grid of Voynich tokens.
    """
    def __init__(self, grammar_path: Path, rows: int = 50, cols: int = 50):
        self.generator = GrammarBasedGenerator(grammar_path)
        self.rows = rows
        self.cols = cols
        self.grid = self._build_grid()

    def _build_grid(self) -> List[List[str]]:
        grid = []
        for _ in range(self.rows):
            grid.append([self.generator.generate_word() for _ in range(self.cols)])
        return grid

    def generate_line(self, length: int) -> List[str]:
        # Start at a random location
        r = random.randint(0, self.rows - 1)
        c = random.randint(0, self.cols - 1)
        
        # Fixed walk (e.g., move right)
        line = []
        for i in range(length):
            line.append(self.grid[r][(c + i) % self.cols])
        return line

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]
