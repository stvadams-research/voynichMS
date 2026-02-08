"""
Geometric Table Generator

Produces text using tables of varying dimensions to test dimensionality signatures.
"""

import random
from typing import List, Dict, Any, Tuple
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class GeometricTableGenerator:
    def __init__(self, grammar_path: Path, rows: int = 10, cols: int = 10):
        self.generator = GrammarBasedGenerator(grammar_path)
        self.rows = rows
        self.cols = cols
        self.table = self._build_table()

    def _build_table(self) -> List[List[str]]:
        table = []
        for _ in range(self.rows):
            row = [self.generator.generate_word() for _ in range(self.cols)]
            table.append(row)
        return table

    def generate(self, target_tokens: int, walk_type: str = "snake") -> List[str]:
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
                r = (r + random.randint(-1, 1)) % self.rows
                c = (c + random.randint(-1, 1)) % self.cols
                
        return tokens
