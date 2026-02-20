"""
Phase 5G Topology Simulators

Implements Grids, Layered Tables, DAGs, and Lattices for non-equivalence testing.
"""

import random
from typing import List, Dict, Any, Tuple, Optional
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator
from phase1_foundation.config import require_seed_if_strict
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class TopologySimulator:
    def __init__(self, grammar_path: Path, vocab_size: int = 3600, seed: Optional[int] = None):
        require_seed_if_strict(seed, "TopologySimulator")
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.nodes = [self.generator.generate_word() for _ in range(vocab_size)]

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class GridTopologySimulator(TopologySimulator):
    """60x60 Grid"""
    def __init__(self, grammar_path: Path, rows: int = 60, cols: int = 60, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size=rows * cols, seed=seed)
        self.rows = rows
        self.cols = cols
        self.grid = []
        for r in range(rows):
            self.grid.append(self.nodes[r*cols : (r+1)*cols])

    def generate_line(self, length: int) -> List[str]:
        r = self.rng.randint(0, self.rows - 1)
        c = self.rng.randint(0, self.cols - 1)
        line = []
        for i in range(length):
            line.append(self.grid[r][(c + i) % self.cols])
        return line

class LayeredTableSimulator(TopologySimulator):
    """10 layers of 20x20 grids"""
    def __init__(self, grammar_path: Path, layers: int = 10, size: int = 20, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size=layers * size * size, seed=seed)
        self.layers = layers
        self.size = size
        self.sheets = []
        for l in range(layers):
            sheet = []
            for r in range(size):
                sheet.append(self.nodes[l*size*size + r*size : l*size*size + (r+1)*size])
            self.sheets.append(sheet)

    def generate_line(self, length: int) -> List[str]:
        l = self.rng.randint(0, self.layers - 1)
        r = self.rng.randint(0, self.size - 1)
        c = self.rng.randint(0, self.size - 1)
        line = []
        for i in range(length):
            line.append(self.sheets[l][r][(c + i) % self.size])
        return line

class DAGTopologySimulator(TopologySimulator):
    """Stratified DAG where each node has a fixed successor rule."""
    def __init__(self, grammar_path: Path, num_nodes: int = 4000, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size=num_nodes, seed=seed)
        self.successors = {}
        # Pre-assign deterministic successors (layered structure)
        for i in range(num_nodes):
            self.successors[i] = (i + 1) % num_nodes

    def generate_line(self, length: int) -> List[str]:
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            line.append(self.nodes[idx])
            idx = self.successors[idx]
        return line

class LatticeTopologySimulator(TopologySimulator):
    """Implicit constraints based on token content."""
    def __init__(self, grammar_path: Path, vocab_size: int = 3600, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size=vocab_size, seed=seed)
        # Successor is the node with the closest string match or some hash rule
        self.node_map = {n: i for i, n in enumerate(self.nodes)}

    def generate_line(self, length: int) -> List[str]:
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            word = self.nodes[idx]
            line.append(word)
            # Pseudo-deterministic skip based on last character
            skip = ord(word[-1]) % 10 + 1
            idx = (idx + skip) % len(self.nodes)
        return line
