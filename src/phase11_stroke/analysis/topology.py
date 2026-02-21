"""
Stroke Topology Analysis (Fractal Lattice Test)

Adapts Phase 5 mechanism discrimination (Lattice vs DAG) to the sub-glyph scale.
Tests whether word-level production rules are recursively present at the character level.
"""

import logging
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from phase11_stroke.schema import StrokeSchema

logger = logging.getLogger(__name__)

class StrokeTopologyAnalyzer:
    """
    Computes signatures designed to distinguish topologies at the sub-glyph scale.
    Treats words as 'lines' and characters as 'tokens'.
    """
    def __init__(self, schema: StrokeSchema | None = None, prefix_len: int = 2):
        self.schema = schema or StrokeSchema()
        self.prefix_len = prefix_len
        # Map characters to feature classes for 'token' identity at stroke scale
        table = self.schema.feature_table()
        feature_matrix = np.array([table[char] for char in self.schema.char_inventory()], dtype=np.float64)
        _, inverse = np.unique(feature_matrix, axis=0, return_inverse=True)
        self.char_to_class = {char: int(idx) for char, idx in zip(self.schema.char_inventory(), inverse)}

    def _to_classes(self, word: str) -> list[int]:
        """Converts a word to a sequence of stroke feature class IDs."""
        return [self.char_to_class[c] for c in word if c in self.char_to_class]

    def analyze_overlap(self, words: list[str]) -> dict[str, Any]:
        """Calculates prefix collision rates at the word-start level."""
        class_words = [self._to_classes(w) for w in words]
        prefixes = [tuple(w[:self.prefix_len]) for w in class_words if len(w) >= self.prefix_len]
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

    def analyze_coverage(self, words: list[str]) -> dict[str, Any]:
        """Measures uniformity of stroke-class visitation (Gini coefficient)."""
        all_classes = []
        for w in words:
            all_classes.extend(self._to_classes(w))
            
        counts = Counter(all_classes)
        freqs = sorted(counts.values())
        
        if not freqs:
            return {"gini_coefficient": 0.0}
            
        n = len(freqs)
        index = np.arange(1, n + 1)
        # Gini Coefficient formula
        gini = (np.sum((2 * index - n - 1) * freqs)) / (n * np.sum(freqs))
        
        return {
            "unique_classes_visited": len(counts),
            "gini_coefficient": float(gini),
            "mean_visitation": float(np.mean(freqs)) if freqs else 0.0
        }

    def analyze_convergence(self, words: list[str]) -> dict[str, Any]:
        """Measures convergence of stroke transitions within words."""
        context_successors = defaultdict(Counter)
        for w in words:
            classes = self._to_classes(w)
            for i in range(len(classes) - 1):
                context = classes[i]
                successor = classes[i+1]
                context_successors[context][successor] += 1
                
        out_degrees = [len(s) for s in context_successors.values()]
        avg_out_degree = sum(out_degrees) / len(out_degrees) if out_degrees else 0.0
        
        return {
            "avg_successor_convergence": float(avg_out_degree),
            "max_successor_fanout": int(max(out_degrees)) if out_degrees else 0
        }

    def run_fractal_lattice_test(self, words: list[str]) -> dict[str, Any]:
        """Performs the full suite of fractal lattice tests."""
        overlap = self.analyze_overlap(words)
        coverage = self.analyze_coverage(words)
        convergence = self.analyze_convergence(words)
        
        # Identification Logic (mirrors Phase 5G)
        # High convergence and high skew (Gini) favor Implicit Lattice over DAG
        is_lattice_like = convergence["avg_successor_convergence"] < 2.0 and coverage["gini_coefficient"] > 0.5
        
        return {
            "overlap": overlap,
            "coverage": coverage,
            "convergence": convergence,
            "is_lattice_like": bool(is_lattice_like),
            "scale": "sub-glyph"
        }
