"""
Entry Point Simulators

Models different mechanisms for selecting starting points in a deterministic structure.
"""

import random
from typing import List, Dict, Any, Tuple
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class EntryMechanismSimulator:
    """
    Simulates path instantiation mechanisms.
    """
    def __init__(self, grammar_path: Path, vocab_size: int = 1000):
        self.generator = GrammarBasedGenerator(grammar_path)
        # We simulate a 'Large Object' as a list of nodes (pre-generated words)
        self.nodes = [self.generator.generate_word() for _ in range(vocab_size)]

    def generate_uniform_independent(self, num_lines: int, line_len: int) -> List[List[str]]:
        """Family 1: Purely random start per line."""
        corpus = []
        for _ in range(num_lines):
            start_idx = random.randint(0, len(self.nodes) - 1)
            line = []
            for i in range(line_len):
                line.append(self.nodes[(start_idx + i) % len(self.nodes)])
            corpus.append(line)
        return corpus

    def generate_locally_coupled(self, num_lines: int, line_len: int, coupling: float = 0.5) -> List[List[str]]:
        """Family 2: Next start is near previous start."""
        corpus = []
        start_idx = random.randint(0, len(self.nodes) - 1)
        
        for _ in range(num_lines):
            line = []
            for i in range(line_len):
                line.append(self.nodes[(start_idx + i) % len(self.nodes)])
            corpus.append(line)
            
            # Choose next start
            if random.random() < coupling:
                # Coupled: move only a small distance
                start_idx = (start_idx + random.randint(1, 10)) % len(self.nodes)
            else:
                # Decoupled: jump anywhere
                start_idx = random.randint(0, len(self.nodes) - 1)
                
        return corpus
