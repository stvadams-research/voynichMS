"""
Geometry Inference (Hardware Deduction)

Analyzes the pattern of mechanical slips to deduce if the tool was 
a Sliding Grille (linear shift) or a Volvelle (angular shift).
"""

from collections import Counter
from typing import Any

import numpy as np


class GeometryInferrer:
    """
    Deduces tool geometry from slip distributions.
    """
    def analyze_slip_geometry(self, slips: list[dict[str, Any]]) -> dict[str, Any]:
        if not slips:
            return {}

        # 1. Vertical Delta Distribution
        # In this first pass, we only looked at line i vs i-1. 
        # A more advanced check would look at i-2, i+1, etc.
        
        # 2. Position Correlation
        # Do slips happen more at the start of a line or end?
        positions = [s['token_index'] for s in slips]
        pos_counts = Counter(positions)
        
        # 3. Word-Length Correlation
        # Are shorter words more likely to slip?
        lengths = [len(s['word']) for s in slips]
        len_counts = Counter(lengths)
        
        return {
            "positional_distribution": dict(pos_counts),
            "length_distribution": dict(len_counts),
            "mean_slip_position": float(np.mean(positions)),
            "std_slip_position": float(np.std(positions)),
            "mean_word_length": float(np.mean(lengths))
        }
