"""
Line Prefix and Entry Point Analysis

Analyzes the statistical properties of the first word(s) of each line 
to infer entry-point selection rules.
"""

import logging
import math
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

class EntryPointAnalyzer:
    """
    Analyzes the distribution and coupling of line-start tokens.
    """
    def __init__(self):
        pass

    def calculate_start_distribution(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        How uniform is the starting word selection?
        """
        starts = [l[0] for l in lines if l]
        if not starts:
            return {}

        counts = Counter(starts)
        total = len(starts)

        # Entropy of start words
        entropy = -sum((c/total) * math.log2(c/total) for c in counts.values())

        return {
            "num_lines": total,
            "unique_starts": len(counts),
            "start_entropy": float(entropy),
            "max_freq_start": counts.most_common(1)[0][1] / total if counts else 0.0,
            "top_starts": dict(counts.most_common(10))
        }

    def calculate_adjacency_coupling(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        Do adjacent lines share similar starting points?
        """
        if len(lines) < 2:
            return {"coupling_score": 0.0}

        matches = 0
        total_pairs = 0

        for i in range(len(lines) - 1):
            if lines[i] and lines[i+1]:
                # Simple coupling: do they start with the same word?
                if lines[i][0] == lines[i+1][0]:
                    matches += 1
                total_pairs += 1

        coupling_score = matches / total_pairs if total_pairs > 0 else 0.0

        return {
            "num_pairs": total_pairs,
            "start_word_matches": matches,
            "coupling_score": float(coupling_score)
        }
