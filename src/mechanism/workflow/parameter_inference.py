"""
Line-Level Parameter Inference

Infers distributions of parameters governing line generators from real data.
"""

from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import numpy as np
import math
import logging
logger = logging.getLogger(__name__)

class WorkflowParameterInferrer:
    """
    Analyzes line-level statistics to infer latent workflow parameters.
    """
    def __init__(self):
        pass

    def infer_line_parameters(self, line_tokens: List[str]) -> Dict[str, Any]:
        """
        Calculate metrics for a single line of text.
        """
        if not line_tokens:
            return {}

        counts = Counter(line_tokens)
        num_tokens = len(line_tokens)
        num_unique = len(counts)
        
        # 1. Local TTR
        ttr = num_unique / num_tokens if num_tokens > 0 else 0.0
        
        # 2. Local Entropy (Successor)
        successor_entropy = 0.0
        if num_tokens > 1:
            transitions = Counter()
            for i in range(num_tokens - 1):
                transitions[(line_tokens[i], line_tokens[i+1])] += 1
            
            total_trans = sum(transitions.values())
            for count in transitions.values():
                p = count / total_trans
                successor_entropy -= p * math.log2(p)
                
        # 3. Novelty Position
        # (Where in the line do 'new' tokens appear relative to the whole corpus?)
        # For simplicity in this module, we just look at first occurrence in THIS line.
        
        return {
            "num_tokens": num_tokens,
            "num_unique": num_unique,
            "ttr": ttr,
            "successor_entropy": successor_entropy
        }

    def aggregate_distributions(self, all_lines: List[List[str]]) -> Dict[str, Any]:
        """
        Infers distributions across all lines.
        """
        results = [self.infer_line_parameters(line) for line in all_lines if line]
        
        if not results:
            return {}
            
        ttrs = [r['ttr'] for r in results]
        entropies = [r['successor_entropy'] for r in results]
        
        return {
            "mean_ttr": float(np.mean(ttrs)),
            "std_ttr": float(np.std(ttrs)),
            "mean_entropy": float(np.mean(entropies)),
            "std_entropy": float(np.std(entropies)),
            "num_lines": len(results)
        }
