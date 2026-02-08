"""
Phase 5G Topology Simulators

Implements Grids, Layered Tables, DAGs, and Lattices for non-equivalence testing.
"""

import random
from typing import List, Dict, Any, Tuple
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class TopologySimulator:
    def __init__(self, grammar_path: Path, vocab_size: int = 3600):
        self.generator = GrammarBasedGenerator(grammar_path)
        self.nodes = [self.generator.generate_word() for _ in range(vocab_size)]

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class GridTopologySimulator(TopologySimulator):
    """60x60 Grid"""
    def __init__(self, grammar_path: Path, rows: int = 60, cols: int = 60):
        super().__init__(grammar_path, vocab_size=rows * cols)
        self.rows = rows
        self.cols = cols
        self.grid = []
        for r in range(rows):
            self.grid.append(self.nodes[r*cols : (r+1)*cols])

    def generate_line(self, length: int) -> List[str]:
        r = random.randint(0, self.rows - 1)
        c = random.randint(0, self.cols - 1)
        line = []
        for i in range(length):
            line.append(self.grid[r][(c + i) % self.cols])
        return line

class LayeredTableSimulator(TopologySimulator):
    """10 layers of 20x20 grids"""
    def __init__(self, grammar_path: Path, layers: int = 10, size: int = 20):
        super().__init__(grammar_path, vocab_size=layers * size * size)
        self.layers = layers
        self.size = size
        self.sheets = []
        for l in range(layers):
            sheet = []
            for r in range(size):
                sheet.append(self.nodes[l*size*size + r*size : l*size*size + (r+1)*size])
            self.sheets.append(sheet)

    def generate_line(self, length: int) -> List[str]:
        l = random.randint(0, self.layers - 1)
        r = random.randint(0, self.size - 1)
        c = random.randint(0, self.size - 1)
        line = []
        for i in range(length):
            line.append(self.sheets[l][r][(c + i) % self.size])
        return line

class DAGTopologySimulator(TopologySimulator):
    """Stratified DAG where each node has a fixed successor rule."""
    def __init__(self, grammar_path: Path, num_nodes: int = 4000):
        super().__init__(grammar_path, vocab_size=num_nodes)
        self.successors = {}
        # Pre-assign deterministic successors (layered structure)
        for i in range(num_nodes):
            self.successors[i] = (i + 1) % num_nodes

    def generate_line(self, length: int) -> List[str]:
        idx = random.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            line.append(self.nodes[idx])
            idx = self.successors[idx]
        return line

class LatticeTopologySimulator(TopologySimulator):
    """Implicit constraints based on token content."""
    def __init__(self, grammar_path: Path, vocab_size: int = 3600):
        super().__init__(grammar_path, vocab_size=vocab_size)
        # Successor is the node with the closest string match or some hash rule
        self.node_map = {n: i for i, n in enumerate(self.nodes)}

    def generate_line(self, length: int) -> List[str]:
        idx = random.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            word = self.nodes[idx]
            line.append(word)
            # Pseudo-deterministic skip based on last character
            skip = ord(word[-1]) % 10 + 1
            idx = (idx + skip) % len(self.nodes)
        return line
