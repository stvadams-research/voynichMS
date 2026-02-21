"""
Sliding Residual Mapper

Maps 'Linguistic Tension' (z-scores) across the corpus to identify change points.
"""

import math
from collections import Counter
from typing import Any

import numpy as np


class SlidingResidualMapper:
    """
    Slides a window across the token stream and calculates the residual 
    deviation from the expected lattice entropy.
    """
    def __init__(self, window_size: int = 500, step_size: int = 100):
        self.window_size = window_size
        self.step_size = step_size

    def _calculate_entropy(self, tokens: list[str]) -> float:
        if not tokens:
            return 0.0
        counts = Counter(tokens)
        total = len(tokens)
        entropy = 0.0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)
        return entropy

    def map_corpus(self, tokens: list[str], folio_ids: list[str]) -> dict[str, Any]:
        """
        Produces a map of z-scores over the token stream.
        """
        n = len(tokens)
        results = []

        # Calculate global baseline for this run
        global_entropy = self._calculate_entropy(tokens)

        print(f"Mapping corpus ({n} tokens) with window={self.window_size}...")

        for start in range(0, n - self.window_size, self.step_size):
            end = start + self.window_size
            window_tokens = tokens[start:end]
            window_folios = list(set(folio_ids[start:end]))

            # Entropy residual
            local_entropy = self._calculate_entropy(window_tokens)
            residual = local_entropy - global_entropy

            results.append({
                "token_index": start,
                "folio_ids": window_folios,
                "residual": float(residual)
            })

        # Calculate z-scores of the residuals
        residuals = [r['residual'] for r in results]
        mean_r = np.mean(residuals)
        std_r = np.std(residuals)

        for r in results:
            r['z_score'] = float((r['residual'] - mean_r) / std_r) if std_r > 0 else 0.0

        # Detect Change Points (simple derivative threshold)
        change_points = []
        for i in range(1, len(results)):
            delta = abs(results[i]['z_score'] - results[i-1]['z_score'])
            if delta > 2.0: # Significant jump in tension
                change_points.append({
                    "token_index": results[i]['token_index'],
                    "folio_ids": results[i]['folio_ids'],
                    "magnitude": float(delta)
                })

        return {
            "window_size": self.window_size,
            "step_size": self.step_size,
            "global_entropy": float(global_entropy),
            "series": results,
            "change_points": change_points
        }
