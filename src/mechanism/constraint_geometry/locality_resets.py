"""
Constraint Locality and Reset Analyzer

Evaluates if transition rules persist globally or reset at boundaries.
"""

from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple
import math

class LocalityResetAnalyzer:
    """
    Analyzes constraint persistence across boundaries.
    """
    def __init__(self, min_freq: int = 5):
        self.min_freq = min_freq

    def analyze_resets(self, tokens: List[str], boundaries: List[int]) -> Dict[str, Any]:
        """
        Compare transitions across boundaries vs within boundaries.
        """
        if not tokens:
            return {}

        intra_transitions = defaultdict(Counter)
        inter_transitions = defaultdict(Counter)
        
        boundary_set = set(boundaries)
        
        for i in range(len(tokens) - 1):
            u, v = tokens[i], tokens[i+1]
            if i in boundary_set:
                inter_transitions[u][v] += 1
            else:
                intra_transitions[u][v] += 1
                
        # Calculate Jaccard similarity of successor sets for top tokens
        all_tokens = set(intra_transitions.keys()) | set(inter_transitions.keys())
        similarities = []
        
        for token in all_tokens:
            intra_succ = set(intra_transitions[token].keys())
            inter_succ = set(inter_transitions[token].keys())
            
            if len(intra_succ) > self.min_freq and len(inter_succ) > self.min_freq:
                intersection = len(intra_succ & inter_succ)
                union = len(intra_succ | inter_succ)
                similarities.append(intersection / union)
                
        avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
        
        # Reset score: 1 - similarity (high = strong reset)
        reset_score = 1.0 - avg_similarity
        
        return {
            "avg_successor_overlap": avg_similarity,
            "reset_score": float(reset_score),
            "num_compared_tokens": len(similarities)
        }
