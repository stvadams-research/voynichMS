"""
Method D: Language ID under Flexible Transforms

Quantifies the risk of false positives when searching for language matches 
under multiple transformations.
"""

from collections import Counter
import numpy as np
from typing import List, Dict, Any, Tuple
import re
import logging
logger = logging.getLogger(__name__)

class LanguageIDAnalyzer:
    """
    Analyzes language matching confidence under transformations.
    """
    def __init__(self):
        self.language_profiles = {}

    def build_profile(self, name: str, text: str):
        """Build character 3-gram profile for a language."""
        text = text.lower()
        chars = re.findall(r'[a-z]', text)
        ngrams = ["".join(chars[i:i+3]) for i in range(len(chars)-2)]
        counts = Counter(ngrams)
        total = sum(counts.values())
        self.language_profiles[name] = {k: v/total for k, v in counts.items()}

    def score_match(self, text: str, target_lang: str) -> float:
        """Calculate similarity between text and target language profile."""
        text = text.lower()
        chars = re.findall(r'[a-z]', text)
        if not chars: return 0.0
        
        ngrams = ["".join(chars[i:i+3]) for i in range(len(chars)-2)]
        counts = Counter(ngrams)
        total = sum(counts.values())
        profile = {k: v/total for k, v in counts.items()}
        
        target_profile = self.language_profiles[target_lang]
        
        # Cosine similarity on n-gram vectors
        all_keys = set(profile.keys()) | set(target_profile.keys())
        v1 = np.array([profile.get(k, 0) for k in all_keys])
        v2 = np.array([target_profile.get(k, 0) for k in all_keys])
        
        dot = np.dot(v1, v2)
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        
        return float(dot / (norm1 * norm2)) if norm1 > 0 and norm2 > 0 else 0.0

    def find_best_transform(self, text: str, target_lang: str, transforms: List[Dict[str, str]]) -> Tuple[float, Dict[str, str]]:
        """
        Search for the best character mapping to match a target language.
        Simulates the multiple comparisons risk in decipherment claims.
        """
        best_score = 0.0
        best_mapping = {}
        
        for mapping in transforms:
            # Apply mapping
            transformed = "".join([mapping.get(c, c) for c in text.lower()])
            score = self.score_match(transformed, target_lang)
            if score > best_score:
                best_score = score
                best_mapping = mapping
                
        return best_score, best_mapping
