"""
Mechanical Slip Cluster Analysis

Analyzes if slips are clustered in specific paragraphs or folios, 
indicating sustained mechanical misalignment.
"""

from collections import defaultdict
from typing import Any


class SlipClusterAnalyzer:
    """
    Groups slips by line proximity to identify sustained misalignment events.
    """
    def __init__(self, window_size: int = 10):
        self.window_size = window_size

    def analyze_clusters(self, slips: list[dict[str, Any]]) -> dict[str, Any]:
        if not slips:
            return {}

        # Group by line index
        line_to_slips = defaultdict(list)
        for s in slips:
            line_to_slips[s['line_index']].append(s)

        line_indices = sorted(line_to_slips.keys())
        clusters = []

        if not line_indices:
            return {}

        current_cluster = [line_indices[0]]

        for i in range(1, len(line_indices)):
            if line_indices[i] - line_indices[i-1] <= self.window_size:
                current_cluster.append(line_indices[i])
            else:
                if len(current_cluster) >= 3: # A cluster must have at least 3 lines with slips
                    clusters.append(current_cluster)
                current_cluster = [line_indices[i]]

        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        cluster_details = []
        for c in clusters:
            total_slips = sum(len(line_to_slips[l]) for l in c)
            cluster_details.append({
                "start_line": c[0],
                "end_line": c[-1],
                "num_affected_lines": len(c),
                "total_slips": total_slips,
                "density": total_slips / (c[-1] - c[0] + 1)
            })

        return {
            "num_clusters": len(clusters),
            "clusters": cluster_details
        }
