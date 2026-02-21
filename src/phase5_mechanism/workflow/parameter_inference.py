"""
Line-Level Parameter Inference

Infers distributions of parameters governing line generators from real data.
"""

import logging
import math
from collections import Counter
from typing import Any

import numpy as np

from phase5_mechanism.dependency_scope.features import TokenFeatureExtractor

logger = logging.getLogger(__name__)

class WorkflowParameterInferrer:
    """
    Analyzes line-level statistics to infer latent workflow parameters.
    """
    def __init__(self):
        self.extractor = TokenFeatureExtractor()

    def infer_line_parameters(self, line_tokens: list[str]) -> dict[str, Any]:
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
        
        # 3. Feature Consistency (Task 2.2): Target Method K residuals
        # Measures how much token length and suffix are conserved or predictable across transitions
        len_consistency = 0.0
        suffix_consistency = 0.0
        
        if num_tokens > 1:
            transitions = Counter()
            feats = [self.extractor.extract_features(t) for t in line_tokens]
            
            l_matches = 0
            s_matches = 0
            
            for i in range(num_tokens - 1):
                transitions[(line_tokens[i], line_tokens[i+1])] += 1
                
                # Check for feature conservation (stochastic baseline)
                if feats[i]['length'] == feats[i+1]['length']:
                    l_matches += 1
                if feats[i]['suffix_1'] == feats[i+1]['suffix_1']:
                    s_matches += 1
            
            total_trans = sum(transitions.values())
            for count in transitions.values():
                p = count / total_trans
                successor_entropy -= p * math.log2(p)
                
            len_consistency = l_matches / total_trans
            suffix_consistency = s_matches / total_trans
                
        return {
            "num_tokens": num_tokens,
            "num_unique": num_unique,
            "ttr": ttr,
            "successor_entropy": successor_entropy,
            "len_consistency": len_consistency,
            "suffix_consistency": suffix_consistency
        }

    def aggregate_distributions(self, all_lines: list[list[str]]) -> dict[str, Any]:
        """
        Infers distributions across all lines.
        """
        results = [self.infer_line_parameters(line) for line in all_lines if line]
        
        if not results:
            return {}
            
        ttrs = [r['ttr'] for r in results]
        entropies = [r['successor_entropy'] for r in results]
        len_cons = [r['len_consistency'] for r in results]
        suf_cons = [r['suffix_consistency'] for r in results]
        
        return {
            "mean_ttr": float(np.mean(ttrs)),
            "std_ttr": float(np.std(ttrs)),
            "mean_entropy": float(np.mean(entropies)),
            "std_entropy": float(np.std(entropies)),
            "mean_len_consistency": float(np.mean(len_cons)),
            "mean_suffix_consistency": float(np.mean(suf_cons)),
            "num_lines": len(results)
        }
