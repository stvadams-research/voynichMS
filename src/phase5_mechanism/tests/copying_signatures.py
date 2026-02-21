"""
C5.COPY.1: Variant Family Clustering Test

Detects signatures of scribal copying by identifying local clusters of 
near-identical tokens (edit distance <= 1).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

class CopyingSignatureTest:
    """
    Analyzes local neighborhood for clusters of mutated tokens.
    """
    def __init__(self, window_size: int = 50, max_edit_dist: int = 1):
        self.window_size = window_size
        self.max_edit_dist = max_edit_dist

    def calculate_variant_clustering(self, tokens: list[str]) -> dict[str, Any]:
        """
        Measure frequency of near-duplicate neighbors.
        """
        if not tokens:
            return {}

        local_matches = 0
        total_pairs_checked = 0

        # O(N * window)
        for i in range(len(tokens)):
            target = tokens[i]
            # Look ahead in window
            for j in range(i + 1, min(i + self.window_size, len(tokens))):
                neighbor = tokens[j]

                # Check for near-identity
                # Simple optimization: skip if length difference > max_edit_dist
                if abs(len(target) - len(neighbor)) <= self.max_edit_dist:
                    if self._edit_distance(target, neighbor) <= self.max_edit_dist:
                        local_matches += 1

                total_pairs_checked += 1

        clustering_score = local_matches / len(tokens) if tokens else 0.0

        return {
            "num_tokens": len(tokens),
            "window_size": self.window_size,
            "local_variant_matches": local_matches,
            "clustering_score": clustering_score
        }

    def _edit_distance(self, s1: str, s2: str) -> int:
        """Simple Levenshtein distance implementation."""
        if len(s1) < len(s2):
            return self._edit_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]
