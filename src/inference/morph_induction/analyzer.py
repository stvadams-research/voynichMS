"""
Method E: Unsupervised Morphology Induction

Identifies stable prefixes and suffixes and measures their consistency.
"""

from collections import Counter
from typing import List, Dict, Any, Tuple

class MorphologyAnalyzer:
    """
    Analyzes morphological structure via prefix/suffix induction.
    """
    def __init__(self, min_affix_len: int = 1, max_affix_len: int = 3):
        self.min_affix_len = min_affix_len
        self.max_affix_len = max_affix_len

    def analyze(self, tokens: List[str]) -> Dict[str, Any]:
        """
        Induce affixes and measure consistency.
        """
        if not tokens:
            return {}

        counts = Counter(tokens)
        unique_words = list(counts.keys())
        
        # 1. Induce Suffixes
        suffixes = Counter()
        for word in unique_words:
            if len(word) > self.max_affix_len:
                for l in range(self.min_affix_len, self.max_affix_len + 1):
                    suffixes[word[-l:]] += 1
                    
        # Filter for top suffixes (top 5% or threshold)
        top_suffixes = [s for s, count in suffixes.most_common(20)]
        
        # 2. Measure Stem Stability
        # If we remove a common suffix, does the remaining stem appear elsewhere?
        stems = Counter()
        stem_with_affix_count = 0
        for word in unique_words:
            for s in top_suffixes:
                if word.endswith(s):
                    stem = word[:-len(s)]
                    if stem:
                        stems[stem] += 1
                        stem_with_affix_count += 1
                        break
                        
        # Morphological Consistency Score: 
        # (Stem reuse count / Total words with affixes)
        reused_stems = sum(1 for s, count in stems.items() if count > 1)
        consistency = reused_stems / len(unique_words) if unique_words else 0.0
        
        return {
            "num_unique_words": len(unique_words),
            "top_suffixes": suffixes.most_common(10),
            "morph_consistency": float(consistency),
            "reused_stems_count": reused_stems
        }
