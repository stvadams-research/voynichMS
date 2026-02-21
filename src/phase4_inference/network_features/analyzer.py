"""
Method B: Network Features (Amancio et al. style)

Computes Word Adjacency Network (WAN) metrics and statistical distributions.
"""

import logging
from collections import Counter
from typing import Any

import networkx as nx
import numpy as np
from networkx.exception import NetworkXException

logger = logging.getLogger(__name__)

class NetworkAnalyzer:
    """
    Analyzes Word Adjacency Network (WAN) and statistical properties.
    """
    def __init__(self, max_tokens: int = 10000):
        # We limit the network size for performance during stress testing
        self.max_tokens = max_tokens

    def analyze(self, tokens: list[str]) -> dict[str, Any]:
        """
        Compute network and distribution features.
        """
        if not tokens:
            logger.warning("NetworkAnalyzer.analyze received no tokens")
            return {
                "status": "no_data",
                "metrics": {},
                "num_nodes": 0,
                "num_edges": 0,
                "avg_degree": 0.0,
                "avg_clustering": 0.0,
                "assortativity": 0.0,
                "zipf_alpha": 0.0,
                "vocabulary_size": 0,
                "ttr": 0.0,
            }

        # Limit scale for network metrics
        subset = tokens[:self.max_tokens]
        
        # 1. Build Graph
        G = nx.DiGraph()
        for i in range(len(subset) - 1):
            u, v = subset[i], subset[i+1]
            if G.has_edge(u, v):
                G[u][v]['weight'] += 1
            else:
                G.add_edge(u, v, weight=1)
                
        # 2. Network Metrics
        # Average Degree
        avg_degree = sum(dict(G.degree()).values()) / G.number_of_nodes() if G.number_of_nodes() > 0 else 0
        
        # Clustering Coefficient (Undirected version)
        G_undir = G.to_undirected()
        avg_clustering = nx.average_clustering(G_undir)
        
        # Assortativity (Degree correlation)
        try:
            assortativity = nx.degree_assortativity_coefficient(G)
        except (NetworkXException, ZeroDivisionError, ValueError):
            logger.warning(
                "Assortativity computation failed; using 0.0 fallback",
                exc_info=True,
            )
            assortativity = 0.0
            
        # 3. Distribution Metrics
        global_counts = Counter(tokens)
        frequencies = sorted(global_counts.values(), reverse=True)
        
        # Zipf Slope (Alpha) - simple linear regression on log-log
        # log(freq) = C - alpha * log(rank)
        ranks = np.arange(1, len(frequencies) + 1)
        log_ranks = np.log(ranks)
        log_freqs = np.log(frequencies)
        
        # Limit to top 500 ranks for Zipf fit.
        # Standard practice: ranks beyond ~500 are dominated by hapax legomena
        # and distort the power-law fit. Voynich vocabulary plateaus at ~450.
        # See governance/THRESHOLDS_RATIONALE.md for rationale.
        limit = min(500, len(frequencies))
        if limit > 5:
            slope, intercept = np.polyfit(log_ranks[:limit], log_freqs[:limit], 1)
            zipf_alpha = -slope
        else:
            zipf_alpha = 0.0
            
        return {
            "num_nodes": G.number_of_nodes(),
            "num_edges": G.number_of_edges(),
            "avg_degree": float(avg_degree),
            "avg_clustering": float(avg_clustering),
            "assortativity": float(assortativity),
            "zipf_alpha": float(zipf_alpha),
            "vocabulary_size": len(global_counts),
            "ttr": len(global_counts) / len(tokens) if tokens else 0.0 # Type-Token Ratio
        }
