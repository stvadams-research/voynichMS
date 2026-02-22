from collections import Counter, defaultdict
import numpy as np
from scipy.stats import spearmanr

class EffortCorrelationAnalyzer:
    """Analyzes the correlation between physical effort (strokes) and selection bias."""

    def __init__(self, choices, costs):
        """
        Args:
            choices (list): List of choice dictionaries.
            costs (dict): Mapping from word to its physical effort score.
        """
        self.choices = choices
        self.costs = costs

    def analyze_selection_correlation(self, min_window_samples=20):
        """
        Tests if lower-effort words are chosen more frequently within windows.
        
        Returns:
            dict: Correlation statistics.
        """
        # 1. Compute per-window selection frequency
        win_word_counts = defaultdict(Counter)
        win_totals = defaultdict(int)
        for c in self.choices:
            wid = c.get('window_id')
            word = c.get('chosen_word')
            if wid is None or word is None:
                continue
            win_word_counts[wid][word] += 1
            win_totals[wid] += 1

        # 2. Build pairs for correlation
        efforts = []
        frequencies = []
        for wid, word_counts in win_word_counts.items():
            total = win_totals[wid]
            if total < min_window_samples:
                continue
            for word, count in word_counts.items():
                if word in self.costs:
                    efforts.append(self.costs[word])
                    frequencies.append(count / total)

        if len(efforts) < 10:
            return {
                "correlation_rho": 0.0,
                "p_value": 1.0,
                "num_pairs": len(efforts),
                "is_significant": False
            }

        rho, p_value = spearmanr(efforts, frequencies)
        return {
            "correlation_rho": float(rho),
            "p_value": float(p_value),
            "num_pairs": len(efforts),
            "is_significant": bool(p_value < 0.01 and abs(rho) > 0.1)
        }

    def analyze_effort_gradient(self, limit=10000):
        """
        Analyzes the physical effort stability between consecutive selections.
        """
        effort_seq = []
        for c in self.choices[:limit]:
            word = c.get('chosen_word')
            if word and word in self.costs:
                effort_seq.append(self.costs[word])
        
        if not effort_seq:
            return 0.0
            
        gradients = [abs(effort_seq[i] - effort_seq[i-1]) for i in range(1, len(effort_seq))]
        return float(np.mean(gradients)) if gradients else 0.0
