"""
Pilot Generator for Bounded Pool Reuse

Matches Voynich structural summaries while enforcing pool constraints.
"""

import random
from typing import List, Dict, Any, Optional
from phase3_synthesis.generators.grammar_based import GrammarBasedGenerator
from phase1_foundation.config import require_seed_if_strict
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class PoolGenerator:
    def __init__(self, grammar_path: Path, pool_size: int = 20, seed: Optional[int] = None):
        require_seed_if_strict(seed, "PoolGenerator")
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.pool_size = pool_size
        self.pool = []

    def generate(self, target_tokens: int) -> List[str]:
        tokens = []
        # Initial pool
        self.pool = [self.generator.generate_word() for _ in range(self.pool_size)]
        
        while len(tokens) < target_tokens:
            # Randomly reuse from pool
            tokens.append(self.rng.choice(self.pool))
            
            # 5% chance to replenish one pool slot
            if self.rng.random() < 0.05:
                self.pool[self.rng.randint(0, self.pool_size - 1)] = self.generator.generate_word()
                
        return tokens
