"""
Topology-Sensitive Signatures

Analyzes path overlap, coverage uniformity, and successor convergence.
"""

import logging
from collections import Counter, defaultdict
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class TopologySignatureAnalyzer:
    """
    Computes signatures designed to distinguish large-object topologies.
    """
    def __init__(self, prefix_len: int = 2):
        self.prefix_len = prefix_len

    def analyze_overlap(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        Calculates prefix collision rates.
        """
        prefixes = [tuple(l[:self.prefix_len]) for l in lines if len(l) >= self.prefix_len]
        counts = Counter(prefixes)

        total_prefixes = len(prefixes)
        num_collisions = sum(1 for c in counts.values() if c > 1)
        collision_rate = num_collisions / total_prefixes if total_prefixes > 0 else 0.0

        return {
            "total_prefixes": total_prefixes,
            "unique_prefixes": len(counts),
            "collision_rate": float(collision_rate),
            "max_collision_depth": int(counts.most_common(1)[0][1]) if counts else 0
        }

    def analyze_coverage(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        Measures uniformity of node visitation (Gini coefficient).
        """
        all_tokens = [t for l in lines for t in l]
        counts = Counter(all_tokens)
        freqs = sorted(counts.values())

        # Gini Coefficient: 0 = perfect equality, 1 = maximum inequality
        if not freqs:
            return {"gini": 0.0}

        n = len(freqs)
        index = np.arange(1, n + 1)
        gini = (np.sum((2 * index - n - 1) * freqs)) / (n * np.sum(freqs))

        return {
            "unique_nodes_visited": len(counts),
            "gini_coefficient": float(gini),
            "mean_visitation": float(np.mean(freqs))
        }

    def analyze_convergence(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        Measures how often distinct paths converge on the same successor.
        """
        # Successor consistency for recurring contexts
        context_successors = defaultdict(Counter)
        for line in lines:
            for i in range(len(line) - 1):
                context = line[i]
                successor = line[i+1]
                context_successors[context][successor] += 1

        # Convergence: average number of unique successors per node
        out_degrees = [len(s) for s in context_successors.values()]
        avg_out_degree = sum(out_degrees) / len(out_degrees) if out_degrees else 0.0

        return {
            "avg_successor_convergence": float(avg_out_degree),
            "max_successor_fanout": int(max(out_degrees)) if out_degrees else 0
        }
