"""
Quire Boundary and Continuity Analysis

Tests whether text properties shift across quire boundaries.
Phase 7B implementation.
"""

import numpy as np
from collections import defaultdict
from typing import List, Dict, Any, Tuple

class QuireAnalyzer:
    """
    Analyzes discontinuities across quire boundaries.
    """
    def __init__(self):
        # Simplified quire mapping (8 folios per quire approx)
        # In reality Voynich quires vary, but for a structural proxy this is a start.
        pass

    def get_quire(self, folio_id: str) -> int:
        """
        Maps folio ID to a quire number.
        Simplified 8-folio rule.
        """
        try:
            num = int("".join([c for c in folio_id if c.isdigit()]))
            return (num - 1) // 8 + 1
        except:
            return 0

    def analyze_continuity(self, pages: Dict[str, List[List[str]]]) -> Dict[str, Any]:
        """
        6.2 Quire Boundary Discontinuity Test
        """
        quire_stats = defaultdict(list)
        for folio_id, lines in pages.items():
            q = self.get_quire(folio_id)
            if q == 0: continue
            
            # Simple metric: mean word length in quire
            word_lens = [len(w) for line in lines for w in line]
            if word_lens:
                quire_stats[q].append(np.mean(word_lens))
        
        # Calculate variance between quires vs within quires
        between_quire_means = [np.mean(vals) for vals in quire_stats.values() if vals]
        
        return {
            "num_quires": len(between_quire_means),
            "between_quire_variance": float(np.var(between_quire_means)) if between_quire_means else 0,
            "quire_means": {q: float(np.mean(v)) for q, v in quire_stats.items()}
        }
