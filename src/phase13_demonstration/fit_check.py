import math
from collections import Counter


class StructuralFitAnalyzer:
    """Analyzes structural fit between real and simulated corpora using entropy."""

    @staticmethod
    def calculate_entropy(tokens):
        """Calculates Shannon entropy of a token sequence."""
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        total = len(tokens)
        return -sum((c/total) * math.log2(c/total) for c in counts.values())

    def compare_corpora(self, real_tokens, syn_tokens):
        """
        Compares entropy of real and synthetic corpora.
        
        Returns:
            dict: Entropy values and fit score.
        """
        real_entropy = self.calculate_entropy(real_tokens)
        syn_entropy = self.calculate_entropy(syn_tokens)
        
        if real_entropy > 0:
            fit = 1.0 - abs(real_entropy - syn_entropy) / real_entropy
        else:
            fit = 0.0

        return {
            "real_entropy": real_entropy,
            "syn_entropy": syn_entropy,
            "fit_score": fit,
            "is_sufficient": fit > 0.9
        }
