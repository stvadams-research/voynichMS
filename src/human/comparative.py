"""
Comparative Artifact Analysis

Situates the Voynich Manuscript within a broader class of formal systems.
Phase 7C implementation.
"""

import numpy as np
from collections import Counter, defaultdict
from typing import List, Dict, Any, Tuple

class ComparativeAnalyzer:
    """
    Analyzes structural fingerprints of different corpora to situate Voynich.
    """
    def __init__(self):
        pass

    def calculate_fingerprint(self, lines: List[List[str]]) -> Dict[str, Any]:
        """
        Calculates the structural fingerprint of a corpus.
        """
        if not lines:
            return {}

        # 1. TTR
        tokens = [t for line in lines for t in line]
        unique_tokens = len(set(tokens))
        ttr = unique_tokens / len(tokens) if tokens else 0

        # 2. Determinism (Successor Entropy)
        # We use (Prev, Curr, Pos) as state context
        context_map = defaultdict(Counter)
        for line in lines:
            for i in range(len(line) - 1):
                prev = line[i-1] if i > 0 else "<START>"
                curr = line[i]
                nxt = line[i+1]
                context_map[(prev, curr, i)][nxt] += 1
        
        entropies = []
        weights = []
        for nxts in context_map.values():
            total = sum(nxts.values())
            probs = np.array([count / total for count in nxts.values()])
            ent = -np.sum(probs * np.log2(probs))
            entropies.append(ent)
            weights.append(total)
            
        avg_entropy = np.average(entropies, weights=weights) if entropies else 0
        determinism = 1.0 / (1.0 + avg_entropy) # Higher = more deterministic

        # 3. Sparsity (Hapax ratio of states)
        unique_states = len(context_map)
        total_visits = sum(weights)
        hapax_states = sum(1 for nxts in context_map.values() if sum(nxts.values()) == 1)
        sparsity = hapax_states / unique_states if unique_states > 0 else 0

        # 4. Novelty Convergence (Slope of novelty curve)
        seen_states = set()
        chunk_size = 100
        novelty_rates = []
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i+chunk_size]
            chunk_states = []
            for line in chunk:
                for j in range(len(line)):
                    p = line[j-1] if j > 0 else "<START>"
                    chunk_states.append((p, line[j], j))
            
            if not chunk_states: continue
            new_count = 0
            for s in chunk_states:
                if s not in seen_states:
                    new_count += 1
                    seen_states.add(s)
            novelty_rates.append(new_count / len(chunk_states))
        
        # Convergence = (initial - final) / initial
        if len(novelty_rates) > 1:
            convergence = (novelty_rates[0] - novelty_rates[-1]) / novelty_rates[0]
        else:
            convergence = 0

        return {
            "ttr": float(ttr),
            "determinism": float(determinism),
            "sparsity": float(sparsity),
            "convergence": float(convergence)
        }

    def compute_distance(self, f1: Dict[str, float], f2: Dict[str, float]) -> float:
        """
        Euclidean distance between fingerprints.
        """
        keys = ["ttr", "determinism", "sparsity", "convergence"]
        v1 = np.array([f1.get(k, 0) for k in keys])
        v2 = np.array([f2.get(k, 0) for k in keys])
        return float(np.linalg.norm(v1 - v2))
