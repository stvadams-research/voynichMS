"""
Efficiency and Optimization Metrics

Implementation of metrics for Phase 6B:
- Reuse Suppression Index
- Path Length Efficiency
- Redundancy Avoidance
- Compression Opportunity
"""

import logging
import zlib
from collections import Counter
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

class EfficiencyAnalyzer:
    """
    Analyzes optimization pressure and efficiency in a corpus.
    """
    def __init__(self):
        pass

    def calculate_reuse_suppression(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.1 Reuse Suppression Index
        Measures whether the system actively suppresses reuse.
        """
        states = []
        for line in lines:
            for i, token in enumerate(line):
                prev = line[i-1] if i > 0 else "<START>"
                states.append((prev, token, i))

        counts = Counter(states)
        total_visits = len(states)
        unique_states = len(counts)

        # Entropy of state distribution
        freqs = np.array(list(counts.values()))
        probs = freqs / total_visits
        entropy = -np.sum(probs * np.log2(probs))
        max_entropy = np.log2(unique_states) if unique_states > 0 else 0

        suppression_index = entropy / max_entropy if max_entropy > 0 else 0

        return {
            "total_visits": total_visits,
            "unique_states": unique_states,
            "state_entropy": float(entropy),
            "reuse_suppression_index": float(suppression_index)
        }

    def calculate_path_efficiency(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.2 Path Length Efficiency
        Mean path length per unique node visited.
        """
        total_tokens = sum(len(line) for line in lines)
        unique_tokens = len(set(token for line in lines for token in line))

        efficiency = unique_tokens / total_tokens if total_tokens > 0 else 0

        return {
            "total_tokens": total_tokens,
            "unique_tokens": unique_tokens,
            "tokens_per_unique": float(total_tokens / unique_tokens) if unique_tokens > 0 else 0,
            "path_efficiency": float(efficiency)
        }

    def calculate_redundancy_cost(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.3 Redundancy Avoidance vs Cost
        Cost proxy = rule evaluations per unique output.
        """
        unique_lines = set(tuple(line) for line in lines)
        total_lines = len(lines)

        redundancy_rate = (total_lines - len(unique_lines)) / total_lines if total_lines > 0 else 0

        return {
            "total_lines": total_lines,
            "unique_lines": len(unique_lines),
            "redundancy_rate": float(redundancy_rate),
            "cost_per_unique_line": float(total_lines / len(unique_lines)) if unique_lines else 0
        }

    def calculate_compressibility(self, lines: list[list[str]]) -> dict[str, Any]:
        """
        4.4 Compression Opportunity Test
        Compression ratio under structure-preserving encodings.
        """
        text = "\n".join([" ".join(line) for line in lines])
        raw_bytes = text.encode('utf-8')
        compressed_bytes = zlib.compress(raw_bytes)

        ratio = len(compressed_bytes) / len(raw_bytes) if raw_bytes else 1.0

        return {
            "raw_size": len(raw_bytes),
            "compressed_size": len(compressed_bytes),
            "compression_ratio": float(ratio)
        }

    def run_efficiency_audit(self, lines: list[list[str]]) -> dict[str, Any]:
        return {
            "reuse_suppression": self.calculate_reuse_suppression(lines),
            "path_efficiency": self.calculate_path_efficiency(lines),
            "redundancy_cost": self.calculate_redundancy_cost(lines),
            "compressibility": self.calculate_compressibility(lines)
        }
