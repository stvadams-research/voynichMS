"""
Formal System Simulators

Implements simulators for Phase 6A evaluation.
"""

import logging
import random

logger = logging.getLogger(__name__)

class LatticeTraversalSimulator:
    """
    Simulates traversal through an implicit constraint lattice.
    Consistent with Phase 5 findings:
    - State: (Prev, Curr, Position)
    - Line resets
    - Independent entry
    """
    def __init__(self, vocab_size: int = 1000, max_pos: int = 15, seed: int = 42):
        self.vocab = [f"w{i}" for i in range(vocab_size)]
        self.max_pos = max_pos
        self.rules = {}
        self.random = random.Random(seed)

    def _get_nexts(self, prev: str, curr: str, pos: int) -> list[str]:
        state = (prev, curr, pos)
        if state not in self.rules:
            # Generate a mostly deterministic rule (1-2 choices)
            num_choices = self.random.choices([1, 2, 3], weights=[0.8, 0.15, 0.05])[0]
            self.rules[state] = self.random.sample(self.vocab, num_choices)
        return self.rules[state]

    def generate_line(self, line_len: int = 8) -> list[str]:
        line = []
        prev = "<START>"
        # Start word chosen from a large pool
        curr = self.random.choice(self.vocab)
        line.append(curr)
        
        for pos in range(1, line_len):
            possible_nexts = self._get_nexts(prev, curr, pos-1)
            nxt = self.random.choice(possible_nexts)
            prev = curr
            curr = nxt
            line.append(curr)
        return line

    def generate_corpus(self, num_lines: int, line_len: int = 8) -> list[list[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class ExhaustiveFormalSimulator(LatticeTraversalSimulator):
    """
    A simulator that specifically attempts to 'exhaust' its state space
    by preferring unvisited or low-visit states (if it were adaptive),
    or just by being run for a long time.
    For Phase 6A, we'll use a version that has a smaller total state space
    to demonstrate 'exhaustion' signatures.
    """
    def __init__(self, vocab_size: int = 100, max_pos: int = 5, seed: int = 42):
        super().__init__(vocab_size=vocab_size, max_pos=max_pos, seed=seed)
