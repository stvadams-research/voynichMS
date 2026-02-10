"""
Slot Boundary Detection

Detects implicit slot boundaries by analyzing positional constraints 
and transition sharpness.
"""

from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np
import math
import logging
logger = logging.getLogger(__name__)

class SlotBoundaryDetector:
    """
    Analyzes token-position alignment to detect structural slots.
    """
    def __init__(self, max_pos: int = 10):
        self.max_pos = max_pos

    def calculate_positional_entropy(self, all_lines: List[List[str]]) -> Dict[int, float]:
        """
        Calculates entropy of token distributions at each position in the line.
        """
        pos_counts = defaultdict(Counter)
        
        for line in all_lines:
            for i, token in enumerate(line):
                if i < self.max_pos:
                    pos_counts[i][token] += 1
                    
        entropies = {}
        for pos, counts in pos_counts.items():
            total = sum(counts.values())
            entropy = 0.0
            for count in counts.values():
                p = count / total
                entropy -= p * math.log2(p)
            # Normalize by log2(total) to see how 'saturated' the slot is
            entropies[pos] = entropy
            
        return entropies

    def calculate_successor_sharpness(self, all_lines: List[List[str]]) -> List[float]:
        """
        Calculates successor entropy as a function of word position.
        """
        pos_successors = defaultdict(Counter)
        
        for line in all_lines:
            for i in range(len(line) - 1):
                if i < self.max_pos:
                    u, v = line[i], line[i+1]
                    pos_successors[i][v] += 1 # Distribution of what follows word at pos i
                    
        entropies = []
        for i in range(self.max_pos):
            counts = pos_successors[i]
            if not counts:
                break
            total = sum(counts.values())
            entropy = 0.0
            for count in counts.values():
                p = count / total
                entropy -= p * math.log2(p)
            entropies.append(entropy)
            
        return entropies
