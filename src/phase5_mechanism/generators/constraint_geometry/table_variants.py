"""
Geometric Table Generator

Produces text using tables of varying dimensions to test dimensionality signatures.
"""

import logging
import random
from pathlib import Path

from phase1_foundation.config import require_seed_if_strict
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator

logger = logging.getLogger(__name__)

class GeometricTableGenerator:
    def __init__(self, grammar_path: Path, rows: int = 10, cols: int = 10, seed: int | None = None):
        require_seed_if_strict(seed, "GeometricTableGenerator")
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.rng = random.Random(seed)
        self.rows = rows
        self.cols = cols
        self.table = self._build_table()

    def _build_table(self) -> list[list[str]]:
        table = []
        for _ in range(self.rows):
            row = [self.generator.generate_word() for _ in range(self.cols)]
            table.append(row)
        return table

    def generate(self, target_tokens: int, walk_type: str = "snake") -> list[str]:
        tokens = []
        r, c = 0, 0

        while len(tokens) < target_tokens:
            tokens.append(self.table[r][c])

            if walk_type == "snake":
                # Snake walk
                c += 1
                if c >= self.cols:
                    c = 0
                    r = (r + 1) % self.rows
            elif walk_type == "knight":
                # Knight's move
                r = (r + 2) % self.rows
                c = (c + 1) % self.cols
            else:
                # Random walk on table
                r = (r + self.rng.randint(-1, 1)) % self.rows
                c = (c + self.rng.randint(-1, 1)) % self.cols

        return tokens
