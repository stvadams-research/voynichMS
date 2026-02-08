"""
Feature Extraction for Dependency Scope Analysis.
"""

from typing import List, Dict, Any, Tuple
import numpy as np

class TokenFeatureExtractor:
    """
    Extracts formal features from tokens without semantic interpretation.
    """
    def __init__(self):
        pass

    def extract_features(self, token: str) -> Dict[str, Any]:
        """
        Extracts a feature vector for a single token.
        """
        if not token:
            return {}
            
        features = {
            "length": len(token),
            "prefix_1": token[0] if len(token) > 0 else "",
            "prefix_2": token[:2] if len(token) > 1 else "",
            "suffix_1": token[-1] if len(token) > 0 else "",
            "suffix_2": token[-2:] if len(token) > 1 else "",
            "has_repeated": 1.0 if len(set(token)) < len(token) else 0.0,
            "vowel_like_count": sum(1 for c in token if c in 'aeo'), # EVA vowel-like
            "char_entropy": self._char_entropy(token)
        }
        return features

    def _char_entropy(self, token: str) -> float:
        from collections import Counter
        import math
        counts = Counter(token)
        probs = [c / len(token) for c in counts.values()]
        return -sum(p * math.log2(p) for p in probs)

    def extract_positional_features(self, line: List[str], index: int) -> Dict[str, Any]:
        """
        Features dependent on position in line.
        """
        return {
            "pos_index": index,
            "pos_ratio": index / len(line) if len(line) > 0 else 0,
            "is_start": 1.0 if index == 0 else 0.0,
            "is_end": 1.0 if index == len(line) - 1 else 0.0
        }
