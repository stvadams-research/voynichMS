"""
Phase 5K Simulators: Parsimony Collapse.

Models:
1. M1: Position-Indexed Explicit Graph (Augmented DAG).
   Nodes = (Word, Position). Edges = Fixed table.
2. M2: Implicit Constraint Lattice.
   Nodes = Word. Edges = Evaluated rule f(word, position).
"""

import random
from typing import List, Dict, Any, Tuple, Optional
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path
from phase5_mechanism.dependency_scope.features import TokenFeatureExtractor
import logging
logger = logging.getLogger(__name__)

class ParsimonySimulator:
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, seed: Optional[int] = None):
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.nodes = [self.generator.generate_word() for _ in range(vocab_size)]
        self.extractor = TokenFeatureExtractor()

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class PositionIndexedDAGSimulator(ParsimonySimulator):
    """
    M1: Explodes state space to (Word, Position).
    """
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, max_len: int = 10, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size, seed=seed)
        self.max_len = max_len
        self.transitions = {} # Key: (node_idx, pos), Value: next_node_idx
        
        # Pre-assign deterministic transitions for every (node, pos)
        for i in range(vocab_size):
            for p in range(max_len):
                # Arbitrary deterministic rule simulating a lookup table
                # We use a hash to make it look like a random table
                trans_seed = i * 1000 + p
                if seed is not None:
                    trans_seed += seed
                rng = random.Random(trans_seed)
                self.transitions[(i, p)] = rng.randint(0, vocab_size - 1)

    def generate_line(self, length: int) -> List[str]:
        # Start node depends on nothing (or random)
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for p in range(length):
            line.append(self.nodes[idx])
            # Transition depends on (node, p)
            if p < length - 1:
                idx = self.transitions.get((idx, p), 0)
        return line
        
    def get_state_count(self) -> int:
        return len(self.transitions)

class ImplicitLatticeSimulator(ParsimonySimulator):
    """
    M2: Implicit constraints based on features and position.
    """
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, seed: Optional[int] = None):
        super().__init__(grammar_path, vocab_size, seed=seed)
        # Rule: Next word matches a feature condition derived from current word + position
        self.node_features = [self.extractor.extract_features(w) for w in self.nodes]
        
        # Optimization: Map features to nodes for quick lookup
        self.feature_map = {} # Key: (length, suffix), Value: List[idx]
        for i, feat in enumerate(self.node_features):
            key = (feat['length'], feat['suffix_1'])
            if key not in self.feature_map:
                self.feature_map[key] = []
            self.feature_map[key].append(i)

    def generate_line(self, length: int) -> List[str]:
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for p in range(length):
            line.append(self.nodes[idx])
            
            if p < length - 1:
                # Implicit Rule:
                # Target length = (current_length + p) % 5 + 2
                # Target suffix = same as current
                feat = self.node_features[idx]
                target_len = (feat['length'] + p) % 5 + 3
                target_suffix = feat['suffix_1']
                
                candidates = self.feature_map.get((target_len, target_suffix), [])
                if candidates:
                    # Deterministic pick (e.g. smallest index > current index)
                    # to simulate a lattice walk
                    best = None
                    for c in candidates:
                        if c > idx:
                            best = c
                            break
                    idx = best if best is not None else candidates[0]
                else:
                    # Fallback
                    idx = (idx + 1) % len(self.nodes)
        return line

    def get_state_count(self) -> int:
        # State space is just the vocab, rules are global
        return len(self.nodes)
