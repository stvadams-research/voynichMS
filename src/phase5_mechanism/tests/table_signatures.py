"""
C5.TABLE.1: Successor Set Sharpness Test

Detects signatures of table-based production by measuring the 
abruptness of constraints on token successors.
"""

import logging
import math
from collections import Counter, defaultdict
from typing import Any

logger = logging.getLogger(__name__)

class TableSignatureTest:
    """
    Analyzes successor distributions for hidden-state signatures.
    """
    def __init__(self, min_freq: int = 10):
        self.min_freq = min_freq

    def calculate_successor_sharpness(self, tokens: list[str]) -> dict[str, Any]:
        """
        Measure entropy of successor distributions compared to global frequency.
        """
        if not tokens:
            return {}

        successors = defaultdict(Counter)
        for i in range(len(tokens) - 1):
            successors[tokens[i]][tokens[i+1]] += 1
            
        entropies = []
        for token, counts in successors.items():
            total = sum(counts.values())
            if total >= self.min_freq:
                # Calculate Shannon entropy of successors
                entropy = 0.0
                for count in counts.values():
                    p = count / total
                    entropy -= p * math.log2(p)
                entropies.append(entropy)
                
        if not entropies:
            return {"mean_successor_entropy": 0.0, "status": "insufficient_data"}
            
        mean_entropy = sum(entropies) / len(entropies)
        
        return {
            "num_qualified_tokens": len(entropies),
            "mean_successor_entropy": float(mean_entropy),
            "min_successor_entropy": float(min(entropies))
        }
