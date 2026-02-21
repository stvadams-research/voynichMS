"""
Efficiency-Aware Simulators for Phase 6B
"""

import logging

from phase6_functional.formal_system.simulators import LatticeTraversalSimulator

logger = logging.getLogger(__name__)

class OptimizedLatticeSimulator(LatticeTraversalSimulator):
    """
    H6B.1: Efficiency-Optimized Formal Tool.
    Optimizes for reuse of tokens and paths to minimize 'cost'.
    """
    def __init__(self, vocab_size: int = 500, seed: int = 42):
        # Smaller vocab to force reuse
        super().__init__(vocab_size=vocab_size, seed=seed)
        self.preferred_tokens = self.vocab[:50] # 10% of vocab are 'cheap' to use

    def _get_nexts(self, prev: str, curr: str, pos: int) -> list[str]:
        state = (prev, curr, pos)
        if state not in self.rules:
            # Prefer using 'cheap' tokens as successors
            num_choices = self.random.choices([1, 2], weights=[0.9, 0.1])[0]
            # Mix some preferred tokens with random ones
            candidates = self.random.sample(self.preferred_tokens, min(len(self.preferred_tokens), 5))
            candidates += self.random.sample(self.vocab, 5)
            self.rules[state] = self.random.sample(candidates, num_choices)
        return self.rules[state]

    def generate_line(self, line_len: int = 8) -> list[str]:
        line = []
        prev = "<START>"
        # Prefer starting with cheap tokens
        curr = self.random.choice(self.preferred_tokens)
        line.append(curr)

        for pos in range(1, line_len):
            possible_nexts = self._get_nexts(prev, curr, pos-1)
            nxt = self.random.choice(possible_nexts)
            prev = curr
            curr = nxt
            line.append(curr)
        return line
