"""
Deterministic Grammar Simulators

Implements minimal non-stochastic generators for slot-based models.
"""

import logging
import random
from pathlib import Path

from phase1_foundation.config import require_seed_if_strict
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator

logger = logging.getLogger(__name__)

class DeterministicSlotSimulator:
    """
    Family 1: Each line is a sequence of N slots from disjoint pools.
    """
    def __init__(self, grammar_path: Path, num_slots: int = 8, seed: int | None = None):
        require_seed_if_strict(seed, "DeterministicSlotSimulator")
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.num_slots = num_slots
        # Pre-generate a fixed 'table' of possible tokens per slot
        self.slot_pools = []
        for _ in range(num_slots):
            # Each slot has a unique pool of 100 possible words
            self.slot_pools.append([self.generator.generate_word() for _ in range(100)])

    def generate_line(self) -> list[str]:
        # Selection is 'deterministic' in structure: exactly one from each pool
        # For simulation variability, we pick a random one, but the order is fixed.
        line = []
        for i in range(self.num_slots):
            line.append(self.rng.choice(self.slot_pools[i]))
        return line

    def generate_corpus(self, num_lines: int) -> list[list[str]]:
        return [self.generate_line() for _ in range(num_lines)]
