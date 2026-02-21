"""
Dependency Scope Analysis Tools.
"""

import logging
import math
from collections import Counter, defaultdict
from typing import Any

from phase5_mechanism.dependency_scope.features import TokenFeatureExtractor

logger = logging.getLogger(__name__)

class DependencyScopeAnalyzer:
    """Measures predictive lift of features over nodes."""

    def __init__(self):
        self.extractor = TokenFeatureExtractor()

    def _calculate_conditional_entropy(self, successors_map: dict[Any, Counter]) -> float:
        """Helper to calculate H(S|Context)."""
        entropies = []
        weights = []
        for context, counts in successors_map.items():
            total = sum(counts.values())
            if total == 0:
                continue
            probs = [c / total for c in counts.values()]
            ent = -sum(p * math.log2(p) for p in probs if p > 0)
            entropies.append(ent)
            weights.append(total)

        if not weights:
            return 0.0
        return sum(e * w for e, w in zip(entropies, weights)) / sum(weights)

    def analyze_predictive_lift(self, lines: list[list[str]]) -> dict[str, Any]:
        """Compares successor entropy: H(S|Node) vs H(S|Node, Features)."""
        node_successors = defaultdict(Counter)
        node_feature_successors = defaultdict(Counter)

        for line in lines:
            for i in range(len(line) - 1):
                node = line[i]
                successor = line[i+1]
                feat = self.extractor.extract_features(node)
                feat_key = (node, feat['length'], feat['suffix_1'])

                node_successors[node][successor] += 1
                node_feature_successors[feat_key][successor] += 1

        h_node = self._calculate_conditional_entropy(node_successors)
        h_feat = self._calculate_conditional_entropy(node_feature_successors)
        lift = h_node - h_feat

        return {
            "h_node": float(h_node),
            "h_node_feat": float(h_feat),
            "predictive_lift": float(lift),
            "rel_lift": float(lift / h_node) if h_node > 0 else 0.0
        }

    def analyze_equivalence_splitting(self, lines: list[list[str]]) -> dict[str, Any]:
        """Tests if identical words split into distinct classes based on position."""
        node_successors = defaultdict(Counter)
        pos_node_successors = defaultdict(Counter)

        for line in lines:
            for i in range(len(line) - 1):
                node = line[i]
                successor = line[i+1]
                pos_key = (node, i)

                node_successors[node][successor] += 1
                pos_node_successors[pos_key][successor] += 1

        h_node = self._calculate_conditional_entropy(node_successors)
        h_pos = self._calculate_conditional_entropy(pos_node_successors)
        lift = h_node - h_pos

        return {
            "h_node": float(h_node),
            "h_node_pos": float(h_pos),
            "pos_predictive_lift": float(lift),
            "pos_rel_lift": float(lift / h_node) if h_node > 0 else 0.0
        }
