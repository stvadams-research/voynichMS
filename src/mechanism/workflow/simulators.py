"""
Phase 5C Workflow Simulators

Implements minimal simulators for line-conditioned workflows.
"""

import random
from typing import List, Dict, Any, Tuple, Optional
from synthesis.generators.grammar_based import GrammarBasedGenerator
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

class LineScopedPoolSimulator:
    """
    Family 1: Each line has its own independent, bounded pool.
    """
    def __init__(self, grammar_path: Path, mean_pool_size: float = 10.0, seed: Optional[int] = None):
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.mean_pool_size = mean_pool_size

    def generate_line(self, target_len: int) -> List[str]:
        # 1. Sample pool size for this line
        pool_size = max(1, int(self.rng.gauss(self.mean_pool_size, 2.0)))
        
        # 2. Populate pool
        pool = [self.generator.generate_word() for _ in range(pool_size)]
        
        # 3. Fill line
        return [self.rng.choice(pool) for _ in range(target_len)]

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]

class WeaklyCoupledPoolSimulator:
    """
    Family 2: Line pools are sampled from a drifting reservoir.
    """
    def __init__(self, grammar_path: Path, reservoir_size: int = 50, drift_rate: float = 0.1, seed: Optional[int] = None):
        # Intentional controller bypass: simulators keep local RNG state per run.
        self.rng = random.Random(seed)
        self.generator = GrammarBasedGenerator(grammar_path, seed=seed)
        self.reservoir_size = reservoir_size
        self.drift_rate = drift_rate
        self.reservoir = [self.generator.generate_word() for _ in range(reservoir_size)]

    def generate_line(self, target_len: int) -> List[str]:
        # 1. Select pool from reservoir
        pool_size = 15 # Fixed for this simulator variant
        pool = self.rng.sample(self.reservoir, min(pool_size, len(self.reservoir)))
        
        line = [self.rng.choice(pool) for _ in range(target_len)]
        
        # 2. Drift the reservoir
        for i in range(len(self.reservoir)):
            if self.rng.random() < self.drift_rate:
                self.reservoir[i] = self.generator.generate_word()
                
        return line

    def generate_corpus(self, num_lines: int, line_len: int) -> List[List[str]]:
        return [self.generate_line(line_len) for _ in range(num_lines)]
