"""
Pilot Generator for Bounded Pool Reuse

Matches Voynich structural summaries while enforcing pool constraints.
"""

import random
from typing import List, Dict, Any
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path

class PoolGenerator:
    def __init__(self, grammar_path: Path, pool_size: int = 20):
        self.generator = GrammarBasedGenerator(grammar_path)
        self.pool_size = pool_size
        self.pool = []

    def generate(self, target_tokens: int) -> List[str]:
        tokens = []
        # Initial pool
        self.pool = [self.generator.generate_word() for _ in range(self.pool_size)]
        
        while len(tokens) < target_tokens:
            # Randomly reuse from pool
            tokens.append(random.choice(self.pool))
            
            # 5% chance to replenish one pool slot
            if random.random() < 0.05:
                self.pool[random.randint(0, self.pool_size - 1)] = self.generator.generate_word()
                
        return tokens
