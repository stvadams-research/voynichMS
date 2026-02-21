"""
Dependency Scope Simulators.
"""

import logging
import random
from pathlib import Path

from phase1_foundation.config import require_seed_if_strict
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator
from phase5_mechanism.dependency_scope.features import TokenFeatureExtractor

logger = logging.getLogger(__name__)

class DependencySimulator:
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, seed: int | None = None):
        require_seed_if_strict(seed, "DependencySimulator")
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.nodes = [self.generator.generate_word() for _ in range(vocab_size)]
        self.extractor = TokenFeatureExtractor()

    def generate_corpus(self, num_lines: int, line_len: int) -> list[list[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class LocalTransitionSimulator(DependencySimulator):
    """
    H1: Purely local transition (explicit DAG).
    Successor depends only on the current node.
    """
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, seed: int | None = None):
        super().__init__(grammar_path, vocab_size, seed=seed)
        self.transitions = {}
        # Pre-assign deterministic transitions
        for i in range(vocab_size):
            # One deterministic successor for each node
            self.transitions[i] = (i + 1) % vocab_size

    def generate_line(self, length: int) -> list[str]:
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            line.append(self.nodes[idx])
            idx = self.transitions[idx]
        return line

class FeatureConditionedSimulator(DependencySimulator):
    """
    H2: Feature-conditioned transition (Implicit Lattice).
    Successor depends on features of the current word.
    """
    def __init__(self, grammar_path: Path, vocab_size: int = 1000, seed: int | None = None):
        super().__init__(grammar_path, vocab_size, seed=seed)
        # No pre-assigned transitions.
        # Rule: Next word must have same first char as current word's last char.
        # This is an implicit rule.
        self.node_by_first_char = {}
        for i, word in enumerate(self.nodes):
            c = word[0] if word else ""
            if c not in self.node_by_first_char:
                self.node_by_first_char[c] = []
            self.node_by_first_char[c].append(i)

    def generate_line(self, length: int) -> list[str]:
        idx = self.rng.randint(0, len(self.nodes) - 1)
        line = []
        for _ in range(length):
            word = self.nodes[idx]
            line.append(word)
            last_char = word[-1] if word else ""

            # Follow the rule: find nodes starting with last_char
            candidates = self.node_by_first_char.get(last_char, [])
            if not candidates:
                # Fallback to random if no match
                idx = self.rng.randint(0, len(self.nodes) - 1)
            else:
                # Deterministic pick from candidates (e.g. first one)
                idx = candidates[0]
        return line
