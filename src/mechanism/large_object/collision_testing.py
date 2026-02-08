"""
Path Collision and Successor Consistency Testing

Detects if identical local contexts force identical successors across different lines.
"""

from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

class PathCollisionTester:
    """
    Measures the 'stiffness' of the large-object topology.
    """
    def __init__(self, context_len: int = 2):
        self.context_len = context_len

    def calculate_successor_consistency(self, all_lines: List[List[str]]) -> Dict[str, Any]:
        """
        How often does context X lead to the same successor Y?
        """
        context_successors = defaultdict(Counter)
        
        for line in all_lines:
            for i in range(len(line) - self.context_len):
                context = tuple(line[i : i + self.context_len])
                successor = line[i + self.context_len]
                context_successors[context][successor] += 1
                
        # Calculate consistency for contexts that appear multiple times
        consistencies = []
        for context, successors in context_successors.items():
            total = sum(successors.values())
            if total > 1:
                # Probability of the most common successor
                max_freq = successors.most_common(1)[0][1]
                consistencies.append(max_freq / total)
                
        if not consistencies:
            return {"mean_consistency": 0.0, "sample_size": 0}
            
        mean_cons = sum(consistencies) / len(consistencies)
        
        return {
            "mean_consistency": float(mean_cons),
            "num_recurring_contexts": len(consistencies),
            "max_consistency": float(max(consistencies))
        }
